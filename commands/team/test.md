---
description: "Use when the user asks to add missing tests, close coverage gaps, or prove a suite runs. Runs the /team test pipeline: coverage analysis, test writing, then a regression gate that treats any skip as unverified. Tests only, no source."
---

# /team test: Test Pipeline

> Called by team.md router when action is `test`.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst | 2 |
| L2 | qa-test-architect + (domain engineers) | 3-4 |
| L3 | domain-accuracy | 1-2 |
| L4 | principal-architect | 1 |

## Stage 1: Brownfield Map

```
python3 ~/.claude/skills/team-gate/scripts/brownfield_map.py --for "<the coverage gap or test task in words>" --repo-root .
```
exit 0: continue; read `.team-ship/BROWNFIELD-MAP.md` before reading any code.
exit 1: not used; a map is not a pass or fail judgement.
exit 2: UNVERIFIED; quote the gate file's summary (gates/handoff-1-map.json).

No test-pipeline aggregator exists to require this gate file; the map is the first step by instruction.

## Pipeline Customization

### Layer 1: Coverage Analysis
L1 agents focus on the following areas.
- Current test coverage map (which modules have tests, which don't)
- Critical paths that lack coverage
- Existing test patterns and conventions
- Test infrastructure setup (frameworks, fixtures, mocks)

### Layer 2: Test Writing
- **Mode:** `bypassPermissions`
- File ownership: each agent owns `tests/test_{module}*` files
- DO NOT TOUCH: source code (tests only), other agents' test files
- Follow existing test patterns (fixtures, naming, assertions)

**Toolkit integration:**
- Check team:toolkit.md for "Test-Driven Development" entry
- qa-test-architect designs the test strategy; domain engineers write module-specific tests

1. Read the owned source module to understand behavior, then identify untested edge cases and error paths.
2. Run `run_gate.py discover` to find the repository's authoritative test commands, then `run_gate.py parity` to check the local tool versions against the versions CI pins.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py discover --repo-root .
python3 ~/.claude/skills/team-gate/scripts/run_gate.py parity --repo-root .
```
exit 0: continue and quote each gate file's summary (gates/7-discover.json, gates/7.json).
exit 1: BLOCK; parity names the tool whose version differs, quote it and align the tool before continuing.
exit 2: UNVERIFIED; the suite is not confirmed passing until the gate passes or an override receipt names the gate.

3. Run `run_gate.py run` for the baseline, before any new test is committed. Record this run's head now: step 4 commits and step 5 rewrites gates/8.json, so the head this step writes is captured here for step 6's `--base`, not read fresh from gates/8.json later.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py run --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/8.json).
exit 1: BLOCK; quote the reasons from the gate file and loop back to test writing.
exit 2: UNVERIFIED; the suite is not confirmed passing until the gate passes or an override receipt names the gate.

Provision what CI provisions. When something cannot be provisioned, record "override integration: <reason>" in your own words as the human, and run_gate's skip rule decides the rest.

4. Write the tests following existing patterns, then commit them alone: `test({module}): add missing tests for {description}`.
5. The commit in step 4 moved HEAD, and `run` refuses a discover file recorded at a different HEAD, so run `run_gate.py discover` again before `run_gate.py run`, so the new tests are checked at HEAD.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py discover --repo-root .
python3 ~/.claude/skills/team-gate/scripts/run_gate.py run --repo-root .
```
exit 0: continue and quote each gate file's summary (gates/7-discover.json, gates/8.json); gates/8.json is rewritten and the latest receipt wins.
exit 1: BLOCK; for the command that stopped, quote its gate file's summary and loop back to test writing.
exit 2: UNVERIFIED; for the command that stopped, quote its gate file's summary; the suite is not confirmed passing until the gate passes or an override receipt names the gate.

6. Run `prove_red.py prove --base <the head recorded in gates/8.json by the baseline run in step 3> --repo-root .`. prove_red runs each new test green at HEAD, reverts the implementation in a throwaway worktree, and proves it goes red for the right reason.

```
python3 ~/.claude/skills/team-gate/scripts/prove_red.py prove --base <the head recorded in gates/8.json by the baseline run in step 3> --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/9.json).
exit 1: BLOCK; a never-red or invalid-red classification, quote the reason from gates/9.json.
exit 2: UNVERIFIED; the suite is not confirmed passing until the gate passes or an override receipt names the gate.

On a tests-only change prove_red switches to its stub mode: it replaces the implementation modules the new test imports with stubs in the throwaway worktree and proves the test fails against them, recording the class valid-red-stub; a test that still passes, or imports no implementation module, is never-red with the reason "exercises no implementation module".

7. Run `prove_red.py recheck` to confirm the proved tests still hold.

```
python3 ~/.claude/skills/team-gate/scripts/prove_red.py recheck --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/9-recheck.json).
exit 1: BLOCK; quote the reasons from the gate file and loop back to test writing.
exit 2: UNVERIFIED; the suite is not confirmed passing until the gate passes or an override receipt names the gate.

### Layer 3: Test Quality Review

L3 agents verify the following properties.
- Tests actually test behavior (not implementation details)
- No test interdependence or shared mutable state
- Edge cases covered (null, empty, boundary, error paths)
- Test names describe the scenario being tested

Run `run_gate.py evidence`, which assembles EVIDENCE.json and renders EVIDENCE.md, so execution is confirmed rather than narrated.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py evidence --repo-root .
```
exit 0: continue and quote `.team-ship/EVIDENCE.md`; a pass claimed without this file's entries is a finding, not a pass.
exit 1: not used; evidence exits 0 or 2.
exit 2: UNVERIFIED; the suite is not confirmed passing until the gate passes or an override receipt names the gate.

### Full Regression

Run after all Layer 2 agents complete. Their combined commits moved HEAD past the last discover, so discover again before running the merged suite.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py discover --repo-root .
python3 ~/.claude/skills/team-gate/scripts/run_gate.py run --repo-root .
python3 ~/.claude/skills/team-gate/scripts/run_gate.py coverage --repo-root .
python3 ~/.claude/skills/team-gate/scripts/run_gate.py evidence --repo-root .
```
exit 0: continue and quote each gate file's summary (gates/7-discover.json, gates/8.json, gates/10.json) and `.team-ship/EVIDENCE.md`.
exit 1: BLOCK; for the command that stopped, quote its gate file's summary and loop back to test writing.
exit 2: UNVERIFIED; for `coverage`, no pytest-shaped command gives NOT_APPLICABLE, which still blocks unless an override receipt names gate "coverage"; for any other command that stopped, the suite is not confirmed passing until the gate passes or an override receipt names the gate.

Write `.team-ship/PR-BODY.md` with a Results section in which every sentence carries one [E<n>] tag naming an EVIDENCE.json entry, then check its claims against the evidence; a green claim without a backing entry is a finding, not a pass.

```
python3 ~/.claude/skills/team-gate/scripts/claim_evidence.py check .team-ship/PR-BODY.md --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/12.json).
exit 1: BLOCK; quote the findings from gates/12.json and reword or remove each unbacked claim.
exit 2: UNVERIFIED; the claims are not confirmed until the check passes or an override receipt names the gate.

## GSD Integration

When `.planning/` exists, L2 agents check test requirements from REQUIREMENTS.md. Test files follow GSD naming conventions.
