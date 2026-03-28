import asyncio
import subprocess
import os
import signal
import threading
import time
import psutil
import structlog
from app.db.connections import get_platform_db, _connect
from app.config import PLATFORM_DB_PATH, MAX_CONCURRENT_AGENTS, AGENT_TIMEOUT_MINUTES
from app.services.collaboration_context import auto_capture_output
from app.services.event_bus import event_bus

log = structlog.get_logger()


class ProcessManager:
    def __init__(self):
        self._processes: dict[str, subprocess.Popen] = {}
        self._readers: dict[str, threading.Thread] = {}
        self._agent_meta: dict[str, dict] = {}  # agent_id -> {node_id, role}
        self._spawn_lock = threading.Lock()
        self._spawn_semaphore = asyncio.Semaphore(MAX_CONCURRENT_AGENTS)

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
              node_id: str | None = None, role: str | None = None) -> int:
        """Spawn a claude -p process. Returns PID.

        Uses a lock to make the running-count check atomic, preventing
        race conditions where two simultaneous spawns both pass the limit.
        """
        with self._spawn_lock:
            running = sum(1 for p in self._processes.values() if p.poll() is None)
            if running >= MAX_CONCURRENT_AGENTS:
                raise RuntimeError(f"Max {MAX_CONCURRENT_AGENTS} concurrent agents")

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

            cmd = ["claude", "-p", "--output-format", "stream-json"]
            if model:
                cmd.extend(["--model", model])
            cmd.append(task)

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
