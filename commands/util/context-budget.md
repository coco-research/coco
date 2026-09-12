---
description: "Audit context window token consumption across all loaded components and recommend optimizations"
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
---

# /context-budget — Token Consumption Audit

Run the context-budget skill to analyze token overhead across agents, skills, rules, MCP servers, and system prompts.

## Usage
```
/context-budget              # Full audit
/context-budget --quick      # Summary only (top 5 savings)
/context-budget --verbose    # Include per-file breakdown
```

## What It Does
1. Scans all component directories (agents/, skills/, rules/, MCP configs)
2. Estimates token count per component (words × 1.3 for text, × 1.5 for code)
3. Classifies each as Always/Sometimes/Rarely needed
4. Produces prioritized savings report with actionable recommendations

## When to Run
- Before adding new skills or agents
- When session quality degrades mid-conversation
- After installing a new system bundle (GSD, Brain, Team)
- As part of `/team:ship` pre-flight checks
