import asyncio
import subprocess
import os
import signal
import threading
import time
import psutil
import structlog
from app.db.connections import get_platform_db, _connect
from app.config import PLATFORM_DB_PATH, MAX_CONCURRENT_AGENTS, AGENT_TIMEOUT_MINUTES, USE_AGENT_SDK
from app.services.collaboration_context import auto_capture_output, build_knowledge_context, build_coco_context, build_yolo_constraints
from app.services.event_bus import event_bus

log = structlog.get_logger()


class ProcessManager:
    def __init__(self):
        self._processes: dict[str, subprocess.Popen] = {}
        self._readers: dict[str, threading.Thread] = {}
        self._agent_meta: dict[str, dict] = {}  # agent_id -> {node_id, role}
        self._spawn_lock = threading.Lock()
        self._concurrency_semaphore = threading.Semaphore(MAX_CONCURRENT_AGENTS)
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None

    def start_heartbeat(self):
        """Start the background heartbeat loop that detects crashed agents."""
        if self._heartbeat_thread is not None:
            return
        self._heartbeat_stop.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name="agent-heartbeat"
        )
        self._heartbeat_thread.start()
        log.info("heartbeat_started", interval_seconds=30)

    def stop_heartbeat(self):
        """Signal the heartbeat loop to stop."""
        self._heartbeat_stop.set()
        self._heartbeat_thread = None

    def _heartbeat_loop(self):
        """Runs every 30 seconds checking for crashed agents."""
        while not self._heartbeat_stop.is_set():
            try:
                self._heartbeat_check()
            except Exception as e:
                log.error("heartbeat_check_error", error=str(e))
            self._heartbeat_stop.wait(timeout=30)

    def _heartbeat_check(self):
        """Query all running agents and mark dead ones as failed."""
        try:
            with get_platform_db() as db:
                rows = db.execute(
                    "SELECT id, pid FROM agents WHERE status = 'running'"
                ).fetchall()
                updated = 0
                for row in rows:
                    agent_id = row["id"]
                    pid = row["pid"]
                    if pid is None:
                        db.execute(
                            "UPDATE agents SET status = 'failed', stopped_at = datetime('now') WHERE id = ?",
                            (agent_id,),
                        )
                        updated += 1
                        log.warning("heartbeat_no_pid", agent_id=agent_id)
                        event_bus.emit("agent.failed", {"agent_id": agent_id, "status": "failed", "reason": "no_pid"})
                        continue
                    # Also check in-memory process handle first (more reliable)
                    proc = self._processes.get(agent_id)
                    if proc is not None:
                        if proc.poll() is None:
                            continue  # still alive
                        # Process finished but reader thread hasn't cleaned up yet — skip,
                        # the reader thread will handle status update
                        continue
                    # No in-memory handle — check via OS
                    try:
                        os.kill(pid, 0)
                    except OSError:
                        db.execute(
                            "UPDATE agents SET status = 'failed', stopped_at = datetime('now') WHERE id = ?",
                            (agent_id,),
                        )
                        updated += 1
                        log.warning("heartbeat_dead_agent", agent_id=agent_id, pid=pid)
                        event_bus.emit("agent.failed", {"agent_id": agent_id, "status": "failed", "reason": "process_dead"})
                        # Release semaphore for the dead agent
                        self._concurrency_semaphore.release()
                if updated:
                    db.commit()
                    log.info("heartbeat_cleaned", count=updated)
        except Exception as e:
            log.error("heartbeat_check_failed", error=str(e))

    def reconcile_on_startup(self):
        """Check for orphaned agents from a previous session and mark dead ones as failed."""
        try:
            with get_platform_db() as db:
                rows = db.execute(
                    "SELECT id, pid FROM agents WHERE status IN ('running', 'paused')"
                ).fetchall()
                for row in rows:
                    agent_id = row["id"]
                    pid = row["pid"]
                    if pid is None:
                        db.execute(
                            "UPDATE agents SET status = 'failed', stopped_at = datetime('now') WHERE id = ?",
                            (agent_id,),
                        )
                        log.warning("orphaned_agent_no_pid", agent_id=agent_id)
                        continue
                    try:
                        os.kill(pid, 0)
                        log.warning("agent_still_running", agent_id=agent_id, pid=pid,
                                    msg=f"Agent {agent_id} still running from previous session, PID {pid}")
                    except OSError:
                        db.execute(
                            "UPDATE agents SET status = 'failed', stopped_at = datetime('now') WHERE id = ?",
                            (agent_id,),
                        )
                        log.info("orphaned_agent_cleaned", agent_id=agent_id, pid=pid)
                db.commit()
        except Exception as e:
            log.error("reconcile_on_startup_failed", error=str(e))

    def spawn(self, agent_id: str, task: str, cwd: str | None = None, model: str = "sonnet",
              node_id: str | None = None, role: str | None = None,
              yolo_mode: bool = False) -> int:
        """Spawn a claude agent. Returns PID (or 0 for SDK-based agents).

        Uses a threading semaphore to enforce the concurrent agent limit.
        The semaphore is acquired before spawn and released when the agent
        finishes (in _read_output or _run_sdk_agent).
        """
        acquired = self._concurrency_semaphore.acquire(blocking=False)
        if not acquired:
            raise RuntimeError(f"Max {MAX_CONCURRENT_AGENTS} concurrent agents")

        # Build context prefix for the agent
        context_parts: list[str] = []

        # CoCo brain context
        if node_id:
            brain_ctx = build_coco_context(node_id)
            if brain_ctx:
                context_parts.append(brain_ctx)

        # YOLO constraints
        if yolo_mode:
            project_id = None
            if node_id:
                try:
                    with get_platform_db() as db:
                        row = db.execute(
                            "SELECT project_id FROM tree_nodes WHERE id = ?", (node_id,)
                        ).fetchone()
                        if row:
                            project_id = row["project_id"]
                except Exception:
                    pass
            yolo_ctx = build_yolo_constraints(project_id)
            if yolo_ctx:
                context_parts.append(yolo_ctx)

        # Prepend context to task
        if context_parts:
            context_block = "\n\n---\n\n".join(context_parts)
            task = f"{context_block}\n\n---\n\nTASK:\n{task}"

        # --- SDK path ---
        if USE_AGENT_SDK:
            from app.services.agent_sdk_client import agent_sdk
            if agent_sdk.is_available():
                self._agent_meta[agent_id] = {"node_id": node_id, "role": role or "custom"}
                sdk_thread = threading.Thread(
                    target=self._run_sdk_agent_sync,
                    args=(agent_id, task, model, node_id, role),
                    daemon=True,
                    name=f"sdk-agent-{agent_id[:8]}",
                )
                sdk_thread.start()
                self._readers[agent_id] = sdk_thread
                return 0

        # --- Subprocess path (fallback) ---
        with self._spawn_lock:

            # Store metadata for auto-capture on completion
            self._agent_meta[agent_id] = {"node_id": node_id, "role": role or "custom"}

            # Minimal environment whitelist to avoid leaking secrets
            _ALLOWED_ENV_KEYS = {
                "HOME", "PATH", "USER", "SHELL", "TERM", "LANG",
                "ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "XDG_CONFIG_HOME",
            }
            env = {k: v for k, v in os.environ.items()
                   if k in _ALLOWED_ENV_KEYS or k.startswith("CLAUDE_")}
            env.pop("CLAUDE_CODE_ENTRYPOINT", None)

            # Inject knowledge context into the task prompt
            enriched_task = task
            try:
                # Resolve project_id from node_id
                kc_project_id = None
                if node_id:
                    with get_platform_db() as db:
                        nrow = db.execute(
                            "SELECT hub_project_id FROM nodes WHERE id = ?", (node_id,)
                        ).fetchone()
                        if nrow and nrow["hub_project_id"]:
                            kc_project_id = nrow["hub_project_id"]

                knowledge_ctx = build_knowledge_context(
                    node_id=node_id, project_id=kc_project_id, token_budget=2000
                )
                if knowledge_ctx:
                    enriched_task = f"{knowledge_ctx}\n\n---\n\n{task}"
            except Exception as e:
                log.debug("knowledge_context_injection_skipped", agent_id=agent_id, error=str(e))

            cmd = ["claude", "-p", "--output-format", "stream-json"]
            if model:
                cmd.extend(["--model", model])
            cmd.append(enriched_task)

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd or os.environ["HOME"],
                env=env,
            )
            self._processes[agent_id] = proc

        # Start output reader thread (outside lock — doesn't affect count)
        reader = threading.Thread(target=self._read_output, args=(agent_id, proc), daemon=True)
        reader.start()
        self._readers[agent_id] = reader

        return proc.pid

    def _run_sdk_agent_sync(self, agent_id: str, task: str, model: str,
                            node_id: str | None, role: str | None):
        """Run an SDK agent call in a new asyncio event loop (called from a thread)."""
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self._run_sdk_agent(agent_id, task, model, node_id, role))
        finally:
            loop.close()

    async def _run_sdk_agent(self, agent_id: str, task: str, model: str,
                             node_id: str | None, role: str | None):
        """Async SDK agent execution with output recording and cost tracking."""
        from app.services.agent_sdk_client import agent_sdk

        status = "completed"
        exit_code = 0
        try:
            result = await asyncio.wait_for(
                agent_sdk.spawn_agent(task=task, model=model, max_tokens=16384),
                timeout=AGENT_TIMEOUT_MINUTES * 60,
            )

            content = result.get("content", "")
            input_tokens = result.get("input_tokens", 0)
            output_tokens = result.get("output_tokens", 0)
            response_model = result.get("model", model)

            # Write output chunks to agent_output
            with get_platform_db() as db:
                # Write content in reasonable chunks (by paragraph)
                chunks = content.split("\n\n") if content else ["(no output)"]
                for chunk in chunks:
                    if chunk.strip():
                        db.execute(
                            "INSERT INTO agent_output (agent_id, stream, chunk) VALUES (?, 'stdout', ?)",
                            (agent_id, chunk),
                        )
                db.execute(
                    "UPDATE agents SET last_heartbeat = datetime('now') WHERE id = ?",
                    (agent_id,),
                )
                db.commit()

            # Record cost
            from app.services.agent_sdk_client import record_sdk_cost
            record_sdk_cost(
                model=response_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                source="agent",
                agent_id=agent_id,
                node_id=node_id,
            )

        except asyncio.TimeoutError:
            log.warning("sdk_agent_timeout", agent_id=agent_id)
            status = "failed"
            exit_code = -1
        except Exception as e:
            log.warning("sdk_agent_error", agent_id=agent_id, error=str(e))
            status = "failed"
            exit_code = -1
        finally:
            # Update agent status
            with get_platform_db() as db:
                db.execute(
                    "UPDATE agents SET status = ?, exit_code = ?, stopped_at = datetime('now') WHERE id = ?",
                    (status, exit_code, agent_id),
                )
                db.execute(
                    "DELETE FROM agent_output WHERE agent_id = ? AND id NOT IN "
                    "(SELECT id FROM agent_output WHERE agent_id = ? ORDER BY id DESC LIMIT 1000)",
                    (agent_id, agent_id),
                )
                db.commit()

            # Emit event bus notification
            event_bus.emit(f"agent.{status}", {
                "agent_id": agent_id,
                "status": status,
                "exit_code": exit_code,
            })

            # Auto-capture output for collaboration
            if status == "completed":
                meta = self._agent_meta.get(agent_id, {})
                cap_node_id = meta.get("node_id")
                cap_role = meta.get("role", "custom")
                if cap_node_id:
                    try:
                        auto_capture_output(agent_id, cap_role, cap_node_id)
                    except Exception as e:
                        log.warning("sdk_auto_capture_failed", agent_id=agent_id, error=str(e))

            # Check analysis job completion
            try:
                self._check_analysis_job_completion(agent_id, status)
            except Exception as e:
                log.warning("sdk_analysis_job_check_failed", agent_id=agent_id, error=str(e))

            # Check self-improve cycle
            try:
                self._check_self_improve_agent(agent_id, status)
            except Exception as e:
                log.warning("sdk_self_improve_check_failed", agent_id=agent_id, error=str(e))

            # Release concurrency semaphore
            self._concurrency_semaphore.release()

            # Clean up metadata
            self._agent_meta.pop(agent_id, None)

    def _read_output(self, agent_id: str, proc: subprocess.Popen):
        """Read stdout and store in platform.db"""
        timed_out = False
        try:
            start_time = time.monotonic()
            timeout_seconds = AGENT_TIMEOUT_MINUTES * 60
            batch: list[str] = []
            last_commit = time.monotonic()
            db = _connect(PLATFORM_DB_PATH, read_only=False)
            try:
                for line in iter(proc.stdout.readline, b''):
                    # Check timeout
                    elapsed = time.monotonic() - start_time
                    if elapsed > timeout_seconds:
                        log.warning("agent_timeout", agent_id=agent_id, elapsed_minutes=round(elapsed / 60, 1))
                        proc.terminate()
                        try:
                            proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                        timed_out = True
                        break

                    text = line.decode('utf-8', errors='replace').rstrip()
                    if text:
                        db.execute(
                            "INSERT INTO agent_output (agent_id, stream, chunk) VALUES (?, 'stdout', ?)",
                            (agent_id, text)
                        )
                        batch.append(text)

                        # Batch commits: every 10 lines or every 2 seconds
                        now = time.monotonic()
                        if len(batch) >= 10 or (now - last_commit) >= 2.0:
                            db.execute(
                                "UPDATE agents SET last_heartbeat = datetime('now') WHERE id = ?",
                                (agent_id,)
                            )
                            db.commit()
                            batch.clear()
                            last_commit = now

                # Flush remaining batch
                if batch:
                    db.execute(
                        "UPDATE agents SET last_heartbeat = datetime('now') WHERE id = ?",
                        (agent_id,)
                    )
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            log.warning("agent_output_read_error", agent_id=agent_id, error=str(e))
        finally:
            if timed_out:
                exit_code = proc.poll() or -1
            else:
                exit_code = proc.wait()
            with get_platform_db() as db:
                status = 'failed' if timed_out else ('completed' if exit_code == 0 else 'failed')
                db.execute(
                    "UPDATE agents SET status = ?, exit_code = ?, stopped_at = datetime('now') WHERE id = ?",
                    (status, exit_code, agent_id)
                )
                # Keep only last 1000 lines per agent
                db.execute(
                    "DELETE FROM agent_output WHERE agent_id = ? AND id NOT IN "
                    "(SELECT id FROM agent_output WHERE agent_id = ? ORDER BY id DESC LIMIT 1000)",
                    (agent_id, agent_id)
                )
                db.commit()

            # Emit event bus notification for real-time SSE
            event_name = f"agent.{status}"  # agent.completed or agent.failed
            event_bus.emit(event_name, {
                "agent_id": agent_id,
                "status": status,
                "exit_code": exit_code,
            })

            # Auto-capture output as project_context for team collaboration
            if status == 'completed':
                meta = self._agent_meta.get(agent_id, {})
                node_id = meta.get("node_id")
                role = meta.get("role", "custom")
                if node_id:
                    try:
                        auto_capture_output(agent_id, role, node_id)
                    except Exception as e:
                        log.warning("auto_capture_failed", agent_id=agent_id, error=str(e))

            # Check if this agent belongs to an analysis job and update job status
            try:
                self._check_analysis_job_completion(agent_id, status)
            except Exception as e:
                log.warning("analysis_job_check_failed", agent_id=agent_id, error=str(e))

            # Check if this agent belongs to a self-improve cycle
            try:
                self._check_self_improve_agent(agent_id, status)
            except Exception as e:
                log.warning("self_improve_check_failed", agent_id=agent_id, error=str(e))

            # Release concurrency semaphore so another agent can spawn
            self._concurrency_semaphore.release()

            # Clean up metadata
            self._agent_meta.pop(agent_id, None)

    def pause(self, agent_id: str):
        proc = self._processes.get(agent_id)
        if proc and proc.poll() is None:
            os.kill(proc.pid, signal.SIGSTOP)

    def resume(self, agent_id: str):
        proc = self._processes.get(agent_id)
        if proc and proc.poll() is None:
            os.kill(proc.pid, signal.SIGCONT)

    def kill(self, agent_id: str):
        proc = self._processes.get(agent_id)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    def is_alive(self, agent_id: str) -> bool:
        proc = self._processes.get(agent_id)
        return proc is not None and proc.poll() is None

    def _check_self_improve_agent(self, agent_id: str, agent_status: str):
        """Check if this agent belongs to a self-improve cycle and notify the service."""
        with get_platform_db() as db:
            row = db.execute(
                "SELECT agent_id FROM self_improve_agents WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()
            if not row:
                return

        # Import here to avoid circular imports at module level
        from app.services.self_improve import self_improve_service
        self_improve_service.on_agent_completed(agent_id, agent_status)

    def _check_analysis_job_completion(self, agent_id: str, agent_status: str):
        """Check if this agent's completion should update an analysis job."""
        import json

        with get_platform_db() as db:
            # Find running analysis jobs that include this agent
            jobs = db.execute(
                "SELECT id, agent_ids FROM analysis_jobs WHERE status = 'running'"
            ).fetchall()

            for job in jobs:
                agent_ids = json.loads(job["agent_ids"] or "[]")
                if agent_id not in agent_ids:
                    continue

                # Check if all agents in this job are done
                all_done = True
                any_failed = False
                for aid in agent_ids:
                    row = db.execute(
                        "SELECT status FROM agents WHERE id = ?", (aid,)
                    ).fetchone()
                    if not row:
                        continue
                    s = row["status"]
                    if s in ("running", "paused"):
                        all_done = False
                        break
                    if s in ("failed", "killed"):
                        any_failed = True

                if all_done:
                    # Build results summary from all agent outputs
                    summaries: list[str] = []
                    for aid in agent_ids:
                        agent_row = db.execute(
                            "SELECT name, role FROM agents WHERE id = ?", (aid,)
                        ).fetchone()
                        output_rows = db.execute(
                            "SELECT chunk FROM agent_output WHERE agent_id = ? ORDER BY id DESC LIMIT 50",
                            (aid,),
                        ).fetchall()
                        if output_rows and agent_row:
                            role_label = (agent_row["role"] or "agent").replace("-", " ").title()
                            output_text = "\n".join(r["chunk"] for r in reversed(output_rows))
                            summaries.append(f"## {role_label} ({agent_row['name']})\n\n{output_text}")

                    results_summary = "\n\n---\n\n".join(summaries) if summaries else "No output captured."
                    final_status = "completed" if not any_failed else "failed"

                    db.execute(
                        """UPDATE analysis_jobs
                           SET status = ?, results_summary = ?, completed_at = datetime('now')
                           WHERE id = ?""",
                        (final_status, results_summary, job["id"]),
                    )
                    db.commit()
                    log.info("analysis_job_completed", job_id=job["id"], agent_count=len(agent_ids))


process_manager = ProcessManager()
