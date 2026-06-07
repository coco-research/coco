# Plan: Make `/team:ship` Stop Reporting False Test/Quality Results

**Date:** 2026-05-30
**Author:** Forensic analysis + remediation design (handoff to the agent fixing the `/team` slash command)
**Status:** Proposal for review and implementation
**Scope:** The `/team:ship` pipeline and the sub-pipelines it calls (`/team:develop`, `/team:test`, `/team:verify`). Skill/command files live in `~/.claude/commands/team:*.md`.

---

## 1. Objective

`/team:ship` produced pull requests that **claimed** comprehensive tests were written and passing, with high branch coverage and a clean lint/type gate — when in reality the tests were skipped, could never pass, encoded the bug as the expected value, or were checked with a weaker local toolchain than CI. Reviewers (Leobardo Mora, Souman Trivedi, and the Copilot reviewer) had to find and fix these problems after the fact.

The objective of this plan is to **add hard, evidence-based verification stages to `/team:ship`** so that the pipeline can never again report a green result that CI or a human reviewer then contradicts. The guiding principle:

> **Evidence or it didn't happen.** Every quality claim in a PR must be backed by a captured command invocation and its raw output. Any claim without matching evidence is deleted or blocks the PR.

This plan is written so that another agent can implement it directly. It contains the diagnosis (with proof), the new pipeline design, the exact file edits, and acceptance criteria for the fix itself.

---

## 2. Background — What Went Wrong (Evidence)

A 10-agent forensic review compared the only memory-layer PR that reached `main` (PR-1, GitHub #473) against the corrected version that reviewers produced. Findings, each proven by commit diff:

| # | Defect | Proof (commit) | What `/team:ship` claimed |
|---|--------|----------------|----------------------------|
| 1 | **Test that can never pass.** A GIN-index assertion compared an upper-case needle (`"USING gin"`) against a lower-cased haystack (`indexdef.lower()`) — always `False`, so the assert always raised. | `b2cec56` | "GIN index tested" |
| 2 | **Untested DB path.** `insert_edges_chunked` (the real edge-write path) had zero real-DB assertions; only the pure list-slicer and the SQL string were tested. Real coverage was backfilled after review. | `7158adf` | "chunker tested" |
| 3 | **Test encoded the bug as correct.** A full-dedup replay asserted `== 120` inserted rows (should be `0`), with the wrong reasoning written into a comment. The chunker returned input-row count instead of `cursor.rowcount`. | `e8b82f4`, `acd94e9` | "ON CONFLICT dedup proven" |
| 4 | **Non-atomic schema applier, untested failure path.** `apply_schema` ran each file on an autocommit connection, leaving a half-applied schema on mid-batch failure. No rollback test existed; the atomicity test file was created *by the fix*. | `91b93ac` | "idempotent, tested applier" |
| 5 | **Broken trigger.** `degree_count` was INSERT-only and counted expired/forgotten edges (structural degree, not live degree). Delete/forget/restore paths were never tested. | `0f2d7a8` | "tested triggers" |
| 6 | **Alarm-spam.** `pg_notify` fired on every insert above the threshold, not once on the crossing. The test only asserted the alarm fires, never that it stays silent afterward (happy-path only). | `9875405` | "comprehensive tests" |
| 7 | **Dishonest immutability narrative.** The append-only (AU-9) claim relied on `REVOKE ... FROM PUBLIC`, which is a no-op; the owning role could still `TRUNCATE`/`DISABLE TRIGGER`. The narrative was rewritten to be honest. | `33cab01` | "append-only enforced" |

### Systemic findings (apply to the whole stacked PR series, not just PR-1)

1. **Skipped tests counted as passes.** Roughly **56 pg-integration tests** are gated `@pytest.mark.skipif(not os.environ.get("MARVIN_PG_TEST_DSN"))` (and similar `MARVIN_TEST_POSTGRES_URL` gates). CI runs bare `uv run pytest` with **no Postgres service and the DSN never set**, so all of them **silently skip**. About **57% of the schema-test surface never runs in CI.** One test docstring even falsely claims "CI sets it to a sidecar container."
2. **Local toolchain ≠ CI toolchain.** The pipeline's local gate used ruff 0.7.4, which cannot even see `UP047`; CI uses ruff 0.15.12 and the `make check` re-run **failed** on it, plus flagged unformatted files — while the pipeline reported "ruff/format clean." `mypy` is not in CI at all, yet "mypy clean" was claimed.
3. **Coverage was asserted, not measured.** "99% / 100% branch coverage" was only obtainable locally (and only with a DB DSN). CI runs no `--cov`. The numbers are not reproducible from a clean checkout.
4. **`/team:verify` trusted the builder's self-report** instead of independently re-running anything.
5. **Stacked "MERGED" badges masqueraded as main merges.** Only PR-1 reached `main`; PR-2/5/7/9/1.2b "MERGED" into throwaway intermediate stack branches, implying CI-green/merged status they never had.

### Root cause (one sentence)

The pipeline **defines no test execution environment and no definition of "pass,"** so agents run a weaker-than-CI gate locally, skipped tests are folded into "passed," coverage is narrated rather than measured, and the verification stage reads the builder's summary instead of re-executing.

---

## 3. Current Pipeline (for reference)

`/team:ship` (`~/.claude/commands/team:ship.md`) runs 7 stages with one approval gate:

```
1 Research → 2 Think → 3 Plan → 4 Review Plan
        ═══ APPROVAL GATE ═══
5 Fix Plan → 6 Build → 7 Verify → Post-Ship
```

The sub-pipelines have the weak points:

- `team:test.md` Layer 2, step 4: *"Run tests to verify they pass"* — no skip accounting, no CI-equivalent environment, no captured evidence.
- `team:develop.md` "Regression Tests: Run after Layer 2" — no captured evidence.
- `team:verify.md` Layer 2: *"Run any available tests"* in **read-only** mode — trusts output, can fold skips into "MET."
- `team:ship.md` Stage 7 Verify and Post-Ship: advisory only; no hard gate before the PR is opened.

---

## 4. Fix Design — Expanded `/team:ship` with Hard Gate Stages

Insert seven new **hard gate** stages between Build and PR-open. Each gate emits evidence, each can **BLOCK** (which loops back to Build for a fix, bounded to 3 rounds), and **none can be satisfied by narration**.

```
1 Research → 2 Think → 3 Plan → 4 Review Plan
        ═══ APPROVAL GATE (unchanged) ═══
5 Fix Plan → 6 Build
─── NEW HARD GATES (each writes EVIDENCE.md; each can BLOCK → loop to Build, max 3 rounds) ───
7  ENV PARITY        Detect CI config; pin ruff/mypy to the versions CI uses; provision the
                     integration dependencies CI needs but never has (e.g. Postgres) and export
                     the DSN so DB-gated tests actually execute.
8  TEST EXECUTION     Run the repo's authoritative gate (e.g. `make check`) AND the full test
                     suite with the integration DSN set. Capture raw stdout/stderr + exit codes.
                     ANY skipped test → status UNVERIFIED (never "pass"). Any red → BLOCK.
9  TDD RED-GREEN      For each newly added test, prove it was RED before the implementation
                     existed (right failure reason), then GREEN after. A test that was never red
                     is rejected (this catches always-fail, always-pass, and bug-encoding tests).
10 COVERAGE           Run coverage for real (`--cov --cov-branch`) and capture the number. If a
                     dependency could not be provisioned, label coverage "unit-only" and forbid
                     any integration-coverage claim.
11 INDEPENDENT VERIFY Fresh agents, CLEAN checkout, re-run the gate themselves. They must NOT
                     read the builder's summary. Their captured output is compared to the claims;
                     any mismatch → BLOCK. (Kills self-report trust.)
12 CLAIM↔EVIDENCE     Every claim destined for the PR body is cross-checked against EVIDENCE.md.
                     Unbacked claims are stripped. Merge-honesty check: do not imply CI-green or
                     "merged" for a branch that is not reachable from `main`.
13 CI MIRROR          Run the actual CI workflow's gate locally (the same commands the CI
                     watchdog re-runs) so local == CI before push.
──────────────────────────────────────────────────────────────────────────────────────────
14 PR OPEN            Only if stages 7–13 are all GREEN with evidence. Otherwise: stop, report
                     BLOCK + prioritized gap list, do not open the PR.
```

### Gate semantics (the part that prevents recurrence)

- **BLOCK is real.** A failed gate stops the pipeline and loops back to Build for a fix; it does not proceed to PR. This is not advisory.
- **Skipped ≠ passed.** Hardcoded across stages 8 and 11. A skip forces `UNVERIFIED` and triggers provision-or-block, never "pass."
- **Evidence-or-it-didn't-happen.** Every claim needs a pasted command + output block in `EVIDENCE.md`. No matching evidence → the claim is deleted.
- **Independent re-execution.** Stage 11 agents never see the builder's summary; they run the gate from a clean clone. This removes the self-report trust that let PR-1 through.

### Priority (if scope must be cut)

- **Essential (catch the most, implement first):** Stage 8 (test execution + skip≠pass), Stage 11 (independent re-exec), Stage 12 (claim↔evidence).
- **Depth (implement next):** Stage 7 (env parity), Stage 9 (red-green), Stage 10 (coverage), Stage 13 (CI mirror).

### Which gate catches which past failure

| Past failure | Caught by |
|---|---|
| Always-fail GIN assertion (#1) | 9 (red-green), 11 |
| Untested DB path (#2) | 7 (provision), 8, 10 |
| Bug encoded as expected value (#3) | 9 (red-green), 11 |
| Non-atomic applier, untested failure (#4) | 8 (full suite w/ DSN), 9 |
| Broken trigger, untested paths (#5) | 7, 8 |
| Alarm-spam, happy-path-only test (#6) | 9, 11 |
| DB tests skip in CI (systemic 1) | 7, 8 (skip≠pass), 13 |
| ruff red while "clean" claimed (systemic 2) | 7 (CI versions), 8, 13 |
| Coverage asserted not measured (systemic 3) | 10, 12 |
| Verify trusted self-report (systemic 4) | 11 |
| Stacked "MERGED" masquerade (systemic 5) | 12 |

---

## 5. Shared "Test Evidence Protocol"

Add one canonical protocol block and reference it from `team:test.md`, `team:develop.md`, `team:verify.md`, and `team:ship.md`. Suggested home: a new section in `team:toolkit.md` titled **"Test Evidence Protocol"**, or a new file `~/.claude/commands/team:evidence.md`. The protocol:

1. **Determine the authoritative gate.** Read `.github/workflows/*.yml`, `Makefile`, `lefthook.yml`, and any pre-push hook to find the exact commands CI runs and the exact tool versions (e.g. `ruff@0.15.12`, `mypy`, `pytest`). Use those — never a self-chosen local equivalent.
2. **Provision integration dependencies.** If tests are gated on an env var (e.g. `MARVIN_PG_TEST_DSN`, `MARVIN_TEST_POSTGRES_URL`), start the required service (Docker Postgres/pgvector), export the variable, and confirm the previously-skipped tests now collect and run. If provisioning is impossible, the affected tests are reported `UNVERIFIED` and any claim relying on them is forbidden.
3. **Run and capture.** Execute each gate command, capturing the full command line, exit code, and raw output tail. Parse the pytest summary line (`N passed, M skipped, K failed, …`).
4. **Apply pass rules.**
   - `failed > 0` → **BLOCK**.
   - `skipped > 0` → **UNVERIFIED** for the skipped surface; never reported as pass. Resolve by provisioning (step 2) or by explicitly labeling the gap.
   - `passed` is only meaningful for tests that actually executed.
5. **Write `EVIDENCE.md`** to the workspace (e.g. `.team-ship/EVIDENCE.md`) containing, per gate, the command, exit code, and captured output block. This file is the single source of truth for every PR-body claim.

### `EVIDENCE.md` format (template)

```markdown
# Ship Evidence — <branch> — <ISO timestamp>

## Toolchain parity
- CI ruff: 0.15.12  | local ruff used: 0.15.12  ✅
- CI mypy: <ver>     | local mypy used: <ver>    ✅
- Integration deps provisioned: Postgres 16 @ DSN set ✅ (or: NOT PROVISIONED ❌)

## Gate: lint (`uvx ruff@0.15.12 check . && uvx ruff@0.15.12 format --check .`)
exit: 0
```
<captured output tail>
```

## Gate: tests (`MARVIN_PG_TEST_DSN=... uv run pytest -q`)
exit: 0
summary: 312 passed, 0 skipped, 0 failed
```
<captured output tail, including the summary line>
```

## Gate: coverage (`... pytest --cov=<pkgs> --cov-branch`)
measured: 94% branch (CI-reproducible: yes / unit-only: no)
```
<captured cov table>
```

## Gate: TDD red-green (per new test)
- test_x::test_y — RED at <impl-reverted sha> (AssertionError: expected…), GREEN at HEAD ✅

## Independent re-exec (clean checkout, separate agent)
- re-ran gate at <sha> in /tmp/clean-clone — summary matches claims ✅
```

### PR-body claim rule

Every quantitative claim in the PR body (`N tests pass`, `X% coverage`, `ruff/mypy clean`) must correspond to an entry in `EVIDENCE.md`. If it does not, **delete the claim**. Do not render "MERGED"/CI-green implications for a branch not reachable from `main`.

---

## 6. Exact File Edits

> These are the precise edits the implementing agent should make. Keep all documentation in full prose (no caveman compression — this is a project rule for doc artifacts).

### 6.1 `~/.claude/commands/team:ship.md`

- **Replace** the "Pipeline: 7 Stages" section so that Build (Stage 6) is followed by the seven hard gates (Stages 7–13) and PR-open (Stage 14) exactly as in Section 4 of this plan.
- **Add** a new subsection **"Hard Gate Semantics"** stating: BLOCK is real and loops back to Build (max 3 rounds); skipped ≠ passed; evidence-or-it-didn't-happen; Stage 11 independent re-execution must not read the builder's summary.
- **Modify** the existing "Post-Ship" section: a PR may only be opened after Stages 7–13 are GREEN with evidence; otherwise stop and report a BLOCK + gap list. Remove any wording that lets verify be advisory.
- **Add** to "Failure Handling": a gate BLOCK is a first-class stop reason; `--resume` picks up at the failed gate.
- **Add** a reference to the shared Test Evidence Protocol (Section 5).

### 6.2 `~/.claude/commands/team:test.md`

- **Replace** Layer 2 step 4 ("Run tests to verify they pass") with: "Run the authoritative gate per the Test Evidence Protocol; provision integration dependencies; treat any skip as UNVERIFIED; capture output to `EVIDENCE.md`."
- **Add** a Layer 2 requirement: each new test must follow TDD red-green (demonstrably red before implementation, green after); a never-red test is rejected.
- **Replace** "Full Regression" with: "Run the CI-equivalent gate with integration deps provisioned; report the parsed pytest summary (passed/skipped/failed) and the measured coverage; skips block a 'pass' claim."

### 6.3 `~/.claude/commands/team:develop.md`

- **Replace** "Regression Tests: Run after Layer 2" with the Test Evidence Protocol run + `EVIDENCE.md` capture; skips and reds are surfaced in `REVIEW-PACKAGE.md`, not hidden.

### 6.4 `~/.claude/commands/team:verify.md`

- **Change Layer 2 from read-only narration to mandatory independent re-execution:** verify agents run the authoritative gate themselves from a clean checkout, must not read the builder's summary, and paste raw captured output (exit codes, pytest summary, skip count, coverage %).
- **Strengthen Layer 3 (Evidence Audit):** explicitly check for (a) skipped-as-passed, (b) coverage claims with no captured measurement, (c) claims not reproducible in CI, (d) "merged" implications for branches not reachable from `main`. Any of these downgrades the verdict.
- **Layer 4 verdict** may only be Pass if every requirement's evidence is reproduced by the verify agents, not merely cited by the builder.

### 6.5 Shared protocol home

- Create the **Test Evidence Protocol** (Section 5) in `team:toolkit.md` (new entry) or a new `team:evidence.md`, and reference it from 6.1–6.4.

---

## 7. Acceptance Criteria for This Fix

The agent implementing this plan should verify the fix itself against these criteria (meta-verification):

1. **Skip is never a pass.** Construct a repo whose only "passing" tests are `skipif`-gated and unset the gate; the pipeline must report `UNVERIFIED`/BLOCK, not green.
2. **Toolchain parity enforced.** Introduce a lint error only the CI ruff version detects; the pipeline must catch it (i.e., it uses the CI version), not pass.
3. **Red-green enforced.** Add an always-true (`assert True`) or always-false test; Stage 9 must reject it for never having been red for the right reason.
4. **Independent verify catches a lie.** Have the builder claim "100 tests pass" while the suite actually skips; Stage 11's clean-checkout re-run must contradict and BLOCK.
5. **Claims are evidence-backed.** A PR body generated by the pipeline must contain only claims that map to `EVIDENCE.md` entries; remove the evidence and the claim must disappear.
6. **Merge honesty.** A stacked branch not reachable from `main` must not be described as merged/CI-green.

If all six hold, the pipeline can no longer reproduce the PR-1 class of failures.

---

## 8. Rollout Notes

- **Cost:** Seven added stages mean a slower, more token-intensive ship. Stages 8, 11, 12 are the essential core; 7, 9, 10, 13 add depth. If the implementing agent must phase delivery, ship the essential core first.
- **Dependency provisioning** (Stage 7) needs Docker (or an ephemeral Postgres) available in the environment where `/team:ship` runs. If unavailable, the pipeline must degrade honestly: label integration coverage "unit-only" and never claim CI-verified integration tests.
- **Backward compatibility:** The new gates are additive to the existing 1–6 stages and the approval gate; the front half of the pipeline is unchanged.
- **Related hygiene (optional, out of scope but recommended):** make CI provision a Postgres service and set the DSN, add `mypy` and `--cov` to CI, so that "CI-verifiable" becomes true rather than aspirational. The pipeline fix above protects correctness even if CI is not changed, but fixing CI closes the gap permanently.

---

## 9. Appendix — Source of the Diagnosis

- Only PR-1 (GitHub #473) reached `main`; it is the one case with a corrected version to diff against. Findings 1–7 in Section 2 are proven line-by-line from its review-fix commits: `b2cec56`, `7158adf`, `e8b82f4`, `acd94e9`, `91b93ac`, `0f2d7a8`, `9875405`, `33cab01`.
- The systemic findings (skip-gating, toolchain mismatch, unmeasured coverage, self-report trust, stacked-merge masquerade) were established across PR-2 through PR-1.2b by inspecting their test files, PR bodies, and the CI workflow configuration (`.github/workflows/`), which provisions no Postgres and sets no test DSN.
- The CI watchdog comments on PR #473 independently confirm the local gate was bypassed (`MARVIN_SKIP_KIND_VALIDATE=1`, `MARVIN_SKIP_SLACK_PROBE=1`) and that the authoritative `make check` re-run failed on `UP047` and unformatted files at the time "clean" was claimed.
