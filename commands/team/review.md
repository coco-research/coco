# /team review — Review Pipeline

> Called by team.md router when action is `review`.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst, security-analyst | 2 |
| L2 | (domain-dependent engineers) + senior-pm | 3-5 |
| L3 | domain-accuracy, doc-quality, grammar-editor, accessibility-specialist (if frontend domain) | 2 |
| L4 | principal-architect | 1 |

### Key Difference from Old System

**Old:** 5 identical reviewer clones with the same prompt → redundant findings.
**New:** 3-5 specialists each reviewing through a different lens:
- Backend engineer reviews API design and data modeling
- Security analyst reviews auth flows and secrets
- Frontend engineer reviews component patterns and a11y
- PM reviews requirements coverage and user stories
- QA reviews test adequacy and edge cases

## Pipeline Customization

### Layer 1: Scope Mapping
L1 agents determine:
- What files/modules are in scope for review
- What changed since last review (git log analysis)
- What the original requirements/spec was
- What risk areas to focus on

### Layer 2: Specialist Review
- **Mode:** `default` (read-only)
- Each L2 agent reviews through their specialist lens
- Every finding classified as: CRITICAL | MAJOR | MINOR | SUGGESTION
- Every finding includes: file path, line number, specific quote, suggested fix

**If GSD active:** Map findings back to requirements from REQUIREMENTS.md.

**Toolkit integration:**
- Check team-toolkit.md for "Code Review" entry for review methodology
- If GSD active, use GSD phase context for requirements traceability

### Layer 3: Cross-Review
L3 agents check the reviewers' work:
- Are findings accurate? (domain-accuracy verifies claims)
- Are severity classifications consistent?
- Any overlapping or contradictory findings?

### Layer 4: Synthesis
Principal produces:
- Prioritized findings list (deduplicated, severity-consistent)
- Architectural assessment (is the overall approach sound?)
- Recommended action items with effort estimates
