# Team gate retrofit: scripts measure, hooks certify, prose judges

## What this changes

The `/team:*` slash commands enforced their verification steps in prose that a model could follow or skip. This branch retrofits the pipeline so that every gate is measured by a Python script that writes a gate file and a receipt, every gate file is chained in an append-only receipt log the aggregators verify, and the command documents invoke those scripts and quote their output instead of describing the check. Judgement stays with the model; measurement moves to the scripts; certification moves to the hooks.

The work lives under `skills/team-gate/`:

- `scripts/gate_state.py` is the shared library: run directories under `~/.team/runs/<run-id>/`, an append-only `receipts.jsonl` with a hash chain, fourteen closed receipt kinds, two-way verification of every gate file and artifact a receipt names, and path containment for everything it resolves.
- `scripts/brownfield_map.py` writes the Stage 1 code map from ripwire, an offline tree-sitter based call-graph tool, so a run on an existing repository starts from a machine-made map before the model reads anything.
- `scripts/check_artifacts.py`, `run_gate.py`, `prove_red.py`, `verify_independent.py`, `claim_evidence.py`, `arch_gate.py` and the three renderers measure the stage handoffs, the CI commands and their parity, the red-green proof of every new test (including a stubbed-implementation proof for tests-only changes), the independent re-run in a clean worktree, the claims in the PR body against the evidence, the requirements matrix through the tests that back each requirement, and the architecture baseline, declared plan and conformance.
- `scripts/ship_gate.py` and `fix_gate.py` aggregate the gates into one verdict with a three-valued exit (0 pass, 1 block, 2 unrunnable), answer whether a stage may open, honour override receipts written in the human's own words, and block a fourth build round.
- `hooks/` holds four Node hooks with no dependencies that run in observe mode by default: the turn log records approvals and overrides from the human's literal words, the artifact guard asks the aggregator before a stage artifact is written and denies writes to evidence and gate files, the stage guard gates `gh pr create` and `git push` on the ship verdict, and the stop guard blocks a turn from ending mid-pipeline once. `hooks/install.py` registers them.
- `commands/team/{fix,test,develop,verify,reanalyse,ship}.md` now invoke the scripts by their installed path, state the sequence of actions between gates, and keep judgement prose word for word.

## How it was verified

Every script carries a `--self-test` that regenerates deterministic fixtures with pinned dates and runs the script's own CLI on temporary copies; `scripts/run_fixtures.sh` runs all fourteen suites and joins the existing CI step. The suite passed from a detached clean checkout at every milestone, most recently at 45e5dd2 with 14 of 14; one such run caught a regression a scoped review had missed, which is why the clean-checkout run stays the proof. Every task was built by one agent and verified by a separate agent that reproduced the claims live, and the verifier briefs and rulings are recorded in the handoff documents kept outside the repository.

Two pilot runs of the fix pipeline on a planted bug in a unittest repository, using the real ripwire binary, exercised the whole chain. Run 1 found five defects (the red classifier attributed a unittest assertion to the standard library frame, the claim checker read a flat evidence shape run_gate never wrote, the matrix could not map a requirement to any gate, a flag position, and a stale-discover rule the prose had not stated); each became a fixed and verified task. Run 2 passed every step with fix_gate reporting PASS, an intact chain, and a certified would-deny receipt for the deliberate attempt to hand-write the evidence file; an independent verifier confirmed it from the run directory alone. The ship pipeline was then executed end to end by two independent verifiers on a scratch repository, which exposed that the head rule blocked every pre-build gate after the build's commits; the rule is now scoped by stage (pre-build gates accept an ancestor head, built-tree gates require the exact HEAD) and the pipeline reaches PASS_WITH_OVERRIDE without rerunning any stage check.

## What is deliberately not in this branch

The hooks run in observe mode and record what they would have denied. Switching the denies on, one at a time, and observing a real pipeline under the harness needs a live Claude Code session started inside a pilot repository with an isolated configuration directory, which a subagent of the build session cannot exercise. Those steps are the next tasks and are documented in the hooks README. The command files invoke scripts at `~/.claude/skills/team-gate/scripts/`, matching the arch-index arrangement; that symlink is created after merge.

## Review notes

The commit history is one commit per verified task with full-prose messages. The five earliest commits below f3f028c are a first fixture generator's accidental commits, squashed into one honestly named commit before this PR was opened. `.team-ship/` and `.claude/` are ignored; nothing under either is committed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
