<purpose>
Create executable phase prompts (PLAN.md files) for a roadmap phase with integrated research and verification. Default flow: Research (if needed) -> Plan -> Verify -> Done. Orchestrates gsd-phase-researcher, gsd-planner, and gsd-plan-checker agents with a revision loop (max 3 iterations).
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.

@~/.claude/get-shit-done/references/ui-brand.md
@~/.claude/get-shit-done/references/revision-loop.md
@~/.claude/get-shit-done/references/gate-prompts.md
@~/.claude/get-shit-done/references/agent-contracts.md
@~/.claude/get-shit-done/references/gates.md
</required_reading>

<available_agent_types>
Valid GSD subagent types (use exact names — do not fall back to 'general-purpose'):
- gsd-phase-researcher — Researches technical approaches for a phase
- gsd-pattern-mapper — Analyzes codebase for existing patterns, produces PATTERNS.md
- gsd-planner — Creates detailed plans from phase scope
- gsd-plan-checker — Reviews plan quality before execution
</available_agent_types>

<process>

## 0. Git Branch Invariant

**Do not create, rename, or switch git branches during plan-phase.** Branch identity is established at discuss-phase and is owned by the user's git workflow. A phase rename in ROADMAP.md is a plan-level change only — it does not mutate git branch names. If `phase_slug` in the init JSON differs from the current branch name, that is expected and correct; leave the branch unchanged.

## 1. Initialize

Load all context in one call (paths only to minimize orchestrator context):

```bash
INIT=$(gsd-sdk query init.plan-phase "$PHASE")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_RESEARCHER=$(gsd-sdk query agent-skills gsd-phase-researcher)
AGENT_SKILLS_PLANNER=$(gsd-sdk query agent-skills gsd-planner)
AGENT_SKILLS_CHECKER=$(gsd-sdk query agent-skills gsd-plan-checker)
CONTEXT_WINDOW=$(gsd-sdk query config-get context_window 2>/dev/null || echo "200000")
TDD_MODE=$(gsd-sdk query config-get workflow.tdd_mode 2>/dev/null || echo "false")
MVP_MODE_CFG=$(gsd-sdk query config-get workflow.mvp_mode 2>/dev/null || echo "false")
```

When `TDD_MODE` is `true`, the planner agent is instructed to apply `type: tdd` to eligible tasks using heuristics from `references/tdd.md`. The planner's `<required_reading>` is extended to include `@~/.claude/get-shit-done/references/tdd.md` so gate enforcement rules are available during planning.

When `CONTEXT_WINDOW >= 500000`, the planner prompt includes the 3 most recent prior phase CONTEXT.md and SUMMARY.md files PLUS any phases explicitly listed in the current phase's `Depends on:` field in ROADMAP.md. Explicit dependencies always load regardless of recency (e.g., Phase 7 declaring `Depends on: Phase 2` always sees Phase 2's context). Bounded recency keeps the planner's context budget focused on recent work.

Parse JSON for: `researcher_model`, `planner_model`, `checker_model`, `research_enabled`, `plan_checker_enabled`, `nyquist_validation_enabled`, `commit_docs`, `text_mode`, `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`, `has_research`, `has_context`, `has_reviews`, `has_plans`, `plan_count`, `phase_status` (#3569), `planning_exists`, `roadmap_exists`, `phase_req_ids`, `response_language`.

**If `response_language` is set:** Include `response_language: {value}` in all spawned subagent prompts so any user-facing output stays in the configured language.

**File paths (for <files_to_read> blocks):** `state_path`, `roadmap_path`, `requirements_path`, `context_path`, `research_path`, `verification_path`, `uat_path`, `reviews_path`. These are null if files don't exist.

**If `planning_exists` is false:** Error — run `/gsd:new-project` first.

## 1.5. Closed-Phase Gate (#3569)

The init JSON includes `phase_status` — one of `Pending | Planned | In Progress | Executed | Complete | Needs Review`. `Complete` means the phase has all summaries AND a `VERIFICATION.md` with `status: passed`. Replanning a closed phase silently rewrites plan docs that no longer match the shipped code, so the workflow must hard-stop here unless the operator explicitly overrides.

Parse `phase_status` from the init JSON, then:

```bash
FORCE_REPLAN=false
if [[ "$ARGUMENTS" =~ (^|[[:space:]])--force([[:space:]]|$) ]]; then
  FORCE_REPLAN=true
fi

if [ "${phase_status}" = "Complete" ]; then
  if [[ "$ARGUMENTS" =~ (^|[[:space:]])--reviews([[:space:]]|$) ]]; then
    # --reviews on a closed phase is never legitimate — concerns belong in a
    # new phase or issue against the closed phase's commits.
    cat <<EOF >&2
Phase ${phase_number} (${phase_name}) is already CLOSED (VERIFICATION status: passed).
/gsd:plan-phase --reviews cannot replan a closed phase. If the review surfaced
real concerns, open a follow-up phase or file an issue against the closed
phase's commits. There is no --force override for --reviews on a closed phase.
EOF
    exit 1
  fi
  if [ "$FORCE_REPLAN" != "true" ]; then
    cat <<EOF >&2
Phase ${phase_number} (${phase_name}) is already CLOSED (VERIFICATION status: passed).
Replanning a closed phase will overwrite plan docs that no longer match the
shipped code. If you intentionally want to replan over closed work, re-run
with: /gsd:plan-phase ${phase_number} --force

Otherwise, to view what shipped, see: ${verification_path}
EOF
    exit 1
  fi
  # FORCE_REPLAN=true: continue, but emit a banner so the operator sees the
  # decision in the transcript and in any committed plan docs.
  echo "WARNING: Replanning CLOSED phase ${phase_number} under --force. Verify the closeout was wrong before committing new plan docs." >&2
fi
```

The gate fires only on `Complete`. `Executed` and `Needs Review` are not gated — those states mean planning was finished but verification did not pass, and replanning is a legitimate next step.

## 2. Parse and Normalize Arguments

Extract from $ARGUMENTS: phase number (integer or decimal like `2.1`), flags (`--research`, `--skip-research`, `--research-phase <N>`, `--gaps`, `--skip-verify`, `--skip-ui`, `--prd <filepath>`, `--ingest <path-or-glob>`, `--ingest-format <auto|nygard|madr|narrative>`, `--reviews`, `--text`, `--bounce`, `--skip-bounce`, `--chunked`, `--mvp`, `--force` (override closed-phase gate, see §1.5)).

**`--research-phase <N>` — research-only mode (#3042 + #3044).** When this flag is present, parse `<N>` as the phase number (overrides any positional phase argument), set `RESEARCH_ONLY=true`, and treat the rest of this workflow as a research-dispatch only — the planner spawn (step 8), plan-checker, verification, gaps, bounce, and post-planning-gaps blocks all skip on `RESEARCH_ONLY`. Use this for cross-phase research, doc review before committing to a planning approach, and correction-without-replanning loops. Replaces the deleted `/gsd-research-phase` command.

In research-only mode, two modifiers control behavior when `RESEARCH.md` already exists:

- **`--research`** — force-refresh re-research without prompting. Re-spawns the researcher unconditionally and overwrites the existing RESEARCH.md. (This is the existing `--research` flag's standard "force re-research" semantics, reused here.)
- **`--view`** — view-only: print existing `RESEARCH.md` to stdout, do **not** spawn the researcher. Sets `VIEW_ONLY=true`. Cheapest mode for the correction-without-replanning loop. If `RESEARCH.md` does not exist, error with a hint to drop `--view`.

```bash
RESEARCH_ONLY=false
VIEW_ONLY=false
if [[ "$ARGUMENTS" =~ --research-phase[[:space:]]+([0-9]+(\.[0-9]+)?) ]]; then
  RESEARCH_ONLY=true
  PHASE="${BASH_REMATCH[1]}"
fi
if $RESEARCH_ONLY && [[ "$ARGUMENTS" =~ (^|[[:space:]])--view([[:space:]]|$) ]]; then
  VIEW_ONLY=true
fi
```

Set `TEXT_MODE=true` if `--text` is present in $ARGUMENTS OR `text_mode` from init JSON is `true`. When `TEXT_MODE` is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for Claude Code remote sessions (`/rc` mode) where TUI menus don't work through the Claude App.

**MVP_MODE resolution.** Resolve `MVP_MODE` once via the centralized `phase.mvp-mode` query verb. Precedence (first hit wins): CLI flag → ROADMAP.md `**Mode:** mvp` → `workflow.mvp_mode` config → false. The verb is the single source of truth — do not re-implement the chain.

```bash
MVP_FLAG_ARG=""
if [[ "$ARGUMENTS" =~ (^|[[:space:]])--mvp([[:space:]]|$) ]]; then MVP_FLAG_ARG="--cli-flag"; fi
```

Defer the `phase.mvp-mode` query until `PHASE` is finalized (after explicit argument parsing/fallback phase detection + validation).
The verb returns `true|false`. Full result also exposes `source` (`cli_flag` | `roadmap` | `config` | `none`) for diagnostics. The mode is **all-or-nothing per phase** (PRD decision Q1) — never selective per task.

**Walking Skeleton gate.** When `MVP_MODE=true` AND `phase_number == "01"` AND there are zero prior phase summaries (new project), the planner runs in **Walking Skeleton mode** (per PRD decision Q2 — new projects only). Detect with:

```bash
WALKING_SKELETON=false
if [ "$MVP_MODE" = "true" ] && [ "$padded_phase" = "01" ]; then
  PRIOR_SUMMARIES=$(gsd-sdk query phases.list --pick summaries_total 2>/dev/null || echo "0")
  if [ "$PRIOR_SUMMARIES" = "0" ]; then WALKING_SKELETON=true; fi
fi
```

When `WALKING_SKELETON=true`:
- Planner is instructed to produce `SKELETON.md` in the phase directory alongside `PLAN.md`. The template lives at `@~/.claude/get-shit-done/references/skeleton-template.md`.
- The plan must scaffold project + routing + one real DB read/write + one real UI interaction + dev deployment — the thinnest possible end-to-end working slice.

**Interaction with `--prd <filepath>`.** `--mvp` and `--prd` compose. The PRD express path (Step 3.5) creates `CONTEXT.md` from the PRD file and continues to research; the Walking Skeleton gate fires independently from the conditions above. When both are active on Phase 1 of a new project, the planner receives `WALKING_SKELETON=true` and PRD-derived context simultaneously — the PRD informs *what the skeleton should prove*. No precedence is needed; the two signals are orthogonal. See [`references/mvp-concepts.md`](../references/mvp-concepts.md) for the broader interaction map.

Extract express-path args from $ARGUMENTS: `PRD_FILE` (`--prd <filepath>`), `INGEST_PATH` (`--ingest <path-or-glob>`), and optional `INGEST_FORMAT` (`--ingest-format <auto|nygard|madr|narrative>`, default `auto`).

`--prd` and `--ingest` are mutually exclusive. If both are present, error and exit:
`Invalid arguments: cannot combine \`--prd\` with \`--ingest\`.`

**If no phase number:** Detect next unplanned phase from roadmap.

**If `phase_found` is false:** Validate phase exists in ROADMAP.md. If valid, create the directory using `expected_phase_dir` from init (includes `project_code` prefix when set):
```bash
mkdir -p "${expected_phase_dir}"
```

Set `phase_dir="${expected_phase_dir}"` after creation.

**Existing artifacts from init:** `has_research`, `has_plans`, `plan_count`.

Set `CHUNKED_MODE` from flag or config:
```bash
CHUNKED_CFG=$(gsd-sdk query config-get workflow.plan_chunked 2>/dev/null || echo "false")
CHUNKED_MODE=false
if [[ "$ARGUMENTS" =~ --chunked ]] || [[ "$CHUNKED_CFG" == "true" ]]; then
  CHUNKED_MODE=true
fi
```

## 2.5. Validate `--reviews` Prerequisite

**Skip if:** No `--reviews` flag.

**If `--reviews` AND `--gaps`:** Error — cannot combine `--reviews` with `--gaps`. These are conflicting modes.

**If `--reviews` AND `has_reviews` is false (no REVIEWS.md in phase dir):**

Error:
```
No REVIEWS.md found for Phase {N}. Run reviews first:

/gsd:review --phase {N}

Then re-run /gsd:plan-phase {N} --reviews
```
Exit workflow.

## 3. Validate Phase

```bash
PHASE_INFO=$(gsd-sdk query roadmap.get-phase "${PHASE}")
```

**If `found` is false:** Error with available phases. **If `found` is true:** Extract `phase_number`, `phase_name`, `goal` from JSON.

Now that `PHASE` is finalized, resolve MVP mode:
```bash
MVP_MODE=$(gsd-sdk query phase.mvp-mode "${PHASE}" $MVP_FLAG_ARG --pick active)
```

## 3.5. Handle PRD Express Path

**Skip if:** No `--prd` flag in arguments.

**If `--prd <filepath>` provided:**

1. Read the PRD file:
```bash
PRD_CONTENT=$(cat "$PRD_FILE" 2>/dev/null)
if [ -z "$PRD_CONTENT" ]; then
  echo "Error: PRD file not found: $PRD_FILE"
  exit 1
fi
```

2. Display banner:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► PRD EXPRESS PATH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Using PRD: {PRD_FILE}
Generating CONTEXT.md from requirements...
```

3. Parse the PRD content and generate CONTEXT.md. The orchestrator should:
   - Extract all requirements, user stories, acceptance criteria, and constraints from the PRD
   - Map each to a locked decision (everything in the PRD is treated as a locked decision)
   - Identify any areas the PRD doesn't cover and mark as "Claude's Discretion"
   - **Extract canonical refs** from ROADMAP.md for this phase, plus any specs/ADRs referenced in the PRD — expand to full file paths (MANDATORY)
   - Create CONTEXT.md in the phase directory

4. Write CONTEXT.md:
```markdown
# Phase [X]: [Name] - Context

**Gathered:** [date]
**Status:** Ready for planning
**Source:** PRD Express Path ({PRD_FILE})

<domain>
## Phase Boundary

[Extracted from PRD — what this phase delivers]

</domain>

<decisions>
## Implementation Decisions

{For each requirement/story/criterion in the PRD:}
### [Category derived from content]
- [Requirement as locked decision]

### Claude's Discretion
[Areas not covered by PRD — implementation details, technical choices]

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

[MANDATORY. Extract from ROADMAP.md and any docs referenced in the PRD.
Use full relative paths. Group by topic area.]

### [Topic area]
- `path/to/spec-or-adr.md` — [What it decides/defines]

[If no external specs: "No external specs — requirements fully captured in decisions above"]

</canonical_refs>

<specifics>
## Specific Ideas

[Any specific references, examples, or concrete requirements from PRD]

</specifics>

<deferred>
## Deferred Ideas

[Items in PRD explicitly marked as future/v2/out-of-scope]
[If none: "None — PRD covers phase scope"]

</deferred>

---

*Phase: XX-name*
*Context gathered: [date] via PRD Express Path*
```

5. Commit:
```bash
gsd-sdk query commit "docs(${padded_phase}): generate context from PRD" --files "${phase_dir}/${padded_phase}-CONTEXT.md"
```

6. Set `context_content` to the generated CONTEXT.md content and continue to step 5 (Handle Research).

**Effect:** This completely bypasses step 4 (Load CONTEXT.md) since we just created it. The rest of the workflow (research, planning, verification) proceeds normally with the PRD-derived context.

## 3.6. Handle ADR Ingest Express Path

**Skip if:** No `--ingest` flag in arguments.

**If `--ingest <path-or-glob>` provided:**

1. Display banner: `GSD ► ADR Ingest Express Path` with `{INGEST_PATH}` and `{INGEST_FORMAT}`.
2. Parse each resolved ADR through `get-shit-done/bin/lib/adr-parser.cjs` (`--input`, `--format`) and collect normalized records.
3. Status gate: reject `superseded`/`rejected`/`deprecated`; warn on `proposed`; missing status defaults to `accepted`.
4. Empty-decisions fallback: if all parsed ADRs have zero `decisions[]`, emit `ADR ingest produced no locked decisions; fall back to discuss-phase for this phase.` and exit with `/gsd:discuss-phase {N}` guidance.
5. Generate CONTEXT.md using `<domain>`, `<decisions>`, `<canonical_refs>`, `<specifics>`, `<deferred>`, `<scope_fence>`, map `consequences_positive[]` to Success Criteria and `consequences_negative[]` to Risk Summary, and include `**Source:** ADR Ingest Express Path ({INGEST_PATH})`.
6. Commit with `gsd-sdk query commit "docs(${padded_phase}): generate context from ADR ingest" --files "${phase_dir}/${padded_phase}-CONTEXT.md"` and set `context_content`; continue to step 5.

**Effect:** This bypasses step 4 (Load CONTEXT.md) since CONTEXT.md was synthesized from ADR input.

## 4. Load CONTEXT.md

**Skip if:** PRD express path or ADR ingest express path was used (CONTEXT.md already created in step 3.5/3.6).

Check `context_path` from init JSON.

If `context_path` is not null, display: `Using phase context from: ${context_path}`

**If `context_path` is null (no CONTEXT.md exists):**

Read discuss mode for context gate label:
```bash
DISCUSS_MODE=$(gsd-sdk query config-get workflow.discuss_mode 2>/dev/null || echo "discuss")
```

If `TEXT_MODE` is true, present as a plain-text numbered list:
```
No CONTEXT.md found for Phase {X}. Plans will use research and requirements only — your design preferences won't be included.

1. Continue without context — Plan using research + requirements only
[If DISCUSS_MODE is "assumptions":]
2. Gather context (assumptions mode) — Analyze codebase and surface assumptions before planning
[If DISCUSS_MODE is "discuss" or unset:]
2. Run discuss-phase first — Capture design decisions before planning

Enter number:
```

Otherwise use AskUserQuestion:
- header: "No context"
- question: "No CONTEXT.md found for Phase {X}. Plans will use research and requirements only — your design preferences won't be included. Continue or capture context first?"
- options:
  - "Continue without context" — Plan using research + requirements only
  If `DISCUSS_MODE` is `"assumptions"`:
  - "Gather context (assumptions mode)" — Analyze codebase and surface assumptions before planning
  If `DISCUSS_MODE` is `"discuss"` (or unset):
  - "Run discuss-phase first" — Capture design decisions before planning

If "Continue without context": Proceed to step 5.
If "Run discuss-phase first":
  **IMPORTANT:** Do NOT invoke discuss-phase as a nested Skill/Task call — AskUserQuestion
  does not work correctly in nested subcontexts (#1009). Instead, display the command
  and exit so the user runs it as a top-level command:
  ```
  Run this command first, then re-run /gsd:plan-phase {X} ${GSD_WS}:

  /gsd:discuss-phase {X} ${GSD_WS}
  ```
  **Exit the plan-phase workflow. Do not continue.**

## 4.5. Check AI-SPEC

**Skip if:** `ai_integration_phase_enabled` from config is false, or `--skip-ai-spec` flag provided.

```bash
AI_SPEC_FILE=$(ls "${PHASE_DIR}"/*-AI-SPEC.md 2>/dev/null | head -1)
AI_PHASE_CFG=$(gsd-sdk query config-get workflow.ai_integration_phase 2>/dev/null || echo "true")
```

**Skip if `AI_PHASE_CFG` is `false`.**

**If `AI_SPEC_FILE` is empty:** Check phase goal for AI keywords:
```bash
echo "${phase_goal}" | grep -qi "agent\|llm\|rag\|chatbot\|embedding\|langchain\|llamaindex\|crewai\|langgraph\|openai\|anthropic\|vector\|eval\|ai system"
```

**If AI keywords detected AND no AI-SPEC.md:**
```
◆ Note: This phase appears to involve AI system development.
  Consider running /gsd:ai-integration-phase {N} before planning to:
  - Select the right framework for your use case
  - Research its docs and best practices
  - Design an evaluation strategy

  Continue planning without AI-SPEC? (non-blocking — /gsd:ai-integration-phase can be run after)
```

Use AskUserQuestion with options:
- "Continue — plan without AI-SPEC"
- "Stop — I'll run /gsd:ai-integration-phase {N} first"

If "Stop": Exit with `/gsd:ai-integration-phase {N}` reminder.
If "Continue": Proceed. (Non-blocking — planner will note AI-SPEC is absent.)

**If `AI_SPEC_FILE` is non-empty:** Extract framework for planner context:
```bash
FRAMEWORK_LINE=$(grep "Selected Framework:" "${AI_SPEC_FILE}" | head -1)
```
Pass `ai_spec_path` and `framework_line` to planner in step 7 so it can reference the AI design contract.

## 5. Handle Research

**Skip if:** `--gaps` flag or `--skip-research` flag or `--reviews` flag.

### 5.0. Research-Only Modifiers (`--view`, `--research`, prompt)

**Skip if:** `RESEARCH_ONLY` is `false`.

Three branches in research-only mode (`--research-phase <N>`):

1. **`--view`** (or user picks "View" in the prompt below): print `RESEARCH.md` to stdout, no spawn, exit. If `RESEARCH.md` is missing, error with: `--view requires an existing RESEARCH.md; drop --view to spawn the researcher.`
2. **`--research`** (force-refresh): re-spawn researcher unconditionally — fall through to "Spawn gsd-phase-researcher" below.
3. **Neither flag AND `has_research=true`:** emit `RESEARCH.md already exists for Phase ${PHASE}.` and prompt the user with three choices: `1. Update — re-spawn researcher and refresh RESEARCH.md`, `2. View — print existing RESEARCH.md and exit (no spawn)`, `3. Skip — exit without spawning or printing`. Map "Update" → fall through to spawn, "View" → set `VIEW_ONLY=true` and emit RESEARCH.md as in (1), "Skip" → exit cleanly. Mirrors the deleted `/gsd-research-phase` standalone's existing-artifact menu (#3042 parity).

```bash
if [[ "$VIEW_ONLY" == "true" ]]; then
  [[ -f "$research_path" ]] || { echo "Error: --view requires an existing RESEARCH.md (Phase ${PHASE}). Drop --view to spawn the researcher."; exit 1; }
  cat "$research_path"; exit 0
fi
```

### 5.1. Standard Research Decision

**Skip if** `RESEARCH_ONLY=true` (the research-only mode in 5.0 already determined the path: spawn or exit). Without this guard, an LLM following the workflow could fall through into "use existing, skip to step 6" → planner spawn, violating the research-only contract. **CR #3045 finding: this gate makes the early-exit unreachable from any non-research-only branch.**

**If `has_research` is true (from init) AND no `--research` flag:** Use existing, skip to step 6.

**If RESEARCH.md missing OR `--research` flag:**

**If no explicit flag (`--research` or `--skip-research`) and not `--auto`:**
Ask the user whether to research, with a contextual recommendation based on the phase:

If `TEXT_MODE` is true, present as a plain-text numbered list:
```
Research before planning Phase {X}: {phase_name}?

1. Research first (Recommended) — Investigate domain, patterns, and dependencies before planning. Best for new features, unfamiliar integrations, or architectural changes.
2. Skip research — Plan directly from context and requirements. Best for bug fixes, simple refactors, or well-understood tasks.

Enter number:
```

Otherwise use AskUserQuestion:
```
AskUserQuestion([
  {
    question: "Research before planning Phase {X}: {phase_name}?",
    header: "Research",
    multiSelect: false,
    options: [
      { label: "Research first (Recommended)", description: "Investigate domain, patterns, and dependencies before planning. Best for new features, unfamiliar integrations, or architectural changes." },
      { label: "Skip research", description: "Plan directly from context and requirements. Best for bug fixes, simple refactors, or well-understood tasks." }
    ]
  }
])
```

If user selects "Skip research": skip to step 6.

**If `--auto` and `research_enabled` is false:** Skip research silently (preserves automated behavior).

Display banner:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► RESEARCHING PHASE {X}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Spawning researcher...
```

### Spawn gsd-phase-researcher

```bash
PHASE_DESC=$(gsd-sdk query roadmap.get-phase "${PHASE}" --pick section)
```

Research prompt:

```markdown
<objective>
Research how to implement Phase {phase_number}: {phase_name}
Answer: "What do I need to know to PLAN this phase well?"
</objective>

<files_to_read>
- {context_path} (USER DECISIONS from /gsd:discuss-phase)
- {requirements_path} (Project requirements)
- {state_path} (Project decisions and history)
</files_to_read>

${AGENT_SKILLS_RESEARCHER}

<additional_context>
**Phase description:** {phase_description}
**Phase requirement IDs (MUST address):** {phase_req_ids}

**Project instructions:** Read ./CLAUDE.md if exists — follow project-specific guidelines
**Project skills:** Check .claude/skills/ or .agents/skills/ directory (if either exists) — read SKILL.md files, research should account for project skill patterns
</additional_context>

<output>
Write to: {phase_dir}/{phase_num}-RESEARCH.md
</output>
```

```
Agent(
  prompt=research_prompt,
  subagent_type="gsd-phase-researcher",
  model="{researcher_model}",
  description="Research Phase {phase}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

### Handle Researcher Return

- **`## RESEARCH COMPLETE`:** Display confirmation, continue to step 6
- **`## RESEARCH BLOCKED`:** Display blocker, offer: 1) Provide context, 2) Skip research, 3) Abort

### Research-Only Early Exit (`--research-phase`)

**Skip if:** `RESEARCH_ONLY` is `false` (the default).

**If `RESEARCH_ONLY=true`:** the user invoked `/gsd:plan-phase --research-phase <N>` for research-only mode. Do **not** continue to Section 5.5+ (validation strategy, planner, plan-checker, verification, gaps, bounce, post-planning-gaps). Print the research-complete summary and exit cleanly:

```text
✓ Research-only mode complete (#3042)

  Phase:       ${PHASE}
  RESEARCH.md: ${research_path}

Re-run /gsd:plan-phase ${PHASE} to plan the phase using this research,
or /gsd:plan-phase ${PHASE} --research to refresh research and plan.
```

This exits the workflow. The planner / plan-checker / verifier blocks below are skipped.

## 5.5. Create Validation Strategy

Skip if `nyquist_validation_enabled` is false OR `research_enabled` is false.

If `research_enabled` is false and `nyquist_validation_enabled` is true: warn "Nyquist validation enabled but research disabled — VALIDATION.md cannot be created without RESEARCH.md. Plans will lack validation requirements (Dimension 8)." Continue to step 6.

**But Nyquist is not applicable for this run** when all of the following are true:
- `research_enabled` is false
- `has_research` is false
- no `--research` flag was provided

In that case: **skip validation-strategy creation entirely**. Do **not** expect `RESEARCH.md` or `VALIDATION.md` for this run, and continue to Step 6.

```bash
grep -l "## Validation Architecture" "${PHASE_DIR}"/*-RESEARCH.md 2>/dev/null || true
```

**If found:**
1. Read template: `~/.claude/get-shit-done/templates/VALIDATION.md`
2. Write to `${PHASE_DIR}/${PADDED_PHASE}-VALIDATION.md` (use Write tool)
3. Fill frontmatter: `{N}` → phase number, `{phase-slug}` → slug, `{date}` → current date
4. Verify:
```bash
test -f "${PHASE_DIR}/${PADDED_PHASE}-VALIDATION.md" && echo "VALIDATION_CREATED=true" || echo "VALIDATION_CREATED=false"
```
5. If `VALIDATION_CREATED=false`: STOP — do not proceed to Step 6
6. If `commit_docs`: `commit "docs(phase-${PHASE}): add validation strategy"`

**If not found:** Warn and continue — plans may fail Dimension 8.

## 5.55. Security Threat Model Gate

> Skip if `workflow.security_enforcement` is explicitly `false`. Absent = enabled.

```bash
SECURITY_CFG=$(gsd-sdk query config-get workflow.security_enforcement --raw 2>/dev/null || echo "true")
SECURITY_ASVS=$(gsd-sdk query config-get workflow.security_asvs_level --raw 2>/dev/null || echo "1")
SECURITY_BLOCK=$(gsd-sdk query config-get workflow.security_block_on --raw 2>/dev/null || echo "high")
```

**If `SECURITY_CFG` is `false`:** Skip to step 5.6.

**If `SECURITY_CFG` is `true`:** Display banner:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► SECURITY THREAT MODEL REQUIRED (ASVS L{SECURITY_ASVS})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Each PLAN.md must include a <threat_model> block.
Block on: {SECURITY_BLOCK} severity threats.
Opt out: set security_enforcement: false in .planning/config.json
```

Continue to step 5.6. Security config is passed to the planner in step 8.

## 5.6. UI Design Contract Gate

> Skip if `workflow.ui_phase` is explicitly `false` AND `workflow.ui_safety_gate` is explicitly `false` in `.planning/config.json`. If keys are absent, treat as enabled.

```bash
UI_PHASE_CFG=$(gsd-sdk query config-get workflow.ui_phase 2>/dev/null || echo "true")
UI_GATE_CFG=$(gsd-sdk query config-get workflow.ui_safety_gate 2>/dev/null || echo "true")
```

**If both are `false`:** Skip to step 6.

Check if phase has frontend indicators:

```bash
PHASE_SECTION=$(gsd-sdk query roadmap.get-phase "${PHASE}" 2>/dev/null)
# Shell-free word-boundary gate (#3718): Node.js helper — no locale env-var dependency.
# Reads via stdin to avoid OS ARG_MAX limits on large phase text.
# Path anchored to repo root; falls back to CWD if git is unavailable
# Exit codes mirror grep: 0 = UI tokens found, 1 = not found.
GSD_REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
printf '%s' "$PHASE_SECTION" | node "${GSD_REPO_ROOT}/bin/lib/ui-safety-gate.cjs" > /dev/null 2>&1
HAS_UI=$?
```

**If `HAS_UI` is 0 (frontend indicators found):**

Check for existing UI-SPEC:
```bash
UI_SPEC_FILE=$(ls "${PHASE_DIR}"/*-UI-SPEC.md 2>/dev/null | head -1)
```

**If UI-SPEC.md found:** Set `UI_SPEC_PATH=$UI_SPEC_FILE`. Display: `Using UI design contract: ${UI_SPEC_PATH}`

**If UI-SPEC.md missing AND `--skip-ui` flag is present in $ARGUMENTS:** Skip silently to step 6.

**If UI-SPEC.md missing AND `UI_GATE_CFG` is `true`:**

Read ephemeral chain flag (same field as `check.auto-mode` → `auto_chain_active`):
```bash
AUTO_CHAIN=$(gsd-sdk query check auto-mode --pick auto_chain_active 2>/dev/null || echo "false")
```

**If `AUTO_CHAIN` is `true` (running inside a `--chain` or `--auto` pipeline):**

Auto-generate UI-SPEC without prompting:
```
Skill(skill="gsd-ui-phase", args="${PHASE} --auto ${GSD_WS}")
```
After `gsd-ui-phase` returns, re-read:
```bash
UI_SPEC_FILE=$(ls "${PHASE_DIR}"/*-UI-SPEC.md 2>/dev/null | head -1)
UI_SPEC_PATH="${UI_SPEC_FILE}"
```
Continue to step 6.

**If `AUTO_CHAIN` is `false` (manual invocation):**

Output this markdown directly (not as a code block):

```
## ⚠ UI-SPEC.md missing for Phase {N}
▶ Recommended next step:
`/gsd:ui-phase {N} ${GSD_WS}` — generate UI design contract before planning
───────────────────────────────────────────────
Also available:
- `/gsd:plan-phase {N} --skip-ui ${GSD_WS}` — plan without UI-SPEC (not recommended for frontend phases)
```

**Exit the plan-phase workflow. Do not continue.**

**If `HAS_UI` is 1 (no frontend indicators):** Skip silently to step 5.7.

## 5.7. Schema Push Detection Gate

> Detects schema-relevant files in the phase scope and injects a mandatory `[BLOCKING]` schema push task into the plan. Prevents false-positive verification where build/types pass because TypeScript types come from config, not the live database.

Check if any files in the phase scope match schema patterns:

```bash
PHASE_SECTION=$(gsd-sdk query roadmap.get-phase "${PHASE}" --pick section 2>/dev/null)
```

Scan `PHASE_SECTION`, `CONTEXT.md` (if loaded), and `RESEARCH.md` (if exists) for file paths matching these ORM patterns:

| ORM | File Patterns |
|-----|--------------|
| Payload CMS | `src/collections/**/*.ts`, `src/globals/**/*.ts` |
| Prisma | `prisma/schema.prisma`, `prisma/schema/*.prisma` |
| Drizzle | `drizzle/schema.ts`, `src/db/schema.ts`, `drizzle/*.ts` |
| Supabase | `supabase/migrations/*.sql` |
| TypeORM | `src/entities/**/*.ts`, `src/migrations/**/*.ts` |

Also check if any existing PLAN.md files for this phase already reference these file patterns in `files_modified`.

**If schema-relevant files detected:**

Set `SCHEMA_PUSH_REQUIRED=true` and `SCHEMA_ORM={detected_orm}`.

Determine the push command for the detected ORM:

| ORM | Push Command | Non-TTY Workaround |
|-----|-------------|-------------------|
| Payload CMS | `npx payload migrate` | `CI=true PAYLOAD_MIGRATING=true npx payload migrate` |
| Prisma | `npx prisma db push` | `npx prisma db push --accept-data-loss` (if destructive) |
| Drizzle | `npx drizzle-kit push` | `npx drizzle-kit push` |
| Supabase | `supabase db push` | Set `SUPABASE_ACCESS_TOKEN` env var |
| TypeORM | `npx typeorm migration:run` | `npx typeorm migration:run -d src/data-source.ts` |

Inject the following into the planner prompt (step 8) as an additional constraint:

```markdown
<schema_push_requirement>
**[BLOCKING] Schema Push Required**

This phase modifies schema-relevant files ({detected_files}). The planner MUST include
a `[BLOCKING]` task that runs the database schema push command AFTER all schema file
modifications are complete but BEFORE verification.

- ORM detected: {SCHEMA_ORM}
- Push command: {push_command}
- Non-TTY workaround: {env_hint}
- If push requires interactive prompts that cannot be suppressed, flag the task for
  manual intervention with `autonomous: false`

This task is mandatory — the phase CANNOT pass verification without it. Build and
type checks will pass without the push (types come from config, not the live database),
creating a false-positive verification state.
</schema_push_requirement>
```

Display: `Schema files detected ({SCHEMA_ORM}) — [BLOCKING] push task will be injected into plans`

**If no schema-relevant files detected:** Skip silently to step 6.

## 6. Check Existing Plans

```bash
ls "${PHASE_DIR}"/*-PLAN.md 2>/dev/null || true
```

**If exists AND `--reviews` flag:** Skip prompt — go straight to replanning (the purpose of `--reviews` is to replan with review feedback).

**If exists AND no `--reviews` flag:** Offer: 1) Add more plans, 2) View existing, 3) Replan from scratch.

## 7. Use Context Paths from INIT

Extract from INIT JSON:

```bash
_gsd_field() { node -e "const o=JSON.parse(process.argv[1]); const v=o[process.argv[2]]; process.stdout.write(v==null?'':String(v))" "$1" "$2"; }
STATE_PATH=$(_gsd_field "$INIT" state_path)
ROADMAP_PATH=$(_gsd_field "$INIT" roadmap_path)
REQUIREMENTS_PATH=$(_gsd_field "$INIT" requirements_path)
RESEARCH_PATH=$(_gsd_field "$INIT" research_path)
VERIFICATION_PATH=$(_gsd_field "$INIT" verification_path)
UAT_PATH=$(_gsd_field "$INIT" uat_path)
CONTEXT_PATH=$(_gsd_field "$INIT" context_path)
REVIEWS_PATH=$(_gsd_field "$INIT" reviews_path)
PATTERNS_PATH=$(_gsd_field "$INIT" patterns_path)

# Detect spike/sketch findings skills (project-local)
SPIKE_FINDINGS_PATH=$(ls ./.claude/skills/spike-findings-*/SKILL.md 2>/dev/null | head -1 || true)
SKETCH_FINDINGS_PATH=$(ls ./.claude/skills/sketch-findings-*/SKILL.md 2>/dev/null | head -1 || true)
```

## 7.5. Verify Nyquist Artifacts

Skip if `nyquist_validation_enabled` is false OR `research_enabled` is false.

Also skip if all of the following are true:
- `research_enabled` is false
- `has_research` is false
- no `--research` flag was provided

In that no-research path, Nyquist artifacts are **not required** for this run.

```bash
VALIDATION_EXISTS=$(ls "${PHASE_DIR}"/*-VALIDATION.md 2>/dev/null | head -1)
```

If missing and Nyquist is still enabled/applicable — ask user:
1. Re-run: `/gsd:plan-phase {PHASE} --research ${GSD_WS}`
2. Disable Nyquist with the exact command:
   `gsd-sdk query config-set workflow.nyquist_validation false`
3. Continue anyway (plans fail Dimension 8)

Proceed to Step 7.8 (or Step 8 if pattern mapper is disabled) only if user selects 2 or 3.

## 7.8. Spawn gsd-pattern-mapper Agent (Optional)

**Skip if** `workflow.pattern_mapper` is explicitly set to `false` in config.json (absent key = enabled). Also skip if no CONTEXT.md and no RESEARCH.md exist for this phase (nothing to extract file lists from).

Check config:
```bash
PATTERN_MAPPER_CFG=$(gsd-sdk query config-get workflow.pattern_mapper 2>/dev/null || echo "true")
```

**If `PATTERN_MAPPER_CFG` is `false`:** Skip to step 8.

**If PATTERNS.md already exists** (`PATTERNS_PATH` is non-empty from step 7): Skip to step 8 (use existing).

Display banner:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► PATTERN MAPPING PHASE {X}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Spawning pattern mapper...
```

Pattern mapper prompt:

```markdown
<pattern_mapping_context>
**Phase:** {phase_number} - {phase_name}
**Phase directory:** {phase_dir}
**Padded phase:** {padded_phase}

<files_to_read>
- {context_path} (USER DECISIONS from /gsd:discuss-phase)
- {research_path} (Technical Research)
</files_to_read>

**Output file:** {phase_dir}/{padded_phase}-PATTERNS.md

Extract the list of files to be created/modified from CONTEXT.md and RESEARCH.md. For each file, classify by role and data flow, find the closest existing analog in the codebase, extract concrete code excerpts, and produce PATTERNS.md.
</pattern_mapping_context>
```

Spawn with:
```
Agent(
  prompt="{above}",
  subagent_type="gsd-pattern-mapper",
  model="{researcher_model}",
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

**Handle return:**
- **`## PATTERN MAPPING COMPLETE`:** Update `PATTERNS_PATH` to the created file path, continue to step 8.
- **Any error or empty return:** Log warning, continue to step 8 without patterns (non-blocking).

After pattern mapper completes, update the path variable:
```bash
PATTERNS_PATH="${PHASE_DIR}/${PADDED_PHASE}-PATTERNS.md"
```

## 8. Spawn gsd-planner Agent

Display banner:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► PLANNING PHASE {X}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Spawning planner...
```

Planner prompt:

```markdown
<planning_context>
**Phase:** {phase_number}
**Mode:** {standard | gap_closure | reviews}

<files_to_read>
- {state_path} (Project State)
- {roadmap_path} (Roadmap)
- {requirements_path} (Requirements)
- {context_path} (USER DECISIONS from /gsd:discuss-phase)
- {research_path} (Technical Research)
- {PATTERNS_PATH} (Pattern Map — analog files and code excerpts, if exists)
- {verification_path} (Verification Gaps - if --gaps)
- {uat_path} (UAT Gaps - if --gaps)
- {reviews_path} (Cross-AI Review Feedback - if --reviews)
- {UI_SPEC_PATH} (UI Design Contract — visual/interaction specs, if exists)
- {SPIKE_FINDINGS_PATH} (Spike Findings — validated patterns, constraints, landmines from experiments, if exists)
- {SKETCH_FINDINGS_PATH} (Sketch Findings — validated design decisions, CSS patterns, visual direction, if exists)
${CONTEXT_WINDOW >= 500000 ? `
**Cross-phase context (1M model enrichment):**
- CONTEXT.md files from the 3 most recent completed phases (locked decisions — maintain consistency)
- SUMMARY.md files from the 3 most recent completed phases (what was built — reuse patterns, avoid duplication)
- LEARNINGS.md files from the 3 most recent completed phases (structured decisions, patterns, lessons, surprises — skip silently if a phase has no LEARNINGS.md; prefix each block with \`[from Phase N LEARNINGS]\` for source attribution; if total size exceeds 15% of context budget, drop oldest first)
- CONTEXT.md, SUMMARY.md, and LEARNINGS.md from any phases listed in the current phase's "Depends on:" field in ROADMAP.md (regardless of recency — explicit dependencies always load, deduplicated against the 3 most recent)
- Skip all other prior phases to stay within context budget
` : ''}
</files_to_read>

${AGENT_SKILLS_PLANNER}

**Phase requirement IDs (every ID MUST appear in a plan's `requirements` field):** {phase_req_ids}

**Project instructions:** Read ./CLAUDE.md if exists — follow project-specific guidelines
**Project skills:** Check .claude/skills/ or .agents/skills/ directory (if either exists) — read SKILL.md files, plans should account for project skill rules

${TDD_MODE === 'true' ? `
<tdd_mode_active>
**TDD Mode is ENABLED.** Apply TDD heuristics from @~/.claude/get-shit-done/references/tdd.md to all eligible tasks:
- Business logic with defined I/O → type: tdd
- API endpoints with request/response contracts → type: tdd
- Data transformations, validation, algorithms → type: tdd
- UI, config, glue code, CRUD → standard plan (type: execute)
Each TDD plan gets one feature with RED/GREEN/REFACTOR gate sequence.
</tdd_mode_active>
` : ''}

**MVP_MODE:** ${MVP_MODE} (when true, follow vertical-slice rules from `@~/.claude/get-shit-done/references/planner-mvp-mode.md`; when false, ignore MVP guidance entirely.)
**WALKING_SKELETON:** ${WALKING_SKELETON} (when true, the first deliverable must be a Walking Skeleton — produce SKELETON.md alongside PLAN.md.)

${MVP_MODE === 'true' ? `
<mvp_mode_active>
**MVP Mode is ENABLED.** Follow vertical-slice planning rules from @~/.claude/get-shit-done/references/planner-mvp-mode.md. Each plan must deliver a complete vertical slice — thin end-to-end functionality rather than horizontal layers.
</mvp_mode_active>
` : ''}
</planning_context>

<downstream_consumer>
Output consumed by /gsd:execute-phase. Plans need:
- Frontmatter (wave, depends_on, files_modified, autonomous)
- Tasks in XML format with read_first and acceptance_criteria fields (MANDATORY on every task)
- Verification criteria
- must_haves for goal-backward verification
</downstream_consumer>

<deep_work_rules>
## Anti-Shallow Execution Rules (MANDATORY)

Every task MUST include these fields — they are NOT optional:

1. **`<read_first>`** — Files the executor MUST read before touching anything. Always include:
   - The file being modified (so executor sees current state, not assumptions)
   - Any "source of truth" file referenced in CONTEXT.md (reference implementations, existing patterns, config files, schemas)
   - Any file whose patterns, signatures, types, or conventions must be replicated or respected

2. **`<acceptance_criteria>`** — Verifiable conditions that prove the task was done correctly. Rules:
   - Every criterion must be checkable as a source assertion, behavior assertion, test command, or CLI output
   - NEVER use subjective language ("looks correct", "properly configured", "consistent with")
   - Include exact strings, patterns, values, command outputs, or observable behavior where that is the right proof
   - Examples:
     - Code: `auth.py contains def verify_token(` / `test_auth.py exits 0`
     - Behavior: `POST /api/auth/login returns 200 + httpOnly JWT cookie for valid credentials`
     - Config: `.env.example contains DATABASE_URL=` / `Dockerfile contains HEALTHCHECK`
     - Docs: `README.md contains '## Installation'` / `API.md lists all endpoints`
     - Infra: `deploy.yml has rollback step` / `docker-compose.yml has healthcheck for db`

3. **`<action>`** — Must include CONCRETE values, not references. Rules:
   - NEVER say "align X with Y", "match X to Y", "update to be consistent" without specifying the exact target state
   - Include concrete identifiers and reference values: config keys, function signatures, SQL table names, class names, import paths, env vars, endpoint paths, etc.
   - If CONTEXT.md has a comparison table or expected values, copy only the target identifiers/values needed to remove ambiguity
   - Do not include full file contents, fenced code blocks, or complete implementations in `<action>`
   - The executor should understand the intended target state from `<action>` and use `<read_first>` files for current implementation details, patterns, and source-of-truth context

**Why this matters:** Executor agents work from the plan text. Vague instructions like "update the config to match production" produce shallow one-line changes. Concrete instructions like "add DATABASE_URL, set POOL_SIZE=20, add REDIS_URL, and read config/runtime.ts before editing" produce complete work without turning the planner into the executor.
</deep_work_rules>

<quality_gate>
- [ ] PLAN.md files created in phase directory
- [ ] Each plan has valid frontmatter
- [ ] Tasks are specific and actionable
- [ ] Every task has `<read_first>` with at least the file being modified
- [ ] Every task has `<acceptance_criteria>` with behavior, test-command, CLI, or source assertions
- [ ] Every `<action>` contains concrete identifiers without fenced code blocks or full implementations
- [ ] Dependencies correctly identified
- [ ] Waves assigned for parallel execution
- [ ] must_haves derived from phase goal
</quality_gate>
```

**If `CHUNKED_MODE` is `false` (default):** Spawn the planner as a single long-lived Agent:

```text
Agent(
  prompt=filled_prompt,
  subagent_type="gsd-planner",
  model="{planner_model}",
  description="Plan Phase {phase}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

**If `CHUNKED_MODE` is `true`:** Skip the Agent() call above — proceed to step 8.5 instead.

## 8.5. Chunked Planning Mode

**Skip if `CHUNKED_MODE` is `false`.**

Chunked mode splits the single long-lived planner Agent run into a short outline Agent run followed by
N short per-plan Agent runs. Each run is bounded to ~3–5 min; each plan is committed individually
for crash resilience. If any run hangs and the terminal is force-killed, rerunning
`/gsd:plan-phase {N} --chunked` resumes from the last successfully committed plan.

**Intended for new or in-progress chunked runs.** To recover plans already written by a prior
*non-chunked* run, use step 6's "Add more plans" or proceed directly to `/gsd:execute-phase`
— don't start a fresh chunked run over existing non-chunked plans.

### 8.5.1 Outline Phase (outline-only mode, ~2 min)

**Resume detection:** If `${PHASE_DIR}/${PADDED_PHASE}-PLAN-OUTLINE.md` already exists **and
is valid** (contains the `## OUTLINE COMPLETE` marker), skip this sub-step — the outline
already exists from a previous run. Proceed directly to 8.5.2.

```bash
OUTLINE_FILE="${PHASE_DIR}/${PADDED_PHASE}-PLAN-OUTLINE.md"
if [[ -f "$OUTLINE_FILE" ]] && grep -q "^## OUTLINE COMPLETE" "$OUTLINE_FILE"; then
  # reuse existing outline — skip to 8.5.2
fi
```

Display:
```text
◆ Chunked mode: spawning outline planner...
```

Spawn the planner in **outline-only** mode — it must write only the outline manifest, not any
PLAN.md files:

```javascript
Agent(
  prompt="{same planning_context as step 8, plus:}

  **Chunked mode: outline-only.**
  Do NOT write any PLAN.md files in this Task.
  Write only: {PHASE_DIR}/{PADDED_PHASE}-PLAN-OUTLINE.md

  The outline must be a markdown table with columns:
  Plan ID | Objective | Wave | Depends On | Requirements

  Return: ## OUTLINE COMPLETE with plan count.",
  subagent_type="gsd-planner",
  model="{planner_model}",
  description="Outline Phase {phase} (chunked)"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

Handle return:
- **`## OUTLINE COMPLETE`:** Read `PLAN-OUTLINE.md`, extract plan list. Continue to 8.5.2.
- **Any other return or empty:** Display error. Offer: 1) Retry outline, 2) Stop.

### 8.5.2 Per-Plan Tasks (single-plan mode, ~3-5 min each)

For each plan entry extracted from `PLAN-OUTLINE.md`:

1. **Resume check:** If `${PHASE_DIR}/{plan_id}-PLAN.md` already exists on disk **and has
   valid YAML frontmatter** (opening `---` delimiter present), skip this plan (do not
   overwrite completed work — resume safety).

   ```bash
   PLAN_FILE="${PHASE_DIR}/${plan_id}-PLAN.md"
   if [[ -f "$PLAN_FILE" ]] && head -1 "$PLAN_FILE" | grep -q '^---'; then
     continue  # plan already written, skip
   fi
   ```

2. Display:
   ```text
   ◆ Chunked mode: planning {plan_id} ({k}/{N})...
   ```

3. Spawn the planner in **single-plan** mode — it must write exactly one PLAN.md file:
   ```javascript
   Agent(
     prompt="{same planning_context as step 8, plus:}

     **Chunked mode: single-plan.**
     Write exactly ONE plan file: {PHASE_DIR}/{plan_id}-PLAN.md
     Plan to write: {plan_id} — {objective}
     Wave: {wave} | Depends on: {depends_on}
     Phase requirement IDs to cover in this plan: {plan_requirements}

     Return: ## PLAN COMPLETE with the plan ID.",
     subagent_type="gsd-planner",
     model="{planner_model}",
     description="Plan {plan_id} (chunked {k}/{N})"
   )
   ```

   > **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

4. **Verify disk:** Check `${PHASE_DIR}/{plan_id}-PLAN.md` exists. If missing: offer 1) Retry, 2) Stop.

5. **Commit per-plan:**
   ```bash
   gsd-sdk query commit "docs(${PADDED_PHASE}): plan ${plan_id} (chunked)" --files "${PHASE_DIR}/${plan_id}-PLAN.md"
   ```

After all N plans are written and committed, treat this as `## PLANNING COMPLETE` and continue
to step 9.

## 9. Handle Planner Return

- **`## PLANNING COMPLETE`:** Display plan count. If `--skip-verify` or `plan_checker_enabled` is false (from init): skip to step 13. Otherwise: step 10.
- **`## PHASE SPLIT RECOMMENDED`:** The planner determined the phase exceeds the context budget for full-fidelity implementation of all source items. Handle in step 9b.
- **`## ⚠ Source Audit: Unplanned Items Found`:** The planner's multi-source coverage audit found items from REQUIREMENTS.md, RESEARCH.md, ROADMAP goal, or CONTEXT.md decisions that are not covered by any plan. Handle in step 9c.
- **`## CHECKPOINT REACHED`:** Present to user, get response, spawn continuation (step 12)
- **`## PLANNING INCONCLUSIVE`:** Show attempts, offer: Add context / Retry / Manual
- **Empty / truncated / no recognized marker:** → Filesystem fallback (step 9a).

## 9a. Filesystem Fallback (Planner)
