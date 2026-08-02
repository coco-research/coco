# M0 — Cross-Tool Agent Memory

A shared *operational thread* for agents: one small local store that records what
was done, what was verified, and what happens next, so a session starting cold in
one tool can pick up work left by another.

M0 is Coco's own memory bundle. It ships a working server, an MCP server, and a
published wire contract ([`SPEC.md`](SPEC.md)). It is deliberately small: one
SQLite table, two endpoints, Python standard library only, no network calls, no
telemetry. It sits alongside the [cognee](#m0-or-cognee) bundle, which solves a
larger problem in a larger way.

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

27 assertions in a throwaway directory on an ephemeral port: round trip,
idempotency (including the same metadata re-encoded as a string), the deferred
write under a genuinely locked store, the drain on restart, and the MCP tools
over stdio. It touches no existing store. Point `M0_BASE_URL` at another
implementation to check it against the spec.

## M0 or cognee

Both bundles give agents memory that outlives a session. They are not the same
size of thing, and the honest summary is that cognee can do much more.

**cognee is a mature knowledge-graph memory platform** (Apache-2.0, developed
independently of Coco; the `systems/cognee/` bundle wires the upstream project in).
It
builds a real graph with embeddings over your content: semantic search, graph
traversal, cross-dataset entity linking, ingestion pipelines for documents and
code, a choice of vector and graph backends. If you want to ask "what do we know
about X" and get an answer assembled from everything you have ever fed it,
cognee is the right tool and M0 is not a substitute.

**M0 is a session-continuity log.** It answers one question — "where were we, and
what is next" — and answers it in a few milliseconds from a file with no server
dependencies beyond `python3`.

| | M0 | cognee |
|---|---|---|
| Problem solved | Cross-tool session continuity | General long-term knowledge memory |
| Storage | One SQLite table | Knowledge graph + vector store (+ relational) |
| Retrieval | Recent entries by project and kind | Semantic, graph traversal, lexical, hybrid |
| Dependencies | Python standard library | Python package plus graph/vector backends |
| Runtime | ~640 lines of stdlib Python, one process — or none | A server and its backing stores |
| Entity extraction | None | Automatic, LLM-assisted |
| Embeddings / LLM calls | None | Yes, by design |
| Network | Loopback only, no outbound calls | Model and backend endpoints as configured |
| Wire contract | Published, `m0/1`, reimplementable | The project's own API |
| Reads across projects | Yes, flat by `project` key | Yes, as graph queries across datasets |

### What M0 does not do

Stated plainly, so you can rule it out quickly:

- **No semantic search.** Retrieval is by project, kind and recency. There is no
  embedding, no ranking, no similarity. "Show me the last 20 entries" is the query
  model. Nothing else.
- **No entity or relationship extraction.** M0 stores the prose you give it. It
  does not discover that two entries mention the same person or module, and there
  is no graph to traverse.
- **No summarisation, compression or consolidation.** The thread grows
  monotonically. Nothing merges old entries or builds higher-level summaries; if
  you want that, write a `compact_checkpoint` yourself.
- **No ingestion.** It does not read your documents, mail, transcripts or
  repository. Every entry arrives because something called the write endpoint.
- **No multi-user story.** `owner_user_id` and `visibility` exist as columns and
  are stamped on every row, but the reference server enforces nothing and has no
  authentication. It binds to loopback and trusts every caller.
- **No automatic capture.** Nothing writes for you until you wire a hook or an
  agent decides to call `m0_remember`. The `/m0` skill has hook recipes; installing
  them is your choice.
- **No conflict resolution or sync.** One local file. No replication, no merge, no
  remote. Two machines are two threads.

### Choosing

- Pick **M0** if you want session continuity across tools today, with nothing to
  operate and nothing leaving the machine; or if you need a memory contract you
  can implement in another language.
- Pick **cognee** if you want a searchable knowledge base with entity linking and
  semantic retrieval, and you are willing to run and feed it.
- Run **both** if that fits: M0 for "where were we", cognee for "what do we know".
  They share no state and do not interfere.

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
└── tests/m0-smoke.sh               27 assertions against a live server
```

## License

MIT, matching the Coco core. Written from the `m0/1` specification in this
directory; no third-party code is vendored, and nothing here is derived from any
other implementation.
