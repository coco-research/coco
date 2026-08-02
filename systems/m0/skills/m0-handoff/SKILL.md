---
name: m0-handoff
description: "Session handoff and resume for M0. Write a compact_checkpoint before a session ends or context is compacted, and resume from the latest one at the start of a session in any tool. Turns a cold start into a continuation. Triggers on: 'm0 handoff', 'hand off', 'session handoff', 'save session state', 'resume where we left off', 'pick up where we left off', 'before I compact', 'end of session', 'continue in Cursor', 'continue in Claude Code'."
---

# /m0-handoff — Hand Off and Resume

Two halves of one flow, both against the M0 operational thread:

- **Hand off** — write a `compact_checkpoint` that a session with no other context
  could act on.
- **Resume** — read the latest one and continue, in this tool or another.

This is what M0 exists for. Everything else in the bundle supports it.

## Quick Reference

```bash
M0="${M0_BASE_URL:-http://127.0.0.1:8787}"
M0S="$HOME/.claude/skills/m0/scripts"
PROJECT="${M0_PROJECT:-$(basename "$PWD")}"

# Hand off
curl -s -X POST "$M0/api/brain/checkpoint" -H 'Content-Type: application/json' -d "$(python3 - <<'PY'
import json, os, subprocess
def git(*a):
    try: return subprocess.check_output(("git",)+a, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception: return None
print(json.dumps({
  "project": os.environ.get("M0_PROJECT") or os.path.basename(os.getcwd()),
  "kind": "compact_checkpoint",
  "source_tool": "claude-code",
  "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
  "head_sha": git("rev-parse", "--short", "HEAD"),
  "text": "<what state the work is in>",
  "next_step": "<the single next action>",
  "last_verified": "<command and its actual result>",
  "meta_json": {"open_questions": ["<anything unresolved>"]},
}))
PY
)"

# Resume
curl -s "$M0/api/brain/thread?project=$PROJECT&kind=compact_checkpoint&limit=1" | python3 -m json.tool
```

Serverless equivalents, same store:

```bash
python3 "$M0S/m0_server.py" write --project "$PROJECT" --kind compact_checkpoint \
  --text "…" --next-step "…" --last-verified "…" \
  --branch "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" \
  --head-sha "$(git rev-parse --short HEAD 2>/dev/null)"

python3 "$M0S/m0_server.py" read --project "$PROJECT" --kind compact_checkpoint --limit 1
```

## Handing off

Write one before the context window is compacted, before a session ends, and
before switching tools. Do not wait to be asked.

1. **Resolve the project key** — `$M0_PROJECT`, else the repository or directory name.
   The same value the earlier entries used; check with `/m0-recall` if unsure.
2. **Write the four things** that a stranger needs:

   | Field | What belongs there |
   |-------|--------------------|
   | `text` | Where the work stands. What is done, what is half-done, what is broken. Prose, no jargon from this conversation. |
   | `next_step` | The single next action, concrete enough to start on. One action, not a plan. |
   | `last_verified` | The command that was run and what it actually printed. Empty if nothing was verified. |
   | `meta_json` | Anything structured worth keeping: `{"open_questions": [...], "files": [...], "pr": 42}`. |

3. **Include `branch` and `head_sha`.** Without them a reader cannot tell whether
   the checkpoint describes the tree in front of them.
4. **Set `source_tool`** to the tool you are running in, so the next reader knows
   where the work happened.
5. **Confirm the response.** `deferred: true` means the store was busy and the entry
   is spooled to a sidecar file: real, readable, and landing on the next drain, but
   say so rather than reporting a clean write.

### What a good handoff looks like

```json
{
  "kind": "compact_checkpoint",
  "text": "Auth middleware refactor is done and green. The admin router still uses the old wrapper, so admin requests bypass the new nonce check.",
  "next_step": "Replace the old wrapper in routers/admin.py with require_session, then re-run tests/admin.",
  "last_verified": "pytest tests/auth tests/api -q: 214 passed, 0 failed",
  "branch": "feat/auth",
  "head_sha": "9f2c1ab",
  "meta_json": {"open_questions": ["Should legacy tokens keep working past the cutover?"]}
}
```

The failure mode to avoid is a checkpoint that only makes sense to the session
that wrote it: "continued the refactor, tests mostly fine, next step as
discussed". Assume the reader has nothing but this row.

## Resuming

1. **Fetch the latest checkpoint** for the project (`kind=compact_checkpoint`,
   `limit=1`). If there is none, fall back to the full thread via `/m0-recall`.
2. **Reconcile it with reality before acting.** The checkpoint is a claim from an
   earlier moment:

   ```bash
   git rev-parse --abbrev-ref HEAD; git rev-parse --short HEAD; git status --short
   ```

   Same branch and sha means the description probably still holds. Different, or a
   dirty tree, means the world moved — read the newer entries too, and re-run
   whatever `last_verified` claims if you are about to build on it.
3. **Tell the user what you found**, in three lines: where the work stands, what
   was last verified, what the recorded next step is. Then say what you will do.
4. **Ask before acting on a stale next step.** If the recorded next step no longer
   fits the tree, say so and propose the alternative rather than following it
   mechanically.
5. **Write the next entry as you go**, with `/m0-remember`, so the thread does not
   go quiet again until the following handoff.

## Crossing tools

The thread is one local store, keyed by project, with `source_tool` on every row.
So "finish this in the other editor" is just: hand off here, resume there.

- Use the **same project key** in both tools. `M0_PROJECT` in each tool's
  environment is the reliable way; a mismatch produces two threads that each look
  empty.
- Set **`source_tool` honestly** in both, so a reader can tell which tool made a
  claim.
- Nothing syncs between machines. One machine, one thread.

## Automating the handoff

A session-end hook makes a handoff unconditional rather than remembered — see
`/m0 hooks` for the recipe. It writes a `session_end` entry with the branch and
sha even if the agent forgot to write a checkpoint, and because a shutdown hook
runs at a bad moment, this is precisely the case the deferred-write path was built
for: a locked store spools the entry instead of dropping it.

A hook cannot know what the work state was, only that the session ended. It is a
floor, not a substitute for an explicit `compact_checkpoint`.
