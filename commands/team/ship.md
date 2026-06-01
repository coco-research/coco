# /team ship — Idea to Shipped Product Pipeline

> Called by team.md router when action is `ship`.
> The ultimate automation: takes a natural language idea and delivers a built, reviewed, verified product.
> Uses Option B: one approval gate after plan, then full autonomy for build+verify.

## Role Selection Bias

All roles are selected dynamically per stage. The ship pipeline runs 6 build stages,
then 7 hard verification gates (Stages 7–13), then PR-open (Stage 14), each using the
appropriate /team action's role selection.

## Pipeline: 6 Stages + 7 Hard Gates + PR Open

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

### ─── HARD GATES (Stages 7–13) ───

Between Build and PR-open, run seven hard gates. Each gate follows the **Test
Evidence Protocol** (`team:evidence.md`), writes its results to
`.team-ship/EVIDENCE.md`, and can **BLOCK**. A BLOCK loops back to Build for a
fix (bounded to a maximum of 3 rounds) — it is never advisory, and **no gate can
be satisfied by narration.** See "Hard Gate Semantics" below.

If scope must be cut, the essential core is Stage 8 (test execution), Stage 11
(independent re-execution), and Stage 12 (claim ↔ evidence). Stages 7, 9, 10, and
13 add depth.

#### Stage 7: Env Parity
- Detect the CI configuration (`.github/workflows/*.yml`, `Makefile`, pre-push hooks).
- Pin `ruff`, `mypy`, and `pytest` to the exact versions CI uses (resolve floating constraints to the version CI installs).
- Provision the integration dependencies CI needs but never has — for example a Docker Postgres/pgvector — and export the DSN (e.g. `MARVIN_PG_TEST_DSN`) so DB-gated tests actually execute.
- If a dependency cannot be provisioned, degrade honestly: label its surface "unit-only" and forbid any integration claim. Do not let gated tests skip silently.

#### Stage 8: Test Execution  *(essential)*
- Run the repo's authoritative gate (e.g. `make check`) AND the full test suite with the integration DSN set.
- Capture raw stdout/stderr, exit codes, and the parsed pytest summary (`N passed, M skipped, K failed`).
- ANY skipped test → status `UNVERIFIED` (never "pass"). Any failure → **BLOCK**.

#### Stage 9: TDD Red-Green
- For each newly added test, prove it was RED before the implementation existed (for the right failure reason), then GREEN after.
- A test that was never red is rejected. This catches always-fail tests, always-pass (`assert True`) tests, and tests that encode the bug as the expected value.

#### Stage 10: Coverage
- Run coverage for real (`--cov --cov-branch`) and capture the number.
- If a dependency could not be provisioned, label coverage "unit-only" and forbid any integration-coverage claim. Never narrate a coverage number that was not measured.

#### Stage 11: Independent Verify  *(essential)*
- Runs: `/team verify <built product against plan>` with fresh agents from a CLEAN checkout.
- The verify agents must NOT read the builder's summary. They re-run the gate themselves and capture their own output.
- Their captured output is compared to the builder's claims; any mismatch → **BLOCK**. This removes self-report trust.

#### Stage 12: Claim ↔ Evidence  *(essential)*
- Every claim destined for the PR body is cross-checked against `EVIDENCE.md`. Unbacked claims are stripped.
- Merge-honesty check: do not imply CI-green or "merged" for a branch that is not reachable from `main`.

#### Stage 13: CI Mirror
- Run the actual CI workflow's authoritative gate locally (the same commands the CI watchdog re-runs, e.g. `make check`) so local == CI before push.

### Stage 14: PR Open
- Open the PR ONLY if Stages 7–13 are all GREEN with evidence.
- Otherwise: stop, report **BLOCK** plus a prioritized gap list, and do NOT open the PR.

### Hard Gate Semantics
- **BLOCK is real.** A failed gate stops the pipeline and loops back to Build (max 3 rounds). It does not proceed to PR.
- **Skipped ≠ passed.** A skip forces `UNVERIFIED` and triggers provision-or-block, never "pass."
- **Evidence or it didn't happen.** Every claim needs a captured command + output block in `EVIDENCE.md`. No matching evidence → the claim is deleted.
- **Independent re-execution.** Stage 11 agents never see the builder's summary; they run the gate from a clean clone.

### Post-Ship
- A PR may only be opened after Stages 7–13 are GREEN with evidence (see Stage 14). If any gate is BLOCK, stop and report the gap list — do not open the PR, and do not describe the work as shipped.
- Update team:feedback.md with learnings (including any gate that fired).
- macOS notification: "CoCo: Ship complete — {idea}" (only on a GREEN, PR-opened run).
- Report final summary to user, including the `EVIDENCE.md` location.

## Stage Handoffs

Each stage produces artifacts that feed the next:
- Research → RESEARCH-BRIEF.md (key findings, 200 lines max)
- Think → ARCHITECTURE-DECISION.md (chosen option + rationale)
- Plan → PLAN.md (implementation plan)
- Review → REVIEW-FINDINGS.md (issues to fix)
- Fix → Updated PLAN.md
- Build → Built code/files
- Hard Gates (7–13) → `.team-ship/EVIDENCE.md` (captured commands, exit codes, summaries)
- Verify → VERIFICATION-REPORT.md (pass/fail + evidence)

## Failure Handling

- If any stage fails → stop pipeline, report which stage failed and why
- A hard-gate BLOCK (Stages 7–13) is a first-class stop reason: report the BLOCK plus a prioritized gap list, loop back to Build (max 3 rounds), and do NOT open the PR
- User can resume: `/team ship --resume` picks up from the last successful stage — or, for a gate BLOCK, at the failed gate
- All artifacts (including `EVIDENCE.md`) saved to `.team-ship/` directory for resume capability

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
Stages 7-13: Hard gates...
  7 Env parity: ruff 0.15.12 pinned, Postgres 16 provisioned, DSN set
  8 Test execution: 312 passed, 0 skipped, 0 failed (exit 0)
  9 TDD red-green: 18/18 new tests proven red→green
  10 Coverage: 94% branch (measured, CI-reproducible)
  11 Independent verify: clean-checkout re-run matches claims
  12 Claim↔evidence: all PR claims backed by EVIDENCE.md
  13 CI mirror: make check clean (local == CI)
Stage 14: PR opened — all gates GREEN.

Ship complete. 14 files created. Evidence: .team-ship/EVIDENCE.md
```

## GSD Integration

When `.planning/` exists, the ship pipeline creates GSD-compatible artifacts:
- Plan stage produces `.planning/phases/` structure
- Build stage uses `/gsd:execute-phase` conventions
- Verify stage cross-references REQUIREMENTS.md

ARGUMENTS: {{ARGUMENTS}}
