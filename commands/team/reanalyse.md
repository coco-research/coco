---
description: "Use when the user runs /team reanalyse, or already-approved work must be re-checked against current code for regressions. Diffs since the last review, re-verifies requirements, and confirms test regressions with captured evidence."
---
# /team reanalyse: Re-Analysis Pipeline

> Called by team.md router when action is `reanalyse`.
> Re-reviews completed work against current codebase state for regressions.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst, security-analyst | 2 |
| L2 | (domain-dependent engineers) + qa-test-architect | 3-5 |
| L3 | domain-accuracy | 1-2 |
| L4 | principal-architect | 1 |

## Stage 1: Brownfield Map

```
python3 ~/.claude/skills/team-gate/scripts/brownfield_map.py --for "<the reanalysis question in words>" --repo-root .
```
exit 0: continue; read `.team-ship/BROWNFIELD-MAP.md` before reading any code.
exit 1: not used; a map is not a pass or fail judgement.
exit 2: UNVERIFIED; quote the gate file's summary (gates/handoff-1-map.json).

No reanalyse-pipeline aggregator exists to require this gate file; the map is the first step by instruction.

## Pipeline Customization

### Layer 1: Delta Analysis
L1 agents determine the following.
- What has changed since the original implementation or last review. When `.arch/index.json`
  exists, its pin is the baseline for "since".

```
python3 ~/.claude/skills/team-gate/scripts/arch_gate.py --repo-root .
```
exit 0: continue and quote `.arch/ARCH-GATE.json`; take its `pin` field as the baseline commit. A printed MAJOR line means a PRUNE verdict to reconcile later.
exit 1: BLOCK; a REMOVE verdict, quote the reason from `.arch/ARCH-GATE.json`, and carry it into Layer 2 as an ARCHITECTURAL REGRESSION.
exit 2: UNVERIFIED; the index is absent, the pin is behind HEAD, or drift is unreconciled. Report any ARCHITECTURAL REGRESSION finding in Layer 2 as SUSPECTED, not confirmed, until `/team arch drift` reconciles it.

  Diff the baseline against HEAD to see what changed: `git diff --name-status <pin>..HEAD`. No script emits this delta; run the plain git command yourself and quote its output.
- Which requirements need re-verification
- What new code interacts with previously reviewed modules

### Layer 2: Re-Verification
- **Mode:** `bypassPermissions` for any domain involving tests or runtime behavior (agents must be able to re-run the gate); `default` (read-only) for static/doc domains.
- Each agent re-checks their domain against current code
- Reports: STILL GOOD | REGRESSION | NEW ISSUE | IMPROVEMENT | ARCHITECTURAL REGRESSION
- **ARCHITECTURAL REGRESSION** is reserved for structural drift against `.arch/index.json`. A
  REMOVE verdict from Layer 1's `arch_gate.py` gate above is one; report it there, quoting the
  reason. Also report it when new code has landed in a top-level directory no component claims,
  judged by reading `.arch/index.json` directly, since no script flags that case. A component
  reworked inside its own already claimed directory is not an architectural regression by this
  definition; if that is what you found, report it as REGRESSION or NEW ISSUE instead.
- **A regression in test or runtime behavior must be confirmed by re-running the authoritative
  gate**, capturing the before/after summary in `EVIDENCE.md`. A regression claimed from
  code-reading alone, with no captured run, is reported as SUSPECTED, not confirmed.

1. Find the repository's authoritative test commands.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . discover
```
exit 0: continue and quote the gate file's summary (gates/7-discover.json).
exit 1: not used; discover exits 0 or 2.
exit 2: UNVERIFIED; no qualifying test command was found in CI configuration, so the regression check cannot run.

2. Run them at current HEAD as the after-side of the comparison.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . run
```
exit 0: continue and quote the gate file's summary (gates/8.json).
exit 1: REGRESSION confirmed; quote the reasons from the gate file.
exit 2: UNVERIFIED; report any suspected regression as SUSPECTED, not confirmed.

Provision what CI provisions. When something cannot be provisioned, record "override integration: <reason>" in your own words as the human, and run_gate's skip rule decides the rest.

3. Assemble the evidence.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . evidence
```
exit 0: continue and quote `.team-ship/EVIDENCE.md`.
exit 1: not used; evidence exits 0 or 2.
exit 2: UNVERIFIED; the before/after comparison cannot be captured.

The before side of the comparison is the previous run's `EVIDENCE.json`, quoted from the earlier
run directory; the two-commit comparator that would automate this is deferred to task 27, so
until it lands the model compares the two by hand.

- Focus on interactions between modules that changed independently

**If GSD active:** check each requirement against current code.

```
python3 ~/.claude/skills/team-gate/scripts/claim_evidence.py matrix <plan> --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/11-matrix.json); every requirement graded MET.
exit 1: quote the gate file's summary; the requirements it lists are NOT MET.
exit 2: UNVERIFIED; `<plan>` is `.planning/REQUIREMENTS.md` when GSD is active or `.team-ship/PLAN.md` otherwise, and the matrix reads only its `requirements` and `must_haves` lists; a REQUIREMENTS.md without those lists grades every requirement UNVERIFIED.

**Toolkit integration:**
- No specific toolkit entries apply: agents use direct code analysis
- Reference team:feedback.md for past review findings to check if they've regressed

### Layer 3: Regression Confirmation
L3 confirms claimed regressions are real, not false positives. A REGRESSION on test status is
confirmed by the before/after summary Layer 2 captured in `EVIDENCE.md`; a regression claimed
from code-reading alone, with no captured run, stays SUSPECTED, not confirmed.

### Layer 4: Delta Report
Principal produces the following.
- Regression list with severity and recommended fixes
- Confirmation of what's still solid
- New improvement opportunities discovered

## GSD Integration

When `.planning/` exists, re-verify each requirement from REQUIREMENTS.md against current code.
