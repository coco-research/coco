---
name: m0
description: "Use when the user says 'm0', 'm0 status', 'start m0', 'cross-tool memory', 'operational thread', or 'where is my memory stored', or when the M0 daemon or MCP wiring needs attention."
---

# /m0: Reference Server Control Plane

M0 ships the `m0/1` L0 wire contract (`systems/m0/SPEC.md`) and its Python
standard-library reference server (`m0_server.py`) plus stdio MCP server
(`m0_mcp.py`). Together they keep one local SQLite *operational thread* per
project: what was done, what was verified, and what is next.

The write path is `/m0-remember`, the read path is `/m0-recall`, and the
session handoff flow is `/m0-handoff`.

## Quick Reference

```bash
M0S="$HOME/.claude/skills/m0/scripts"           # installed location
M0="${COCO_M0_URL:-http://127.0.0.1:8787}"      # reference server base URL

# Start the stdlib reference server on 127.0.0.1:8787
python3 "$M0S/m0_server.py" serve

# Direct CLI against the same SQLite store (no server required)
python3 "$M0S/m0_server.py" health
python3 "$M0S/m0_server.py" write --project acme-web --text "Did the step."
python3 "$M0S/m0_server.py" read  --project acme-web --limit 5
python3 "$M0S/m0_server.py" drain
```

HTTP endpoints served at `$M0` (default `http://127.0.0.1:8787`, overridable by
`COCO_M0_URL`; keep `COCO_M0_URL` loopback-bound to `127.0.0.1` or `localhost`
because the reference server endpoints carry no authentication):

- `POST /api/brain/checkpoint` (write one idempotent entry; JSON body)
- `GET /api/brain/thread?project=acme-web&limit=5` (read recent entries, newest first)
- `GET /api/health` (optional liveness and store stats)
- `POST /api/brain/sidecars/drain` (optional on-demand sidecar spool drain)

If the scripts are not yet at `$HOME/.claude/skills/m0/scripts`, run them
directly from `systems/m0/skills/m0/scripts`, or see `systems/m0/README.md`
for installation instructions.

## Sub-commands

### /m0 status

Check store health directly with the CLI or by sending `GET $M0/api/health`
(where `M0="${COCO_M0_URL:-http://127.0.0.1:8787}"`):

```bash
python3 "$HOME/.claude/skills/m0/scripts/m0_server.py" health
```

Report in order:
1. **Server:** reachable at `$M0` or stopped (CLI and MCP direct fallback still work).
2. **Store:** `db` path (default `$XDG_DATA_HOME/coco-m0/thread.db`) and `rows` count.
3. **Pending:** if `pending_sidecars > 0`, drain with `POST $M0/api/brain/sidecars/drain` or `m0_server.py drain`.
4. **Degraded:** if set, another process holds the SQLite lock; reads return spooled rows and writes defer cleanly.

### /m0 start

Start the reference server in the foreground (`python3 "$M0S/m0_server.py" serve`)
or background (`nohup python3 "$M0S/m0_server.py" serve > "$HOME/.local/share/coco-m0/server.log" 2>&1 &`).
Key environment variables: `M0_HOST` (`127.0.0.1`), `M0_PORT` (`8787`), `M0_DB`,
`M0_SIDECAR_DIR`, `M0_BUSY_TIMEOUT_MS` (`10000`), `M0_PROJECT`, `M0_SOURCE_TOOL`.

### /m0 mcp

`m0_mcp.py` exposes two stdio JSON-RPC tools (`m0_remember` and `m0_recall`),
preferring loopback HTTP (`M0_BASE_URL`, default `http://127.0.0.1:8787`) and
falling back to the local SQLite store directly when no server is listening.
See `systems/m0/README.md` for optional MCP client setup when the user wants
persistent MCP registration.

### /m0 hooks

Automatic capture is opt-in; do not edit user settings files without asking.
Session-end hook example:

```bash
python3 "$HOME/.claude/skills/m0/scripts/m0_server.py" write \
  --project "$(basename "$PWD")" --kind session_end --source-tool claude-code \
  --branch "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" \
  --head-sha "$(git rev-parse --short HEAD 2>/dev/null)" \
  --text "Session ended."
```

### /m0 verify

```bash
bash systems/m0/tests/m0-smoke.sh
```

Runs 27 assertions in a throwaway directory on an ephemeral port (round trip,
idempotency, locked-store sidecar spool, restart drain, and MCP stdio tools).

### /m0 privacy

Nothing leaves the machine. The reference server binds to `127.0.0.1:8787` with
no outbound network calls and no telemetry. The store is a plain SQLite file
(`$XDG_DATA_HOME/coco-m0/thread.db`): inspect with `sqlite3`, back up with `cp`,
or remove to delete all local entries.

## When to reach for this

- **Use `/m0-recall`** at session start or when picking up work from another tool.
- **Use `/m0-remember`** after a step lands, a decision is made, or something is verified.
- **Use `/m0-handoff`** before context is compacted or a session ends.
- **Use `/m0` (this skill)** for the reference server, store, spool, hooks, and MCP wiring.
