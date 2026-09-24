---
description: "Use when built work must be checked against its spec, plan, or PRD before shipping, or the team router action is verify. Re-runs the gate from a clean checkout per requirement and grades it MET, PARTIAL, NOT MET, or UNVERIFIED."
---
# /team verify: Verification Pipeline

> Called by team.md router when action is `verify`.
> Checks if what was built matches what was planned/specified.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | business-analyst, technical-analyst | 2 |
| L2 | qa-test-architect, (domain-dependent engineers) | 2-4 |
| L3 | domain-accuracy, standards-reviewer, architecture-reviewer (if `.arch/index.json` exists) | 2-3 |
| L4 | principal-pm | 1 |

## Stage 1: Brownfield Map

```
python3 ~/.claude/skills/team-gate/scripts/brownfield_map.py --for "<what is being verified in words>" --repo-root .
```
exit 0: continue; read `.team-ship/BROWNFIELD-MAP.md` before reading any code.
exit 1: not used; a map is not a pass or fail judgement.
exit 2: UNVERIFIED; quote the gate file's summary (gates/handoff-1-map.json).

No verify-pipeline aggregator requires this gate file; until one exists, the map is the first step by instruction.

## Pipeline Customization

### Layer 1: Spec Extraction
L1 agents gather.
- The spec/plan/PRD that defined what should be built
- `.arch/index.json` and its pin, if present, the structural baseline for failure mode (e)
- Success criteria, acceptance criteria, NFRs
- Review findings that were supposed to be addressed
- Build a requirements checklist with unique IDs

```
python3 ~/.claude/skills/team-gate/scripts/arch_gate.py --repo-root .
```
exit 0: continue; the index is CURRENT, quote the pin and head from `.arch/ARCH-GATE.json`.
exit 1: continue; a REMOVE verdict already exists, quote the reason from `.arch/ARCH-GATE.json` and carry it to Layer 3.
exit 2: continue; STALE, the index is absent (no .arch/index.json, which the script reports as not found), or drift is unreconciled, record which and carry it to Layer 3 for failure mode (e).

### Layer 2: Independent Re-Execution
- **Mode:** `bypassPermissions`, verify agents must run the gate themselves, not just read files.
- **Independence rule:** verify agents must not read the builder's summary, REVIEW-PACKAGE.md, or any "tests pass" claim before re-running. They form their own evidence first, then compare.

1. Run `verify_independent.py setup` to create a detached clean worktree at HEAD and print the exact invocation for the Layer 2 verify agent.

```
python3 ~/.claude/skills/team-gate/scripts/verify_independent.py setup --repo-root .
```
exit 0: continue; spawn the Layer 2 verify agent with the printed invocation line and nothing else, so it never reads the builder's summary, REVIEW-PACKAGE.md, or any "tests pass" claim.
exit 1: BLOCK; `.team-ship/` carries tracked files inside the worktree, quote the reason and the tracked file list.
exit 2: UNVERIFIED; git is unavailable or the run state cannot be read.

The worktree is a detached checkout of the same repository at HEAD, not a separate clone.

2. Each Layer 2 agent runs only the three commands the printed invocation names, `run_gate.py --repo-root . --role verifier discover`, then `run`, then `coverage`, and reports their three exit codes, nothing else. This writes gates/7-verifier.json, gates/8-verifier.json, and gates/10-verifier.json.

Provision what CI provisions inside the worktree before spawning the agent. When something cannot be provisioned, record "override integration: <reason>" in your own words as the human, and run_gate's skip rule decides the rest.

3. Run `verify_independent.py compare` to check the verifier's re-run against the builder's own gate file.

```
python3 ~/.claude/skills/team-gate/scripts/verify_independent.py compare --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/11.json).
exit 1: BLOCK; quote the mismatches from the gate file, the discrepancy between the builder's claim and the re-run output.
exit 2: UNVERIFIED; the run directory or either gate file cannot be read.

4. Run `verify_independent.py teardown` to remove the worktree.

```
python3 ~/.claude/skills/team-gate/scripts/verify_independent.py teardown --repo-root .
```
exit 0: continue; the worktree is removed.
exit 1: not used; teardown exits 0 or 2.
exit 2: UNVERIFIED; the worktree or run state cannot be read.

5. Once every Layer 2 agent's re-execution is captured in the run's gate files, run `claim_evidence.py matrix` once over the whole plan to grade every requirement.

```
python3 ~/.claude/skills/team-gate/scripts/claim_evidence.py matrix .team-ship/PLAN.md --repo-root .
```
exit 0: continue; every requirement is MET, quote the gate file's summary (gates/11-matrix.json).
exit 1: NOT MET exists; quote which requirements from the gate file.
exit 2: UNVERIFIED exists with no NOT MET; quote which requirements from the gate file, never counts as MET.

A requirement the matrix grades MET may still be judged PARTIAL on closer inspection, and an implementation that goes beyond what the matrix can see is EXCEEDED, flag for review; both stay model judgement written after the matrix, since the matrix itself grades only MET, NOT MET, or UNVERIFIED.

**Toolkit integration:**
- Check team:toolkit.md for verification tools (e.g., GSD verify-work)
- If GSD active, cross-reference `.planning/REQUIREMENTS.md`

### Layer 3: Evidence Audit
L3 agents verify Layer 2's claims, and explicitly check for these failure modes, any one downgrades the verdict.
- Does the cited evidence actually prove the requirement is met?
- Are any "MET" claims actually PARTIAL on closer inspection?
- **(a) Skipped-as-passed**, tests reported "pass" while the summary shows skips, or DB-gated tests skipped because no dependency was provisioned.
- **(b) Coverage without measurement**, a coverage number with no captured `--cov` output.
- **(c) Not CI-reproducible**, a claim that only holds locally (weaker tool version, or a DSN unavailable in CI).
- **(d) Merge masquerade**, "merged" or CI-green implied for a branch not reachable from `main`.

(a), (b), and (d) are the same finding, a PR-body claim contradicted or unbacked by the evidence it cites.

```
python3 ~/.claude/skills/team-gate/scripts/claim_evidence.py check .team-ship/PR-BODY.md --repo-root .
```
exit 0: continue and quote the gate file's summary (gates/12.json).
exit 1: BLOCK; quote the findings from the gate file, including any merge-claim phrase whose named condition does not hold, and strip the unbacked claim.
exit 2: UNVERIFIED; the repository, run, lexicon, or a required input file (PR-BODY.md, EVIDENCE.json) cannot be read.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . parity
```
exit 0: continue; local tool versions match CI's pinned versions, quote the gate file's summary (gates/7.json).
exit 1: BLOCK; a tool version mismatch, quote the gate file's summary (gates/7.json).
exit 2: UNVERIFIED; discover has not run yet or its gate file cannot be read.

DSN availability in CI for (c) is covered by the same provisioning paragraph in Layer 2.

- **(e) Architecture abandoned**, the build satisfied its requirements while silently
  abandoning the module boundaries it was built against. This is the one failure mode no
  test can surface: tests fail when behaviour changes, not when a component is relocated,
  merged into another, or deleted outright.

  Applies only when `.arch/index.json` exists.

  ```
  python3 ~/.claude/skills/team-gate/scripts/arch_gate.py --repo-root .
  ```
  exit 0: continue; a printed MAJOR line names a PRUNE verdict, quote which paths died from `.arch/ARCH-GATE.json`; otherwise report NO DRIFT for this failure mode.
  exit 1: CRITICAL; a REMOVE verdict (zero surviving primary paths), quote the dead paths from `.arch/ARCH-GATE.json`.
  exit 2: UNVERIFIED, never clean; the pin is behind HEAD, the index is absent (no .arch/index.json, which the script reports as not found), or drift is unreconciled.

  Files added outside every claimed path, forming a new top-level source directory, are MAJOR regardless of exit code, either a component is missing from the index or the build went somewhere it was not supposed to. This stays a review judgement no script makes.

  **Scope limit, and state it in the finding:** this detects *structural* drift only. A
  component whose datastore was swapped inside its own already-claimed directory returns
  `NO DRIFT`. A clean result licenses one sentence, that no structural drift was found,
  and no broader claim about architectural soundness.
- Requirements missed entirely surface as UNVERIFIED in the same requirements matrix (gates/11-matrix.json), a requirement absent from every gate's mapping.

### Layer 4: Verdict
Principal produces.
- **Pass/Fail verdict**: Pass requires compare (gates/11.json), matrix (gates/11-matrix.json), and check (gates/12.json) all at exit 0, and arch_gate (`.arch/ARCH-GATE.json`) at exit 0 or an override receipt naming gate "arch". Any `UNVERIFIED` surface or any Layer 3 finding (a) through (e) forces Fail or a downgraded, gap-listed verdict.
- Requirements traceability matrix, gates/11-matrix.json from Layer 2 (requirement, status, captured evidence)
- Gap list: what's missing, prioritized by impact
- Recommendation: ship as-is, fix gaps first, or rework needed

## GSD Integration

When `.planning/` exists, verify requirements from REQUIREMENTS.md. Cross-reference with phase success criteria.
