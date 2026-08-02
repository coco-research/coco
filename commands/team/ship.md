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
- Writes: `.team-ship/RESEARCH-BRIEF.md`
- Record the architecture baseline for the conformance gate. **This step never spawns
  agents and never reconciles the index.** Read `.arch/pinned-commit` if it exists, record
  it alongside `git rev-parse HEAD`, and continue. That is the whole step.

  | State at Stage 1 | What Stage 1 does | Cost |
  |---|---|---|
  | `--no-arch` passed | Nothing. Gate later reports `DISABLED (--no-arch)`. | Free |
  | No `.arch/index.json` | Nothing. Gate later reports `NOT APPLICABLE`. | Free |
  | Pin equals HEAD | Record `CURRENT`. | Free |
  | Pin behind HEAD | Record `STALE` plus the pin. Gate later reports `UNVERIFIED`. | Free |

  Stage 1 deliberately does **not** run `/team arch build` or `/team arch drift`. An
  earlier version did, which meant every ship after a few commits silently paid for a
  full index reconciliation before any product work started. Rebuilding the index is a
  separate, explicit act: run `/team arch build` or `/team arch drift` yourself when you
  want the baseline refreshed. A stale baseline degrades the gate to `UNVERIFIED`, which
  is the honest outcome and costs nothing.
- Autonomy: Full — no approval needed

### Stage 2: Think
- Runs: `/team think <idea with research context>`
- Purpose: Architecture options, evaluate trade-offs
- Writes: `.team-ship/ARCHITECTURE-OPTIONS.md`, and records the chosen option in the brain decisions store via `/brain-update`
- Autonomy: Full — no approval needed

### Stage 3: Plan
- Runs: `/team plan <idea with chosen architecture>`
- Purpose: Detailed implementation plan with phases, tasks, dependencies
- Writes: `.team-ship/PLAN.md`
- **Also declares the intended architecture** to `.team-ship/ARCH-PLAN.json`. This is the
  forward counterpart to `.arch/index.json`: where the index records what exists, the plan
  records what this ship intends to build and where it intends to put it. Skip when
  `--no-arch` is passed.

  Each component carries an `id`, a `title` using the `[Business Function] +
  [Implementation Context]` formula, a `status` of `new`, `modified`, or `unchanged`, the
  `intendedPaths` it will occupy, and a rationale. The plan also records
  `declaredAtCommit` (the current HEAD, before anything is built) and an `outOfScope` list
  of paths this ship must not touch. Schema and worked examples live in
  `skills/arch-index/references/arch-plan.md`.

  Then run the declaration check, which validates shape only:

  ```bash
  python3 skills/arch-index/scripts/verify_arch_plan.py \
    .team-ship/ARCH-PLAN.json --declare
  ```

  It deliberately does **not** check whether the declared paths exist, because nothing has
  been built yet. A non-zero exit here is a BLOCK: an unsatisfiable plan (a path that also
  appears in `outOfScope`, an asymmetric connection, an invalid status) cannot be checked
  later, so it is worth catching before the approval gate rather than after the build.
- Autonomy: Full — no approval needed

### Stage 4: Review Plan
- Runs: `/team review <plan>`
- Purpose: Specialist review of the plan before building
- Writes: `.team-ship/REVIEW-FINDINGS.md`
- Autonomy: Full — no approval needed

### ═══════════════════════════════════════════════
### APPROVAL GATE
### ═══════════════════════════════════════════════
###
### Present to user, reading each item from the artifact that produced it:
###   - Research summary (key findings) — from .team-ship/RESEARCH-BRIEF.md
###   - Architecture decision (chosen option + rationale) — from
###     .team-ship/ARCHITECTURE-OPTIONS.md
###   - Plan overview (phases, estimated effort) — from .team-ship/PLAN.md
###   - Intended architecture (components, where each will live, what is out of
###     scope) — from .team-ship/ARCH-PLAN.json. Present it as a table of
###     component, status, and intended paths. This is the thing the build will
###     be held to afterwards, so it is the most useful item on this gate to
###     disagree with. Omit only when --no-arch was passed.
###   - Review findings (any critical/major issues) — from
###     .team-ship/REVIEW-FINDINGS.md
###
### If any of those four artifacts is missing, the gate cannot be presented
### honestly. Report which stage did not write its artifact and stop.
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
- Writes: `.team-ship/SHIP-REPORT.md` — the per-gate verdict table plus either the
  pull-request URL or the gap list. This artifact is written on both outcomes, because
  a blocked run is exactly the case where the reader needs to know which gate fired.

### Built-as-declared (runs alongside the seven test gates)

This is the gate that closes the loop opened at Stage 3. It answers one question: did the
build put the code where the plan said it would?

Skip when `--no-arch` was passed, and report `DISABLED (--no-arch)`. If
`.team-ship/ARCH-PLAN.json` is absent, report `NOT APPLICABLE`. Neither is a pass.

```bash
python3 skills/arch-index/scripts/verify_arch_plan.py \
  .team-ship/ARCH-PLAN.json --verify --repo-root .
```

- A component declared `new` or `modified` whose intended path does not exist after the
  build is a **BLOCK**. Either the build went somewhere else, or the component was
  silently dropped. Both are real failures, and neither shows up in any test result.
- A file changed under a path the plan declared `outOfScope` is a **BLOCK**.
- A script that cannot run, or a `declaredAtCommit` that git cannot resolve, is
  **UNVERIFIED**, never clean.

**Why this gate can exist at all.** Path existence cannot be checked at Stage 3, because
nothing has been built yet. It is therefore checked here, after Stage 6. Deferring the
check rather than weakening it is what makes a forward architecture declaration
enforceable: the plan is written when the knowledge exists, and tested when the evidence
exists. Components marked `unchanged` are exempt, since the ship never claimed to build
them.

Capture the output to `.team-ship/ARCH-PLAN-EVIDENCE.md`.

**Scope limit.** This gate proves the declared paths are now real and that nothing landed
out of bounds. It does not prove the code at those paths does what the component said it
would. That remains a review judgement, and a clean result licenses no claim about it.

### Architecture conformance (runs alongside the seven test gates)

Governed by `team:architecture.md`. Resolve the outcome from the baseline Stage 1
recorded, in this order. The first match wins, and each outcome is reported in the exact
words given.

| Baseline | Outcome | Report as |
|---|---|---|
| `--no-arch` was passed | Gate skipped by explicit request | `DISABLED (--no-arch)` |
| No `.arch/index.json` | Repository has not opted in | `NOT APPLICABLE` |
| Pin was `STALE` at Stage 1 | Cannot be checked honestly | `UNVERIFIED` |
| Pin was `CURRENT` at Stage 1 | Run the two scripts below | `PASS` or `BLOCK` |

None of the first three is a pass, and none may be reported as one.

```bash
python3 skills/arch-index/scripts/validate_index.py .arch/index.json --repo-root .
python3 skills/arch-index/scripts/arch_drift.py --repo-root .
```

- Any component with zero surviving primary paths is a **BLOCK**. The build deleted or
  relocated something the architecture said it owned.
- Any file added outside every claimed path, forming a new top-level source directory with
  no recorded justification, is a **BLOCK**. The build went somewhere it was not supposed
  to, or a component is missing from the index.
- A validator that cannot be executed is a **BLOCK**, never a pass.

**Currency is judged at Stage 1, not here.** By the time this gate runs, Stage 6 has
built and its agents have committed, so the pin is *expected* to be behind HEAD. That is
the point: `git diff <pin>..HEAD` is then exactly the set of changes this ship made, which
makes any drift it finds attributable to this build rather than to history. Do not read a
pin-behind-HEAD condition at gate time as staleness and do not downgrade to `UNVERIFIED`
for it. `UNVERIFIED` applies only when the pin was already behind HEAD at Stage 1, because
in that case drift cannot be attributed to this build at all.

Capture the output to `.arch/ARCH-EVIDENCE.md`. Because `.arch/` is committed, this gate
also runs in the Stage 11 clean checkout; an untracked index would silently make it
unrunnable there.

**Structural drift only.** A component reworked inside its own already-claimed directory
produces no drift, so a clean result never licenses a claim that the architecture is
sound. See `team:architecture.md`.

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

Each stage produces artifacts that feed the next. **Every artifact in this table is
written to `.team-ship/` by the stage that owns it, and the orchestrator writes it
before moving to the next stage.** A stage that has not written its artifact has not
completed. This is deliberate: an artifact named in a handoff table but produced by
nothing cannot be read by the next stage, cannot be shown at the approval gate, and
cannot be recovered by `--resume`.

- Research → `.team-ship/RESEARCH-BRIEF.md` (key findings, 200 lines max)
- Think → `.team-ship/ARCHITECTURE-OPTIONS.md` (options considered, the chosen one, and
  the rationale for choosing it). The chosen option is additionally recorded in the
  brain decisions store via `/brain-update`, which is the canonical home for decisions
  per the global instructions.
- Research → `.arch/index.json` + `.arch/ARCH-EVIDENCE.md` (validated structural index,
  produced by `/team arch`; absent by design on repositories that do not want one)
- Plan → `.team-ship/PLAN.md` (implementation plan) and `.team-ship/ARCH-PLAN.json`
  (the intended architecture: components, their intended paths, and what is out of scope).
  The second is what the built-as-declared gate checks the build against.
- Built-as-declared gate → `.team-ship/ARCH-PLAN-EVIDENCE.md` (declared versus actual)
- Review → `.team-ship/REVIEW-FINDINGS.md` (issues to fix)
- Fix → updated `.team-ship/PLAN.md`
- Build → built code and files in the working tree
- Hard Gates (7–13) → `.team-ship/EVIDENCE.md` (captured commands, exit codes, summaries)
- PR Open (14) → `.team-ship/SHIP-REPORT.md` (the per-gate GREEN/BLOCK verdict table, and
  either the pull-request URL or the prioritized gap list that prevented it)

There is no separate Verify stage. Verification is what Stages 7 through 13 are, and
`EVIDENCE.md` is its artifact; an earlier version of this table named a
`VERIFICATION-REPORT.md` produced by a stage that does not exist in the pipeline.

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
