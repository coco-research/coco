---
name: context-budget
description: "Audit token consumption across agents, skills, MCP servers, and rules. Identifies bloat, redundant components, and produces prioritized token-savings recommendations. Use when the context window is filling up too fast or before adding new components."
domain: meta
supports: [claude-code, cursor, codex, generic, windsurf, zed, cline, roo-code, amazon-q]
version: 0.1.0
tags: [context, tokens, optimization, audit]
---

@agents/PROMPT-DEFENSE.md

# Context Budget Audit

Analyze token overhead across every loaded component in a session and surface actionable optimizations to reclaim context space.

## When to Use
- Session performance feels sluggish or output quality is degrading
- You've recently added many skills, agents, or MCP servers
- Planning to add more components and need to know if there's room
- Running `/context-budget` command (this skill backs it)

## Audit Procedure

### Phase 1: Inventory
Scan all component directories and estimate token consumption:

**Agents** (`agents/*.md`)
- Count lines and tokens per file (words × 1.3)
- Extract `description` frontmatter length
- Flag: files >200 lines (heavy), description >30 words (bloated frontmatter)

**Skills** (`skills/*/SKILL.md`)
- Count tokens per SKILL.md
- Flag: files >400 lines
- Check for duplicate copies — skip identical copies to avoid double-counting

**Rules** (`rules/**/*.md`, `rules/**/*.mdc`)
- Count tokens per file
- Flag: files >100 lines
- Detect content overlap between rule files

**MCP Servers** (active MCP config)
- Count configured servers and total tool count
- Estimate schema overhead at ~500 tokens per tool
- Flag: servers with >20 tools

**CLAUDE.md / System Prompts**
- Count tokens in CLAUDE.md chain
- Flag: combined total >300 lines

### Phase 2: Classify
Sort every component into a bucket:

| Bucket | Criteria | Action |
|--------|----------|--------|
| **Always needed** | Referenced in CLAUDE.md, backs active command, matches project type | Keep |
| **Sometimes needed** | Domain-specific, not referenced in CLAUDE.md | Consider on-demand activation |
| **Rarely needed** | No command reference, overlapping content, no project match | Remove or lazy-load |

### Phase 3: Report
Generate a prioritized savings report:

```
CONTEXT BUDGET AUDIT
====================
Total estimated tokens: {total}
Context headroom: {headroom}%

TOP SAVINGS OPPORTUNITIES:
1. {component} — {tokens} tokens ({bucket}) → {recommendation}
2. {component} — {tokens} tokens ({bucket}) → {recommendation}
...

ALWAYS NEEDED (keep):
- {component} ({tokens} tokens)

SOMETIMES NEEDED (lazy-load candidates):
- {component} ({tokens} tokens)

RARELY NEEDED (removal candidates):
- {component} ({tokens} tokens)
```

## Token Estimation Formula
- English text: ~1.3 tokens per word
- Code: ~1.5 tokens per word (more punctuation/symbols)
- YAML frontmatter: ~1.2 tokens per word
- MCP tool schema: ~500 tokens per tool definition

## Integration Points
- Run automatically before `/team:ship` to verify context headroom
- Feed results to learning system as optimization instincts
- Cross-reference with Brain DB decisions about past context issues
