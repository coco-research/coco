---
name: m0-recall
description: "Read the recent M0 operational thread for a project, newest first, to pick up work started in this or another tool. Answers 'where were we' and 'what is next' before asking the user to repeat context. Local SQLite, no embeddings, no network. Triggers on: 'm0 recall', 'where were we', 'what did we do last time', 'catch me up', 'resume context', 'read the thread', 'what is next'."
---

# /m0-recall — Read the Operational Thread

The read path for M0. Returns the most recent entries for a project, newest
first, with the `next_step` and `last_verified` that were recorded when they were
still true.

Retrieval is by project, kind and recency — there is no semantic search. That is
the whole query model, and it is why this returns in milliseconds.

## Quick Reference

```bash
M0="${M0_BASE_URL:-http://127.0.0.1:8787}"
M0S="$HOME/.claude/skills/m0/scripts"

# The recent thread for a project
curl -s "$M0/api/brain/thread?project=acme-web&limit=10" | python3 -m json.tool

# Just the handoffs
curl -s "$M0/api/brain/thread?project=acme-web&kind=compact_checkpoint&limit=3"

# Without a server (same store)
python3 "$M0S/m0_server.py" read --project acme-web --limit 10
```

If the MCP tools are wired (`/m0 mcp`), call `m0_recall` directly — it returns the
same data already formatted for reading.

## Parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| `project` | all projects | Omit only when you genuinely want every project. |
| `limit` | 20 | Capped at 500. |
| `kind` | all kinds | `step_done`, `compact_checkpoint`, `session_end`, `lane_dispatched`, `lane_result`, `ambient_signal`. An unknown value is rejected. |

## Procedure

1. **Resolve the project key** the same way the write path does: `$M0_PROJECT`, else
   the repository or directory name.
2. **Start broad, then narrow.** `limit=10` with no `kind` filter shows what has
   been happening. If the thread is long, `kind=compact_checkpoint` gives the
   handoffs, which is usually the fastest way to orient.
3. **Read the newest entry first.** It carries the freshest `next_step`. Older
   `next_step` values have usually been superseded — do not act on a stale one.
4. **Summarise for the user in three lines:** where the work stands, what was last
   verified, and what the recorded next step is. Then say what you intend to do.
5. **Check `source_tool` and `branch`** on the entries you rely on. An entry written
   by another tool on another branch may not describe the tree you are looking at.
6. **Verify before building on a claim.** `last_verified` records what someone said
   they checked, at some earlier point. If it matters now, re-run it.

## Reading the response

```json
{
  "project": "acme-web",
  "count": 2,
  "pending_sidecars": 0,
  "degraded": null,
  "entries": [ { "ts": "…", "kind": "step_done", "text": "…", "next_step": "…" } ]
}
```

| Signal | What it means |
|--------|---------------|
| `count: 0` | Nothing recorded for that project. Check the project key before concluding the thread is empty — a typo reads as "no memory". |
| `"pending": true` on an entry | It is still in the sidecar spool, not yet in the store. Real, and readable, but not durable until the next drain. |
| `pending_sidecars > 0` | Some writes are spooled. Run `python3 "$M0S/m0_server.py" drain`. |
| `degraded` set | The store could not be read — another process holds the lock — so the entries shown may be only the spooled ones. Say so; do not present a partial thread as complete. |

## When to call this

- **At the start of a session**, before asking the user what you were doing.
- **When picking up work started in another tool** — the thread is shared, so a
  session in one editor can read what another wrote.
- **After a context compaction**, to recover the operational state rather than
  re-reading the whole history.
- **Before re-doing anything expensive.** The thread often already records the
  result, and whether it was verified.

## Limits, stated plainly

- No semantic search, no ranking, no similarity. Recency and `kind`, nothing else.
- No entity or relationship extraction, so there is no "everything about X" query.
- No summarisation. A long thread is long; `compact_checkpoint` entries are the
  compression, and only because someone wrote them.
- Only what was explicitly written is there. Nothing is captured automatically
  unless a hook was installed (`/m0 hooks`).

For semantic retrieval over a knowledge graph, the cognee bundle is the right
tool — see the comparison in `systems/m0/README.md`.
