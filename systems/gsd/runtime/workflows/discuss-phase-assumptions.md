<purpose>
Extract implementation decisions that downstream agents need — using codebase-first analysis
and assumption surfacing instead of interview-style questioning.

You are a thinking partner, not an interviewer. Analyze the codebase deeply, surface what you
believe based on evidence, and ask the user only to correct what's wrong.
</purpose>

<available_agent_types>
Valid GSD subagent types (use exact names — do not fall back to 'general-purpose'):
- gsd-assumptions-analyzer — Analyzes codebase to surface implementation assumptions
</available_agent_types>

<downstream_awareness>
**CONTEXT.md feeds into:**

1. **gsd-phase-researcher** — Reads CONTEXT.md to know WHAT to research
2. **gsd-planner** — Reads CONTEXT.md to know WHAT decisions are locked

**Your job:** Capture decisions clearly enough that downstream agents can act on them
without asking the user again. Output is identical to discuss mode — same CONTEXT.md format.
</downstream_awareness>

<philosophy>
**Assumptions mode philosophy:**

The user is a visionary, not a codebase archaeologist. They need enough context to evaluate
whether your assumptions match their intent — not to answer questions you could figure out
by reading the code.

- Read the codebase FIRST, form opinions SECOND, ask ONLY about what's genuinely unclear
- Every assumption must cite evidence (file paths, patterns found)
- Every assumption must state consequences if wrong
- Minimize user interactions: ~2-4 corrections vs ~15-20 questions
</philosophy>

<scope_guardrail>
**CRITICAL: No scope creep.**

The phase boundary comes from ROADMAP.md and is FIXED. Discussion clarifies HOW to implement
what's scoped, never WHETHER to add new capabilities.

When user suggests scope creep:
"[Feature X] would be a new capability — that's its own phase.
Want me to note it for the roadmap backlog? For now, let's focus on [phase domain]."

Capture the idea in "Deferred Ideas". Don't lose it, don't act on it.
</scope_guardrail>

<answer_validation>
**IMPORTANT: Answer validation** — After every AskUserQuestion call, check if the response
is empty or whitespace-only. If so:
1. Retry the question once with the same parameters
2. If still empty, present the options as a plain-text numbered list

**Text mode (`workflow.text_mode: true` in config or `--text` flag):**
When text mode is active, do not use AskUserQuestion at all. Present every question as a
plain-text numbered list and ask the user to type their choice number.
</answer_validation>

<process>

<step name="initialize" priority="first">
Phase number from argument (required).

```bash
INIT=$(gsd-sdk query init.phase-op "${PHASE}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_ANALYZER=$(gsd-sdk query agent-skills gsd-assumptions-analyzer)
```

Parse JSON for: `commit_docs`, `phase_found`, `phase_dir`, `phase_number`, `phase_name`,
`phase_slug`, `padded_phase`, `has_research`, `has_context`, `has_plans`, `has_verification`,
`plan_count`, `roadmap_exists`, `planning_exists`.

**If `phase_found` is false:**
```
Phase [X] not found in roadmap.

Use /gsd:progress to see available phases.
```
Exit workflow.

**If `phase_found` is true:** Continue to check_existing.

**Auto mode** — If `--auto` is present in ARGUMENTS:
- In `check_existing`: auto-select "Update it" (if context exists) or continue without prompting
- In `present_assumptions`: skip confirmation gate, proceed directly to write CONTEXT.md
- In `correct_assumptions`: auto-select recommended option for each correction
- Log each auto-selected choice inline
- After completion, auto-advance to plan-phase
</step>

<step name="check_existing">
Check if CONTEXT.md already exists using `has_context` from init.

```bash
ls ${phase_dir}/*-CONTEXT.md 2>/dev/null || true
```

**If exists:**

**If `--auto`:** Auto-select "Update it". Log: `[auto] Context exists — updating with assumption-based analysis.`

**Otherwise:** Use AskUserQuestion:
- header: "Context"
- question: "Phase [X] already has context. What do you want to do?"
- options:
  - "Update it" — Re-analyze codebase and refresh assumptions
  - "View it" — Show me what's there
  - "Skip" — Use existing context as-is

If "Update": Load existing, continue to load_prior_context
If "View": Display CONTEXT.md, then offer update/skip
If "Skip": Exit workflow

**If doesn't exist:**

Check `has_plans` and `plan_count` from init. **If `has_plans` is true:**

**If `--auto`:** Auto-select "Continue and replan after". Log: `[auto] Plans exist — continuing with assumption analysis, will replan after.`

**Otherwise:** Use AskUserQuestion:
- header: "Plans exist"
- question: "Phase [X] already has {plan_count} plan(s) created without user context. Your decisions here won't affect existing plans unless you replan."
- options:
  - "Continue and replan after"
  - "View existing plans"
  - "Cancel"

If "Continue and replan after": Continue to load_prior_context.
If "View existing plans": Display plan files, then offer "Continue" / "Cancel".
If "Cancel": Exit workflow.

**If `has_plans` is false:** Continue to load_prior_context.
</step>

<step name="load_prior_context">
Read project-level and prior phase context to avoid re-asking decided questions.

**Step 1: Read project-level files**
```bash
cat .planning/PROJECT.md 2>/dev/null || true
cat .planning/REQUIREMENTS.md 2>/dev/null || true
cat .planning/STATE.md 2>/dev/null || true
```

Extract from these:
- **PROJECT.md** — Vision, principles, non-negotiables, user preferences
- **REQUIREMENTS.md** — Acceptance criteria, constraints
- **STATE.md** — Current progress, any flags

**Step 2: Read all prior CONTEXT.md files**
```bash
(find .planning/phases -name "*-CONTEXT.md" 2>/dev/null || true) | sort
```

For each CONTEXT.md where phase number < current phase:
- Read the `<decisions>` section — these are locked preferences
- Read `<specifics>` — particular references or "I want it like X" moments
- Note patterns (e.g., "user consistently prefers minimal UI")

**Step 3: Build internal `<prior_decisions>` context**

Structure the extracted information for use in assumption generation.

**If no prior context exists:** Continue without — expected for early phases.
</step>

<step name="cross_reference_todos">
Check if any pending todos are relevant to this phase's scope.

```bash
TODO_MATCHES=$(gsd-sdk query todo.match-phase "${PHASE_NUMBER}")
```

Parse JSON for: `todo_count`, `matches[]`.

**If `todo_count` is 0:** Skip silently.

**If matches found:** Present matched todos, use AskUserQuestion (multiSelect) to fold relevant ones into scope.

**For selected (folded) todos:** Store as `<folded_todos>` for CONTEXT.md `<decisions>` section.
**For unselected:** Store as `<reviewed_todos>` for CONTEXT.md `<deferred>` section.

