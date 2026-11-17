<purpose>
Guide the user through MVP-mode planning for a phase. Prompts for an "As a / I want to / So that" user story, runs SPIDR splitting check on the story, writes the result to ROADMAP.md, and delegates to `/gsd plan-phase` (which auto-detects MVP via the roadmap mode field shipped in PRD Phase 1).
</purpose>

<required_reading>
@~/.claude/get-shit-done/references/user-story-template.md
@~/.claude/get-shit-done/references/spidr-splitting.md
@~/.claude/get-shit-done/references/planner-mvp-mode.md
</required_reading>

<runtime_note>
**Copilot (VS Code):** Use `vscode_askquestions` wherever this workflow calls `AskUserQuestion`. They are equivalent.

**TEXT_MODE fallback:** Set TEXT_MODE=true if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is true. When TEXT_MODE is active, replace every AskUserQuestion call with a plain-text numbered list and ask the user to type their choice number.
</runtime_note>

<process>

## 1. Parse and validate phase argument

Extract the phase number from `$ARGUMENTS` (integer or decimal like `2.1`). Optional flag: `--force` (allow operating on `in_progress` / `completed` phases).

If no argument:
```
ERROR: Phase number required
Usage: /gsd mvp-phase <phase-number>
Example: /gsd mvp-phase 1
Example: /gsd mvp-phase 2.1
```
Exit.

Normalize per `@~/.claude/get-shit-done/references/phase-argument-parsing.md` (zero-pad integer phases to two digits).

## 2. Validate phase exists and check status

```bash
PHASE_INFO=$(gsd-sdk query roadmap.get-phase "${PHASE}")
PHASE_FOUND=$(echo "$PHASE_INFO" | jq -r '.found')
PHASE_NAME=$(echo "$PHASE_INFO" | jq -r '.phase_name')
PHASE_GOAL=$(echo "$PHASE_INFO" | jq -r '.goal')
PHASE_MODE=$(echo "$PHASE_INFO" | jq -r '.mode // ""')
PHASE_COMPLETE=$(echo "$PHASE_INFO" | jq -r '.roadmap_complete // false')

ANALYZE=$(gsd-sdk query roadmap.analyze)
if [[ "$ANALYZE" == @file:* ]]; then ANALYZE=$(cat "${ANALYZE#@file:}"); fi
DISK_STATUS=$(echo "$ANALYZE" | jq -r --arg p "$PHASE" '.phases[] | select((.phase_number|tostring)==$p) | .disk_status' | head -1)
if [[ "$DISK_STATUS" == "complete" || "$PHASE_COMPLETE" == "true" ]]; then
  STATUS="completed"
elif [[ "$DISK_STATUS" == "planned" || "$DISK_STATUS" == "partial" ]]; then
  STATUS="in_progress"
else
  STATUS="not_started"
fi
```

If `PHASE_FOUND` is `false`: error and exit. Suggest `/gsd add-phase` or `/gsd insert-phase` to create the phase first.

**Status guard.** If the phase is `in_progress` (has plans but not complete) or `completed`, refuse unless `--force` is in `$ARGUMENTS`:

```text
ERROR: Phase ${PHASE} is currently ${STATUS}.
Converting an active or completed phase to MVP mode mid-flight will
invalidate any existing plans and summaries.

To proceed anyway: /gsd mvp-phase ${PHASE} --force
```

**Already-MVP guard.** If `PHASE_MODE` is already `mvp`, surface this and ask whether to re-prompt the user story or abort:

> "Phase ${PHASE} is already in MVP mode with goal: «${PHASE_GOAL}». Re-run user-story prompts and SPIDR check?"

Use `AskUserQuestion` with options [Re-prompt / Abort]. On Abort, exit cleanly. On Re-prompt, proceed.

## 3. User story prompts

Run three sequential `AskUserQuestion` calls. Each is free-text. After all three, assemble into the canonical sentence per `@~/.claude/get-shit-done/references/user-story-template.md`:

**Prompt 1 — As a:**
> "As a [user role]?"
> (Examples: "new user", "admin", "signed-in customer", "API consumer")

**Prompt 2 — I want to:**
> "I want to [capability]?"
> (Examples: "register and log in", "upload a CSV", "see my dashboard")

**Prompt 3 — So that:**
> "So that [outcome]?"
> (Examples: "I can access my account", "I can bulk-import contacts", "I can see at a glance what needs attention")

Assemble:

```
USER_STORY="As a ${ROLE}, I want to ${CAPABILITY}, so that ${OUTCOME}."
```

If any of the three answers is empty or whitespace-only, error and re-prompt that single field. Do NOT proceed with a partial story.

**Validate via the centralized User Story validator.** The verb owns the canonical regex `/^As a .+, I want to .+, so that .+\.$/` and surfaces per-error guidance:

```bash
USER_STORY_RESULT=$(gsd-sdk query user-story.validate --story "$USER_STORY")
if [ "$(echo "$USER_STORY_RESULT" | jq -r '.valid')" != "true" ]; then
  echo "$USER_STORY_RESULT" | jq -r '.errors[]' >&2
  # Re-prompt the offending field(s) per surfaced errors, then re-run validation.
  # Do not abort the workflow on first invalid draft.
  RE_PROMPT_USER_STORY=true
fi
```

This guarantees the goal stored in ROADMAP.md will satisfy the same guard the verifier applies later.
If `RE_PROMPT_USER_STORY=true`, re-run only the offending prompt field(s), rebuild `USER_STORY`, and validate again before continuing.

## 4. SPIDR splitting check

Run the SPIDR rules from `@~/.claude/get-shit-done/references/spidr-splitting.md`. Briefly:

**Trigger evaluation.** Check the assembled `USER_STORY` against the four size signals from the reference (compound capabilities, multi-actor, length > 120 chars, vague capability). If none fire, **skip SPIDR** entirely — go to step 5.

**If SPIDR triggers.**

a) Restate the story to the user:

> "Your story: «${USER_STORY}»
>
> This story has [signal description, e.g., 'two compound capabilities joined by and']. Splitting it into multiple phases will produce a cleaner Walking Skeleton and reduce the risk of mid-phase scope creep.
