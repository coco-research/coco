---
name: maker-mdap
description: "REQUIRED baseline — Maker MDAP (massively decomposed agentic processes). Use for long multi-step work that must stay reliable: decompose into tiny subtasks, vote across parallel micro-attempts, and red-flag risky outputs. Source: Meyerson et al. arXiv:2511.09030."
domain: foundational
required: true
baseline: maker-mdap
---

# Maker MDAP

**Announce at start:** "Maker MDAP skill activated."

Portable worker guidance from MAKER / MDAP (Meyerson et al., arXiv:2511.09030). See [CREDITS.md](CREDITS.md). No new runtime — apply these steps in-process.

## When to use

- Multi-step tasks where a single long chain is likely to derail
- Reliability-critical reasoning (decisions, diagnoses, plans with many dependent steps)
- Explicit asks for MAKER, MDAP, micro-agents, or consensus voting

## Three pillars

### 1. Maximal Agentic Decomposition (MAD)

Break the goal into the **smallest useful subtasks** (ideally one clear step each). Prefer a DAG of micro-roles over one anthropomorphic mega-agent.

- One subtask → one focused prompt
- No hidden multi-step leaps inside a single micro-task
- Record dependencies so later steps only consume prior outputs

### 2. First-to-ahead-by-k voting

For each critical subtask, run **m** independent attempts (same subtask, separate samples). Accept a result when one answer leads by **k** votes (default: m=3, k=1 unless the host specifies otherwise).

- Discard tied or ambiguous tallies — resample or tighten the subtask
- Prefer exact/structured agreement (same choice, same key fields) over vague paraphrase matches

### 3. Red-flagging

Before a vote counts, drop outputs that look risky or correlated:

- Refusal, empty, or off-format answers
- Self-contradiction or missing required fields
- Near-duplicate failures across samples (same wrong pattern)

Do not let a red-flagged sample vote.

## Minimal loop

```
1. Decompose goal → ordered micro-subtasks (DAG)
2. For each subtask in order:
   a. Sample m attempts
   b. Red-flag each
   c. Vote first-to-ahead-by-k on remaining
   d. Pass only the winning structured result downstream
3. Compose final answer from verified subtask outputs only
```

## Out of scope

- Do not invent a coco runtime, MCP server, or telemetry for this skill
- Do not mesh every TL into an SI panel — SI C-suite spawn stays Cyra + Mira (+ Kavya/Emma when useful)
- Do not treat this as a substitute for `karpathy-guidelines` on ordinary coding edits

## Success

You applied MAD + voting + red-flagging on a multi-step task and can point to which subtasks were verified by vote.
