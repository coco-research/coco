"""StationManager — subprocess agent lifecycle.

Ported from .planning/v3/backend/REFERENCE-IMPL/services/station_manager.py
per DESIGN.md §5 + Service Layer + RISKS R-02/R-06/R-07/R-08/R-17.

Key invariants:
* All subprocess spawns use ``start_new_session=True`` for kill-the-group safety
  (D-17, citation [4.1]).
* Concurrency capped by ``MAX_CONCURRENT_STATIONS`` (asyncio.Semaphore).
* All platform.db writes use ``BEGIN IMMEDIATE`` via SA Core.
* SIGTERM -> 5s -> SIGKILL ladder.
* Heartbeats every 30s; dead-man detection at 120s.
* Crash recovery reconciles rows where ``status='running'`` but pid is dead.
* The injectable ``ProcessRunner`` abstraction lets tests substitute a
  deterministic fake without spawning real processes.
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from sqlalchemy import text
from sqlalchemy.engine import Engine


# ---------------------------------------------------------------------------
# Lightweight types
# ---------------------------------------------------------------------------

def _ulid() -> str:
    """Generate a 26-char upper-case ULID-shape token."""
    h = uuid.uuid4().hex.upper()  # 32 chars
    return h[:26]


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass
class SpawnRequest:
    task_id: str
    project_id: str
    project_name: str
    autonomy: str
    cwd: str
    model: str = "sonnet"
    prompt: str = ""
    idempotency_key: str | None = None
    cost_cap_usd: float = 5.0
    wall_clock_max_s: int = 30 * 60  # 30 min hard backstop


@dataclass
class Station:
    id: str
    task_id: str | None
    project_id: str
    project_name: str
    model: str
    pid: int | None
    status: str
    autonomy: str
    cwd: str
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    exit_code: int | None = None
    started_at: str | None = None
    stopped_at: str | None = None
    last_heartbeat: str | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# ProcessRunner protocol — production uses asyncio.create_subprocess_exec
# ---------------------------------------------------------------------------

class ProcessHandle(Protocol):
    pid: int

    def terminate(self) -> None: ...
    def kill(self) -> None: ...
    async def wait(self) -> int: ...
    def returncode(self) -> int | None: ...


class ProcessRunner(Protocol):
    """Spawns processes. Production impl wraps ``asyncio.create_subprocess_exec``."""

    async def spawn(self, argv: list[str], *, cwd: str, env: dict[str, str]) -> ProcessHandle: ...


class _AsyncProcessHandle:
    """Adapter that exposes ``asyncio.subprocess.Process`` through ProcessHandle."""

    def __init__(self, proc):
        self._proc = proc
        self.pid = proc.pid

    def terminate(self) -> None:
        try:
            self._proc.terminate()
        except ProcessLookupError:
            pass

    def kill(self) -> None:
        try:
            self._proc.kill()
        except ProcessLookupError:
            pass

    async def wait(self) -> int:
        return await self._proc.wait()

    def returncode(self) -> int | None:
        return self._proc.returncode


class DefaultProcessRunner:
    """Production runner. Tests inject ``FakeProcessRunner`` instead."""

    async def spawn(self, argv: list[str], *, cwd: str, env: dict[str, str]) -> ProcessHandle:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
            start_new_session=True,
            close_fds=True,
        )
        return _AsyncProcessHandle(proc)


# ---------------------------------------------------------------------------
# Repository (thin SA Core writer)
# ---------------------------------------------------------------------------

class StationRepo:
    """SA Core writes, scoped to the stations table.

    All writes happen inside engine.begin() — which issues ``BEGIN IMMEDIATE``
    on SQLite when isolation_level is left default.
    """

    def __init__(self, engine: Engine):
        self.engine = engine

    def insert_pending(self, st: Station, *, idempotency_key: str | None) -> None:
        with self.engine.begin() as conn:
            conn.execute(text(
                """INSERT INTO stations
                   (id, task_id, project_id, project_name_snapshot, model, pid,
                    status, autonomy, cwd, prompt_preview, idempotency_key,
                    started_at, last_heartbeat)
                   VALUES (:id, :task_id, :project_id, :project_name, :model, :pid,
                           :status, :autonomy, :cwd, :prompt, :idem,
                           :started_at, :hb)"""
            ), dict(
                id=st.id,
                task_id=st.task_id,
                project_id=st.project_id,
                project_name=st.project_name,
                model=st.model,
                pid=st.pid,
                status=st.status,
                autonomy=st.autonomy,
                cwd=st.cwd,
                prompt="",
                idem=idempotency_key,
                started_at=st.started_at,
                hb=st.last_heartbeat,
            ))

    def update_running(self, station_id: str, pid: int) -> None:
        ts = _utcnow_iso()
        with self.engine.begin() as conn:
            conn.execute(text(
                "UPDATE stations SET pid=:pid, status='running', started_at=:t,"
                " last_heartbeat=:t, updated_at=:t WHERE id=:id"
            ), dict(pid=pid, id=station_id, t=ts))

    def update_status(self, station_id: str, status: str, *, exit_code: int | None = None,
                      notes: str | None = None) -> None:
        ts = _utcnow_iso()
        with self.engine.begin() as conn:
            conn.execute(text(
                "UPDATE stations SET status=:s, exit_code=:rc, notes=COALESCE(:n, notes),"
                " stopped_at=CASE WHEN :s IN ('completed','failed','killed') THEN :t ELSE stopped_at END,"
                " updated_at=:t WHERE id=:id"
            ), dict(s=status, rc=exit_code, n=notes, id=station_id, t=ts))

    def update_cost(self, station_id: str, *, cost_usd: float, in_tok: int, out_tok: int) -> None:
        ts = _utcnow_iso()
        with self.engine.begin() as conn:
            conn.execute(text(
                "UPDATE stations SET cost_usd=:c, input_tokens=:i, output_tokens=:o,"
                " updated_at=:t WHERE id=:id"
            ), dict(c=cost_usd, i=in_tok, o=out_tok, id=station_id, t=ts))

    def heartbeat(self, station_id: str) -> None:
        ts = _utcnow_iso()
        with self.engine.begin() as conn:
            conn.execute(text(
                "UPDATE stations SET last_heartbeat=:t, updated_at=:t WHERE id=:id"
            ), dict(id=station_id, t=ts))

    def append_output(self, station_id: str, stream: str, chunk: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO station_output (station_id, stream, chunk) "
                "VALUES (:id, :s, :c)"
            ), dict(id=station_id, s=stream, c=chunk))

    def insert_cost_event(self, *, station_id: str, project_id: str, project_name: str,
                          model: str, cost_usd: float, in_tok: int, out_tok: int,
                          source: str = "api_token") -> None:
        with self.engine.begin() as conn:
            conn.execute(text(
                """INSERT INTO cost_events
                   (id, station_id, project_id, project_name_snapshot, model, feature,
                    source, input_tokens, output_tokens, cost_usd)
                   VALUES (:id, :sid, :pid, :pn, :m, 'station', :src, :i, :o, :c)"""
            ), dict(id=_ulid(), sid=station_id, pid=project_id, pn=project_name,
                    m=model, src=source, i=in_tok, o=out_tok, c=cost_usd))

    def fetch(self, station_id: str) -> dict | None:
        with self.engine.connect() as conn:
            row = conn.execute(text(
                "SELECT id, task_id, project_id, project_name_snapshot, model, pid,"
                " status, cost_usd, input_tokens, output_tokens, exit_code,"
                " started_at, stopped_at, last_heartbeat, notes"
                " FROM stations WHERE id=:id"
            ), dict(id=station_id)).mappings().first()
            return dict(row) if row else None

    def fetch_running(self) -> list[dict]:
        with self.engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT id, pid FROM stations WHERE status='running'"
            )).mappings().all()
            return [dict(r) for r in rows]

    def fetch_zombies(self, threshold_iso: str) -> list[dict]:
        with self.engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT id, pid, last_heartbeat FROM stations"
                " WHERE status='running' AND last_heartbeat < :t"
            ), dict(t=threshold_iso)).mappings().all()
            return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Event bus protocol (in-process pub/sub)
# ---------------------------------------------------------------------------

class EventBus(Protocol):
    async def emit(self, event_type: str, data: dict[str, Any]) -> None: ...


class InMemoryBus:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []
        self._lock = asyncio.Lock()

    async def emit(self, event_type: str, data: dict[str, Any]) -> None:
        async with self._lock:
            self.events.append((event_type, data))

    def by_type(self, t: str) -> list[dict[str, Any]]:
        return [d for et, d in self.events if et == t]


# ---------------------------------------------------------------------------
# Sandbox utility
# ---------------------------------------------------------------------------

DEFAULT_ALLOWED_ROOTS: tuple[str, ...] = (
    os.path.expanduser("~/projects"),
    os.path.expanduser("~/.coco"),
    os.path.expanduser("~/.hub"),
)


def is_allowed_cwd(path: str, allowed_roots: tuple[str, ...] = DEFAULT_ALLOWED_ROOTS) -> bool:
    """Sandbox check: cwd must resolve under an allowed root."""
    try:
        resolved = os.path.realpath(path)
    except Exception:
        return False
    return any(resolved == r or resolved.startswith(r + os.sep) for r in allowed_roots)


# ---------------------------------------------------------------------------
# StationManager
# ---------------------------------------------------------------------------

class StationManager:
    """Orchestrates lifecycle of subprocess stations.

    Designed for testability: every external dependency (process runner, psutil,
    event bus, repo, time) is injectable.
    """

    def __init__(
        self,
        *,
        repo: StationRepo,
        bus: EventBus,
        runner: ProcessRunner,
        psutil_mod: Any,
        max_concurrent: int = 3,
        allowed_roots: tuple[str, ...] = DEFAULT_ALLOWED_ROOTS,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.repo = repo
        self.bus = bus
        self.runner = runner
        self.psutil = psutil_mod
        self.max_concurrent = max_concurrent
        self.allowed_roots = allowed_roots
        self.clock = clock
        self._sem = asyncio.Semaphore(max_concurrent)
        self._procs: dict[str, ProcessHandle] = {}
        self._readers: dict[str, asyncio.Task] = {}
        self._spawn_lock = asyncio.Lock()  # guards platform.db inserts (race-safe)

    # ----- core operations -----

    async def spawn(self, req: SpawnRequest) -> Station:
        # Sandbox check
        if not is_allowed_cwd(req.cwd, self.allowed_roots):
            raise PermissionError(f"cwd {req.cwd!r} not under allowed roots")
        if not os.path.exists(req.cwd):
            raise FileNotFoundError(req.cwd)

        # Concurrency cap. Acquire with timeout so callers see backpressure.
        try:
            if self._sem.locked() and self._sem._value == 0:
                await asyncio.wait_for(self._sem.acquire(), timeout=0.001)
            else:
                await self._sem.acquire()
        except asyncio.TimeoutError:
            raise OverflowError("MAX_CONCURRENT_STATIONS reached")

        try:
            async with self._spawn_lock:  # serialize DB writes for race-safety
                station_id = _ulid()
                started = _utcnow_iso()
                station = Station(
                    id=station_id, task_id=req.task_id, project_id=req.project_id,
                    project_name=req.project_name, model=req.model, pid=None,
                    status="pending", autonomy=req.autonomy, cwd=req.cwd,
                    started_at=started, last_heartbeat=started,
                )
                self.repo.insert_pending(station, idempotency_key=req.idempotency_key)

                # Spawn
                env = {
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": os.environ.get("HOME", ""),
                    "COCO_STATION_ID": station_id,
                    "COCO_PROJECT_ID": req.project_id,
                }
                argv = ["claude", "-p", "--output-format", "stream-json", req.prompt or ""]
                proc = await self.runner.spawn(argv, cwd=req.cwd, env=env)
                self._procs[station_id] = proc
                self.repo.update_running(station_id, proc.pid)
                station.pid = proc.pid
                station.status = "running"

                await self.bus.emit("station.spawned", {
                    "station_id": station_id, "task_id": req.task_id,
                    "model": req.model, "pid": proc.pid, "project_id": req.project_id,
                })
                return station
        except Exception:
            # If anything fails after sem acquire, release it.
            self._sem.release()
            raise

    async def kill(self, station_id: str, *, reason: str = "user",
                   sigterm_grace_s: float = 5.0) -> None:
        proc = self._procs.get(station_id)
        if proc is None:
            # Already gone or never tracked.
            self.repo.update_status(station_id, "killed", exit_code=-9,
                                    notes=f"kill_no_handle:{reason}")
            await self.bus.emit("station.killed", {"station_id": station_id, "reason": reason})
            return

        proc.terminate()
        try:
            rc = await asyncio.wait_for(proc.wait(), timeout=sigterm_grace_s)
        except asyncio.TimeoutError:
            proc.kill()
            rc = await proc.wait()
        finally:
            self._procs.pop(station_id, None)
            reader = self._readers.pop(station_id, None)
            if reader is not None and not reader.done():
                reader.cancel()
            # Release the semaphore slot — best-effort.
            if self._sem._value < self.max_concurrent:
                self._sem.release()

        self.repo.update_status(station_id, "killed", exit_code=rc, notes=reason)
        await self.bus.emit("station.killed", {"station_id": station_id, "reason": reason})

    async def reap(self, station_id: str) -> None:
        """Mark a process zombie/failed when its OS-level entry is gone."""
        proc = self._procs.pop(station_id, None)
        reader = self._readers.pop(station_id, None)
        if reader is not None and not reader.done():
            reader.cancel()
        self.repo.update_status(station_id, "failed", exit_code=-1, notes="zombie_reaped")
        await self.bus.emit("station.zombie_detected", {"station_id": station_id,
                                                        "last_heartbeat": None})
        if self._sem._value < self.max_concurrent:
            self._sem.release()

    async def monitor(self, station_id: str) -> dict[str, Any]:
        """Return a snapshot of the station's process state."""
        snap: dict[str, Any] = {"station_id": station_id, "alive": False, "rss_mb": 0.0}
        proc = self._procs.get(station_id)
        if proc is None:
            return snap
        pid = proc.pid
        if not self.psutil.pid_exists(pid):
            return snap
        p = self.psutil.Process(pid)
        snap["alive"] = bool(p.is_running())
        try:
            snap["rss_mb"] = p.memory_info().rss / (1024 * 1024)
        except Exception:
            snap["rss_mb"] = 0.0
        # Touch heartbeat
        self.repo.heartbeat(station_id)
        return snap

    async def log_stream(self, station_id: str, lines: list[str], *,
                         cost_cap_usd: float = 5.0) -> None:
        """Consume already-collected stream-json lines."""
        total_in = 0
        total_out = 0
        total_cost = 0.0
        st = self.repo.fetch(station_id)
        if st is None:
            return
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            self.repo.append_output(station_id, "stdout", line[:8000])
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("type") == "usage":
                in_tok = int(obj.get("input_tokens", 0))
                out_tok = int(obj.get("output_tokens", 0))
                cost = float(obj.get("cost_usd", 0.0))
                total_in += in_tok
                total_out += out_tok
                total_cost += cost
                await self.bus.emit("station.usage", {
                    "station_id": station_id,
                    "input_tokens": in_tok, "output_tokens": out_tok,
                    "cost_usd": cost,
                })
        if total_in or total_out or total_cost:
            self.repo.update_cost(
                station_id,
                cost_usd=st.get("cost_usd", 0.0) + total_cost,
                in_tok=st.get("input_tokens", 0) + total_in,
                out_tok=st.get("output_tokens", 0) + total_out,
            )
            self.repo.insert_cost_event(
                station_id=station_id, project_id=st["project_id"],
                project_name=st["project_name_snapshot"], model=st["model"],
                cost_usd=total_cost, in_tok=total_in, out_tok=total_out,
            )
            await self.bus.emit("cost.recorded", {
                "station_id": station_id,
                "project_id": st["project_id"],
                "model": st["model"],
                "cost_usd": total_cost,
            })

            # Cost cap enforcement (per-station)
            new_total = st.get("cost_usd", 0.0) + total_cost
            if new_total >= cost_cap_usd:
                await self.kill(station_id, reason="budget")

    def cost_track(self, station_id: str) -> dict[str, float]:
        """Return cumulative cost+tokens for a station."""
        st = self.repo.fetch(station_id) or {}
        return {
            "cost_usd": float(st.get("cost_usd") or 0.0),
            "input_tokens": int(st.get("input_tokens") or 0),
            "output_tokens": int(st.get("output_tokens") or 0),
        }

    # ----- lifecycle -----

    async def crash_recovery(self) -> int:
        """Lifespan-startup reconciliation (DESIGN §5.5)."""
        n = 0
        for row in self.repo.fetch_running():
            pid = row.get("pid")
            if pid is None:
                self.repo.update_status(row["id"], "failed", exit_code=-1,
                                        notes="reconciled_after_restart")
                await self.bus.emit("station.failed", {
                    "station_id": row["id"], "exit_code": -1,
                    "error": "reconciled_after_restart", "stderr_tail": "",
                })
                n += 1
                continue
            if not self.psutil.pid_exists(pid):
                self.repo.update_status(row["id"], "failed", exit_code=-1,
                                        notes="reconciled_after_restart")
                await self.bus.emit("station.failed", {
                    "station_id": row["id"], "exit_code": -1,
                    "error": "reconciled_after_restart", "stderr_tail": "",
                })
            else:
                # Live orphan — pipe is gone; cannot reattach safely.
                try:
                    os.kill(pid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
                self.repo.update_status(row["id"], "failed", exit_code=-2,
                                        notes="orphan_terminated_on_restart")
                await self.bus.emit("station.failed", {
                    "station_id": row["id"], "exit_code": -2,
                    "error": "orphan_terminated_on_restart", "stderr_tail": "",
                })
            n += 1
        return n

    async def shutdown_all(self, *, timeout: float = 5.0) -> None:
        """Concurrent shutdown of all running stations."""
        ids = list(self._procs.keys())
        if not ids:
            return
        await asyncio.gather(*[
            self.kill(sid, reason="shutdown", sigterm_grace_s=timeout) for sid in ids
        ], return_exceptions=True)


__all__ = [
    "Station",
    "SpawnRequest",
    "StationManager",
    "StationRepo",
    "ProcessRunner",
    "ProcessHandle",
    "DefaultProcessRunner",
    "InMemoryBus",
    "EventBus",
    "is_allowed_cwd",
    "DEFAULT_ALLOWED_ROOTS",
]
