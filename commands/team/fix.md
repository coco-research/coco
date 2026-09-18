---
description: "Use when the user reports a bug, pastes a failing test or an error log, or asks to debug and fix an issue. Diagnoses root cause, writes a failing regression test first, fixes it, and captures the gate command, exit code and evidence."
---
# /team fix: Fix Pipeline

> Called by team.md router when action is `fix`.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst, security-analyst | 2 |
| L2 | (domain-dependent engineers) + qa-test-architect, performance-eng (if perf-related) | 2-4 |
| L3 | domain-accuracy | 2 |
| L4 | principal-architect | 1 |

## Stage 1: Brownfield Map

```
python3 ~/.claude/skills/team-gate/scripts/brownfield_map.py --for "<the bug in words>" --repo-root .
```
exit 0: continue; read `.team-ship/BROWNFIELD-MAP.md` before reading any code.
exit 1: not used; a map is not a pass or fail judgement.
exit 2: UNVERIFIED; quote the gate file's summary (gates/handoff-1-map.json).

fix_gate requires this gate file as its stage 0 row, so the fix pipeline cannot pass without the map; an override receipt naming gate "map" waives it on a throwaway repository.

## Issue Detection

L1 agents identify issues from the following sources.
- Conversation context (user described bugs, review findings, error logs)
- `.planning/` review documents (if GSD active)
- Test failure output

Group issues by file ownership: no two L2 agents touch the same files.

## Pipeline Customization

### Layer 1: Diagnosis
L1 agents focus on the following areas.
- Root cause analysis for each reported issue
- File mapping: which files need changes
- Impact assessment: what else might break
- **Component triage.** When `.arch/index.json` exists and is CURRENT, name the component
  each issue falls inside, from `.arch/INDEX.md`. This is a triage and communication aid: it
  groups related issues and tells a reviewer which boundary is under repair. It is not
  a constraint on which files the fix may touch: a legitimate fix routinely spans several
  components, and the index is at a coarser altitude than the change. Do not escalate a
  cross-component fix as a boundary violation.
- Write `.team-ship/PLAN.md` with a `requirements` list, one item per reported issue phrased
  as the behaviour the fix must satisfy, since `claim_evidence.py matrix` reads that list and
  fix_gate requires gates/11-matrix.json, so a fix run without it cannot pass. Give each item a
  `[tests: ...]` list naming the regression test in the form prove_red records
  (`tests/test_x.py::TestClass.test_method` for unittest, `tests/test_x.py::test_fn` for a
  plain function), so the matrix grades it through the test.

```
python3 ~/.claude/skills/team-gate/scripts/arch_gate.py --repo-root .
```
exit 0: continue and quote `.arch/ARCH-GATE.json`; a printed MAJOR line means a PRUNE verdict to reconcile later.
exit 1: BLOCK; a REMOVE verdict, quote the reason from `.arch/ARCH-GATE.json`.
exit 2: UNVERIFIED; the index is absent (no .arch/index.json, which the script reports as not found), the pin is behind HEAD, or drift is unreconciled.

If a fix genuinely deletes or relocates a component's primary paths, note it so
`/team arch drift` can reconcile the index afterwards.

### Layer 2: Execution
- **Mode:** `bypassPermissions`
- Each agent gets a specific issue set with file ownership
- Atomic commits per fix: `fix({scope}): {description}`

**Toolkit integration:**
- Check team:toolkit.md for "Systematic Debugging" entry
- Apply systematic-debugging methodology for complex bugs

1. Run `run_gate.py discover` to find the repository's authoritative test commands.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . discover
```
exit 0: continue and quote the gate file's summary (gates/7-discover.json).
exit 1: not used; discover exits 0 or 2.
exit 2: UNVERIFIED; the run cannot pass fix_gate until the gate passes or an override receipt names the gate.

2. Run `run_gate.py run` for the baseline.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . run
```
exit 0: continue and quote the gate file's summary (gates/8.json); record this file's head field now as the base for step 6, since the file is rewritten at step 5.
exit 1: BLOCK; quote the reasons from the gate file and loop back to the fix.
exit 2: UNVERIFIED; the run cannot pass fix_gate until the gate passes or an override receipt names the gate.

Provision what CI provisions. When something cannot be provisioned, record "override integration: <reason>" in your own words as the human, and run_gate's skip rule decides the rest.

3. Write the failing regression test that reproduces the bug and commit it alone, before any fix, with the atomic commit convention `test({scope}): {description}`.

4. Apply the fix and commit it with the atomic commit convention `fix({scope}): {description}`.

5. Run `run_gate.py discover` again, since run_gate.py run refuses a discover file recorded at a different HEAD, then run `run_gate.py run` so the fix is checked against the full suite.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . discover
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . run
```
exit 0: continue and quote the gate file's summary for each command; gates/8.json is rewritten and the latest receipt wins.
exit 1: BLOCK; for the command that stopped, quote its gate file's summary and loop back to the fix.
exit 2: UNVERIFIED; for the command that stopped, quote its gate file's summary; the run cannot pass fix_gate until the gate passes or an override receipt names the gate.

6. Run `prove_red.py prove --base <the head recorded at step 2> --repo-root .`. prove_red runs the new test green at HEAD, reverts the implementation in a throwaway worktree and proves it goes red for the right reason; the base is the baseline head, so every test added since is enumerated.

```
python3 ~/.claude/skills/team-gate/scripts/prove_red.py prove --base <the head recorded at step 2> --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/9.json).
exit 1: BLOCK; a never-red or invalid-red classification, quote the reason from gates/9.json.
exit 2: UNVERIFIED; the run cannot pass fix_gate until the gate passes or an override receipt names the gate.

7. Run `prove_red.py recheck` to confirm the proved test still holds.

```
python3 ~/.claude/skills/team-gate/scripts/prove_red.py recheck --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/9-recheck.json).
exit 1: BLOCK; quote the reasons from the gate file and loop back to the fix.
exit 2: UNVERIFIED; the run cannot pass fix_gate until the gate passes or an override receipt names the gate.

### Layer 3: Fix Verification

L3 verifies the fix by assembling evidence and checking claims against it.

1. Run `run_gate.py evidence`, which assembles EVIDENCE.json and renders EVIDENCE.md; its entry ids are what the PR body cites.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . evidence
```
exit 0: continue and quote `.team-ship/EVIDENCE.md`.
exit 1: not used; evidence exits 0 or 2.
exit 2: UNVERIFIED; the run cannot pass fix_gate until the gate passes or an override receipt names the gate.

2. Write `.team-ship/PR-BODY.md` whose Results section carries one [E<n>] tag per sentence from EVIDENCE.json.

3. Check the plan matrix, the PR body's claims, and the overall verdict.

```
python3 ~/.claude/skills/team-gate/scripts/claim_evidence.py matrix .team-ship/PLAN.md --repo-root .
python3 ~/.claude/skills/team-gate/scripts/claim_evidence.py check .team-ship/PR-BODY.md --repo-root .
python3 ~/.claude/skills/team-gate/scripts/fix_gate.py check --repo-root .
```
exit 0: continue and quote the gate file's summary for each command (gates/11-matrix.json, gates/12.json, gates/fix.json).
exit 1: BLOCK; for the command that stopped, quote its gate file's summary and loop back to the fix.
exit 2: UNVERIFIED; for the command that stopped, quote its gate file's summary; the run cannot pass fix_gate until the gate passes or an override receipt names the gate.

Root cause and the absence of new issues stay a review judgement, and per-path coverage attribution does not exist, so this gate confirms the fixed test still holds rather than a coverage percentage.

### Verdict

Run after all Layer 2 agents complete.

The three-round bound is fix_gate's own rounds row, which blocks a fourth build round unless an override receipt names gate "rounds".

## GSD Integration

When `.planning/` exists, L2 agents follow GSD commit conventions. Include fix context in STATE.md.
