#!/usr/bin/env python3
"""M0 reference server - cross-tool operational-thread memory on SQLite.

Implements the M0 wire contract (see systems/m0/SPEC.md):

    POST /api/brain/checkpoint    write one thread entry (idempotent)
    GET  /api/brain/thread        read recent entries, newest first
    GET  /api/health              liveness and store stats (extension)

Standard library only. Binds to loopback by default, makes no outbound
network calls, and emits no telemetry. Every database call carries an
explicit, short busy timeout; a write that still cannot land is persisted
to a sidecar file and reported as deferred, so a write is never lost.

Usage:
    python3 m0_server.py serve [--host 127.0.0.1] [--port 8787] [--db PATH]
    python3 m0_server.py drain [--db PATH]
    python3 m0_server.py write --project P --text T [--kind K] [...]
    python3 m0_server.py read  [--project P] [--limit N] [--kind K]
    python3 m0_server.py health

Environment:
    M0_DB               store path (default $XDG_DATA_HOME/coco-m0/thread.db)
    M0_SIDECAR_DIR      sidecar spool (default <db dir>/sidecars)
    M0_BUSY_TIMEOUT_MS  per-call SQLite busy timeout in ms (default 10000)
    M0_HOST, M0_PORT    serve defaults (127.0.0.1, 8787)
    M0_PROJECT          default project for the CLI
    M0_SESSION_ID       default session_id for writes
    M0_SOURCE_TOOL      default source_tool for writes
    M0_OWNER            default owner_user_id for writes (default "local")
    M0_VISIBILITY       default visibility for writes (default "private")

MIT licensed, part of the Coco M0 bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VERSION = "1.0.0"
SPEC_VERSION = "m0/1"

# Column order is normative: the content hash is computed over these fields,
# minus "id" and "ts", joined in exactly this order. See SPEC.md.
FIELDS = (
    "id",
    "project",
    "session_id",
    "source_tool",
    "role",
    "kind",
    "ts",
    "branch",
    "head_sha",
    "next_step",
    "last_verified",
    "text",
    "meta_json",
    "owner_user_id",
    "visibility",
)

HASHED_FIELDS = tuple(f for f in FIELDS if f not in ("id", "ts"))

KINDS = (
    "step_done",
    "compact_checkpoint",
    "session_end",
    "lane_dispatched",
    "lane_result",
    "ambient_signal",
)

DEFAULT_KIND = "step_done"
DEFAULT_LIMIT = 20
MAX_LIMIT = 500
DEFAULT_BUSY_TIMEOUT_MS = 10_000

SCHEMA = """
CREATE TABLE IF NOT EXISTS operational_thread (
    id            TEXT PRIMARY KEY,
    project       TEXT NOT NULL,
    session_id    TEXT,
    source_tool   TEXT,
    role          TEXT,
    kind          TEXT NOT NULL,
    ts            TEXT NOT NULL,
    branch        TEXT,
    head_sha      TEXT,
    next_step     TEXT,
    last_verified TEXT,
    text          TEXT NOT NULL,
    meta_json     TEXT,
    owner_user_id TEXT,
    visibility    TEXT
);
CREATE INDEX IF NOT EXISTS ix_ot_project_ts   ON operational_thread(project, ts DESC);
CREATE INDEX IF NOT EXISTS ix_ot_project_kind ON operational_thread(project, kind, ts DESC);
"""


class M0Error(Exception):
    """A client-visible request error."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------- paths / time


def default_db_path() -> Path:
    env = os.environ.get("M0_DB")
    if env:
        return Path(env).expanduser()
    base = os.environ.get("XDG_DATA_HOME") or "~/.local/share"
    return Path(base).expanduser() / "coco-m0" / "thread.db"


def sidecar_dir_for(db_path: Path) -> Path:
    env = os.environ.get("M0_SIDECAR_DIR")
    if env:
        return Path(env).expanduser()
    return db_path.parent / "sidecars"


def busy_timeout_ms() -> int:
    raw = os.environ.get("M0_BUSY_TIMEOUT_MS", str(DEFAULT_BUSY_TIMEOUT_MS))
    try:
        value = int(float(raw))
    except ValueError:
        return DEFAULT_BUSY_TIMEOUT_MS
    return max(1, value)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


# ------------------------------------------------------------------ store core


class Store:
    """SQLite-backed operational thread with a sidecar spool."""

    def __init__(self, db_path: Path | None = None, sidecars: Path | None = None,
                 timeout_ms: int | None = None) -> None:
        self.db_path = Path(db_path).expanduser() if db_path else default_db_path()
        self.sidecars = Path(sidecars).expanduser() if sidecars else sidecar_dir_for(self.db_path)
        self.timeout_ms = timeout_ms or busy_timeout_ms()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.sidecars.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # -- connections -------------------------------------------------------

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=self.timeout_ms / 1000.0,
            isolation_level=None,
        )
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout = {self.timeout_ms}")
        return conn

    def _init_schema(self) -> None:
        conn = self.connect()
        try:
            try:
                conn.execute("PRAGMA journal_mode = WAL")
            except sqlite3.OperationalError:
                pass  # a concurrent writer holds the file; WAL is an optimisation
            conn.executescript(SCHEMA)
        finally:
            conn.close()

    # -- normalisation -----------------------------------------------------

    @staticmethod
    def canonical_meta(value) -> str | None:
        """Accept an object, an array, or a string. Never reject.

        A JSON-encoded string is parsed and re-serialised canonically, so the
        same metadata always hashes identically. A string that is not JSON is
        preserved as {"note": <string>} rather than raising, because a metadata
        parameter that rejects valid input is worse than a lenient one.
        """
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True, separators=(",", ":"))
        if isinstance(value, (int, float, bool)):
            return json.dumps({"value": value}, sort_keys=True, separators=(",", ":"))
        text = str(value).strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return json.dumps({"note": str(value)}, sort_keys=True, separators=(",", ":"))
        if isinstance(parsed, (dict, list)):
            return json.dumps(parsed, sort_keys=True, separators=(",", ":"))
        return json.dumps({"value": parsed}, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def content_id(row: dict) -> str:
        joined = "\x00".join((row.get(f) or "") for f in HASHED_FIELDS)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def normalize(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise M0Error("body must be a JSON object")

        project = str(payload.get("project") or os.environ.get("M0_PROJECT") or "").strip()
        if not project:
            raise M0Error("'project' is required")

        text = payload.get("text")
        if text is None or not str(text).strip():
            raise M0Error("'text' is required and must be non-empty")

        kind = str(payload.get("kind") or DEFAULT_KIND).strip()
        if kind not in KINDS:
            raise M0Error(f"unknown kind '{kind}' (expected one of: {', '.join(KINDS)})")

        # meta_json / meta are aliases; either may be an object or a string.
        meta_raw = payload.get("meta_json")
        if meta_raw is None:
            meta_raw = payload.get("meta")

        row = {
            "project": project,
            "session_id": _opt(payload.get("session_id"), os.environ.get("M0_SESSION_ID")),
            "source_tool": _opt(payload.get("source_tool"), os.environ.get("M0_SOURCE_TOOL")),
            "role": _opt(payload.get("role"), "assistant"),
            "kind": kind,
            "ts": _opt(payload.get("ts")) or utc_now(),
            "branch": _opt(payload.get("branch")),
            "head_sha": _opt(payload.get("head_sha")),
            "next_step": _opt(payload.get("next_step")),
            "last_verified": _opt(payload.get("last_verified")),
            "text": str(text).strip(),
            "meta_json": self.canonical_meta(meta_raw),
            "owner_user_id": _opt(payload.get("owner_user_id"), os.environ.get("M0_OWNER"), "local"),
            "visibility": _opt(payload.get("visibility"), os.environ.get("M0_VISIBILITY"), "private"),
        }
        row["id"] = self.content_id(row)
        return row

    # -- writes ------------------------------------------------------------

    def write(self, payload: dict) -> dict:
        """Idempotent write. Falls back to a sidecar file if the store is busy."""
        row = self.normalize(payload)
        try:
            stored_ts = self._insert(row)
            return {"id": row["id"], "ts": stored_ts, "ok": True, "deferred": False}
        except sqlite3.OperationalError:
            self._spool(row)
            return {"id": row["id"], "ts": row["ts"], "ok": True, "deferred": True}

    def _insert(self, row: dict) -> str:
        """Insert if absent, then return the stored ts (first write wins)."""
        columns = ", ".join(FIELDS)
        placeholders = ", ".join("?" for _ in FIELDS)
        conn = self.connect()
        try:
            conn.execute(
                f"INSERT INTO operational_thread ({columns}) VALUES ({placeholders}) "
                f"ON CONFLICT(id) DO NOTHING",
                [row.get(f) for f in FIELDS],
            )
            found = conn.execute(
                "SELECT ts FROM operational_thread WHERE id = ?", (row["id"],)
            ).fetchone()
            return found["ts"] if found else row["ts"]
        finally:
            conn.close()

    def _spool(self, row: dict) -> Path:
        """Persist a write we could not land, atomically (tmp + replace)."""
        self.sidecars.mkdir(parents=True, exist_ok=True)
        safe_ts = row["ts"].replace(":", "").replace(".", "")
        target = self.sidecars / f"{safe_ts}-{row['id'][:16]}.json"
        fd, tmp = tempfile.mkstemp(dir=str(self.sidecars), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(row, handle, ensure_ascii=False, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, target)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        return target

    # -- sidecars ----------------------------------------------------------

    def pending_sidecars(self) -> list[dict]:
        rows = []
        if not self.sidecars.is_dir():
            return rows
        for path in sorted(self.sidecars.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and data.get("id"):
                data["_sidecar"] = path.name
                rows.append(data)
        return rows

    def drain(self) -> dict:
        """Land every spooled write. Called on start and available on demand."""
        drained = 0
        skipped = 0
        quarantined = 0
        if not self.sidecars.is_dir():
            return {"drained": 0, "skipped": 0, "quarantined": 0}
        for path in sorted(self.sidecars.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                path.rename(path.with_suffix(".json.bad"))
                quarantined += 1
                continue
            if not isinstance(data, dict) or not data.get("id"):
                path.rename(path.with_suffix(".json.bad"))
                quarantined += 1
                continue
            data.pop("_sidecar", None)
            try:
                self._insert(data)
            except sqlite3.OperationalError:
                skipped += 1
                break  # store still busy; keep the rest spooled for next time
            try:
                path.unlink()
            except OSError:
                pass
            drained += 1
        return {"drained": drained, "skipped": skipped, "quarantined": quarantined}

    # -- reads -------------------------------------------------------------

    def read(self, project: str | None = None, limit: int = DEFAULT_LIMIT,
             kind: str | None = None) -> dict:
        """Most recent entries, newest first. Union of the store and the spool.

        Reads survive a locked store: if SELECT cannot run, spooled entries are
        still returned and the degraded reason is reported.
        """
        limit = max(1, min(int(limit or DEFAULT_LIMIT), MAX_LIMIT))
        if kind and kind not in KINDS:
            raise M0Error(f"unknown kind '{kind}' (expected one of: {', '.join(KINDS)})")

        entries: list[dict] = []
        degraded = None
        sql = "SELECT * FROM operational_thread"
        clauses, params = [], []
        if project:
            clauses.append("project = ?")
            params.append(project)
        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY ts DESC, id DESC LIMIT ?"
        params.append(limit)

        try:
            conn = self.connect()
            try:
                entries = [dict(r) for r in conn.execute(sql, params).fetchall()]
            finally:
                conn.close()
        except sqlite3.OperationalError as exc:
            degraded = f"store busy: {exc}"

        seen = {e["id"] for e in entries}
        pending = 0
        for row in self.pending_sidecars():
            if project and row.get("project") != project:
                continue
            if kind and row.get("kind") != kind:
                continue
            pending += 1
            if row["id"] in seen:
                continue
            entry = {f: row.get(f) for f in FIELDS}
            entry["pending"] = True
            entries.append(entry)
            seen.add(row["id"])

        entries.sort(key=lambda e: (e.get("ts") or "", e.get("id") or ""), reverse=True)
        entries = entries[:limit]
        return {
            "project": project,
            "kind": kind,
            "limit": limit,
            "count": len(entries),
            "pending_sidecars": pending,
            "degraded": degraded,
            "entries": entries,
        }

    # -- health ------------------------------------------------------------

    def health(self) -> dict:
        rows = None
        projects = None
        degraded = None
        try:
            conn = self.connect()
            try:
                rows = conn.execute("SELECT COUNT(*) AS n FROM operational_thread").fetchone()["n"]
                projects = conn.execute(
                    "SELECT COUNT(DISTINCT project) AS n FROM operational_thread"
                ).fetchone()["n"]
            finally:
                conn.close()
        except sqlite3.OperationalError as exc:
            degraded = f"store busy: {exc}"
        return {
            "ok": degraded is None,
            "version": VERSION,
            "spec": SPEC_VERSION,
            "db": str(self.db_path),
            "sidecar_dir": str(self.sidecars),
            "busy_timeout_ms": self.timeout_ms,
            "rows": rows,
            "projects": projects,
            "pending_sidecars": len(self.pending_sidecars()),
            "degraded": degraded,
            "local_only": True,
        }


def _opt(*candidates):
    """First candidate that is a non-empty string, else None."""
    for value in candidates:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


# ----------------------------------------------------------------- http layer


class Handler(BaseHTTPRequestHandler):
    server_version = f"m0/{VERSION}"
    protocol_version = "HTTP/1.1"
    store: Store  # injected on the server instance

    def log_message(self, fmt: str, *args) -> None:  # keep stdout clean
        sys.stderr.write("m0 %s - %s\n" % (self.address_string(), fmt % args))

    # -- helpers -----------------------------------------------------------

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise M0Error(f"invalid JSON body: {exc}")

    # -- routes ------------------------------------------------------------

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        route = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if route == "/api/brain/checkpoint":
                self._send(200, self.server.store.write(self._body()))
            elif route == "/api/brain/sidecars/drain":
                self._send(200, self.server.store.drain())
            else:
                self._send(404, {"ok": False, "error": f"no route POST {route}"})
        except M0Error as exc:
            self._send(exc.status, {"ok": False, "error": str(exc)})
        except Exception as exc:  # pragma: no cover - last-resort guard
            self._send(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        def one(name, default=None):
            values = query.get(name) or []
            return values[0] if values and values[0] != "" else default

        try:
            if route == "/api/brain/thread":
                limit_raw = one("limit", str(DEFAULT_LIMIT))
                try:
                    limit = int(limit_raw)
                except (TypeError, ValueError):
                    raise M0Error(f"'limit' must be an integer, got '{limit_raw}'")
                self._send(200, self.server.store.read(
                    project=one("project"), limit=limit, kind=one("kind")))
            elif route in ("/api/health", "/health"):
                self._send(200, self.server.store.health())
            else:
                self._send(404, {"ok": False, "error": f"no route GET {route}"})
        except M0Error as exc:
            self._send(exc.status, {"ok": False, "error": str(exc)})
        except Exception as exc:  # pragma: no cover - last-resort guard
            self._send(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})


def serve(store: Store, host: str, port: int) -> None:
    report = store.drain()
    if report["drained"] or report["quarantined"]:
        print(f"m0: drained {report['drained']} sidecar write(s), "
              f"quarantined {report['quarantined']}", flush=True)
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.daemon_threads = True
    httpd.store = store
    if host not in ("127.0.0.1", "localhost", "::1"):
        print(f"m0: WARNING binding {host} exposes the store beyond this machine; "
              f"there is no authentication.", flush=True)
    print(f"m0 {VERSION} listening on http://{host}:{port}", flush=True)
    print(f"m0 store: {store.db_path}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("m0: stopping", flush=True)
    finally:
        httpd.server_close()


# ------------------------------------------------------------------------ cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="m0_server.py", description=__doc__.split("\n")[0])
    parser.add_argument("--db", help="store path (default $M0_DB or XDG data dir)")
    parser.add_argument("--sidecar-dir", help="sidecar spool (default <db dir>/sidecars)")
    parser.add_argument("--busy-timeout-ms", type=int, help="per-call SQLite busy timeout")
    sub = parser.add_subparsers(dest="command")

    p_serve = sub.add_parser("serve", help="run the HTTP server")
    p_serve.add_argument("--host", default=os.environ.get("M0_HOST", "127.0.0.1"))
    p_serve.add_argument("--port", type=int, default=int(os.environ.get("M0_PORT", "8787")))

    sub.add_parser("drain", help="land spooled writes now")
    sub.add_parser("health", help="print store health as JSON")

    p_write = sub.add_parser("write", help="write one entry without HTTP")
    p_write.add_argument("--project", default=os.environ.get("M0_PROJECT"))
    p_write.add_argument("--text", required=True)
    p_write.add_argument("--kind", default=DEFAULT_KIND, choices=list(KINDS))
    p_write.add_argument("--next-step")
    p_write.add_argument("--last-verified")
    p_write.add_argument("--session-id")
    p_write.add_argument("--source-tool")
    p_write.add_argument("--branch")
    p_write.add_argument("--head-sha")
    p_write.add_argument("--meta", help="JSON object, or any string (wrapped as {\"note\": ...})")

    p_read = sub.add_parser("read", help="print recent entries as JSON")
    p_read.add_argument("--project", default=os.environ.get("M0_PROJECT"))
    p_read.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    p_read.add_argument("--kind", choices=list(KINDS))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = Store(db_path=args.db, sidecars=args.sidecar_dir, timeout_ms=args.busy_timeout_ms)
    command = args.command or "serve"

    if command == "serve":
        serve(store, args.host, args.port)
        return 0
    if command == "drain":
        print(json.dumps(store.drain(), indent=2))
        return 0
    if command == "health":
        print(json.dumps(store.health(), indent=2))
        return 0
    if command == "write":
        try:
            result = store.write({
                "project": args.project,
                "text": args.text,
                "kind": args.kind,
                "next_step": args.next_step,
                "last_verified": args.last_verified,
                "session_id": args.session_id,
                "source_tool": args.source_tool,
                "branch": args.branch,
                "head_sha": args.head_sha,
                "meta_json": args.meta,
            })
        except M0Error as exc:
            print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        return 0
    if command == "read":
        try:
            print(json.dumps(store.read(args.project, args.limit, args.kind), indent=2))
        except M0Error as exc:
            print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
            return 2
        return 0

    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
