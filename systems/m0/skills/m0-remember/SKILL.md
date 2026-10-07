---
name: m0-remember
description: "Use when the user says 'm0 remember', 'record what we did', 'note for next session' or 'write a checkpoint', or after finishing a step worth handing to the next session. Appends one entry to the M0 thread (re-sending writes a second entry unless you pass the same `id`)."
---

# /m0-remember — Write to the Operational Thread

The write path for M0. One call appends one entry to the shared thread for a
project.

The token is read from ~/.coco/m0-token on each call; never print it.

## Quick Reference

```bash
M0="${COCO_M0_URL:-http://127.0.0.1:8000}"

curl -s -X POST "$M0/api/brain/checkpoint" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $(cat ~/.coco/m0-token)" \
  -d '{"project":"acme-web","kind":"step_done",
       "text":"Fixed the token refresh race in the auth middleware.",
       "next_step":"Add a regression test for two concurrent refreshes.",
       "last_verified":"pytest tests/auth -q: 31 passed",
       "source_tool":"claude_code"}'
```

If the MCP tool is wired (`/m0 mcp`), call `m0` in `remember` mode directly —
same endpoint, fewer moving parts.

## Fields

| Field | Required | What to put in it |
|-------|----------|-------------------|
| `project` | yes | The project key. Use one stable value per project — the repository or directory name is the usual choice. Getting this wrong splits the thread. |
| `text` | yes | What happened, in one or two plain sentences. Capped at 400 characters and redacted by the daemon. Written for a reader with no other context. |
| `kind` | no | Defaults to `step_done`. See the table below. |
| `next_step` | no | The single next action. Concrete enough to act on without re-deriving it. |
| `last_verified` | no | What was actually checked, and how. A command and its result, not an impression. |
| `session_id` | no | Session identifier, when known. |
| `role` | no | The role the entry was written under, when it matters. |
| `source_tool` | no | Which tool is writing: `claude_code`, `cococode`, `ambient`, `manual`, `hook`, `paperclip`. Fill it in — it is what makes the thread legible across tools. |
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

An unknown `kind` is rejected, deliberately: a typo would create a category no
reader looks in.

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
5. **A durable Lab decision or ruling is not an m0-remember.** It becomes a
   decision record via `decide new` (HQ commits records); the thread gets at most
   a `step_done` pointing at it.

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

- **Local-only.** Loopback daemon, no outbound calls, no telemetry. Text fields
  are capped at 400 characters and redacted by the daemon.
- There is no offline path: if the daemon is down, say so and stop; do not write anywhere else.
- **Reading back:** `/m0-recall`. **Handoffs:** `/m0-handoff`. **Plumbing:** `/m0`.
