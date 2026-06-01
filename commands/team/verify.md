# /team verify — Verification Pipeline

> Called by team.md router when action is `verify`.
> Checks if what was built matches what was planned/specified.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | business-analyst, technical-analyst | 2 |
| L2 | qa-test-architect, (domain-dependent engineers) | 2-4 |
| L3 | domain-accuracy, standards-reviewer | 2 |
| L4 | principal-pm | 1 |

## Pipeline Customization

### Layer 1: Spec Extraction
L1 agents gather:
- The spec/plan/PRD that defined what should be built
- Success criteria, acceptance criteria, NFRs
- Review findings that were supposed to be addressed
- Build a requirements checklist with unique IDs

### Layer 2: Independent Re-Execution
- **Mode:** `bypassPermissions` — verify agents must run the gate themselves, not just read files.
- **Independence rule:** verify agents must NOT read the builder's summary, REVIEW-PACKAGE.md, or any "tests pass" claim before re-running. They form their own evidence first, then compare.
- Re-run the authoritative gate from a CLEAN checkout (a fresh clone, e.g. `/tmp/clean-<branch>`), per the Test Evidence Protocol (`team:evidence.md`): CI-pinned tool versions, integration dependencies provisioned, full suite executed.
- Paste raw captured output: the command line, exit code, the pytest summary (passed / skipped / failed), the skip count, and the measured coverage %.
- Each agent takes a subset of requirements and verifies against actual deliverables. For each requirement, report:
  - **MET** — requirement fully satisfied, backed by captured output (not a cited claim)
  - **PARTIAL** — partially implemented, describe what's missing
  - **NOT MET** — not implemented or not found
  - **UNVERIFIED** — could not execute (e.g. dependency not provisioned, tests skipped); never counts as MET
  - **EXCEEDED** — implementation goes beyond spec (flag for review)
- Any mismatch between the builder's claim and the re-run output → BLOCK with the discrepancy quoted.

**Toolkit integration:**
- Check team:toolkit.md for verification tools (e.g., GSD verify-work)
- If GSD active, cross-reference `.planning/REQUIREMENTS.md`

### Layer 3: Evidence Audit
L3 agents verify Layer 2's claims, and explicitly check for these failure modes — any one downgrades the verdict:
- Does the cited evidence actually prove the requirement is met?
- Are any "MET" claims actually PARTIAL on closer inspection?
- **(a) Skipped-as-passed** — tests reported "pass" while the summary shows skips, or DB-gated tests skipped because no dependency was provisioned.
- **(b) Coverage without measurement** — a coverage number with no captured `--cov` output.
- **(c) Not CI-reproducible** — a claim that only holds locally (weaker tool version, or a DSN unavailable in CI).
- **(d) Merge masquerade** — "merged" / CI-green implied for a branch not reachable from `main`.
- Requirements missed entirely (not even assessed).

### Layer 4: Verdict
Principal produces:
- **Pass/Fail verdict** — Pass is allowed ONLY if every requirement's evidence was reproduced by the Layer 2 verify agents from a clean checkout, not merely cited by the builder. Any `UNVERIFIED` surface or any Layer 3 (a)–(d) finding forces Fail or a downgraded, gap-listed verdict.
- Requirements traceability matrix (requirement → status → captured evidence)
- Gap list: what's missing, prioritized by impact
- Recommendation: ship as-is, fix gaps first, or rework needed

## GSD Integration

When `.planning/` exists, verify requirements from REQUIREMENTS.md. Cross-reference with phase success criteria.
