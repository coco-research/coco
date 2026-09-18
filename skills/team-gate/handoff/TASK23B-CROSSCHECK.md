# TASK23B-CROSSCHECK

Verdict: disagreement on the same committed change. Cause is selection scope plus test naming, with a tool limitation on the default input. ripwire 0.6.1 `--test-gate` names test FILES that belong to a change set (or are partner-named after a changed file). `prove_red.py enumerate` names TEST FUNCTIONS added or modified between `--base` and HEAD. File-level overlap exists (`test_calc.py`). Function-level overlap does not: prove_red reported only `test_calc.py::test_clamp_high`; ripwire reported the whole file and did not name `test_clamp_high`.

## What was measured

A real git repository outside this worktree:

`/Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/repo`

Two commits.

1. `f3db5808d4bc163f2f8ad74a423cddc0be6d671c` initial: `clamp` with a low bound only, `add`, `test_clamp_low`, `test_add`.
2. `803759dad05d918c0ab429e03ab1873a2e7c66e3` HEAD: bug fix adding the high bound in `clamp`, plus new test `test_clamp_high`. `add` and `test_add` unchanged.

`git diff --name-status HEAD~1 HEAD`:

```
M	calc.py
M	test_calc.py
```

Working tree at measurement time: clean for tracked files. `gate_state.py start` then wrote `.team-ship/RUN` (untracked).

Binary: `/Users/rijulkalra/.local/bin/ripwire` version `ripwire 0.6.1 (Release, AppleClang 16.0.0.16000026, emit=std::print, built_from=30f14a274)`. `--test-gate` exists. Flag shape from `ripwire --help=--test-gate` (exit 0, stderr empty):

```
    --test-gate[=F1,F2]        before a PR: name the tests to run and the untested blast radius; exit 4 if either is non-empty
                               agent self-check before a PR (pair with --quality-delta): names the tests to run + the UNTESTED blast radius;
                               exit 4 if either obligation is non-empty (run the tests, then rely on green). (default = git diff)
      run= on a test row        --affected/--situ/--test-gate/--exercises/--pr-context/--pack-task name harness FILES, not commands. A row carries
                               run="<cmd>" when a runner is DERIVABLE from real evidence: a test-dir .sh/.py whose basename stem
                               matches the harness's, or whose TEXT names the harness file. Spelled RELATIVE to the root= the
                               document declares, so it pastes into a shell run from there, and the document does not change
                               with where the tree is checked out (a MULTI-ROOT run declares no single root, so it stays
                               absolute). NO run= means NOT DERIVABLE -- never a guessed suite command
```

## Commands and outputs

CWD for every command below:

`/Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/repo`

ripwire XML stdout is one HTML comment plus one `<test-gate>` element. The comments contain U+2014. Those comments are not copied here. The `<test-gate>` element and the `--json` object are copied byte for byte. stderr was empty for every ripwire invoke.

### 1. Default `--test-gate` (clean tree, default = git diff)

```
/Users/rijulkalra/.local/bin/ripwire /Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/repo --test-gate
```

exit 0

```
<test-gate changed="0" impacted="0" tests="0" untested="0" shown_tests="0" tests_capped="0" shown_untested="0" untested_capped="0" script_gates_unmodelled="0" script_gates_registered="0" script_gates_mapped="0" script_gates_unresolved_dynamic="0" ccx_bar="15" graph_ambiguous="0" graph_unresolved="0" counts_floor="1" at="803759dad" next="--situ"></test-gate>
```

### 2. Same change, files named (the comparable invoke)

```
/Users/rijulkalra/.local/bin/ripwire /Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/repo --test-gate=calc.py,test_calc.py
```

exit 4 (tests obligation non-empty)

```
<test-gate changed="2" impacted="0" tests="1" untested="0" shown_tests="1" tests_capped="0" shown_untested="0" untested_capped="0" script_gates_unmodelled="0" script_gates_registered="0" script_gates_mapped="0" script_gates_unresolved_dynamic="0" ccx_bar="15" graph_ambiguous="0" graph_unresolved="0" counts_floor="1" at="803759dad" root="/Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/repo" next="python3 test_calc.py"><t p="test_calc.py" changed="1" partner="1" run="python3 test_calc.py"/></test-gate>
```

### 3. Same files, `--json`

```
/Users/rijulkalra/.local/bin/ripwire /Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/repo --test-gate=calc.py,test_calc.py --json
```

exit 4

```
{"changed":2,"impacted":0,"tests":1,"untested":0,"shown_tests":1,"tests_capped":false,"shown_untested":0,"untested_capped":false,"script_gates_unmodelled":0,"script_gates_registered":0,"script_gates_mapped":0,"script_gates_unresolved_dynamic":0,"ccx_bar":15,"graph_ambiguous":0,"graph_unresolved":0,"counts_floor":true,"at":"803759dad","root":"/Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/repo","next":"python3 test_calc.py","tests_to_run":[{"p":"test_calc.py","changed":true,"partner":true,"run":"python3 test_calc.py"}],"untested_blast_radius":[]}
```

### 4. prove_red enumerate on the same two commits

Start:

```
TEAM_STATE_ROOT=/Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/state
/usr/local/bin/python3 /Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/gate-wt/skills/team-gate/scripts/gate_state.py start /Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/repo ship
```

exit 0, stdout `20260918-144703-266`

Enumerate (how prove_red selects tests: `changed_paths` then `do_enumerate` walks A/M/R `.py` files, `classify_path`, then `test_functions` for new or AST-changed `test_*` names):

```
TEAM_STATE_ROOT=/Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/state
/usr/local/bin/python3 /Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/gate-wt/skills/team-gate/scripts/prove_red.py enumerate --base f3db5808d4bc163f2f8ad74a423cddc0be6d671c --repo-root /Users/rijulkalra/.pi-desktop/scratch/c9fcf8c9-8e42-41ea-8296-89a875ebd619/task23b-crosscheck/repo
```

exit 0

stdout:

```
test_calc.py::test_clamp_high new test
```

stderr:

```
verdict=PASS tests=1 inseparable=0
```

Gate `gates/9-tests.json` tests array (one record): `nodeid=test_calc.py::test_clamp_high`, `status=new`, `kind=test`. `implementation_paths=["calc.py"]`. Unchanged functions `test_clamp_low` and `test_add` were not listed.

## Agreement and disagreement

Partial file-level agreement on invoke 2/3 vs prove_red: both involve `test_calc.py`.

Disagreement, classified:

1. Selection scope. ripwire lists the harness file because it is in the change set (`changed=1`) and is partner-named (`partner=1`, `test_<stem>`). prove_red lists only the function whose AST is new between base and HEAD. Unchanged tests in the same file are in ripwire's file and out of prove_red's list.
2. Test naming. ripwire: path `test_calc.py`. prove_red: nodeid `test_calc.py::test_clamp_high`. No shared identifier at function grain.
3. Tool limitation on default input. `--test-gate` with no files uses working-tree `git diff`. After the fix is committed, that diff is empty (`changed="0" tests="0"`, exit 0). prove_red diffs `--base`..HEAD, so it sees the commit. The comparable ripwire invoke is `--test-gate=calc.py,test_calc.py`, not the default.
4. Ordering. Not in play (one row each).
5. Exit contract. ripwire exit 4 means "obligation non-empty". prove_red enumerate exit 0 means "PASS: runnable tests found". Different meanings, not a selection disagreement.

## What remains unproven

- A dirty-tree default `--test-gate` (uncommitted `git diff`) vs prove_red on the same bytes. Not run; prove_red enumerates commits, not the index.
- A tests-only change, an impl-only change, a rename, and a multi-file blast radius with hops>0.
- Whether ripwire can name functions. This 0.6.1 run named a file only.
- coco itself, or the pilot `/team:fix` repository. This was a two-file synthetic repo.
- `prove_red.py prove` (red/green), only `enumerate`.
- Attribution into `gates/9.json` `attribution_hint`. Not written; this file is the observation.
