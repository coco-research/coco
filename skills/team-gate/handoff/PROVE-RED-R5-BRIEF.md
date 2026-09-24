# prove_red.py, round 5 builder brief

This brief replaces every earlier prove_red brief. Four rounds produced a ten-line stub whose `prove` subcommand prints "not fully implemented" and exits 2. This round is written at pseudo-code level so that nothing has to be researched. Where this brief and REVIEW-OPUS.md section A differ, this brief wins, because it encodes the brain's rulings recorded in PLAN.md section 4 under "Rulings for prove_red round 5".

## Where to work and what you own

Worktree, work only here, never commit:
`~/projects/coco/.claude/worktrees/team-gate-retrofit`

You own exactly these paths and nothing else:
- `skills/team-gate/scripts/prove_red.py` (rewrite from scratch; the current file is a stub)
- `skills/team-gate/scripts/fixtures/prove_red/make_fixtures.py` (rewrite; the current fixtures are wrong for the design below)
- `skills/team-gate/scripts/fixtures/prove_red/README.md` (new, one paragraph per fixture)

Do not touch `gate_state.py` or any other script. Read `gate_state.py` once for the API: `state_root()`, `find_run(cwd) -> Optional[Path]`, `start_run(repo_root: str, command: str, flags: list) -> str` (returns run_id, writes run.json and the `.team-ship/RUN` pointer), `append_receipt(run_dir, kind, detail) -> dict`. Receipt kinds you may use: `gate-result`, `worktree-registered`. Any other kind raises.

Rules that bind: Python standard library only; type hints on every function; no em dash and no section sign anywhere; `sys.exit` appears only in the `__main__` guard; every exit is 0, 1 or 2; gate files record `head` from `git rev-parse HEAD` of the measured repository; every gate file is followed by a `gate-result` receipt whose detail carries `gate`, `gate_file`, `gate_sha256`, `exit`, `summary`. Failing to find the run directory, the repository, or the base commit is exit 2 with one line on stderr.

Before you report, run this smoke check on your own file and include its output. Every count must be non-zero except the last, which must list exactly one line number, the one inside the `__main__` guard:

```
grep -c "import gate_state" prove_red.py
grep -c "rev-parse" prove_red.py
grep -c "append_receipt" prove_red.py
grep -c -- "--self-test" prove_red.py
grep -c "subprocess.run(\[sys.executable, __file__" prove_red.py
grep -n "sys.exit" prove_red.py
```

Environment facts you must design around: the machine has Python 3.14 and no pytest and no coverage. Tests are therefore run by an internal runner described below, never by pytest. Test functions that take parameters cannot be run and are reported UNRUNNABLE.

## CLI surface

```
prove_red.py enumerate [--base SHA] [--repo-root DIR]
prove_red.py prove     [--base SHA] [--repo-root DIR] [--allow-dirty] [--python PATH]
prove_red.py recheck   [--repo-root DIR]
prove_red.py _run-one  SYS_PATH_ROOT TEST_FILE QUALNAME      (internal, used by prove)
prove_red.py --self-test
```

`--repo-root` defaults to `.`. `--python` defaults to `sys.executable` and is recorded in the gate file under `env_pins.python`.

## Shared helpers

`gr(repo_root, *args)`: read-only git against the repository root. Allowed first arguments: `rev-parse`, `merge-base`, `diff`, `ls-files`, `status`, `cat-file`, `show`, `symbolic-ref`, `worktree`. Any other verb raises `ValueError` before subprocess is called. This is the guard that makes "never mutate the user's worktree" true by construction; `worktree` is allowed because `git worktree add`, `remove`, `prune` and `list` operate on git metadata and the throwaway directory, never on the user's files.

`gw(worktree, *args)`: git against the throwaway worktree. Asserts `os.path.realpath(worktree) != os.path.realpath(repo_root)` before every call.

`resolve_base(repo_root, explicit) -> tuple[str, str]` returns `(sha, source)`:
1. `explicit` given: `gr rev-parse --verify <explicit>^{commit}`; failure is exit 2 "base <explicit> does not resolve".
2. `.team-ship/ARCH-PLAN.json` exists and has `declaredAtCommit`: use it, source `arch-plan`.
3. `gr symbolic-ref -q refs/remotes/origin/HEAD` succeeds: `gr merge-base HEAD <that ref>`, source `merge-base`.
4. No remote at all (`gr ls-files` is fine, and `git remote` is not in the allowlist, so test for remotes via `gr rev-parse --verify -q refs/remotes/origin/HEAD` failing AND the absence of any `refs/remotes/` entry from `gr show-ref`; simpler: if step 3 fails and `gr rev-parse --verify -q HEAD~1` succeeds, use `HEAD~1`, source `head-minus-one`).
5. Otherwise exit 2 "base unresolvable".

`changed_paths(repo_root, base) -> list[tuple[str, str, Optional[str]]]`: `gr diff --name-status -M <base> HEAD`, parsed into `(status, path, old_path)` where status is one of `A`, `M`, `D`, `R`. Renames report `R` with `old_path`.

`classify_path(path) -> str` returns `test`, `support`, or `implementation`:
- `support` when the basename is `conftest.py`, or any path segment is `fixtures`, or the suffix is not `.py`.
- `test` when the path matches any of: starts with `tests/` or `test/`, or basename matches `test_*.py` or `*_test.py`.
- `implementation` otherwise.

`test_functions(source: str) -> dict[str, ast.AST]`: parse with `ast.parse`; collect top-level `FunctionDef` and `AsyncFunctionDef` whose name starts with `test_` under key `<name>`, and methods named `test_*` on top-level classes whose name starts with `Test` under key `<Class>.<method>`. Return the mapping from qualname to node. A `SyntaxError` propagates to the caller.

`ast_hash(node) -> str`: remove a leading docstring (`node.body[0]` when it is an `Expr` whose value is a string `Constant`), then `hashlib.sha256(ast.dump(node, annotate_fields=True, include_attributes=False).encode()).hexdigest()`. Comments and whitespace never affect it; a changed literal always does.

`write_gate(run_dir, name, obj) -> Path`: `json.dump` with `indent=2, sort_keys=True` to `run_dir/gates/<name>`, then `append_receipt(run_dir, "gate-result", {"gate": obj["gate"], "gate_file": "gates/<name>", "gate_sha256": <sha256 of the bytes on disk>, "exit": obj["exit"], "summary": obj["summary"]})`. Create `gates/` if absent.

Every gate object carries at least: `gate`, `argv`, `cwd`, `head`, `base` `{sha, source}`, `env_pins` `{python}`, `exit`, `summary`, `tests`.

## enumerate

1. `run_dir = gate_state.find_run(repo_root)`; None is exit 2 "run directory not found".
2. `head = gr rev-parse HEAD`. Resolve base.
3. For each changed path with status `A`, `M` or `R` and suffix `.py`:
   - `head_src = gr show HEAD:<path>`; parse; a `SyntaxError` at HEAD is exit 1 with the entry recorded as `syntax-error-at-head` (a file that does not parse at HEAD cannot be green).
   - `base_src = gr show <base>:<old_path or path>` when status is `M` or `R`; on `A` there is no base.
   - `base_funcs = test_functions(base_src)` when base_src parses; when base does not parse, treat every test in the file as `modified`.
   - For each `(qualname, node)` in `test_functions(head_src)`: `status = "new"` when absent at base; `"modified"` when `ast_hash` differs from the base node; unchanged tests are skipped.
   - `kind = classify_path(path)`. A test in an `implementation` path is `inseparable`; a test in a `support` path is skipped and listed under `support_tests`.
   - Record `{nodeid: f"{path}::{qualname}", file, qualname, status, kind, ast_hash, params: <number of positional parameters excluding self>}`.
4. Write `gates/9-tests.json` with `gate: "tdd-enumerate"`, `tests`, `implementation_paths`, `support_paths`, `exit`, `summary`. Exit 0 when at least one runnable test was found; exit 2 with `summary: "NOT_APPLICABLE: no new or modified tests"` when the set is empty; exit 2 when every test is inseparable.
5. Print one line per test to stdout: `<nodeid> <status> <kind>`. Print `verdict=... tests=N inseparable=N` as the last stderr line.

## _run-one

Arguments: `SYS_PATH_ROOT` (the worktree), `TEST_FILE` (absolute path), `QUALNAME`. Prints exactly one JSON object to stdout and exits 0 whenever it managed to print; the caller treats a missing or unparseable JSON as UNRUNNABLE.

```
sys.path.insert(0, SYS_PATH_ROOT); sys.path.insert(1, dirname(TEST_FILE)); os.chdir(SYS_PATH_ROOT)
modname = relative path of TEST_FILE from SYS_PATH_ROOT with / replaced by . and .py removed
phase = "import"
try:
    spec = importlib.util.spec_from_file_location(modname, TEST_FILE); mod = module_from_spec(spec); sys.modules[modname] = mod; spec.loader.exec_module(mod)
    phase = "lookup"
    resolve QUALNAME: "Class.method" instantiates Class() then binds method; plain name is getattr(mod, name)
    phase = "call"
    result = func()  (if inspect.iscoroutinefunction(func): asyncio.run(func()))
    emit {"outcome": "pass", "phase": "call"}
except BaseException as exc:
    frames = [{"file": f.filename, "line": f.lineno, "func": f.name} for f in traceback.extract_tb(exc.__traceback__)] with frames whose file equals this script removed
    emit {"outcome": "fail" if isinstance(exc, AssertionError) else "error", "phase": phase,
          "exc_type": type(exc).__name__, "exc_module": type(exc).__module__,
          "message": str(exc)[:2000], "missing_name": getattr(exc, "name", None), "frames": frames}
```

A function whose signature has required parameters is not called; emit `{"outcome": "unrunnable", "phase": "lookup", "message": "test requires N parameters; fixture-aware runner not available"}`.

## prove

1. Find run_dir (exit 2 if absent), head, base. Refuse a dirty tree: `gr status --porcelain --untracked-files=no` non-empty and `--allow-dirty` absent is exit 2 "working tree is dirty; commit first or pass --allow-dirty". With `--allow-dirty`, capture `gr diff HEAD --binary` to apply into the worktree after creation, and record `dirty: true` in the gate.
2. Enumerate in-process using the same functions as `enumerate` (do not shell out to yourself for this). Empty set is exit 2 NOT_APPLICABLE; all inseparable is exit 2; both still write `gates/9.json`.
3. Reaper: for every directory under `run_dir/worktrees/` named `red-*` whose mtime is older than two hours, `gr worktree remove --force <dir>`, ignore failure, then `shutil.rmtree(dir, ignore_errors=True)`. Then `gr worktree prune`.
4. Create the worktree: `wt = run_dir / "worktrees" / f"red-{head[:8]}-{os.getpid()}"`; `gr worktree add --detach <wt> HEAD`; failure is exit 2. Append receipt `worktree-registered` with detail `{"path": str(wt), "head": head, "type": "red-proof"}`. Register `teardown()` with `atexit` and as the handler for `SIGINT` and `SIGTERM`, and call it in a `finally`. `teardown()` is idempotent: `gr worktree remove --force <wt>` then `shutil.rmtree(wt, ignore_errors=True)` then `gr worktree prune`. If `--allow-dirty`, `gw apply --binary <patchfile>` now.
5. GREEN phase, in the worktree at HEAD, for every runnable test: `subprocess.run([python, __file__, "_run-one", str(wt), str(wt / file), qualname], capture_output=True, text=True, timeout=120)`; parse stdout as JSON. `outcome == "pass"` is green; anything else records `green: {outcome, exc_type, message}` and marks the test `green-fails`, which is exit 1 at the end. `outcome == "unrunnable"` marks the test `unrunnable`, which is exit 2 at the end.
6. Revert implementation paths inside the worktree only:
   - status `A`: `os.remove(wt / path)`; also remove now-empty parent directories up to the worktree root so a package that did not exist at base disappears.
   - status `M`: `gw checkout <base> -- <path>`.
   - status `R`: remove the new path and `gw checkout <base> -- <old_path>`.
   - status `D`: `gw checkout <base> -- <path>` (restore what the change deleted).
   - Test and support paths are left at HEAD.
   Record `gw status --porcelain` as `revert.diffstat`.
7. RED phase, same command per runnable test. Classify from the JSON, with `added_impl = {path for (status, path, _) in changed if status == "A" and classify_path(path) == "implementation"}` and `modified_impl` likewise for `M` and `R`:
   - `outcome == "pass"`: `never-red`.
   - `outcome == "fail"` (AssertionError): take the last frame; map its file to a path relative to the worktree; if `classify_path(rel) in ("test", "support")` then `valid-red-assertion`, else `invalid-red` with reason "assertion raised inside implementation path <rel>".
   - `exc_type == "ModuleNotFoundError"`: `mod = missing_name`; candidates are `mod.replace(".", "/") + ".py"` and `mod.replace(".", "/") + "/__init__.py"`; if any candidate is in `added_impl`, `valid-red-missing-name` with `resolvedTo` set to that path; else `invalid-red` "missing module <mod> is not added by this change".
   - `exc_type == "ImportError"` with message matching `cannot import name '(?P<name>\w+)' from '(?P<mod>[\w.]+)'`: resolve `mod` to a path as above; the path must be in `added_impl` or `modified_impl`, and `gr diff -U0 <base> HEAD -- <path>` must contain an added line matching `^\+\s*(async\s+def|def|class)\s+<name>\b` or `^\+\s*<name>\s*=`; then `valid-red-missing-name` with `resolvedTo` `<path>::<name>`; otherwise `invalid-red`.
   - `exc_type == "AttributeError"` with message matching `module '(?P<mod>[\w.]+)' has no attribute '(?P<name>\w+)'`: same resolution as ImportError. Any other AttributeError is `invalid-red`.
   - Everything else, including `SyntaxError`, `IndentationError`, `TypeError`, `NameError`, `FileNotFoundError`, and any error during `phase == "import"` that did not resolve above: `invalid-red` with `exc_type` and the first 200 characters of the message.
8. Per-test verdict: `PASS` for valid-red with green pass; `BLOCK` for never-red, invalid-red, green-fails; `UNVERIFIED` for inseparable; `UNRUNNABLE` for unrunnable. Record per test: `nodeid, file, qualname, status, kind, ast_hash, green {outcome, exc_type, message}, red {class, exc_type, message, last_frame, resolvedTo}, verdict`.
9. Overall exit: 2 when any test is unrunnable, or all are inseparable, or the set is empty; else 1 when any test verdict is BLOCK; else 0. Write `gates/9.json` with `gate: "tdd-redgreen"`, `worktree: str(wt)`, `revert`, `dirty`, `tests`, `counts {tests, pass, block, unverified, unrunnable, never_red, invalid_red, green_fails, inseparable}`, `exit`, `summary`. Violations print one per line on stdout in the form `<nodeid>: <class>: <reason>`. Last stderr line: `verdict=<PASS|BLOCK|UNVERIFIED|NOT_APPLICABLE|UNRUNNABLE> tests=N red_ok=N never_red=N invalid_red=N green_fails=N inseparable=N unrunnable=N`. Teardown runs in `finally` before returning.

## recheck

1. Find run_dir; `gates/9.json` absent is exit 2. Read it; `head_now = gr rev-parse HEAD`.
2. For every test whose verdict was PASS: `src = gr show HEAD:<file>`; parse; find the qualname; recompute `ast_hash`. Missing function is a finding `test removed: <nodeid>`; a differing hash is `hash changed: <nodeid> recorded <old[:12]> now <new[:12]>`. A file that no longer parses is `syntax error at HEAD: <file>`.
3. Write `gates/9-recheck.json` with `gate: "tdd-recheck"`, `proved_at_head`, `head`, `findings`, `exit`, `summary`. Exit 1 when findings is non-empty, else 0. Print findings on stdout; last stderr line `verdict=<PASS|BLOCK> rechecked=N changed=N removed=N`.

## Fixtures, all generated by make_fixtures.py

Generator rules: anchor every output on `Path(__file__).resolve().parent`; accept `--out DIR` to redirect the root; read `TEAM_FIXED_TS` (default `2026-01-01T00:00:00Z`) and set `GIT_AUTHOR_DATE`, `GIT_COMMITTER_DATE` to it and `GIT_AUTHOR_NAME=fixture`, `GIT_AUTHOR_EMAIL=fixture@example.invalid`, same for committer, in the env of every git call, so SHAs are identical between generations; `git init -q --initial-branch=main`; `git -c commit.gpgsign=false commit -q`. Each fixture lives at `<name>/_build/repo` with `<name>/_build/BASE_SHA` holding the base commit. Remove an existing `_build` before regenerating.

Every fixture's test file content is stated here; use it verbatim.

1. `proper-red-green`, expect prove 0, stderr contains `red_ok=1`. Base: `src/__init__.py` empty; `src/calc.py` = `def add(a, b):\n    return a - b\n` (the bug). HEAD: `src/calc.py` = `def add(a, b):\n    return a + b\n`; `tests/test_calc.py` = `from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n`. Red is an AssertionError raised in the test body.
2. `new-module-import-red`, expect 0. Base: `tests/test_calc.py` = `# placeholder\n`. HEAD adds `src/__init__.py` empty, `src/calc.py` = `def add(a, b):\n    return a + b\n`, and `tests/test_calc.py` = `def test_add():\n    from src.calc import add\n    assert add(2, 3) == 5\n`. Red is ModuleNotFoundError for `src`, which resolves to the added `src/__init__.py`.
3. `new-symbol-in-existing-module`, expect 0. Base: `src/__init__.py`; `src/math.py` = `def subtract(a, b):\n    return a - b\n`. HEAD: `src/math.py` gains `\n\ndef add(a, b):\n    return a + b\n`; `tests/test_math.py` = `def test_add():\n    from src.math import add\n    assert add(2, 3) == 5\n`. Red is ImportError "cannot import name 'add'", resolved to an added `def add` line in a modified path.
4. `assertion-in-helper`, expect 0. Same as fixture 1 except the test file is `from src.calc import add\n\n\ndef check(actual, expected):\n    assert actual == expected\n\n\ndef test_add():\n    check(add(2, 3), 5)\n`. Red is an AssertionError raised in a helper inside the test path, which the ruling accepts.
5. `never-red`, expect 1, stderr contains `never_red=1`. Base: `src/__init__.py`; `src/calc.py` = `def add(a, b):\n    return a + b\n`; `tests/test_calc.py` = `from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n`. HEAD appends `\n\ndef test_add_negatives():\n    assert add(-2, 3) == 1\n` to the test file and changes nothing else. The new test passes with the implementation reverted because the implementation never changed.
6. `wrong-reason-syntax-error`, expect 1, stderr contains `invalid_red=1`. Base: `src/__init__.py`; `src/calc.py` = `def add(a, b)\n    return a + b\n` (missing colon). HEAD fixes the colon and adds `tests/test_calc.py` = `from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n`. Red is a SyntaxError raised while importing the reverted implementation.
7. `weakened-after-red`, expect prove 0 and then, after the self-test commits the weakened test, recheck 1 with stdout containing `hash changed`. Base and HEAD as fixture 1. The generator also writes `_build/weakened_test_calc.py` = `from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) in (5, 6)\n`. The self-test copies it over `tests/test_calc.py`, runs `git add` and `git commit -q -m "weaken assertion"` in the fixture repository with the same fixed env, then runs `recheck`.
8. `inseparable-same-file`, expect 2, stderr contains `inseparable=1`. Base: `app.py` = `# empty\n`. HEAD: `app.py` = `def add(a, b):\n    return a + b\n\n\ndef test_add():\n    assert add(2, 3) == 5\n`.
9. `mixed-valid-and-inseparable`, expect 0, stderr contains `red_ok=1` and `inseparable=1`. Fixture 1 plus fixture 8's `app.py` change in the same HEAD commit.
10. `not-applicable-no-new-tests`, expect 2, stderr contains `NOT_APPLICABLE`. Base as fixture 1. HEAD changes only `src/calc.py`.
11. `dirty-tree`, expect 2, stderr contains `dirty`. Fixture 1 fully committed, then the generator appends `# dirty\n` to `src/calc.py` without committing.
12. `unrunnable-parametrised`, expect 2, stderr contains `unrunnable=1`. Fixture 1 with the test written as `def test_add(value):\n    assert add(value, 3) == value + 3\n`.

## --self-test protocol

1. Remove `fixtures/prove_red/*/_build` and run `make_fixtures.py` as a subprocess with `TEAM_FIXED_TS` set; a non-zero return is exit 2. Regeneration on every run is deliberate because fixture 7 mutates its repository.
2. For each fixture in the order above: `tempfile.TemporaryDirectory()` as `TEAM_STATE_ROOT` in the child env; `gate_state.start_run(str(repo), "fix", [])` with the same env set in this process so `state_root()` agrees; `base = BASE_SHA`; run `subprocess.run([sys.executable, __file__, "prove", "--base", base, "--repo-root", str(repo)], capture_output=True, text=True, timeout=300, env=env)`. Assert `returncode`, assert the stderr substring, then assert `git -C repo worktree list --porcelain` reports exactly one worktree (no leak), then assert `run_dir/gates/9.json` exists and `python3 gate_state.py verify-chain` run as a subprocess with `cwd=repo` exits 0. For fixture 7 follow with the weaken commit and `recheck`, asserting 1 and `hash changed` in stdout. For the NOT_APPLICABLE, dirty and unrunnable fixtures skip the gates/9.json assertion only where the brief above says no gate is written (the dirty case exits before any gate is written; NOT_APPLICABLE and unrunnable still write gates/9.json).
3. Print one line per assertion group: `<fixture>: expected <n> got <n> stderr contains '<s>' worktrees=1 chain=0 OK` or the same line ending in `FAIL` with the mismatch named. Exit 0 only when every line is OK. Never assert on a direct function call; the CLI subprocess is the unit under test.

## Report, return only this

1. `git status --porcelain` before you start and after you finish.
2. The smoke-check output from the top of this brief.
3. `python3 -m py_compile skills/team-gate/scripts/prove_red.py skills/team-gate/scripts/fixtures/prove_red/make_fixtures.py; echo exit=$?`
4. Full `--self-test` output, verbatim, including the exit code.
5. The weakened-after-red CLI reproduction: the `prove` command and its last stderr line, the weaken commit, the `recheck` command, its stdout and exit code.
6. `git -C skills/team-gate/scripts/fixtures/prove_red/proper-red-green/_build/repo worktree list` after the self-test, proving no leak.
7. `find skills/team-gate/scripts/fixtures/prove_red -name .git -not -path "*/_build/*"` (must print nothing) and `git check-ignore -v skills/team-gate/scripts/fixtures/prove_red/proper-red-green/_build`.
8. The line "Committed: NO".

If a self-test line is FAIL, report it as FAIL. Do not weaken an assertion, do not mark a fixture as skipped, and do not describe intended behaviour as observed behaviour. Quote only output you actually saw.
