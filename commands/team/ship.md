---
description: "Use when the user wants an idea taken from concept to a shipped, reviewed product, or when the /team router picks ship. Runs six build stages, seven hard verification gates, then PR open, with one approval gate after the plan."
---
# /team ship, Idea to Shipped Product Pipeline

> Called by team.md router when action is `ship`.
> The ultimate automation: takes a natural language idea and delivers a built, reviewed, verified product.
> Approval model: one human approval gate after the plan, then the build and verification stages run without further prompts.

## Role Selection Bias

All roles are selected dynamically per stage. The ship pipeline runs 6 build stages,
then 7 hard verification gates (Stages 7-13), then PR-open (Stage 14), each using the
appropriate /team action's role selection.

## Pipeline: 6 Stages + 7 Hard Gates + PR Open

Every run begins with `python3 ~/.claude/skills/team-gate/scripts/gate_state.py start . ship`
(or `... ship no-arch` when `--no-arch` was passed), whose run id is written to
`.team-ship/RUN`. Every gate invocation below takes `--repo-root .`; `--resume` reads
`gate_state.py status` (see Failure Handling).

### Stage 1: Research

1. Map the repository before reading any code, whatever else this stage does.

```
python3 ~/.claude/skills/team-gate/scripts/brownfield_map.py --for "<the idea>" --repo-root .
```
exit 0: continue; read `.team-ship/BROWNFIELD-MAP.md` before doing anything else.
exit 1: not used; a map is not a pass or fail judgement.
exit 2: UNVERIFIED; quote the gate file's summary (gates/handoff-1-map.json).

2. Record the architecture baseline for the conformance gate. **This step never spawns
   agents and never reconciles the index.**

```
python3 ~/.claude/skills/team-gate/scripts/arch_gate.py baseline --repo-root .
```
exit 0: CURRENT; continue and quote the gate file's summary (gates/1-arch-baseline.json).
exit 2: STALE, NOT_APPLICABLE, or DISABLED; continue anyway and quote the status. This
result is informational only here; Stage 13's `gates/13-arch.json` is where it is
enforced. Stage 1 deliberately does not run `/team arch build` or `/team arch drift` to
refresh a stale index; rebuilding it is a separate, explicit act the human runs themself.

3. Confirm Stage 1's own inputs (there are none) so the handoff into it is recorded.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-inputs 1 --repo-root .
```
exit 0: continue; gates/handoff-1.json now lets Stage 2 open.
exit 1: not reachable for this stage, since Stage 1 declares no inputs to fail.
exit 2: UNVERIFIED; quote the gate file's summary.

4. Research the idea (competitive landscape, technical feasibility, existing tools) and
   write `.team-ship/RESEARCH-BRIEF.md`, 200 lines max.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-output 1 .team-ship/RESEARCH-BRIEF.md --repo-root .
```
exit 0: continue; the artifact is recorded (no gate file of its own for this check).
exit 1: BLOCK; quote the stderr reason and rewrite the brief.
exit 2: UNVERIFIED; quote the stderr reason.

- Autonomy: Full, no approval needed

### Stage 2: Think

1. Confirm Stage 2 may open.

```
python3 ~/.claude/skills/team-gate/scripts/ship_gate.py stage 2 --repo-root .
```
exit 0: allowed; continue.
exit 1: BLOCK; quote the `reason` field and fix the named gate before writing anything.
exit 2: UNVERIFIED; quote the `reason` field.

2. Confirm Stage 2's inputs (the research brief and the brownfield map) are ready.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-inputs 2 --repo-root .
```
exit 0: continue; gates/handoff-2.json now lets Stage 3 open.
exit 1: BLOCK; quote the stderr reason.
exit 2: UNVERIFIED; quote the stderr reason.

3. Evaluate architecture options and write `.team-ship/ARCHITECTURE-OPTIONS.md`, with a
   `## chosen` heading naming the selected option and its rationale. Record the chosen
   option in the brain decisions store via `/brain:update`; no script checks that write.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-output 2 .team-ship/ARCHITECTURE-OPTIONS.md --repo-root .
```
exit 0: continue.
exit 1: BLOCK; quote the stderr reason (commonly a missing `chosen` heading) and rewrite.
exit 2: UNVERIFIED; quote the stderr reason.

- Autonomy: Full, no approval needed

### Stage 3: Plan

1. Confirm Stage 3 may open.

```
python3 ~/.claude/skills/team-gate/scripts/ship_gate.py stage 3 --repo-root .
```
exit 0: allowed; continue.
exit 1: BLOCK; quote the `reason` field.
exit 2: UNVERIFIED; quote the `reason` field.

2. Confirm Stage 3's input (the architecture options) is ready.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-inputs 3 --repo-root .
```
exit 0: continue; gates/handoff-3.json now lets Stage 4 open.
exit 1: BLOCK; quote the stderr reason.
exit 2: UNVERIFIED; quote the stderr reason.

3. Write the detailed implementation plan to `.team-ship/PLAN.md` (phases, tasks,
   dependencies, and a `requirements` list, one item per requirement, since
   `claim_evidence.py matrix` reads that list at Stage 12). Name each requirement's
   tests in the form prove_red records: `tests/test_x.py::TestClass.test_method` for a
   unittest method (a dot between class and method) or `tests/test_x.py::test_fn` for a
   plain function; a mismatched name grades the requirement UNVERIFIED at Stage 12, and
   the plan cannot be edited afterwards without breaking its artifact receipt.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-output 3 .team-ship/PLAN.md --repo-root .
```
exit 0: continue.
exit 1: BLOCK; quote the stderr reason and rewrite.
exit 2: UNVERIFIED; quote the stderr reason.

4. Also declare the intended architecture to `.team-ship/ARCH-PLAN.json`, the forward
   counterpart to `.arch/index.json`: where the index records what exists, this plan
   records what this ship intends to build and where it intends to put it. Skip this
   sub-step and the two below when `--no-arch` was passed. Each component carries an
   `id`, a `title` using the `[Business Function] + [Implementation Context]` formula, a
   `status` of `new`, `modified`, or `unchanged`, the `intendedPaths` it will occupy, and
   a rationale; the plan also records `declaredAtCommit` (HEAD before anything is built)
   and an `outOfScope` list of paths this ship must not touch. Schema and worked examples
   live in `skills/arch-index/references/arch-plan.md`.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-output 3 .team-ship/ARCH-PLAN.json --repo-root .
```
exit 0: continue.
exit 1: BLOCK; quote the stderr reason and rewrite.
exit 2: UNVERIFIED; quote the stderr reason.

5. Declare the plan's shape, before anything is built. This checks identifiers,
   statuses, symmetry, non-empty declarations, and scope self-consistency; it
   deliberately does not check whether the declared paths exist yet, because nothing has
   been built.

```
python3 ~/.claude/skills/team-gate/scripts/arch_gate.py plan-declare --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/3-arch-plan.json).
exit 1: BLOCK; an unsatisfiable plan (a path in both a component's `intendedPaths` and
`outOfScope`, an asymmetric connection, an invalid status); quote the reason and rewrite
`ARCH-PLAN.json` before the approval gate rather than after the build.
exit 2: UNVERIFIED; the script could not run or `ARCH-PLAN.json` is absent; the run
cannot pass Stage 13's `arch` row until this gate passes or an override receipt names it.

- Autonomy: Full, no approval needed

### Stage 4: Review Plan

1. Confirm Stage 4 may open.

```
python3 ~/.claude/skills/team-gate/scripts/ship_gate.py stage 4 --repo-root .
```
exit 0: allowed; continue.
exit 1: BLOCK; quote the `reason` field.
exit 2: UNVERIFIED; quote the `reason` field.

2. Confirm Stage 4's input (the plan) is ready.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-inputs 4 --repo-root .
```
exit 0: continue; gates/handoff-4.json now lets Stage 5 open.
exit 1: BLOCK; quote the stderr reason.
exit 2: UNVERIFIED; quote the stderr reason.

3. Have specialists review the plan and write `.team-ship/REVIEW-FINDINGS.md`.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-output 4 .team-ship/REVIEW-FINDINGS.md --repo-root .
```
exit 0: continue.
exit 1: BLOCK; quote the stderr reason and rewrite.
exit 2: UNVERIFIED; quote the stderr reason.

- Autonomy: Full, no approval needed

### APPROVAL GATE

1. Confirm every approval-gate artifact exists and is non-trivial.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py approval-ready --repo-root .
```
exit 0: continue.
exit 1: BLOCK; the gate cannot be presented honestly; report which stage did not write
its artifact and stop.
exit 2: UNVERIFIED; quote the stderr reason.

2. Render the approval text from the five artifacts.

```
python3 ~/.claude/skills/team-gate/scripts/render_approval.py --repo-root .
```
exit 0: continue; present `.team-ship/APPROVAL.md` to the user. It carries the research
summary, the architecture decision, the plan overview, the intended architecture as a
table of component, status, and intended paths (omitted only when `--no-arch` was
passed, since it is the thing the build will be held to afterwards and the most useful
item on this gate to disagree with), and the review findings.
exit 1: BLOCK; an approval-gate artifact is missing; quote the stderr reason.
exit 2: UNVERIFIED; quote the stderr reason.

3. Ask: "Plan ready. Proceed with build? [Y/n]"

The human's answer is written as an approval receipt by the harness's turn-log hook,
from their own words, never by the model. `ship_gate.py stage 6` will not open without
it. If the user says no, stop and keep all artifacts for later. If the user says yes,
full autonomy from here.

### Stage 5: Fix Plan

1. Confirm Stage 5 may open.

```
python3 ~/.claude/skills/team-gate/scripts/ship_gate.py stage 5 --repo-root .
```
exit 0: allowed; continue.
exit 1: BLOCK; quote the `reason` field.
exit 2: UNVERIFIED; quote the `reason` field.

2. Confirm Stage 5's input (the review findings) is ready.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-inputs 5 --repo-root .
```
exit 0: continue; gates/handoff-5.json now lets Stage 6 open.
exit 1: BLOCK; quote the stderr reason.
exit 2: UNVERIFIED; quote the stderr reason.

3. Run `/team fix` on the review findings and rewrite `.team-ship/PLAN.md` to address
   them.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-output 5 .team-ship/PLAN.md --repo-root .
```
exit 0: continue.
exit 1: BLOCK; quote the stderr reason and rewrite.
exit 2: UNVERIFIED; quote the stderr reason.

- Autonomy: Full (post-approval)

### Stage 6: Build

1. Confirm Stage 6 may open.

```
python3 ~/.claude/skills/team-gate/scripts/ship_gate.py stage 6 --repo-root .
```
exit 0: allowed; continue.
exit 1: BLOCK; the approval receipt is the most common missing item here; quote the
`reason` field.
exit 2: UNVERIFIED; quote the `reason` field.

2. Confirm Stage 6's input (the plan) is ready.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-inputs 6 --repo-root .
```
exit 0: continue; gates/handoff-6.json now lets Stage 7 open.
exit 1: BLOCK; quote the stderr reason.
exit 2: UNVERIFIED; quote the stderr reason.

3. Establish the pre-build baseline before any commit lands, so Stage 9 has a base to
   prove tests red against.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . discover
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . run
```
exit 0: continue and quote the gate file's summary for each command; record this run's
head field now as the base for Stage 9, since Stage 8 rewrites gates/8.json after the
build.
exit 1: BLOCK before the build; a failure here is a pre-existing break in the
repository, quote the reasons and stop rather than looping back to a build that has not
happened.
exit 2: UNVERIFIED; quote the stderr reason for the command that stopped.

4. Run `/team develop <scope from plan>` to build the actual product. bypassPermissions
   mode; full autonomy.

- Autonomy: Full (post-approval), bypassPermissions mode

### HARD GATES (Stages 7-13)

Between Build and PR-open, run seven hard gates, each writing into a gate file under the
run directory and into `.team-ship/EVIDENCE.md`, and each able to BLOCK. No gate can be
satisfied by narration. The gate files of stages 1 to 6 keep the pre-build head they were
measured at; ship_gate accepts them when that head is an ancestor of HEAD, and requires
the exact HEAD only of the gates that measure the built tree. The three-round bound on
looping back to Build is `ship_gate.py check`'s own rounds row, covered at Stage 14. See
"Hard Gate Semantics" below.

If scope must be cut, the essential core is Stage 8 (test execution), Stage 11
(independent re-execution), and Stage 12 (claim ↔ evidence). Stages 7, 9, 10, and
13 add depth.

#### Stage 7: Env Parity

1. Re-run discover now that Build has committed; `run_gate.py run` refuses a discover
   file recorded at a different HEAD, so discover always precedes it after a commit.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . discover
```
exit 0: continue and quote the gate file's summary (gates/7-discover.json).
exit 1: not used; discover exits 0 or 2.
exit 2: UNVERIFIED; zero commands qualified; the run cannot pass Stage 14 until this
gate passes or an override receipt names it.

2. Compare locally installed `ruff`, `mypy`, and `pytest` against the versions CI pins.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . parity
```
exit 0: continue and quote the gate file's summary (gates/7.json).
exit 1: BLOCK; a version mismatch; quote the reasons and loop back to Build.
exit 2: UNVERIFIED; quote the reasons.

Provision what CI provisions, for example a Docker Postgres or pgvector, and export the
DSN it needs (such as `APP_PG_TEST_DSN`) so DB-gated tests actually run. When something
cannot be provisioned, record "override integration: <reason>" in your own words as the
human; run_gate's own skip rule decides the rest, since any skipped test still forces
`UNVERIFIED` rather than a silent pass.

#### Stage 8: Test Execution *(essential)*

1. Run every command discover recorded, with the integration DSN set, and capture the
   parsed summary.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . run
```
exit 0: continue and quote the gate file's summary (gates/8.json); this rewrites the
baseline recorded at Stage 6, which is why that head was noted separately.
exit 1: BLOCK; quote the reasons from the gate file and loop back to Build.
exit 2: UNVERIFIED; any skipped test forces this outcome rather than a pass; quote the
reasons.

#### Stage 9: TDD Red-Green

1. Prove every test added or modified since the Stage 6 baseline was red before the
   implementation existed, for the right reason, then green after.

```
python3 ~/.claude/skills/team-gate/scripts/prove_red.py prove --base <the head noted at Stage 6> --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/9.json).
exit 1: BLOCK; a never-red or invalid-red classification catches an always-fail test, an
always-pass test, or a test that encodes the bug as the expected value; quote the reason
and loop back to Build. Whether a specific red class actually encodes the bug stays a
review judgement no script makes.
exit 2: UNVERIFIED; quote the reason.

2. Re-hash every proved test at the current HEAD to confirm none of them changed after
   being proved.

```
python3 ~/.claude/skills/team-gate/scripts/prove_red.py recheck --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/9-recheck.json).
exit 1: BLOCK; a changed or removed test; quote the reasons and loop back to Build.
exit 2: UNVERIFIED; quote the reasons.

#### Stage 10: Coverage

1. Re-run the discovered test command with branch coverage and capture the real number.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . coverage
```
exit 0: continue and quote the gate file's summary (gates/10.json); never narrate a
coverage number that was not measured this way.
exit 1: not used; coverage exits 0 or 2.
exit 2: NOT_APPLICABLE when discover found no pytest-shaped command, otherwise
UNVERIFIED for any other measurement failure; this blocks like any other gate unless an
override receipt names gate "10". A dependency that could not be provisioned at Stage 7
is the usual reason coverage reads unit-only rather than measured; no script records
that label, so say so in the override's own words.

#### Stage 11: Independent Verify *(essential)*

1. Set up a clean, detached worktree at HEAD with no `.team-ship/` of its own, and spawn
   the verifier.

```
python3 ~/.claude/skills/team-gate/scripts/verify_independent.py setup --repo-root .
```
exit 0: continue; the printed line is the exact `claude -p` invocation to spawn, in the
printed worktree, with the verifier role.
exit 1: BLOCK; independence failed (a stray `.team-ship/` in the fresh worktree); quote
the reason.
exit 2: UNVERIFIED; quote the reason.

2. The verifier, in that worktree, without reading `.team-ship/EVIDENCE.md` or any
   builder claim, runs the same three commands under the verifier role, which write
   `gates/<n>-verifier.json` instead of overwriting the builder's own gate files.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . --role verifier discover
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . --role verifier run
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . --role verifier coverage
```
exit 0/1/2 per command: the same contract as Stages 7, 8, and 10 above; the verifier
reports only the three exit codes, nothing else.

3. Compare the builder's gate files against the verifier's.

```
python3 ~/.claude/skills/team-gate/scripts/verify_independent.py compare --repo-root .
```
exit 0: continue; the captured re-run matches the builder's claims.
exit 1: BLOCK; any mismatch (exit, passed, skipped, failed); quote the discrepancy and
loop back to Build. This removes self-report trust.
exit 2: UNVERIFIED; quote the reason.

4. Tear down the worktree.

```
python3 ~/.claude/skills/team-gate/scripts/verify_independent.py teardown --repo-root .
```
exit 0: continue.
exit 1: not used; teardown exits 0 or 2.
exit 2: UNVERIFIED; quote the reason.

#### Stage 12: Claim <-> Evidence *(essential)*

1. Assemble the run's gate files into `.team-ship/EVIDENCE.json` and render
   `.team-ship/EVIDENCE.md`.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . evidence
```
exit 0: continue and quote `.team-ship/EVIDENCE.md`; its entry ids are what the PR body
cites.
exit 1: not used; evidence exits 0 or 2.
exit 2: UNVERIFIED; quote the stderr reason.

2. Grade the plan's requirements against the run's gate files.

```
python3 ~/.claude/skills/team-gate/scripts/claim_evidence.py matrix .team-ship/PLAN.md --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/11-matrix.json).
exit 1: BLOCK; a requirement graded NOT MET; quote the reason and loop back to Build.
exit 2: UNVERIFIED; a requirement graded UNVERIFIED with none NOT MET; quote the reason.

3. Write the narrative section to `.team-ship/PR-NARRATIVE.md`, then render
   `.team-ship/PR-BODY.md`: the narrative plus a quantitative section generated from
   `EVIDENCE.json`, one `[E<n>]`-tagged sentence per gate entry.

```
python3 ~/.claude/skills/team-gate/scripts/render_pr_body.py --repo-root .
```
exit 0: continue.
exit 2: UNVERIFIED; quote the stderr reason. There is no block outcome here; a missing
narrative is not an error, since the narrative is optional model-written prose.

4. Check every claim in the rendered PR body against `EVIDENCE.json`, including the
   merge-honesty check: never imply "merged," "shipped," or "CI green" for a branch not
   reachable from `main` (see the lexicon's mergeClaims entries).

```
python3 ~/.claude/skills/team-gate/scripts/claim_evidence.py check .team-ship/PR-BODY.md --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/12.json).
exit 1: BLOCK; any finding, unbacked claim, contradicted number, or merge-claim without
its condition met; quote the finding and strip or reword the claim.
exit 2: UNVERIFIED; quote the stderr reason.

#### Stage 13: CI Mirror

The CI-mirror comparison here has no invocation of its own: `ship_gate.py check` (Stage
14) computes it directly from `gates/7-discover.json` and `gates/8.json`, proving the
commands run locally were exactly the commands CI runs. Two architecture checks run
alongside it, both at this stage.

1. Verify the build put every declared `new` or `modified` component where the plan
   said it would, and touched nothing declared `outOfScope`. Skip when `--no-arch` was
   passed. Components marked `unchanged` are exempt, since the ship never claimed to
   build them.

```
python3 ~/.claude/skills/team-gate/scripts/arch_gate.py plan-verify --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/13-arch-plan.json).
exit 1: BLOCK; a declared path missing after the build, a change under an `outOfScope`
path, or a `declaredAtCommit` git cannot resolve; quote the reason and loop back to
Build.
exit 2: UNVERIFIED; the script could not run.

**Scope limit.** This gate proves the declared paths are now real and that nothing landed
out of bounds. It does not prove the code at those paths does what the component said it
would. That remains a review judgement, and a clean result licenses no claim about it.

2. Re-check architecture conformance against the Stage 1 baseline. Currency was judged
   once, at Stage 1; this reproduces that status rather than re-deriving it, so a pin
   that is now behind HEAD because Stage 6 committed is expected and never read as fresh
   staleness.

```
python3 ~/.claude/skills/team-gate/scripts/arch_gate.py conformance --repo-root .
```
exit 0: CURRENT at Stage 1; continue and quote `.arch/ARCH-GATE.json`.
exit 1: BLOCK; a component with zero surviving primary paths, or a file added outside
every claimed path forming a new top-level source directory with no recorded
justification; quote the reason and loop back to Build.
exit 2: STALE, NOT_APPLICABLE, or DISABLED at Stage 1, reproduced here, or the validator
could not run; none of these is a pass. This blocks Stage 14 unless an override receipt
names gate "arch"; both this file and `gates/13-arch-plan.json` above share that one
override name.

**Structural drift only.** A component reworked inside its own already-claimed directory
produces no drift, so a clean result never licenses a claim that the architecture is
sound. See `team:architecture.md`.

### Hard Gate Semantics

- BLOCK is real: a failed gate stops the pipeline and loops back to Build, bounded by
  `ship_gate.py check`'s rounds row (Stage 14).
- Skipped is never passed: `run_gate.py run` forces `UNVERIFIED` on any skip.
- Evidence or it did not happen: Stage 12's `claim_evidence.py check` strips any claim
  `render_pr_body.py` did not back with an `EVIDENCE.json` entry.
- Independent re-execution: Stage 11's verifier never reads the builder's summary and
  runs the gate itself, from a clean worktree.

### Stage 14: PR Open

1. Aggregate every gate above into one verdict.

```
python3 ~/.claude/skills/team-gate/scripts/ship_gate.py check --repo-root .
```
exit 0: PASS or PASS_WITH_OVERRIDE; open the PR. `gh pr create` is denied by the stage
guard hook on any other outcome, so this is not optional ceremony.
exit 1: BLOCK; quote every failing line the command prints, stop, and do not open the
PR. A build_rounds count above 3 is this same row, named "rounds"; a fourth round needs
an override receipt naming gate "rounds" in the human's own words.
exit 2: UNRUNNABLE; ship_gate itself could not measure the run; quote the reason.

The hooks start in observe mode and record what they would have denied as certified
receipts; a run started with `gate_state.py start . ship hooks=enforce` turns the denies
on, and the hooks README describes both modes.

2. Write `.team-ship/SHIP-REPORT.md`, the per-gate verdict table plus either the pull
   request URL or the prioritized gap list that blocked it. This artifact is written on
   both outcomes, because a blocked run is exactly the case where the reader needs to
   know which gate fired. Deciding which gaps matter most stays a judgement no script
   makes.

```
python3 ~/.claude/skills/team-gate/scripts/check_artifacts.py stage-output 14 .team-ship/SHIP-REPORT.md --repo-root .
```
exit 0: continue.
exit 1: BLOCK; quote the stderr reason and rewrite.
exit 2: UNVERIFIED; quote the stderr reason.

### Post-Ship

- A PR may only be opened after Stage 14 reports PASS or PASS_WITH_OVERRIDE. If it
  reports BLOCK, stop and report the gap list; do not open the PR, and do not describe
  the work as shipped.
- Update team:feedback.md with learnings, including any gate that fired.
- macOS notification, "CoCo: Ship complete, {idea}", only once a `pr-opened` receipt
  exists for this run.
- Report the final summary to the user, including the `.team-ship/EVIDENCE.md` location.

## Stage Handoffs

Each stage produces artifacts that feed the next. **Every artifact in this table is
written to `.team-ship/` by the stage that owns it, and the orchestrator writes it
before moving to the next stage.** A stage that has not written its artifact has not
completed. This is deliberate: an artifact named in a handoff table but produced by
nothing cannot be read by the next stage, cannot be shown at the approval gate, and
cannot be recovered by `--resume`.

- Research → `.team-ship/RESEARCH-BRIEF.md` (key findings, 200 lines max) and
  `.team-ship/BROWNFIELD-MAP.md` (the Stage 1 map)
- Research → `gates/1-arch-baseline.json` (the architecture baseline: pin, HEAD, and
  status at Stage 1; absent by design on repositories that do not want one)
- Think → `.team-ship/ARCHITECTURE-OPTIONS.md` (options considered, the chosen one, and
  the rationale for choosing it). The chosen option is additionally recorded in the
  brain decisions store via `/brain:update`, which is the canonical home for decisions
  per the global instructions.
- Plan → `.team-ship/PLAN.md` (implementation plan) and `.team-ship/ARCH-PLAN.json`
  (the intended architecture: components, their intended paths, and what is out of
  scope), declared by `gates/3-arch-plan.json`.
- Stage 13 → `gates/13-arch-plan.json` (declared versus actual) and `gates/13-arch.json`
  (conformance, reproducing the Stage 1 baseline status)
- Review → `.team-ship/REVIEW-FINDINGS.md` (issues to fix)
- Fix → updated `.team-ship/PLAN.md`
- Build → built code and files in the working tree
- Hard Gates (7-13) → `.team-ship/EVIDENCE.md` (captured commands, exit codes, summaries)
- PR Open (14) → `.team-ship/SHIP-REPORT.md` (the per-gate GREEN/BLOCK verdict table, and
  either the pull-request URL or the prioritized gap list that prevented it)

There is no separate Verify stage. Verification is what Stages 7 through 13 are, and
`EVIDENCE.md` is its artifact.

## Failure Handling

- If any stage fails, stop the pipeline and report which stage failed and why, by
  quoting the `reason` field `ship_gate.py stage N` or `ship_gate.py check` printed.
- A hard-gate BLOCK (Stages 7-13) is a first-class stop reason: report the BLOCK plus
  the gap list, loop back to Build, and do NOT open the PR. `ship_gate.py check`'s
  rounds row is the max-3-rounds bound; a fourth round needs an override naming
  "rounds."
- User can resume: `/team ship --resume` reads `gate_state.py status` (`stage_cursor`,
  `last_gate`) to pick up from the last successful stage, or, for a gate BLOCK, at the
  failed gate.
- All artifacts, including `EVIDENCE.md`, are saved to `.team-ship/` for resume
  capability.

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
  9 TDD red-green: 18/18 new tests proven red then green
  10 Coverage: 94% branch (measured, CI-reproducible)
  11 Independent verify: clean-checkout re-run matches claims
  12 Claim vs evidence: all PR claims backed by EVIDENCE.md
  13 CI mirror: make check clean (local equals CI)
Stage 14: PR opened, all gates GREEN.

Ship complete. 14 files created. Evidence: .team-ship/EVIDENCE.md
```

## GSD Integration

When `.planning/` exists, the ship pipeline creates GSD-compatible artifacts.
- Plan stage produces `.planning/phases/` structure
- Build stage uses `/gsd-execute-phase` conventions
- Verify stage cross-references REQUIREMENTS.md

ARGUMENTS: $ARGUMENTS
