# /team research — Research Pipeline

> Called by team.md router when action is `research`.
> L1-heavy action: most agents are in the research layer.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | domain-researcher, technical-analyst, business-analyst, security-analyst, ux-researcher | 4-6 |
| L2 | technical-writer (compiles findings) | 1-2 |
| L3 | domain-accuracy, doc-quality | 1 |
| L4 | principal-architect or principal-pm (topic-dependent) | 1 |

### Research Angle Assignment

Each L1 agent gets a specific research angle to prevent overlap:
- **domain-researcher** → Industry context, competitive landscape, prior art
- **technical-analyst** → Technical feasibility, architecture options, dependency analysis
- **business-analyst** → Business case, stakeholder impact, requirements implications
- **security-analyst** → Security implications, compliance requirements, threat landscape
- **ux-researcher** → User impact, usability considerations, accessibility implications

## Pipeline Customization

### Layer 1: Deep Research (Primary Layer)
- **Mode:** `default` (read-only + web tools)
- Each agent uses WebSearch, WebFetch, and project file reads
- Agents produce structured findings with sources and confidence levels
- This is the main work layer — expect 70% of effort here

### Layer 2: Compilation
- **Mode:** `default`
- technical-writer compiles all L1 findings into a unified research document
- Structure: Summary → Analysis by Angle → Cross-Cutting Themes → Recommendation
- Deduplicates and resolves conflicting findings

**Toolkit integration:**
- Check team-toolkit.md for document compilation tools if producing a formal research report
- If outputting to Confluence, check "Confluence Publishing" entry for API notes

### Layer 3: Accuracy Check
L3 domain-accuracy verifies:
- Source URLs are valid and claims match sources
- Technical claims are accurate
- No outdated information presented as current

### Layer 4: Strategic Synthesis
Principal produces:
- Executive summary for decision-makers
- Ranked recommendations with trade-offs
- Identified unknowns and suggested next steps

## GSD Integration

N/A — Research is project-context-independent.
