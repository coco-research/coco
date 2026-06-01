# Test Evidence Protocol

> **Purpose:** One canonical definition of what "tests pass," "lint clean," and
> "coverage N%" mean inside the `/team` pipeline. Referenced by `team:ship.md`,
> `team:test.md`, `team:develop.md`, and `team:verify.md`. Whenever any of those
> pipelines makes a quality claim, it must follow this protocol and produce the
> `EVIDENCE.md` artifact described below.
>
> **Guiding principle — Evidence or it didn't happen.** Every quality claim must
> be backed by a captured command invocation and its raw output. Any claim
> without matching evidence is deleted from the deliverable or blocks the
> pull request.

This protocol exists because a pipeline that runs a weaker-than-CI gate locally,
folds skipped tests into "passed," narrates coverage instead of measuring it, and
trusts the builder's self-report will report green results that CI or a human
reviewer later contradicts. The steps below remove each of those failure modes.

---

## The protocol

### 1. Determine the authoritative gate

Do not invent a local equivalent. Read the project's real configuration to find
the exact commands and tool versions CI runs:

- `.github/workflows/*.yml` — the CI jobs and the commands they execute
- `Makefile` — targets such as `make check` (often the authoritative gate)
- `lefthook.yml`, `.pre-commit-config.yaml`, `.husky/`, any pre-push hook
- The pinned tool versions (for example `ruff==0.15.12`, `mypy`, `pytest`). If a
  version is floating (`ruff>=0.7`), resolve the version CI actually installs and
  use that exact version locally (for example `uvx ruff@<ci-version>`).

Use those commands and versions verbatim. A local gate that uses a different tool
version than CI is not evidence of anything.

### 2. Provision integration dependencies

If tests are gated on an environment variable (for example
`MARVIN_PG_TEST_DSN`, `MARVIN_TEST_POSTGRES_URL`, a database URL, or a service
host), the gate is meaningless until that dependency is actually running:

- Start the required service (for example a Docker Postgres or pgvector
  container), export the variable, and **confirm the previously-skipped tests now
  collect and run** (the skip count must drop).
- If provisioning is genuinely impossible in this environment, the affected tests
  are reported `UNVERIFIED`. Any claim that relies on them is forbidden, and
  integration coverage must be labeled "unit-only." Never silently let the gated
  tests skip and call the result a pass.

### 3. Run and capture

Execute each gate command and capture, for each:

- the full command line (including the version and any env vars set),
- the exit code,
- the raw output tail (last ~20 lines), and
- the parsed test summary line (for pytest: `N passed, M skipped, K failed, ...`).

The orchestrator runs these commands and captures the output itself. A subagent's
prose summary ("all tests pass") is not a substitute for captured output.

### 4. Apply the pass rules

These rules are absolute — they are the definition of "pass":

- `failed > 0` → **BLOCK.** The pipeline stops and loops back to Build for a fix.
- `skipped > 0` → **UNVERIFIED** for the skipped surface. A skip is never a pass.
  Resolve it by provisioning the dependency (step 2) or by explicitly labeling the
  gap as an uncovered surface. Do not report the run as green while tests skip.
- `passed` is only meaningful for tests that actually executed. A suite of
  `passed` results where most tests skipped is `UNVERIFIED`, not green.
- A lint/type/format gate is "clean" only at the CI-pinned tool version with a
  captured exit code of 0.

### 5. Write `EVIDENCE.md`

Write the artifact to the workspace (for example `.team-ship/EVIDENCE.md`). This
file is the single source of truth for every claim that reaches the deliverable
or the PR body. Use the template below.

---

## `EVIDENCE.md` template

```markdown
# Ship Evidence — <branch> — <ISO timestamp>

## Toolchain parity
- CI ruff: <ver>  | local ruff used: <ver>  [match? ✅/❌]
- CI mypy: <ver>  | local mypy used: <ver>  [match? ✅/❌]
- Integration deps provisioned: Postgres <ver> @ DSN set ✅  (or: NOT PROVISIONED ❌)

## Gate: lint (`uvx ruff@<ci-ver> check . && uvx ruff@<ci-ver> format --check .`)
exit: 0
<captured output tail>

## Gate: tests (`MARVIN_PG_TEST_DSN=... uv run pytest -q`)
exit: 0
summary: 312 passed, 0 skipped, 0 failed
<captured output tail, including the summary line>

## Gate: coverage (`... pytest --cov=<pkgs> --cov-branch`)
measured: 94% branch  (CI-reproducible: yes | unit-only: no)
<captured cov table>

## Gate: TDD red-green (per new test)
- test_x::test_y — RED at <impl-reverted sha> (AssertionError: expected ...), GREEN at HEAD ✅

## Independent re-exec (clean checkout, separate agent)
- re-ran gate at <sha> in /tmp/clean-clone — summary matches claims ✅
```

---

## PR-body claim rule

Every quantitative claim in a deliverable or PR body (`N tests pass`,
`X% coverage`, `ruff/mypy clean`, "idempotent", "tested", "comprehensive") must
correspond to an entry in `EVIDENCE.md`. If it does not, **delete the claim.**

Do not render "MERGED" or CI-green implications for a branch that is not reachable
from `main`. A merge into a throwaway intermediate stack branch is not a merge to
`main` and must not be described as one.

---

## Hard gate semantics (shared by all pipelines)

- **BLOCK is real.** A failed gate stops the pipeline and loops back to Build for a
  fix (bounded to a maximum of 3 rounds). It is never advisory.
- **Skipped ≠ passed.** Enforced everywhere a result is interpreted.
- **Evidence or it didn't happen.** No matching `EVIDENCE.md` entry → the claim is
  deleted.
- **Independent re-execution.** Verification agents re-run the gate themselves from
  a clean checkout and must not read the builder's summary before doing so.
