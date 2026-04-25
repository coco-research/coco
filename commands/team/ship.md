# /team ship — Idea to Shipped Product Pipeline

> Called by team.md router when action is `ship`.
> The ultimate automation: takes a natural language idea and delivers a built, reviewed, verified product.
> Uses Option B: one approval gate after plan, then full autonomy for build+verify.

## Role Selection Bias

All roles are selected dynamically per stage. The ship pipeline runs 7 stages sequentially,
each using the appropriate /team action's role selection.

## Pipeline: 7 Stages

### Stage 1: Research
- Runs: `/team research <idea>`
- Purpose: Competitive landscape, technical feasibility, existing tools
- Autonomy: Full — no approval needed

### Stage 2: Think
- Runs: `/team think <idea with research context>`
- Purpose: Architecture options, evaluate trade-offs
- Autonomy: Full — no approval needed

### Stage 3: Plan
- Runs: `/team plan <idea with chosen architecture>`
- Purpose: Detailed implementation plan with phases, tasks, dependencies
- Autonomy: Full — no approval needed

### Stage 4: Review Plan
- Runs: `/team review <plan>`
- Purpose: Specialist review of the plan before building
- Autonomy: Full — no approval needed

### ═══════════════════════════════════════════════
### APPROVAL GATE
### ═══════════════════════════════════════════════
###
### Present to user:
###   - Research summary (key findings)
###   - Architecture decision (chosen option + rationale)
###   - Plan overview (phases, estimated effort)
###   - Review findings (any critical/major issues)
###
### Ask: "Plan ready. Proceed with build? [Y/n]"
###
### If user says no → stop, save all artifacts for later
### If user says yes → full autonomy from here
### ═══════════════════════════════════════════════

### Stage 5: Fix Plan
- Runs: `/team fix <plan issues from review>`
- Purpose: Address review findings before building
- Autonomy: Full (post-approval)

### Stage 6: Build
- Runs: `/team develop <scope from plan>`
- Purpose: Build the actual product
- Autonomy: Full (post-approval) — bypassPermissions mode

### Stage 7: Verify
- Runs: `/team verify <built product against plan>`
- Purpose: Confirm deliverables match spec
- Autonomy: Full (post-approval)

### Post-Ship
- If verify finds issues → `/team fix` automatically, then re-verify (max 2 rounds)
- Update team-feedback.md with learnings
- macOS notification: "CoCo: Ship complete — {idea}"
- Report final summary to user

## Stage Handoffs

Each stage produces artifacts that feed the next:
- Research → RESEARCH-BRIEF.md (key findings, 200 lines max)
- Think → ARCHITECTURE-DECISION.md (chosen option + rationale)
- Plan → PLAN.md (implementation plan)
- Review → REVIEW-FINDINGS.md (issues to fix)
- Fix → Updated PLAN.md
- Build → Built code/files
- Verify → VERIFICATION-REPORT.md (pass/fail + evidence)

## Failure Handling

- If any stage fails → stop pipeline, report which stage failed and why
- User can resume: `/team ship --resume` picks up from last successful stage
- All artifacts saved to `.team-ship/` directory for resume capability

## Example

```
/team ship build a CLI tool that monitors AWS costs and alerts on anomalies

Stage 1: Researching AWS cost monitoring tools...
Stage 2: Evaluating architecture options...
Stage 3: Creating implementation plan...
Stage 4: Reviewing plan...

═══════════════════════════════════════════════
Plan ready. 3 phases, ~5 days estimated.
Research: 8 existing tools found, none with real-time alerting
Architecture: Node.js + AWS Cost Explorer API + SNS
Review: 2 minor findings (already addressed)

Proceed with build? [Y/n]
═══════════════════════════════════════════════

> y

Stage 5: Fixing plan issues...
Stage 6: Building... (4-layer pipeline, 8 agents)
Stage 7: Verifying... 12/12 requirements MET

Ship complete. 14 files created, all tests passing.
```

## GSD Integration

When `.planning/` exists, the ship pipeline creates GSD-compatible artifacts:
- Plan stage produces `.planning/phases/` structure
- Build stage uses `/gsd:execute-phase` conventions
- Verify stage cross-references REQUIREMENTS.md

ARGUMENTS: {{ARGUMENTS}}
