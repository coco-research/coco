import asyncio
import subprocess
import os
import signal
import threading
import time
import psutil
import structlog
from app.db.session import get_db
from app.db.engine import engine
from app.config import MAX_CONCURRENT_AGENTS, AGENT_TIMEOUT_MINUTES, USE_AGENT_SDK
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
            with get_db() as conn:
                rows = conn.exec_driver_sql(
                    "SELECT id, pid FROM agents WHERE status = 'running'"
                ).fetchall()
                updated = 0
                for row in rows:
                    rm = row._mapping
                    agent_id = rm["id"]
                    pid = rm["pid"]
                    if pid is None:
                        conn.exec_driver_sql(
                            "UPDATE agents SET status = 'failed', stopped_at = datetime('now') WHERE id = ?",
                            (agent_id,),
                        )
                        updated += 1
                        log.warning("heartbeat_no_pid", agent_id=agent_id)
                        event_bus.emit("agent.failed", {"agent_id": agent_id, "status": "failed", "reason": "no_pid"})
                        continue
                    proc = self._processes.get(agent_id)
                    if proc is not None:
                        if proc.poll() is None:
                            continue
                        continue
                    try:
                        os.kill(pid, 0)
                    except OSError:
                        conn.exec_driver_sql(
                            "UPDATE agents SET status = 'failed', stopped_at = datetime('now') WHERE id = ?",
                            (agent_id,),
                        )
                        updated += 1
                        log.warning("heartbeat_dead_agent", agent_id=agent_id, pid=pid)
                        event_bus.emit("agent.failed", {"agent_id": agent_id, "status": "failed", "reason": "process_dead"})
                        self._concurrency_semaphore.release()
                if updated:
                    log.info("heartbeat_cleaned", count=updated)
        except Exception as e:
            log.error("heartbeat_check_failed", error=str(e))

    def reconcile_on_startup(self):
        """Check for orphaned agents from a previous session and mark dead ones as failed."""
        try:
            with get_db() as conn:
                rows = conn.exec_driver_sql(
                    "SELECT id, pid FROM agents WHERE status IN ('running', 'paused')"
                ).fetchall()
                for row in rows:
                    rm = row._mapping
                    agent_id = rm["id"]
                    pid = rm["pid"]
                    if pid is None:
                        conn.exec_driver_sql(
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
                        conn.exec_driver_sql(
                            "UPDATE agents SET status = 'failed', stopped_at = datetime('now') WHERE id = ?",
                            (agent_id,),
                        )
                        log.info("orphaned_agent_cleaned", agent_id=agent_id, pid=pid)
        except Exception as e:
            log.error("reconcile_on_startup_failed", error=str(e))

    def spawn(self, agent_id: str, task: str, cwd: str | None = None, model: str = "sonnet",
              node_id: str | None = None, role: str | None = None,
              yolo_mode: bool = False) -> int:
        """Spawn a claude agent. Returns PID (or 0 for SDK-based agents)."""
        acquired = self._concurrency_semaphore.acquire(blocking=False)
        if not acquired:
            raise RuntimeError(f"Max {MAX_CONCURRENT_AGENTS} concurrent agents")

        # Build context prefix for the agent
        context_parts: list[str] = []

        if node_id:
            brain_ctx = build_coco_context(node_id)
            if brain_ctx:
                context_parts.append(brain_ctx)

        if yolo_mode:
            project_id = None
            if node_id:
                try:
                    with get_db() as conn:
                        row = conn.exec_driver_sql(
                            "SELECT project_id FROM tree_nodes WHERE id = ?", (node_id,)
                        ).fetchone()
                        if row:
                            project_id = row._mapping["project_id"]
                except Exception:
                    pass
            yolo_ctx = build_yolo_constraints(project_id)
            if yolo_ctx:
                context_parts.append(yolo_ctx)

        try:
            kc_project_id = None
            if node_id:
                with get_db() as conn:
                    nrow = conn.exec_driver_sql(
                        "SELECT hub_project_id FROM nodes WHERE id = ?", (node_id,)
                    ).fetchone()
                    if nrow and nrow._mapping["hub_project_id"]:
                        kc_project_id = nrow._mapping["hub_project_id"]

            knowledge_ctx = build_knowledge_context(
                node_id=node_id, project_id=kc_project_id, token_budget=2000
            )
            if knowledge_ctx:
                context_parts.append(knowledge_ctx)
        except Exception as e:
            log.debug("knowledge_context_injection_skipped", agent_id=agent_id, error=str(e))

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
            self._agent_meta[agent_id] = {"node_id": node_id, "role": role or "custom"}

            _ALLOWED_ENV_KEYS = {
                "HOME", "PATH", "USER", "SHELL", "TERM", "LANG",
                "ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "XDG_CONFIG_HOME",
            }
            env = {k: v for k, v in os.environ.items()
                   if k in _ALLOWED_ENV_KEYS or k.startswith("CLAUDE_")}
            env.pop("CLAUDE_CODE_ENTRYPOINT", None)

            cmd = ["claude", "-p", "--verbose", "--output-format", "stream-json"]
            if model:
                cmd.extend(["--model", model])
            cmd.append(task)

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # merge stderr into stdout to prevent pipe deadlock
                cwd=cwd or os.environ["HOME"],
                env=env,
            )
            self._processes[agent_id] = proc

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

            with get_db() as conn:
                chunks = content.split("\n\n") if content else ["(no output)"]
                for chunk in chunks:
                    if chunk.strip():
                        conn.exec_driver_sql(
                            "INSERT INTO agent_output (agent_id, stream, chunk) VALUES (?, 'stdout', ?)",
                            (agent_id, chunk),
                        )
                conn.exec_driver_sql(
                    "UPDATE agents SET last_heartbeat = datetime('now') WHERE id = ?",
                    (agent_id,),
                )

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
            with get_db() as conn:
                conn.exec_driver_sql(
                    "UPDATE agents SET status = ?, exit_code = ?, stopped_at = datetime('now') WHERE id = ?",
                    (status, exit_code, agent_id),
                )
                conn.exec_driver_sql(
                    "DELETE FROM agent_output WHERE agent_id = ? AND id NOT IN "
                    "(SELECT id FROM agent_output WHERE agent_id = ? ORDER BY id DESC LIMIT 1000)",
                    (agent_id, agent_id),
                )

            event_bus.emit(f"agent.{status}", {
                "agent_id": agent_id,
                "status": status,
                "exit_code": exit_code,
            })

            if status == "completed":
                meta = self._agent_meta.get(agent_id, {})
                cap_node_id = meta.get("node_id")
                cap_role = meta.get("role", "custom")
                if cap_node_id:
                    try:
                        auto_capture_output(agent_id, cap_role, cap_node_id)
                    except Exception as e:
                        log.warning("sdk_auto_capture_failed", agent_id=agent_id, error=str(e))

            try:
                self._check_analysis_job_completion(agent_id, status)
            except Exception as e:
                log.warning("sdk_analysis_job_check_failed", agent_id=agent_id, error=str(e))

            try:
                self._check_self_improve_agent(agent_id, status)
            except Exception as e:
                log.warning("sdk_self_improve_check_failed", agent_id=agent_id, error=str(e))

            self._concurrency_semaphore.release()
            self._agent_meta.pop(agent_id, None)

    @staticmethod
    def _extract_stream_text(raw_line: str) -> str | None:
        """Extract human-readable text from a stream-json line.

        Claude CLI --output-format stream-json emits JSON events.  We only
        want the actual assistant text, not system/hook/tool metadata.
        Returns the text fragment or None if the line should be skipped.
        """
        import json as _json
        try:
            obj = _json.loads(raw_line)
        except (ValueError, TypeError):
            # Not JSON — could be plain text from --verbose; keep it
            return raw_line if raw_line.strip() else None

        etype = obj.get("type", "")

        # stream-json content_block_delta with text
        if etype == "content_block_delta":
            delta = obj.get("delta", {})
            if delta.get("type") == "text_delta":
                return delta.get("text", "")

        # Final result message (non-streaming)
        if etype == "result":
            return obj.get("result", "")

        # Assistant message with text content blocks
        if etype == "assistant":
            content = obj.get("content", [])
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
            if parts:
                return "\n".join(parts)

        # Skip system, hook_started, hook_response, tool_use, etc.
        return None

    def _read_output(self, agent_id: str, proc: subprocess.Popen):
        """Read stdout and store in platform.db.

        Uses engine.raw_connection() for the hot output reader loop to avoid
        the overhead of SA connection pooling in a tight thread loop.
        """
        timed_out = False
        try:
            start_time = time.monotonic()
            timeout_seconds = AGENT_TIMEOUT_MINUTES * 60
            batch: list[str] = []
            last_commit = time.monotonic()
            # Use raw DBAPI connection for the hot loop (thread-safe, avoids SA overhead)
            raw_conn = engine.raw_connection()
            raw_conn.execute("PRAGMA journal_mode=WAL")
            raw_conn.execute("PRAGMA busy_timeout=5000")
            raw_conn.execute("PRAGMA foreign_keys=ON")
            try:
                for line in iter(proc.stdout.readline, b''):
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
                        # Parse stream-json: extract only assistant text content
                        content_text = self._extract_stream_text(text)
                        if content_text:
                            raw_conn.execute(
                                "INSERT INTO agent_output (agent_id, stream, chunk) VALUES (?, 'stdout', ?)",
                                (agent_id, content_text)
                            )
                        batch.append(text)

                        now = time.monotonic()
                        if len(batch) >= 10 or (now - last_commit) >= 2.0:
                            raw_conn.execute(
                                "UPDATE agents SET last_heartbeat = datetime('now') WHERE id = ?",
                                (agent_id,)
                            )
                            raw_conn.commit()
                            batch.clear()
                            last_commit = now

                if batch:
                    raw_conn.execute(
                        "UPDATE agents SET last_heartbeat = datetime('now') WHERE id = ?",
                        (agent_id,)
                    )
                    raw_conn.commit()
            finally:
                raw_conn.close()
        except Exception as e:
            log.warning("agent_output_read_error", agent_id=agent_id, error=str(e))
        finally:
            if timed_out:
                exit_code = proc.poll() or -1
            else:
                exit_code = proc.wait()
            with get_db() as conn:
                status = 'failed' if timed_out else ('completed' if exit_code == 0 else 'failed')
                conn.exec_driver_sql(
                    "UPDATE agents SET status = ?, exit_code = ?, stopped_at = datetime('now') WHERE id = ?",
                    (status, exit_code, agent_id)
                )
                conn.exec_driver_sql(
                    "DELETE FROM agent_output WHERE agent_id = ? AND id NOT IN "
                    "(SELECT id FROM agent_output WHERE agent_id = ? ORDER BY id DESC LIMIT 1000)",
                    (agent_id, agent_id)
                )

            event_name = f"agent.{status}"
            event_bus.emit(event_name, {
                "agent_id": agent_id,
                "status": status,
                "exit_code": exit_code,
            })

            if status == 'completed':
                meta = self._agent_meta.get(agent_id, {})
                node_id = meta.get("node_id")
                role = meta.get("role", "custom")
                if node_id:
                    try:
                        auto_capture_output(agent_id, role, node_id)
                    except Exception as e:
                        log.warning("auto_capture_failed", agent_id=agent_id, error=str(e))

            try:
                self._check_analysis_job_completion(agent_id, status)
            except Exception as e:
                log.warning("analysis_job_check_failed", agent_id=agent_id, error=str(e))

            try:
                self._check_self_improve_agent(agent_id, status)
            except Exception as e:
                log.warning("self_improve_check_failed", agent_id=agent_id, error=str(e))

            self._concurrency_semaphore.release()
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
        with get_db() as conn:
            row = conn.exec_driver_sql(
                "SELECT agent_id FROM self_improve_agents WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()
            if not row:
                return

        from app.services.self_improve import self_improve_service
        self_improve_service.on_agent_completed(agent_id, agent_status)

    def _check_analysis_job_completion(self, agent_id: str, agent_status: str):
        """Check if this agent's completion should update an analysis job."""
        import json

        with get_db() as conn:
            jobs = conn.exec_driver_sql(
                "SELECT id, agent_ids FROM analysis_jobs WHERE status = 'running'"
            ).fetchall()

            for job in jobs:
                jm = job._mapping
                agent_ids = json.loads(jm["agent_ids"] or "[]")
                if agent_id not in agent_ids:
                    continue

                all_done = True
                any_failed = False
                for aid in agent_ids:
                    row = conn.exec_driver_sql(
                        "SELECT status FROM agents WHERE id = ?", (aid,)
                    ).fetchone()
                    if not row:
                        continue
                    s = row._mapping["status"]
                    if s in ("running", "paused"):
                        all_done = False
                        break
                    if s in ("failed", "killed"):
                        any_failed = True

                if all_done:
                    summaries: list[str] = []
                    for aid in agent_ids:
                        agent_row = conn.exec_driver_sql(
                            "SELECT name, role FROM agents WHERE id = ?", (aid,)
                        ).fetchone()
                        output_rows = conn.exec_driver_sql(
                            "SELECT chunk FROM agent_output WHERE agent_id = ? ORDER BY id DESC LIMIT 50",
                            (aid,),
                        ).fetchall()
                        if output_rows and agent_row:
                            arm = agent_row._mapping
                            role_label = (arm["role"] or "agent").replace("-", " ").title()
                            output_text = "\n".join(r._mapping["chunk"] for r in reversed(output_rows))
                            summaries.append(f"## {role_label} ({arm['name']})\n\n{output_text}")

                    results_summary = "\n\n---\n\n".join(summaries) if summaries else "No output captured."
                    final_status = "completed" if not any_failed else "failed"

                    conn.exec_driver_sql(
                        "UPDATE analysis_jobs SET status = ?, results_summary = ?, completed_at = datetime('now') WHERE id = ?",
                        (final_status, results_summary, jm["id"]),
                    )
                    log.info("analysis_job_completed", job_id=jm["id"], agent_count=len(agent_ids))


process_manager = ProcessManager()
