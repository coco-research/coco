# Task 19 brief: the /team:fix pilot on a planted bug

PLAN.md section 8 defines success: a deliberately planted bug, a run that ends with gates/*.json present and chained, a receipts.jsonl whose chain verifies, an EVIDENCE.json whose head is HEAD, and one deliberate attempt to skip the red proof that the hook records (observe mode: a would-deny certified receipt; enforce mode, task 17 and 18: a real deny visible in the transcript). The pilot runs the scripts from the worktree path, because the installed path ~/.claude/skills/team-gate does not exist until the branch merges (ruling R9). Runner: a Haiku agent executes the steps and pastes every command and output; a Sonnet agent verifies from the run directory and the repository alone, without reading the runner's report.

## The pilot repository

A fresh git repository under a mktemp directory, fixed-date commits, with:

- `calc/__init__.py` exposing `add(a, b)` and `mean(xs)`; the planted bug is `mean` dividing by `len(xs) + 1`.
- `tests/test_calc.py` using the standard library `unittest`, covering `add` only, so the suite is green with the bug present.
- `scripts/test.sh`: `#!/usr/bin/env bash` then `python3 -m unittest discover -s tests -v`, executable.
- `.github/workflows/ci.yml` with one job whose steps are `actions/checkout@v4` and a run step `bash scripts/test.sh`. run_gate's discovery accepts the `bash *test*.sh` runner shape, so no pytest is needed; this machine has none, and fix_gate has no coverage stage.
- `.gitignore` containing `.team-ship/` and `.claude/`.
- One initial commit, then `gate_state.py start <repo> fix` and the run id written to `.team-ship/RUN`.

Hooks: `python3 <worktree>/skills/team-gate/hooks/install.py --project <repo>` registers the four hooks in `<repo>/.claude/settings.json` with observe mode as the run default, and the runner records `install.py --check` output. Project settings are read from the directory a Claude Code session starts in, so a subagent of this session that merely changes directory into the pilot repository does not have those hooks fired on its tool calls. The pilot therefore drives each hook directly with a constructed payload, exactly as hooks_selftest.py does (`node <worktree>/skills/team-gate/hooks/<hook>.js < payload.json` with cwd set to the pilot repository), for the skip attempt and for one artifact write; the harness-fired path is exercised in tasks 16 to 18 from an isolated CLAUDE_CONFIG_DIR session started inside the pilot repository. The brief states this so nobody reads the pilot's receipts as proof that the harness fired the hooks.

## The steps, each a gate

Every invocation is `python3 <worktree>/skills/team-gate/scripts/<script> ... --repo-root <repo>` from inside the repository. After each step the runner pastes the exit, the one-line stderr or stdout, and `cat` of the gate file named.

1. Stage 1 map: `brownfield_map.py --for "fix mean dividing by one too many"`; expect exit 0, gates/handoff-1-map.json, two artifacts.
2. Discover: `run_gate.py discover`; expect exit 0, gates/7-discover.json with commands [["bash", "scripts/test.sh"]].
3. Parity: `run_gate.py parity`; expect exit 0 (no pins beyond python, which is present) and gates/7.json; if parity reports a missing pin, paste it and continue, because the fix pipeline requires 7-discover and 8, not 7.
4. Baseline run: `run_gate.py run`; expect exit 0 and gates/8.json whose summary records the unittest counts. Verified before the pilot: run_gate's summary parser reads only pytest-shaped lines ("N passed"), so unittest output ("Ran N tests" then "OK" or "FAILED (failures=F, errors=E, skipped=S)") parsed as zero tests and exited 1 "no tests collected". Task 28 added the unittest shape to the parser and is committed, so step 4 is a real measurement.
5. Red test: the runner writes `tests/test_mean.py` asserting `mean([2, 4]) == 3` and commits it alone with a fixed date, `test(calc): mean of two values`.
6. Fix and proof: the runner fixes `mean`, commits `fix(calc): divide by the count`, runs `run_gate.py discover` again and then `run_gate.py run` (run refuses a discover file recorded at another HEAD; gates/8.json rewritten, latest receipt wins), then `prove_red.py prove --base <the head recorded in gates/8.json by the baseline run in step 4>`; prove_red runs the new test green at HEAD in a throwaway worktree, reverts the implementation paths there and proves it goes red for the right reason, so gates/9.json must classify the test valid-red-assertion with exit 0. Then `prove_red.py recheck`; expect gates/9-recheck.json exit 0. (An earlier version of this brief ran prove before the fix, which contradicts prove_red's contract; corrected 2026-09-18 mid-pilot.)
7. Matrix: the runner writes `.team-ship/PLAN.md` with a `requirements` list of one item in the scalar form "R1: mean returns the arithmetic mean [tests: tests/test_mean.py::TestMean.test_mean]" and runs `claim_evidence.py matrix .team-ship/PLAN.md`; expect MET with route tests and exit 0 (task 32), and paste the row from gates/11-matrix.json.
8. Evidence: `run_gate.py evidence`; expect .team-ship/EVIDENCE.json with head equal to HEAD and EVIDENCE.md rendered; `render_evidence.py --check` exit 0.
9. Claims: the runner writes `.team-ship/PR-BODY.md` with a Results section carrying one backed sentence ("2 passed [E<k>]" where E<k> is the test-execution entry in EVIDENCE.json) and one deliberately unbacked sentence ("all tests pass, coverage is 95%" without a tag); `claim_evidence.py check .team-ship/PR-BODY.md` must exit 1 naming the uncited claims; the runner then removes the unbacked sentence and reruns to exit 0 with the resolved path entry.detail.parsed shown in gates/12.json (task 31); paste both.
10. Verdict: `fix_gate.py check`; expect exit 0 PASS and gates/fix.json, or paste the blocking lines. `gate_state.py verify-chain` exit 0 and `gate_state.py status` pasted.

## The deliberate skip

Before step 5, the runner constructs a PreToolUse payload for a Write of `.team-ship/EVIDENCE.md` (tool_input.file_path absolute under the pilot repository, cwd the repository, a made-up tool_use_id) and feeds it to team-artifact-guard.js; in observe mode the hook writes nothing to stdout and appends a certified receipt with decision would-deny and reason "evidence and gate files are written only by team-gate scripts". The runner then feeds the matching PostToolUse payload and confirms no gate-timeout receipt appears (the pair is certified). No file is written. The runner pastes both receipts from receipts.jsonl. This is the observe-mode half of PLAN.md section 8's skip; tasks 17 and 18 repeat it with hooks=enforce and paste the deny.

## What the verifier checks, from the run directory and the repository only

- Every gate file named above exists under `<TEAM_STATE_ROOT>/<run-id>/gates/` with head equal to the commit it measured and exit as claimed.
- `gate_state.py verify-chain` exits 0; `gate_state.py status` shows the stage cursor and no block receipt.
- The certified would-deny receipt for the skip exists and names the path.
- `.team-ship/EVIDENCE.json` head equals `git rev-parse HEAD`; `render_evidence.py --check` exits 0.
- `fix_gate.py check` rerun by the verifier reproduces the runner's verdict.
- The receipts show every artifact-written receipt for the artifacts present and no artifact without one.

## Run 2 (2026-09-18, after tasks 28, 30, 31, 32, 33)

Run 2 repeats every step on a fresh repository with the scripts at the current HEAD. Expected: every step PASS, fix_gate.py check exit 0 with verdict PASS, chain intact, the would-deny certified receipt present. Any FINDING is recorded, not patched.

## Findings the pilot is expected to surface, to be recorded rather than patched during the pilot

The matrix mapping from requirements to gates; the hooks' behaviour on the runner's own tool calls in this harness; the time each step takes. Each becomes a register row.
