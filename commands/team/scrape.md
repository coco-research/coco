# /team scrape — Web Research Pipeline

> Called by team.md router when action is `scrape`.
> Parallel web research across URLs or topics.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | domain-researcher (1 per URL/topic, max 6) | 2-6 |
| L2 | technical-writer (compilation) | 1 |
| L3 | domain-accuracy | 1 |
| L4 | principal-architect or principal-pm | 1 |

### Input Parsing

- URLs (starts with http/https) → one L1 agent per URL
- Quoted topics → one L1 agent per topic (uses WebSearch)
- Mixed → one agent per item
- Maximum 6 L1 agents

## Pipeline Customization

### Layer 1: Parallel Scraping
- **Mode:** `default` (web tools)
- URL agents: WebFetch → extract key info, code examples, API details
- Topic agents: WebSearch → WebFetch top 3-5 results → synthesize findings
- Each agent reports: key facts, code snippets, source URLs, confidence level

### Layer 2: Compilation
technical-writer compiles all L1 findings into a unified research document:
- Deduplicated findings
- Cross-source validation
- Structured by topic/theme

**Toolkit integration:**
- No specific toolkit entries apply — agents use WebSearch/WebFetch directly
- Check team-toolkit.md only if outputting a formal document (e.g., research report)

### Layer 3: Source Verification
domain-accuracy spot-checks:
- Are source URLs still valid?
- Do claims match what the sources actually say?
- Any contradictory information between sources?

### Layer 4: Synthesis
Principal produces executive summary with ranked findings and recommended actions.

## GSD Integration

N/A — Web scraping is project-context-independent.
