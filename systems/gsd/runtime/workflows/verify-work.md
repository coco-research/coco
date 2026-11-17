<purpose>
Validate built features through conversational testing with persistent state. Creates UAT.md that tracks test progress, survives /clear, and feeds gaps into /gsd:plan-phase --gaps.

User tests, Claude records. One test at a time. Plain text responses.
</purpose>

<available_agent_types>
Valid GSD subagent types (use exact names — do not fall back to 'general-purpose'):
- gsd-planner — Creates detailed plans from phase scope
- gsd-plan-checker — Reviews plan quality before execution
</available_agent_types>

<philosophy>
**Show expected, ask if reality matches.**

Claude presents what SHOULD happen. User confirms or describes what's different.
- "yes" / "y" / "next" / empty → pass
- Anything else → logged as issue, severity inferred

No Pass/Fail buttons. No severity questions. Just: "Here's what should happen. Does it?"
</philosophy>

<template>
@~/.claude/get-shit-done/templates/UAT.md
</template>

<process>

<step name="initialize" priority="first">
If $ARGUMENTS contains a phase number, load context:

```bash
GSD_WS=""
echo "$ARGUMENTS" | grep -qE -- '--ws[[:space:]]+[^[:space:]]+' && GSD_WS=$(echo "$ARGUMENTS" | grep -oE -- '--ws[[:space:]]+[^[:space:]]+')
PHASE_ARG=$(echo "$ARGUMENTS" | sed -E 's/--ws[[:space:]]+[^[:space:]]+//g' | xargs)

INIT=$(gsd-sdk query init.verify-work "${PHASE_ARG}" ${GSD_WS})
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_PLANNER=$(gsd-sdk query agent-skills gsd-planner)
AGENT_SKILLS_CHECKER=$(gsd-sdk query agent-skills gsd-plan-checker)
```

Parse JSON for: `planner_model`, `checker_model`, `commit_docs`, `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `has_verification`, `uat_path`.

```bash
# MVP mode detection via the centralized phase.mvp-mode resolver.
# verify-work has no --mvp CLI flag (mode is inherited from the planned phase),
# so we omit --cli-flag — the verb falls through roadmap → config → false.
MVP_MODE=$(gsd-sdk query phase.mvp-mode "${phase_number}" ${GSD_WS} --pick active)
```
</step>

<step name="check_active_session">
**First: Check for active UAT sessions**

```bash
(find .planning/phases -name "*-UAT.md" -type f 2>/dev/null || true)
```

**If active sessions exist AND no $ARGUMENTS provided:**

Read each file's frontmatter (status, phase) and Current Test section.

Display inline:

```
## Active UAT Sessions

| # | Phase | Status | Current Test | Progress |
|---|-------|--------|--------------|----------|
| 1 | 04-comments | testing | 3. Reply to Comment | 2/6 |
| 2 | 05-auth | testing | 1. Login Form | 0/4 |

Reply with a number to resume, or provide a phase number to start new.
```

Wait for user response.

- If user replies with number (1, 2) → Load that file, go to `resume_from_file`
- If user replies with phase number → Treat as new session, go to `create_uat_file`

**If active sessions exist AND $ARGUMENTS provided:**

Check if session exists for that phase. If yes, offer to resume or restart.
If no, continue to `create_uat_file`.

**If no active sessions AND no $ARGUMENTS:**

```
No active UAT sessions.

Provide a phase number to start testing (e.g., /gsd:verify-work 4)
```

**If no active sessions AND $ARGUMENTS provided:**

Continue to `create_uat_file`.
</step>

<step name="automated_ui_verification">
**Automated UI Verification (when Playwright-MCP is available)**

Before running manual UAT, check whether this phase has a UI component and whether
`mcp__playwright__*` or `mcp__puppeteer__*` tools are available in the current session.

```
UI_PHASE_FLAG=$(gsd-sdk query config-get workflow.ui_phase --raw 2>/dev/null || echo "true")
UI_SPEC_FILE=$(ls "${PHASE_DIR}"/*-UI-SPEC.md 2>/dev/null | head -1)
```

**If Playwright-MCP tools are available in this session (`mcp__playwright__*` tools
respond to tool calls) AND (`UI_PHASE_FLAG` is `true` OR `UI_SPEC_FILE` is non-empty):**

For each UI checkpoint listed in the phase's UI-SPEC.md (or inferred from SUMMARY.md):

1. Use `mcp__playwright__navigate` (or equivalent) to open the component's URL.
2. Use `mcp__playwright__screenshot` to capture a screenshot.
3. Compare the screenshot visually against the spec's stated requirements
   (dimensions, color, layout, spacing).
4. Automatically mark checkpoints as **passed** or **needs review** based on the
   visual comparison — no manual question required for items that clearly match.
5. Flag items that require human judgment (subjective aesthetics, content accuracy)
   and present only those as manual UAT questions.

If automated verification is not available, fall back to the standard manual
checkpoint questions defined in this workflow unchanged. This step is entirely
conditional: if Playwright-MCP is not configured, behavior is unchanged from today.

**Display summary line before proceeding:**
```
UI checkpoints: {N} auto-verified, {M} queued for manual review
```

</step>

<step name="find_summaries">
**Find what to test:**

Use `phase_dir` from init (or run init if not already done).

```bash
ls "$phase_dir"/*-SUMMARY.md 2>/dev/null || true
```

Read each SUMMARY.md to extract testable deliverables.
</step>

<step name="extract_tests">
**MVP-mode UAT framing.** When `MVP_MODE=true`, follow the rules in `@~/.claude/get-shit-done/references/verify-mvp-mode.md`. Briefly:

1. Generate the UAT script in three ordered sections: (a) user-flow walk-through derived from the phase's user-story goal, (b) technical checks (deferred — only run after user flow passes), (c) coverage check (goal-backward, narrowed to the user story's outcome clause).
2. **User-flow steps run first.** Each step is one user action: open, fill, click, type, observe. No HTTP verbs, no JSON shapes, no error codes in user-flow steps.
3. **Technical checks are deferred.** They run AFTER the user flow passes — same checks as non-MVP mode (endpoint schemas, error states, edge cases), just reordered.
4. **If user-flow step N fails, do not advance.** The verdict is FAIL; technical checks do not run. The user can re-run after fixing the underlying flow.

When `MVP_MODE=false` (mode is null, absent, or the phase has no `**Mode:**` line in ROADMAP.md), fall back to the standard UAT generation path — no behavioral change.

**User-story format guard.** When `MVP_MODE=true`, also verify the phase's goal is in User Story format via the centralized validator:

```bash
PHASE_GOAL=$(gsd-sdk query roadmap.get-phase "${phase_number}" ${GSD_WS} --pick goal)
USER_STORY_VALID=$(gsd-sdk query user-story.validate --story "$PHASE_GOAL" --pick valid)
if [ "$USER_STORY_VALID" != "true" ]; then
  echo "Phase ${phase_number} has '**Mode:** mvp' in ROADMAP.md but the **Goal:** is not in user-story format."
  echo "Run /gsd mvp-phase ${phase_number} to set a user-story goal before verifying."
  exit 1
fi
```

The verb owns the canonical regex `/^As a .+, I want to .+, so that .+\.$/` and returns slot extractions plus per-error guidance when invalid. Halt UAT generation on failure — never attempt to derive user-flow steps from a non-User-Story goal (low-quality UAT).

**Extract testable deliverables from SUMMARY.md:**

Parse for:
1. **Accomplishments** - Features/functionality added
2. **User-facing changes** - UI, workflows, interactions

Focus on USER-OBSERVABLE outcomes, not implementation details.

For each deliverable, create a test:
- name: Brief test name
- expected: What the user should see/experience (specific, observable)

Examples:
- Accomplishment: "Added comment threading with infinite nesting"
  → Test: "Reply to a Comment"
  → Expected: "Clicking Reply opens inline composer below comment. Submitting shows reply nested under parent with visual indentation."

Skip internal/non-observable items (refactors, type changes, etc.).

**Cold-start smoke test injection:**

After extracting tests from SUMMARYs, scan the SUMMARY files for modified/created file paths. If ANY path matches these patterns:

`server.ts`, `server.js`, `app.ts`, `app.js`, `index.ts`, `index.js`, `main.ts`, `main.js`, `database/*`, `db/*`, `seed/*`, `seeds/*`, `migrations/*`, `startup*`, `docker-compose*`, `Dockerfile*`

Then **prepend** this test to the test list:

- name: "Cold Start Smoke Test"
- expected: "Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application from scratch. Server boots without errors, any seed/migration completes, and a primary query (health check, homepage load, or basic API call) returns live data."

This catches bugs that only manifest on fresh start — race conditions in startup sequences, silent seed failures, missing environment setup — which pass against warm state but break in production.
</step>

<step name="create_uat_file">
**Create UAT file with all tests:**

```bash
mkdir -p "$PHASE_DIR"
```

Build test list from extracted deliverables.

Create file:

```markdown
---
status: testing
phase: XX-name
source: [list of SUMMARY.md files]
started: [ISO timestamp]
updated: [ISO timestamp]
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 1
name: [first test name]
expected: |
  [what user should observe]
awaiting: user response

## Tests

### 1. [Test Name]
expected: [observable behavior]
result: [pending]

### 2. [Test Name]
expected: [observable behavior]
result: [pending]

...

## Summary

total: [N]
passed: 0
issues: 0
pending: [N]
skipped: 0

## Gaps

[none yet]
```

Write to `.planning/phases/XX-name/{phase_num}-UAT.md`

Proceed to `present_test`.
</step>

<step name="present_test">
**Present current test to user:**

Render the checkpoint from the structured UAT file instead of composing it freehand:

```bash
CHECKPOINT=$(gsd-sdk query uat.render-checkpoint --file "$uat_path" --raw)
if [[ "$CHECKPOINT" == @file:* ]]; then CHECKPOINT=$(cat "${CHECKPOINT#@file:}"); fi
```

Display the returned checkpoint EXACTLY as-is:

```
{CHECKPOINT}
```

**Critical response hygiene:**
- Your entire response MUST equal `{CHECKPOINT}` byte-for-byte.
- Do NOT add commentary before or after the block.
- If you notice protocol/meta markers such as `to=all:`, role-routing text, XML system tags, hidden instruction markers, ad copy, or any unrelated suffix, discard the draft and output `{CHECKPOINT}` only.


**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
Wait for user response (plain text, no AskUserQuestion).
</step>

<step name="process_response">
**Process user response and update file:**

**If response indicates pass:**
- Empty response, "yes", "y", "ok", "pass", "next", "approved", "✓"

Update Tests section:
```
### {N}. {name}
expected: {expected}
result: pass
```

**If response indicates skip:**
- "skip", "can't test", "n/a"

Update Tests section:
```
### {N}. {name}
expected: {expected}
result: skipped
reason: [user's reason if provided]
```

**If response indicates blocked:**
- "blocked", "can't test - server not running", "need physical device", "need release build"
- Or any response containing: "server", "blocked", "not running", "physical device", "release build"

Infer blocked_by tag from response:
- Contains: server, not running, gateway, API → `server`
- Contains: physical, device, hardware, real phone → `physical-device`
- Contains: release, preview, build, EAS → `release-build`
- Contains: stripe, twilio, third-party, configure → `third-party`
- Contains: depends on, prior phase, prerequisite → `prior-phase`
- Default: `other`

Update Tests section:
```
### {N}. {name}
expected: {expected}
result: blocked
blocked_by: {inferred tag}
reason: "{verbatim user response}"
```

Note: Blocked tests do NOT go into the Gaps section (they aren't code issues — they're prerequisite gates).

**If response is anything else:**
- Treat as issue description

Infer severity from description:
- Contains: crash, error, exception, fails, broken, unusable → blocker
- Contains: doesn't work, wrong, missing, can't → major
- Contains: slow, weird, off, minor, small → minor
- Contains: color, font, spacing, alignment, visual → cosmetic
- Default if unclear: major

Update Tests section:
```
### {N}. {name}
expected: {expected}
result: issue
reported: "{verbatim user response}"
severity: {inferred}
```

Append to Gaps section (structured YAML for plan-phase --gaps):
```yaml
- truth: "{expected behavior from test}"
  status: failed
  reason: "User reported: {verbatim user response}"
  severity: {inferred}
  test: {N}
  artifacts: []  # Filled by diagnosis
  missing: []    # Filled by diagnosis
```

**After any response:**

Update Summary counts.
Update frontmatter.updated timestamp.

If more tests remain → Update Current Test, go to `present_test`
If no more tests → Go to `complete_session`
</step>

<step name="resume_from_file">
**Resume testing from UAT file:**

Read the full UAT file.

Find first test with `result: [pending]`.

Announce:
```
Resuming: Phase {phase} UAT
Progress: {passed + issues + skipped}/{total}
Issues found so far: {issues count}

Continuing from Test {N}...
```

Update Current Test section with the pending test.
Proceed to `present_test`.
</step>

<step name="complete_session">
**Complete testing and commit:**

**Determine final status:**

Count results:
- `pending_count`: tests with `result: [pending]`
- `blocked_count`: tests with `result: blocked`
- `skipped_no_reason`: tests with `result: skipped` and no `reason` field

```
if pending_count > 0 OR blocked_count > 0 OR skipped_no_reason > 0:
  status: partial
  # Session ended but not all tests resolved
else:
  status: complete
  # All tests have a definitive result (pass, issue, or skipped-with-reason)
```

Update frontmatter:
- status: {computed status}
- updated: [now]
