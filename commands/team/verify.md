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

### Layer 2: Verification Testing
- **Mode:** `default` (read-only)
- Each agent takes a subset of requirements and verifies against actual deliverables
- For each requirement, report:
  - **MET** — requirement fully satisfied, with evidence (file:line or output)
  - **PARTIAL** — partially implemented, describe what's missing
  - **NOT MET** — not implemented or not found
  - **EXCEEDED** — implementation goes beyond spec (flag for review)
- Run any available tests to verify behavioral requirements

**Toolkit integration:**
- Check team-toolkit.md for verification tools (e.g., GSD verify-work)
- If GSD active, cross-reference `.planning/REQUIREMENTS.md`

### Layer 3: Evidence Audit
L3 agents verify Layer 2's claims:
- Does the cited evidence actually prove the requirement is met?
- Are any "MET" claims actually PARTIAL on closer inspection?
- Are severity classifications appropriate?
- Check for requirements that were missed entirely (not even assessed)

### Layer 4: Verdict
Principal produces:
- **Pass/Fail verdict** with confidence level
- Requirements traceability matrix (requirement → status → evidence)
- Gap list: what's missing, prioritized by impact
- Recommendation: ship as-is, fix gaps first, or rework needed

## GSD Integration

When `.planning/` exists, verify requirements from REQUIREMENTS.md. Cross-reference with phase success criteria.
