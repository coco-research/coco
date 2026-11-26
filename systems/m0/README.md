# M0: m0/1 L0 Wire Contract and Stdlib Reference Server

This bundle ships the `m0/1` L0 wire contract ([`SPEC.md`](SPEC.md)) and its
Python standard-library reference server (`m0_server.py`) plus stdio MCP wrapper
(`m0_mcp.py`). Together they provide a small local *operational thread* for
agents: one SQLite table recording what was done, what was verified, and what
happens next, so a session starting cold in one tool can pick up work left by
another.

The wire contract defines two core endpoints (`POST /api/brain/checkpoint` and
`GET /api/brain/thread`) and two optional endpoints (`GET /api/health` and
`POST /api/brain/sidecars/drain`). The stdlib reference server started below
implements all four with Python standard library only, no outbound network
calls, and no telemetry.

---

## Install

```bash
bash install.sh --systems m0
```

Or together with other bundles:

```bash
bash install.sh --adapter claude-code --systems brain,m0
```

That wires four skills into your IDE. Nothing runs until you start the server.

### Start the server

```bash
python3 ~/.claude/skills/m0/scripts/m0_server.py serve
# m0 1.0.0 listening on http://127.0.0.1:8787
```

There are no dependencies to install. `python3` (3.9+) and its bundled `sqlite3`
are the whole requirement.

### Wire the MCP tools (optional)

```bash
claude mcp add coco-m0 -- python3 ~/.claude/skills/m0/scripts/m0_mcp.py
```

The MCP server exposes `m0_remember` and `m0_recall`. It prefers the HTTP server
and falls back to the local store directly when nothing is listening, so the
tools work whether or not you keep a server running.

## Skills

| Skill | What it does |
|-------|-------------|
| `/m0` | Status, start/stop, store location, drain, MCP wiring, hook recipes |
| `/m0-remember` | Write one entry to the thread — a step, a decision, a verification |
| `/m0-recall` | Read the recent thread for a project, newest first |
| `/m0-handoff` | Write a handoff before a session ends; resume from one at the start |

## The whole protocol

Two operations. One table. That is all there is.

```bash
# write
curl -s -X POST http://127.0.0.1:8787/api/brain/checkpoint \
  -H 'Content-Type: application/json' \
  -d '{"project":"acme-web","kind":"step_done",
       "text":"Fixed the token refresh race.",
       "next_step":"Add a regression test for concurrent refresh.",
       "last_verified":"pytest tests/auth -q: 31 passed",
       "meta_json":{"pr":42}}'
# {"id":"9a71de71…","ts":"2026-08-01T13:31:26.536Z","ok":true,"deferred":false}

# read
curl -s 'http://127.0.0.1:8787/api/brain/thread?project=acme-web&limit=5'
```

Entries carry a `kind`: `step_done` (a fact or decision, the default),
`compact_checkpoint` (a session handoff), `session_end`, `lane_dispatched`,
`lane_result`, `ambient_signal`.

Four guarantees, all specified in [`SPEC.md`](SPEC.md) and all covered by the
smoke test:

- **Idempotent.** `id` is a content hash. The same write twice leaves one row and
  returns the same response, so retries and re-fired hooks are harmless.
- **Never loses a write.** If the store is briefly locked, the entry is spooled to
  a sidecar file and the response says `deferred: true`; the spool drains on next
  start. This is what makes it safe to call from a shutdown hook.
- **Bounded.** Every database call carries a short, configurable busy timeout
  (10s by default). A caller can always tell "busy" from "hung".
- **Local-only.** SQLite on disk, loopback bind, no outbound calls, no telemetry.

### Where your data lives

`$XDG_DATA_HOME/coco-m0/thread.db`, i.e. `~/.local/share/coco-m0/thread.db` on a
default setup. Override with `M0_DB`. Sidecars sit in `sidecars/` next to it.
It is a plain SQLite file: inspect it with `sqlite3`, back it up with `cp`, delete
it to forget everything. Uninstalling is removing the symlinked skills and that
file.

## Verify it

```bash
bash systems/m0/tests/m0-smoke.sh
```

Smoke assertions in a throwaway directory on an ephemeral port: round trip,
idempotency (including the same metadata re-encoded as a string), the deferred
write under a genuinely locked store, the drain on restart, and the MCP tools
over stdio. It touches no existing store. Point `M0_BASE_URL` at another
implementation to check it against the spec.

## Reference server limits

The bundled stdlib reference server implements the `m0/1` L0 operational thread only:

- **Recency retrieval only.** `GET /api/brain/thread` filters by `project` and
  `kind` and returns entries newest first (capped at 500). It provides no
  semantic search, embeddings, ranking, or graph traversal.
- **Explicit writes only.** The thread grows monotonically as callers post to
  `POST /api/brain/checkpoint` or run `m0_server.py write`. It does not extract
  entities, summarise old entries, or ingest documents automatically.
- **Single-machine, single-store, no authentication.** It binds to loopback
  (`127.0.0.1:8787`) and trusts local callers. `owner_user_id` and `visibility`
  are stored as columns per the wire contract, not enforced. There is no sync or
  replication between machines.

## Layout

```
systems/m0/
├── README.md                       this file
├── SPEC.md                         the wire contract (m0/1)
├── skills/
│   ├── m0/
│   │   ├── SKILL.md                control plane
│   │   └── scripts/
│   │       ├── m0_server.py        reference server + CLI (stdlib only)
│   │       └── m0_mcp.py           MCP server, two tools (stdlib only)
│   ├── m0-remember/SKILL.md        write path
│   ├── m0-recall/SKILL.md          read path
│   └── m0-handoff/SKILL.md         handoff / resume flow
└── tests/m0-smoke.sh               smoke assertions against a live server
```

## License

MIT, matching the Coco core. Written from the `m0/1` specification in this
directory; no third-party code is vendored, and nothing here is derived from any
other implementation.
