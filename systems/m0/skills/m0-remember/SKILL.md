---
name: m0-remember
description: "Write one entry to the M0 operational thread so the next session, in this tool or any other, can continue the work. Records a completed step, a decision, a verification result, or a dispatched lane. Idempotent and local-only. Triggers on: 'remember this', 'm0 remember', 'save to memory', 'log this decision', 'record what we did', 'note for next session', 'write a checkpoint'."
---

# /m0-remember — Write to the Operational Thread

The write path for M0. One call appends one entry to the shared thread for a
project. Writing the same content twice creates one row, so this is safe to call
after every step and safe to retry.

## Quick Reference

```bash
M0="${M0_BASE_URL:-http://127.0.0.1:8787}"
M0S="$HOME/.claude/skills/m0/scripts"

# Over HTTP
curl -s -X POST "$M0/api/brain/checkpoint" \
  -H 'Content-Type: application/json' \
  -d '{"project":"acme-web","kind":"step_done",
       "text":"Fixed the token refresh race in the auth middleware.",
       "next_step":"Add a regression test for two concurrent refreshes.",
       "last_verified":"pytest tests/auth -q: 31 passed",
       "source_tool":"claude-code","meta_json":{"pr":42}}'
# {"id":"9a71de71…","ts":"2026-08-01T13:31:26.536Z","ok":true,"deferred":false}

# Without a server (same store, same guarantees)
python3 "$M0S/m0_server.py" write \
  --project acme-web --kind step_done \
  --text "Fixed the token refresh race in the auth middleware." \
  --next-step "Add a regression test for two concurrent refreshes." \
  --last-verified "pytest tests/auth -q: 31 passed" \
  --source-tool claude-code --meta '{"pr":42}'
```

If the MCP tools are wired (`/m0 mcp`), call `m0_remember` directly instead — same
endpoint, fewer moving parts, and `meta` takes a real JSON object.

## Fields

| Field | Required | What to put in it |
|-------|----------|-------------------|
| `project` | yes | The project key. Use one stable value per project — the repository or directory name is the usual choice. Getting this wrong splits the thread. |
| `text` | yes | What happened, in one or two plain sentences. Written for a reader with no other context. |
| `kind` | no | Defaults to `step_done`. See the table below. |
| `next_step` | no | The single next action. Concrete enough to act on without re-deriving it. |
| `last_verified` | no | What was actually checked, and how. A command and its result, not an impression. |
| `meta_json` | no | Structured metadata as a JSON object, e.g. `{"pr":42,"tests":"green"}`. |
| `session_id` | no | Session identifier, when known. |
| `source_tool` | no | Which tool is writing. Fill it in — it is what makes the thread legible across tools. |
| `branch`, `head_sha` | no | Version-control position. Worth including whenever the entry is about code. |

Kinds:

| `kind` | Use it for |
|--------|-----------|
| `step_done` | A completed step, a fact, or a decision. The default. |
| `compact_checkpoint` | A session handoff — see `/m0-handoff`. |
| `session_end` | A session closing, usually from a hook. |
| `lane_dispatched` | Work handed to a subagent or parallel lane. |
| `lane_result` | The outcome of that work. |
| `ambient_signal` | Context observed rather than reported. |

An unknown `kind` is rejected with HTTP 400, deliberately: a typo would create a
category no reader looks in.

## Procedure

1. **Resolve the project key.** Use `$M0_PROJECT` if set, otherwise the repository
   or directory name. Reuse whatever earlier entries used — check with
   `/m0-recall` if unsure. Do not invent a variant.
2. **Write one entry per meaningful thing.** A step that landed, a decision with
   its reason, a verification result. Not a running commentary.
3. **Include version-control context** when the entry is about code:

   ```bash
   BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
   SHA="$(git rev-parse --short HEAD 2>/dev/null)"
   ```
4. **Be honest in `last_verified`.** Put the command and its actual result there.
   If nothing was verified, leave it empty. A false verification claim in a
   memory store outlives the session that made it and misleads every later reader.
5. **Check the response.** `{"ok":true,"deferred":false}` means it is durable.
   `"deferred":true` means the store was busy and the entry is spooled to a
   sidecar file — it is not lost and lands on the next drain or server start. Say
   so rather than reporting a clean write.

## Good and bad entries

```
text:          "Fixed the token refresh race in the auth middleware: the retry
                path double-incremented the nonce."
next_step:     "Add a regression test for two concurrent refreshes."
last_verified: "pytest tests/auth -q: 31 passed"
```

```
text:          "Made some progress on auth."          # nothing to act on
next_step:     "Continue."                            # not a next step
last_verified: "Tests should pass now."               # a claim, not a check
```

## Notes

- **Idempotent.** `id` is a SHA-256 of the content fields, `ts` excluded. Re-writing
  identical content returns the identical response and leaves one row. Retry
  freely.
- **Metadata is lenient.** An object, a JSON string, or free text all work: a JSON
  string is parsed and canonicalised, anything else is stored as `{"note": "…"}`.
  It never rejects what it could have kept.
- **Local-only.** SQLite on disk, loopback server, no outbound calls, no telemetry.
- **Reading back:** `/m0-recall`. **Handoffs:** `/m0-handoff`. **Plumbing:** `/m0`.
