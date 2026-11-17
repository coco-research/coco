<purpose>
Verify phase goal achievement through goal-backward analysis. Check that the codebase delivers what the phase promised, not just that tasks completed.

Executed by a verification subagent spawned from execute-phase.md.
</purpose>

<core_principle>
**Task completion ≠ Goal achievement**

A task "create chat component" can be marked complete when the component is a placeholder. The task was done — but the goal "working chat interface" was not achieved.

Goal-backward verification:
1. What must be TRUE for the goal to be achieved?
2. What must EXIST for those truths to hold?
3. What must be WIRED for those artifacts to function?
4. What must TESTS PROVE for those truths to be evidenced?

Then verify each level against the actual codebase.
</core_principle>

<required_reading>
@~/.claude/get-shit-done/references/verification-patterns.md
@~/.claude/get-shit-done/templates/verification-report.md
</required_reading>

<process>

<step name="load_context" priority="first">
Load phase operation context:

```bash
INIT=$(gsd-sdk query init.phase-op "${PHASE_ARG}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Extract from init JSON: `phase_dir`, `phase_number`, `phase_name`, `has_plans`, `plan_count`.

Then load phase details and list plans/summaries:
```bash
gsd-sdk query roadmap.get-phase "${phase_number}"
grep -E "^| ${phase_number}" .planning/REQUIREMENTS.md 2>/dev/null || true
ls "$phase_dir"/*-SUMMARY.md "$phase_dir"/*-PLAN.md 2>/dev/null || true
```

Load full milestone phases for deferred-item filtering (Step 9b):
```bash
gsd-sdk query roadmap.analyze
```

Extract **phase goal** from ROADMAP.md (the outcome to verify, not tasks), **requirements** from REQUIREMENTS.md if it exists, and **all milestone phases** from roadmap analyze (for cross-referencing gaps against later phases).
</step>

<step name="establish_must_haves">
**Option A: Must-haves in PLAN frontmatter**

Use `gsd-sdk query` verify handlers (or legacy gsd-tools) to extract must_haves from each PLAN:

```bash
for plan in "$PHASE_DIR"/*-PLAN.md; do
  MUST_HAVES=$(gsd-sdk query frontmatter.get "$plan" --field must_haves)
  echo "=== $plan ===" && echo "$MUST_HAVES"
done
```

Returns JSON: `{ truths: [...], artifacts: [...], key_links: [...] }`

Aggregate all must_haves across plans for phase-level verification.

**Option B: Use Success Criteria from ROADMAP.md**

If no must_haves in frontmatter (MUST_HAVES returns error or empty), check for Success Criteria:

```bash
PHASE_DATA=$(gsd-sdk query roadmap.get-phase "${phase_number}" --raw)
```

Parse the `success_criteria` array from the JSON output. If non-empty:
1. Use each Success Criterion directly as a **truth** (they are already written as observable, testable behaviors)
2. Derive **artifacts** (concrete file paths for each truth)
3. Derive **key links** (critical wiring where stubs hide)
4. Document the must-haves before proceeding

Success Criteria from ROADMAP.md are the contract — they override PLAN-level must_haves when both exist.

**Option C: Derive from phase goal (fallback)**

If no must_haves in frontmatter AND no Success Criteria in ROADMAP:
1. State the goal from ROADMAP.md
2. Derive **truths** (3-7 observable behaviors, each testable)
3. Derive **artifacts** (concrete file paths for each truth)
4. Derive **key links** (critical wiring where stubs hide)
5. Document derived must-haves before proceeding
</step>

<step name="verify_truths">
For each observable truth, determine if the codebase enables it.

**Status:** ✓ VERIFIED (all supporting artifacts pass) | ✗ FAILED (artifact missing/stub/unwired) | ? UNCERTAIN (needs human)

For each truth: identify supporting artifacts → check artifact status → check wiring → determine truth status.

**Example:** Truth "User can see existing messages" depends on Chat.tsx (renders), /api/chat GET (provides), Message model (schema). If Chat.tsx is a stub or API returns hardcoded [] → FAILED. If all exist, are substantive, and connected → VERIFIED.
</step>

<step name="verify_artifacts">
Use `gsd-sdk query verify.artifacts` (or legacy gsd-tools) for artifact verification against must_haves in each PLAN:

```bash
for plan in "$PHASE_DIR"/*-PLAN.md; do
  ARTIFACT_RESULT=$(gsd-sdk query verify.artifacts "$plan")
  echo "=== $plan ===" && echo "$ARTIFACT_RESULT"
done
```

Parse JSON result: `{ all_passed, passed, total, artifacts: [{path, exists, issues, passed}] }`

**Artifact status from result:**
- `exists=false` → MISSING
- `issues` not empty → STUB (check issues for "Only N lines" or "Missing pattern")
- `passed=true` → VERIFIED (Levels 1-2 pass)

**Level 3 — Wired (manual check for artifacts that pass Levels 1-2):**
```bash
grep -r "import.*$artifact_name" src/ --include="*.ts" --include="*.tsx"  # IMPORTED
grep -r "$artifact_name" src/ --include="*.ts" --include="*.tsx" | grep -v "import"  # USED
```
WIRED = imported AND used. ORPHANED = exists but not imported/used.

| Exists | Substantive | Wired | Status |
|--------|-------------|-------|--------|
| ✓ | ✓ | ✓ | ✓ VERIFIED |
| ✓ | ✓ | ✗ | ⚠️ ORPHANED |
| ✓ | ✗ | - | ✗ STUB |
| ✗ | - | - | ✗ MISSING |

**Export-level spot check (WARNING severity):**

For artifacts that pass Level 3, spot-check individual exports:
- Extract key exported symbols (functions, constants, classes — skip types/interfaces)
- For each, grep for usage outside the defining file
- Flag exports with zero external call sites as "exported but unused"

This catches dead stores like `setPlan()` that exist in a wired file but are
never actually called. Report as WARNING — may indicate incomplete cross-plan
wiring or leftover code from plan revisions.
</step>

<step name="verify_wiring">
Use `gsd-sdk query verify.key-links` (or legacy gsd-tools) for key link verification against must_haves in each PLAN:

```bash
for plan in "$PHASE_DIR"/*-PLAN.md; do
  LINKS_RESULT=$(gsd-sdk query verify.key-links "$plan")
  echo "=== $plan ===" && echo "$LINKS_RESULT"
done
```

Parse JSON result: `{ all_verified, verified, total, links: [{from, to, via, verified, detail}] }`

**Link status from result:**
- `verified=true` → WIRED
- `verified=false` with "not found" → NOT_WIRED
- `verified=false` with "Pattern not found" → PARTIAL

**Fallback patterns (if key_links not in must_haves):**

| Pattern | Check | Status |
|---------|-------|--------|
| Component → API | fetch/axios call to API path, response used (await/.then/setState) | WIRED / PARTIAL (call but unused response) / NOT_WIRED |
| API → Database | Prisma/DB query on model, result returned via res.json() | WIRED / PARTIAL (query but not returned) / NOT_WIRED |
| Form → Handler | onSubmit with real implementation (fetch/axios/mutate/dispatch), not console.log/empty | WIRED / STUB (log-only/empty) / NOT_WIRED |
| State → Render | useState variable appears in JSX (`{stateVar}` or `{stateVar.property}`) | WIRED / NOT_WIRED |

Record status and evidence for each key link.
</step>

<step name="verify_requirements">
If REQUIREMENTS.md exists:
```bash
grep -E "Phase ${PHASE_NUM}" .planning/REQUIREMENTS.md 2>/dev/null || true
```

For each requirement: parse description → identify supporting truths/artifacts → status: ✓ SATISFIED / ✗ BLOCKED / ? NEEDS HUMAN.
</step>

<step name="verify_decisions">
**Decision coverage validation gate (issue #2492).**

After requirements coverage, also check that each trackable CONTEXT.md
`<decisions>` entry shows up somewhere in the shipped artifacts (plans,
SUMMARY.md, files modified by the phase, or recent commit subjects on the
phase branch).

This gate is **non-blocking / warning only** by deliberate asymmetry with
the plan-phase translation gate. The plan-phase gate already blocked at
translation time, so by the time verification runs every decision has
either been translated or explicitly deferred. This gate's job is to
surface decisions that *were* translated but vanished during execution —
that's a soft signal because "honors a decision" is a fuzzy substring
heuristic, and we don't want a paraphrase miss to fail an otherwise good
phase.

**Skip if** `workflow.context_coverage_gate` is explicitly set to `false`
(absent key = enabled). Also skip cleanly when CONTEXT.md is missing or has
no `<decisions>` block.

```bash
GATE_CFG=$(gsd-sdk query config-get workflow.context_coverage_gate 2>/dev/null || echo "true")
if [ "$GATE_CFG" != "false" ]; then
  # Discover the phase CONTEXT.md via glob expansion rather than `ls | head`
  # (review F17 / ShellCheck SC2012). Globs preserve filenames containing
  # spaces and avoid an extra subprocess.
  CONTEXT_PATH=""
  for f in "${PHASE_DIR}"/*-CONTEXT.md; do
    [ -e "$f" ] && CONTEXT_PATH="$f" && break
  done
  DECISION_RESULT=$(gsd-sdk query check.decision-coverage-verify "${PHASE_DIR}" "${CONTEXT_PATH}")
fi
```

The handler returns JSON `{ skipped, blocking: false, total, honored,
not_honored: [...], message }`.

**Reporting:** Append the handler's `message` (a `### Decision Coverage`
section) to VERIFICATION.md regardless of outcome — even when all
decisions are honored, recording the count helps reviewers spot drift over
time. Set `decision_coverage` in the verification result to
`{honored, total, not_honored: [...]}` so downstream tooling can read it.

**Status impact:** none. The decision gate does NOT influence the
`gaps_found` / `human_needed` / `passed` decision tree in
`determine_status`. Its findings are warnings the user reviews and may act
on by re-opening the phase or by acknowledging the decision was abandoned
intentionally.
</step>

<step name="behavioral_verification">
**Run the project's test suite and CLI commands to verify behavior, not just structure.**

Static checks (grep, file existence, wiring) catch structural gaps but miss runtime
failures. This step runs actual tests and project commands to verify the phase goal
is behaviorally achieved.

This follows Anthropic's harness engineering principle: separating generation from
evaluation, with the evaluator interacting with the running system rather than
inspecting static artifacts.

**Step 1: Run test suite**

```bash
# Resolve test command: project config > Makefile > language sniff
TEST_CMD=$(gsd-sdk query config-get workflow.test_command --default "" 2>/dev/null || true)
if [ -z "$TEST_CMD" ]; then
  if [ -f "Makefile" ] && grep -q "^test:" Makefile; then
    TEST_CMD="make test"
  elif [ -f "Justfile" ] || [ -f "justfile" ]; then
    TEST_CMD="just test"
  elif [ -f "package.json" ]; then
    TEST_CMD="npm test"
  elif [ -f "Cargo.toml" ]; then
