# Phase Prompt Template

> **Note:** Planning methodology is in `agents/gsd-planner.md`.
> This template defines the PLAN.md output format that the agent produces.

Template for `.planning/phases/XX-name/{phase}-{plan}-PLAN.md` - executable phase plans optimized for parallel execution.

**Naming:** Use `{phase}-{plan}-PLAN.md` format (e.g., `01-02-PLAN.md` for Phase 1, Plan 2)

---

## File Template

```markdown
---
phase: XX-name
plan: NN
type: execute
wave: N                     # Execution wave (1, 2, 3...). Pre-computed at plan time.
depends_on: []              # Plan IDs this plan requires (e.g., ["01-01"]).
files_modified: []          # Files this plan modifies.
autonomous: true            # false if plan has checkpoints requiring user interaction
requirements: []            # REQUIRED — Requirement IDs from ROADMAP this plan addresses. MUST NOT be empty.
user_setup: []              # Human-required setup Claude cannot automate (see below)

# Goal-backward verification (derived during planning, verified after execution)
must_haves:
  truths: []                # Observable behaviors that must be true for goal achievement
  artifacts: []             # Files that must exist with real implementation
  key_links: []             # Critical connections between artifacts
---

<objective>
[What this plan accomplishes]

Purpose: [Why this matters for the project]
Output: [What artifacts will be created]
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
[If plan contains checkpoint tasks (type="checkpoint:*"), add:]
@~/.claude/get-shit-done/references/checkpoints.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md

# Only reference prior plan SUMMARYs if genuinely needed:
# - This plan uses types/exports from prior plan
# - Prior plan made decision that affects this plan
# Do NOT reflexively chain: Plan 02 refs 01, Plan 03 refs 02...

[Relevant source files:]
@src/path/to/relevant.ts
</context>

<tasks>

<task type="auto">
  <name>Task 1: [Action-oriented name]</name>
  <files>path/to/file.ext, another/file.ext</files>
  <read_first>path/to/reference.ext, path/to/source-of-truth.ext</read_first>
  <action>[Specific implementation - what to do, how to do it, what to avoid and WHY. Include CONCRETE values: exact identifiers, parameters, expected outputs, file paths, command arguments. Never say "align X with Y" without specifying the exact target state.]</action>
  <verify>[Command or check to prove it worked]</verify>
  <acceptance_criteria>
    - [Grep-verifiable condition: "file.ext contains 'exact string'"]
    - [Measurable condition: "output.ext uses 'expected-value', NOT 'wrong-value'"]
  </acceptance_criteria>
  <done>[Measurable acceptance criteria]</done>
</task>

<task type="auto">
  <name>Task 2: [Action-oriented name]</name>
  <files>path/to/file.ext</files>
  <read_first>path/to/reference.ext</read_first>
  <action>[Specific implementation with concrete values]</action>
  <verify>[Command or check]</verify>
  <acceptance_criteria>
    - [Grep-verifiable condition]
  </acceptance_criteria>
  <done>[Acceptance criteria]</done>
</task>

<!-- For checkpoint task examples and patterns, see @~/.claude/get-shit-done/references/checkpoints.md -->

<task type="checkpoint:decision" gate="blocking">
  <decision>[What needs deciding]</decision>
  <context>[Why this decision matters]</context>
  <options>
    <option id="option-a"><name>[Name]</name><pros>[Benefits]</pros><cons>[Tradeoffs]</cons></option>
    <option id="option-b"><name>[Name]</name><pros>[Benefits]</pros><cons>[Tradeoffs]</cons></option>
  </options>
  <resume-signal>Select: option-a or option-b</resume-signal>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>[What Claude built] - server running at [URL]</what-built>
  <how-to-verify>Visit [URL] and verify: [visual checks only, NO CLI commands]</how-to-verify>
  <resume-signal>Type "approved" or describe issues</resume-signal>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] [Specific test command]
- [ ] [Build/type check passes]
- [ ] [Behavior verification]
</verification>

<success_criteria>

- All tasks completed
- All verification checks pass
- No errors or warnings introduced
- [Plan-specific criteria]
  </success_criteria>

<output>
After completion, create `.planning/phases/XX-name/{phase}-{plan}-SUMMARY.md`
</output>
```

---

## Frontmatter Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `phase` | Yes | Phase identifier (e.g., `01-foundation`) |
| `plan` | Yes | Plan number within phase (e.g., `01`, `02`) |
| `type` | Yes | Always `execute` for standard plans, `tdd` for TDD plans |
| `wave` | Yes | Execution wave number (1, 2, 3...). Pre-computed at plan time. |
| `depends_on` | Yes | Array of plan IDs this plan requires. |
| `files_modified` | Yes | Files this plan touches. |
| `autonomous` | Yes | `true` if no checkpoints, `false` if has checkpoints |
| `requirements` | Yes | **MUST** list requirement IDs from ROADMAP. Every roadmap requirement MUST appear in at least one plan. |
| `user_setup` | No | Array of human-required setup items (external services) |
| `must_haves` | Yes | Goal-backward verification criteria (see below) |

**Wave is pre-computed:** Wave numbers are assigned during `/gsd:plan-phase`. Execute-phase reads `wave` directly from frontmatter and groups plans by wave number. No runtime dependency analysis needed.

**Must-haves enable verification:** The `must_haves` field carries goal-backward requirements from planning to execution. After all plans complete, execute-phase spawns a verification subagent that checks these criteria against the actual codebase.

---

## Parallel vs Sequential

<parallel_examples>

**Wave 1 candidates (parallel):**

```yaml
# Plan 01 - User feature
wave: 1
depends_on: []
files_modified: [src/models/user.ts, src/api/users.ts]
autonomous: true

# Plan 02 - Product feature (no overlap with Plan 01)
wave: 1
depends_on: []
files_modified: [src/models/product.ts, src/api/products.ts]
autonomous: true

# Plan 03 - Order feature (no overlap)
wave: 1
depends_on: []
files_modified: [src/models/order.ts, src/api/orders.ts]
autonomous: true
```

All three run in parallel (Wave 1) - no dependencies, no file conflicts.

**Sequential (genuine dependency):**

```yaml
# Plan 01 - Auth foundation
