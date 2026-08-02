---
name: m0
description: "Cross-tool agent memory control plane. Start, stop, and check the M0 operational-thread server; find the store; drain deferred writes; wire the MCP tools and session hooks. Local SQLite, no dependencies, no network. Triggers on: 'm0', 'm0 status', 'start m0', 'cross-tool memory', 'operational thread', 'agent memory server', 'where is my memory stored'."
---

# /m0 — Cross-Tool Agent Memory

M0 keeps one local *operational thread* per project: what was done, what was
verified, what is next. Any tool can write to it and read it back, so a session
that starts cold can continue work another tool began.

Two operations, one SQLite table, standard library only. The wire contract is in
`systems/m0/SPEC.md`; the write path is `/m0-remember`, the read path is
`/m0-recall`, and the session handoff flow is `/m0-handoff`.

## Quick Reference

```bash
M0S="$HOME/.claude/skills/m0/scripts"          # installed location
M0="${M0_BASE_URL:-http://127.0.0.1:8787}"     # server base URL

# Is it up, and where does it store?
curl -s "$M0/api/health" | python3 -m json.tool

# Start it (foreground)
python3 "$M0S/m0_server.py" serve

# Start it in the background, logging to the store directory
nohup python3 "$M0S/m0_server.py" serve > "$HOME/.local/share/coco-m0/server.log" 2>&1 &

# Write and read without any server at all
python3 "$M0S/m0_server.py" write --project my-project --text "Did the thing."
python3 "$M0S/m0_server.py" read  --project my-project --limit 5

# Land any writes that were deferred while the store was busy
python3 "$M0S/m0_server.py" drain
```

If the scripts are not at `$HOME/.claude/skills/m0/scripts`, the bundle was
installed elsewhere: run `bash install.sh --systems m0` from the Coco checkout,
or use the in-repo path `systems/m0/skills/m0/scripts`.

## Sub-commands

### /m0 status — is memory working, and where does it live

```bash
M0="${M0_BASE_URL:-http://127.0.0.1:8787}"
if curl -fsS "$M0/api/health" >/dev/null 2>&1; then
    curl -s "$M0/api/health" | python3 -m json.tool
else
    echo "No M0 server at $M0."
    echo "Direct store access still works:"
    python3 "$HOME/.claude/skills/m0/scripts/m0_server.py" health
fi
```

Report to the user, in this order:

1. **Server** — running at `<url>`, or not running (and that this is fine; the CLI
   and the MCP tools both fall back to the store directly).
2. **Store** — the `db` path and the `rows` count. This is the whole dataset.
3. **Pending** — if `pending_sidecars` is above zero, some writes are spooled but
   not yet landed. Run `drain`.
4. **Degraded** — if `degraded` is set, another process holds the write lock.
   Reads still work; writes will defer rather than fail.

### /m0 start — run the server

Ask which the user wants:

- **Foreground** for a quick session: `python3 "$M0S/m0_server.py" serve`
- **Background** for daily use: the `nohup` line above.
- **Nothing** — the CLI and MCP tools work against the store directly. A server
  is only needed when several tools should share one process, or when something
  can only speak HTTP.

Useful flags and variables:

| Setting | Effect |
|---------|--------|
| `--port` / `M0_PORT` | Listen port (default 8787) |
| `--host` / `M0_HOST` | Bind address (default `127.0.0.1`; anything else warns, there is no auth) |
| `--db` / `M0_DB` | Store path (default `$XDG_DATA_HOME/coco-m0/thread.db`) |
| `--busy-timeout-ms` / `M0_BUSY_TIMEOUT_MS` | Per-call SQLite busy timeout (default 10000) |
| `M0_PROJECT` | Default project when a caller omits one |
| `M0_SOURCE_TOOL` | Stamped on writes, so you can tell which tool wrote what |

Never set `M0_BUSY_TIMEOUT_MS` to a large value. A long wait inside a shutdown
hook is indistinguishable from a hang; the deferred-write path exists so waiting
is never necessary.

### /m0 mcp — wire the two tools

```bash
claude mcp add coco-m0 -- python3 "$HOME/.claude/skills/m0/scripts/m0_mcp.py"
claude mcp list          # confirm it is registered
```

That exposes `m0_remember` and `m0_recall` as tools the agent can call directly,
which is the lowest-friction way to make memory habitual. For editors that read a
project `.mcp.json`, the equivalent entry is:

```json
{
  "mcpServers": {
    "coco-m0": {
      "command": "python3",
      "args": ["<absolute path>/skills/m0/scripts/m0_mcp.py"],
      "env": { "M0_PROJECT": "<this project>" }
    }
  }
}
```

The MCP server prefers the HTTP server and falls back to the store directly when
nothing is listening, so either mode works. Each result reports which path served
it under `via`.

### /m0 hooks — capture without being asked

Automatic capture is opt-in. These are recipes for the user to install; **do not
edit the user's settings files without asking first.** Show the snippet, explain
what it does, and let them decide.

Session end, so a closing session always leaves a trace:

```bash
python3 "$HOME/.claude/skills/m0/scripts/m0_server.py" write \
  --project "$(basename "$PWD")" --kind session_end \
  --source-tool claude-code \
  --branch "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" \
  --head-sha "$(git rev-parse --short HEAD 2>/dev/null)" \
  --text "Session ended."
```

This is exactly the case the deferred-write path was built for: if the store is
locked at that moment, the entry is spooled to a sidecar file and lands on the
next start rather than being lost.

Session start, to inject the thread into a fresh session:

```bash
python3 "$HOME/.claude/skills/m0/scripts/m0_server.py" read \
  --project "$(basename "$PWD")" --limit 10
```

### /m0 drain — land deferred writes

```bash
python3 "$HOME/.claude/skills/m0/scripts/m0_server.py" drain
# {"drained": 1, "skipped": 0, "quarantined": 0}
```

- `drained` — entries moved from the spool into the store.
- `skipped` — the store was still busy; they stay spooled for next time.
- `quarantined` — files that were not valid entries, renamed `*.json.bad` so they
  stop blocking the queue. Inspect them; they are plain JSON.

A server drains automatically on start, so this is only needed when running
serverless or after an unusual amount of write contention.

### /m0 verify — prove it works

```bash
bash systems/m0/tests/m0-smoke.sh
```

27 assertions in a throwaway directory on an ephemeral port: the round trip,
idempotency, a deferred write under a genuinely locked store, the drain on
restart, and the MCP tools over stdio. It touches no existing store. Run it
before trusting a change to this bundle, and quote the output rather than
summarising it.

### /m0 privacy — what leaves the machine

Nothing. The store is a SQLite file on local disk, the server binds to loopback,
there are no outbound calls in the request path and no telemetry. To inspect,
back up or forget:

```bash
DB="$(python3 "$HOME/.claude/skills/m0/scripts/m0_server.py" health | python3 -c 'import json,sys;print(json.load(sys.stdin)["db"])')"
sqlite3 "$DB" "SELECT ts, kind, substr(text,1,60) FROM operational_thread ORDER BY ts DESC LIMIT 10;"
cp "$DB" ~/m0-backup.db     # back up
rm "$DB"                    # forget everything
```

## When to reach for this

- **Use `/m0-recall`** at the start of a session, or when picking up work started
  elsewhere, before asking the user to repeat context.
- **Use `/m0-remember`** after a step lands, a decision is made, or something is
  verified.
- **Use `/m0-handoff`** before context is compacted or a session ends.
- **Use `/m0` (this skill)** for the plumbing: server, store, spool, wiring.

M0 answers "where were we and what is next". It does not do semantic search,
entity extraction or summarisation — see the comparison with the cognee bundle in
`systems/m0/README.md` before choosing.
