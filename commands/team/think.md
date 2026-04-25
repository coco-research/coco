# /team think — Analysis & Brainstorm Pipeline

> Called by team.md router when action is `think`.
> Balanced pipeline: L1 researches, L2 generates options, L3 stress-tests them.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | domain-researcher, technical-analyst, business-analyst | 3-4 |
| L2 | senior-pm, senior-backend-eng or senior-frontend-eng (domain-dependent), technical-writer | 2-3 |
| L3 | domain-accuracy, doc-quality | 2 |
| L4 | principal-architect or principal-pm | 1 |

## Pipeline Customization

### Layer 1: Problem Analysis
L1 agents decompose the problem:
- **domain-researcher** → What approaches exist in the industry?
- **technical-analyst** → What are the technical constraints and options?
- **business-analyst** → What are the business constraints and stakeholder needs?

### Layer 2: Option Generation
L2 agents produce structured options:
- Each option has: Description, Pros, Cons, Effort estimate, Risk assessment
- Options are compared in a decision matrix
- senior-pm frames options from product perspective
- Engineers frame options from technical perspective

**Toolkit integration:**
- Check team-toolkit.md for brainstorming tools
- Apply structured thinking frameworks (MECE, first principles, inversion)

### Layer 3: Stress Testing
L3 agents challenge each option:
- What could go wrong?
- What assumptions are we making?
- What's the worst-case scenario?
- Which option survives scrutiny best?

### Layer 4: Decision Recommendation
Principal produces:
- Recommended option with rationale
- Risk mitigation plan for the recommended option
- Conditions under which alternative options would be better
- Decision framework for the user to make the final call

## GSD Integration

N/A — Brainstorming is project-context-independent.
