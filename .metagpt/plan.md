# PLAN: the self-evolution loop, persona scale, and the cadence

Stage `plan`, written 2026-09-18. Owner: Rijul Kalra. Status: awaiting approval.
Spec: [`arch.md`](arch.md) and [`prd.md`](prd.md). Diagram: [`arch-diagram.html`](arch-diagram.html).

Numbered tasks, in build order. The first five are the working set this plan starts with.
Each task names its files, what makes it done, and the test that proves it. No task hides
two unrelated jobs behind one "and then".

House rules that apply to every task below, inherited from the repository and from the
team-gate retrofit now merged on main:

- Three valued exit everywhere: 0 pass, 1 blocked by a guard, 2 unrunnable or unmeasured.
- Every script takes `--self-test`; every case invokes the CLI through
  `subprocess.run([sys.executable, __file__, ...])`, asserts the return code AND a stderr
  substring, and runs on a temporary copy, never on committed fixtures.
- Fixtures are hermetic: no network, no model, no `$HOME` dependency, no installed copy of
  anything. This session's two red CI runs both passed on macOS and failed on Linux, so a
  fixture that depends on the machine it runs on is a defect.
- No em dash and no section sign in any artifact.
- The brain commits; builders do not. One commit per verified task, conventional subject
  under 72 characters, full prose body.

Prerequisite outside the task list: the `~/.claude/skills/team-gate` symlink needs the
owner's word before it is created on this machine. Nothing in this plan depends on it, and
local invocations use the repository path until it exists.

---

## Working set

### 1. Land the skill tree and its count coupling

**Files:** `skills/skill-evolution/SKILL.md` (frontmatter with `name` and `description`),
`skills/skill-evolution/references/lanes.json`,
`skills/skill-evolution/references/proposal-schema.json`,
`skills/skill-evolution/references/signal-sources.md`,
`skills/skill-evolution/state/ledger.jsonl` (empty at first commit), and the count coupled
hand written files: `README.md`, `package.json`, `.claude-plugin.json`, `index.html`,
`coco/index.html`, `docs/install.md`, `docs/INDEX.md`, `agents/README.md`,
`assets/og-image.svg`, `systems/superintelligence/HOW-IT-WORKS.html`. Generated files
(`docs/asset-counts.json`, the four INDEX files, `docs/by-domain/`) are regenerated, never
hand edited.

**Done when:** `python3 scripts/build-index.py` leaves no diff on a second run, and
`bash tests/check-asset-counts.sh` exits 0 with the new skill counted.

**Test:** those two commands, plus CI's frontmatter lint on the next push (the workflow
validates skills frontmatter and runs only when `skills/**/SKILL.md` changes).

### 2. ledger.py: the committed ledger

**Files:** `skills/skill-evolution/scripts/ledger.py`,
`skills/skill-evolution/scripts/fixtures/ledger/`.

**Done when:** `append(record)` writes one JSON line atomically, `rejected_recent(diff_sha256)`
returns whether the same diff was rejected inside the two cycle window, a malformed ledger
line is an error rather than a silent skip, and the CLI honours the three valued exit.

**Test:** `python3 skills/skill-evolution/scripts/ledger.py --self-test` on temporary
copies, with cases for append, append to an existing chain, rejected-recent true and false,
malformed line, and a missing ledger file.

### 3. lane.py: the only model adapter

**Files:** `skills/skill-evolution/scripts/lane.py`, `skills/skill-evolution/references/lanes.json`,
`skills/skill-evolution/scripts/fixtures/lane/`.

**Done when:** lane resolution reads `lanes.json`, the per cycle budget is checked before
any call and an over-budget cycle exits 1 naming the budget, the expensive review lane
refuses without an explicit owner flag, and every call records lane id, calls and tokens.
Tests never touch the network: a stub lane is a fixture, and the real lane is exercised only
by a documented manual command.

**Test:** `python3 skills/skill-evolution/scripts/lane.py --self-test`, cases for stub call
with cost recorded, budget exceeded exit 1, expensive lane refused exit 1, unknown lane exit
2, and malformed `lanes.json` exit 2.

### 4. observe.py: the deterministic signal step

**Files:** `skills/skill-evolution/scripts/observe.py`,
`skills/skill-evolution/references/signal-sources.md`,
`skills/skill-evolution/scripts/fixtures/observe/`.

**Done when:** it writes `signals/<cycle>.json` matching the schema in `arch.md` section 4,
`pinned_commit` is the resolved HEAD, a window with no signal exits 0 and says there is
nothing to observe, and two runs over the same window and commit are byte identical.

**Test:** `python3 skills/skill-evolution/scripts/observe.py --self-test`, including a
determinism case that runs twice and compares bytes, and a case asserting no model lane is
consulted (the stub lane records zero calls).

### 5. validate.py: the guard

**Files:** `skills/skill-evolution/scripts/validate.py`,
`skills/skill-evolution/scripts/fixtures/validate/`.

**Done when:** it refuses an out of scope path (a persona file, a command file, a count
file, the loop's own scripts) with exit 1; refuses a citation that does not resolve at the
pinned commit with exit 2; refuses a cycle over the proposal cap and states the remainder;
refuses a diff the ledger already rejected inside the window; and refuses a count move whose
coupled files did not move, by running the repository's own checkers rather than a private
copy of their rules.

**Test:** `python3 skills/skill-evolution/scripts/validate.py --self-test`, one case per
refusal above plus one clean acceptance, each on a temporary copy of a fixture repository.

---

## Remaining tasks

### 6. propose.py: the single model write

**Files:** `skills/skill-evolution/scripts/propose.py`,
`skills/skill-evolution/scripts/fixtures/propose/`.

**Done when:** it reads a signals file, asks one lane for candidates, and writes
`proposals/<id>.json` plus `proposals/<id>.patch` in the documented shape; a stub lane
produces byte identical proposals on two runs; the lane budget is passed through and
recorded.

**Test:** `--self-test` with a stub lane, cases for one candidate, no candidate (empty
cycle), malformed lane response (exit 2), and the recorded cost fields.

### 7. render_cycle.py: the human artifact

**Files:** `skills/skill-evolution/scripts/render_cycle.py`,
`skills/skill-evolution/scripts/fixtures/render_cycle/`.

**Done when:** `CYCLE.md` renders from the signals, proposals, validations and ledger for a
cycle, contains no wall clock timestamp outside the ledger's own values, and rerenders
identically.

**Test:** `--self-test` comparing two renders byte for byte, plus a case for a cycle with
zero proposals.

### 8. evolve.py: the entry point

**Files:** `skills/skill-evolution/scripts/evolve.py`.

**Done when:** `evolve.py run --window 30d` performs observe, propose, validate, and record;
`--dry-run` stops before opening a branch and reports what it would have proposed, using the
stub lane when `--lane stub` is given; `evolve.py status` prints the last cycle and open
proposals; the exit code is three valued.

**Test:** `--self-test` end to end on a temporary repository with the stub lane, in dry run
and in a branch creating run, asserting the branch name, the commit count and that `main`
was never written.

### 9. run_fixtures.sh and the CI join

**Files:** `skills/skill-evolution/scripts/run_fixtures.sh`, `.github/workflows/ci.yml`.

**Done when:** the runner exercises every script above, prints `N/N passed` and exits 0, and
CI runs it in the standalone suites step beside `skills/team-gate/scripts/run_fixtures.sh`.

**Test:** the runner locally, and the CI run on the pull request that lands it.

### 10. build_personas.py: the generator

**Files:** `systems/superintelligence/scripts/build_personas.py`,
`systems/superintelligence/references/persona-spec.example.json`,
`systems/superintelligence/scripts/fixtures/build_personas/`.

**Done when:** a spec file (department, archetype, domain, count) produces persona files
with the existing frontmatter contract and the DISCLAIMER line, in archetype sized batches,
and `coupled_files(counts)` names every published claim that moves when the persona count
moves.

**Test:** `--self-test` with a five persona fixture: files pass the frontmatter contract
checks and `check-persona-counts.py`; a fixture that moves a count without the coupled files
fails.

### 11. The first persona batch

**Files:** the generated persona files for one department, plus the coupled count files.

**Done when:** the batch lands with `python3 systems/team/validate_roles.py`,
`python3 systems/team/build_roster.py --check` and `bash tests/check-asset-counts.sh` all
exiting 0, and the owner has seen a sample of the generated personas before the merge.

**Test:** the three commands above, plus `python3 scripts/build-index.py` leaving no diff.

### 12. Cadence: the workflow and its document

**Files:** `.github/workflows/evolution-cycle.yml`, `workflows/evolution-cycle.md`.

**Done when:** the workflow runs monthly and on demand in `--dry-run` with no model
credentials present, the document states how to run a real cycle where credentials exist,
and the workflow parses and passes the repository's own `bash -n` and action checks.

**Test:** a local `--dry-run` invocation of the same command the workflow calls, plus the
workflow running green on `main` after the merge.

### 13. One recorded dry run against coco

**Files:** `state/CYCLE.md` for the first cycle, plus the ledger rows it appends.

**Done when:** a dry run over coco's own last 30 days produces a signals file, a proposal
set and a rendered cycle, committed as evidence, and the run's cost is recorded.

**Test:** the committed artifacts, plus a rerun showing byte identical signals for the same
pinned commit.

### 14. The acceptance run

**Files:** whatever the first real cycle proposes.

**Done when:** one real cycle opens a real pull request whose evidence the owner can check
by hand, and the owner has merged or rejected it with the reason recorded in the ledger.

**Test:** the pull request itself, and the ledger showing the proposal and its fate. This is
the PRD's acceptance test: the loop is proven by one honest cycle, not by its own suite.

### 15. Team-gate leftovers

**Files:** `skills/team-gate/scripts/arch_gate.py` or its fixtures, and
`skills/team-gate/scripts/prove_red.py` or its fixtures, whichever the work needs.

**Done when:** the two `arch_gate` cases that SKIP on CI because no installed copy of the
skill exists there either run or say why they cannot, and row 9b's pytest fixture-aware
runner is either built or recorded as a dated deferral with its reason.

**Test:** the two touched suites' own self-tests, plus the full
`bash skills/team-gate/scripts/run_fixtures.sh` at 14/14.

Register row 27 (the before and after comparator for reanalyse) stays deferred by ruling R7.
It is not in this plan.

---

## Order and dependencies

1 to 5 are independent of each other except that 3 and 5 are needed by 6. 6 needs 3, 4 and 5.
8 needs 2 through 7. 9 needs 2 through 8. 10 and 11 are independent of the loop entirely and
can run in parallel with 2 through 9. 12 needs 8. 13 needs 9 and 12. 14 needs 13 and the
owner's live credentials. 15 is independent of everything else and can run at any point.

## Verification standard

Every task is built by one agent and verified by a separate one that reproduces the claims
live, per the roster now recorded in the merged handoff. No task is done on a builder's
report: the report must carry pasted output, and the brain re-runs the suite before
committing. A task whose suite passes on one platform and fails on another is not done.
