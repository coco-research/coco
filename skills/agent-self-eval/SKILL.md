---
name: agent-self-eval
description: "Post-run self-evaluation system that scores agent output on correctness, clarity, actionability, and conciseness. Use after /team runs, skill executions, or when explicitly asked to evaluate output quality."
domain: meta
supports: [claude-code, cursor, codex, generic, windsurf, zed, cline, roo-code, amazon-q]
version: 0.1.0
tags: [evaluation, quality, scoring, feedback]
---

@agents/PROMPT-DEFENSE.md

# Agent Self-Evaluation

Score your own output (or another agent's output) across four axes to identify quality gaps and feed improvements into the learning system.

## When to Use
- After completing a `/team:*` pipeline run
- After generating a deliverable (PRD, architecture doc, code review)
- When user asks "how did I do?" or "evaluate this output"
- Automatically at end of `/gsd-execute-phase` for quality tracking

## Evaluation Axes

| Axis | Question | Failure Signals |
|------|----------|-----------------|
| **Correctness** | Is the output factually accurate and technically sound? | Wrong APIs, broken references, hallucinated facts, logic errors |
| **Clarity** | Is the explanation understandable and well-structured? | Confusing structure, undefined jargon, missing context, rambling |
| **Actionability** | Can the user act on the output immediately? | Vague suggestions, missing steps, no verification path |
| **Conciseness** | Did it use the minimum tokens needed? | Redundancy, over-explanation, filler content, restating the question |

## Scoring Scale
```
5 — Exceptional: no reasonable improvement possible
4 — Good: minor nits only, no substantive gaps
3 — Adequate: meets request but has notable weakness on ≥1 axis
2 — Weak: clear gap affecting usability or correctness
1 — Poor: fundamentally misses request or contains significant errors
```

## The Evidence Rule
Every score below 5 MUST cite specific evidence. A score of 3 cannot just say "could be better" — it must say exactly what is missing or wrong. **"Show the gap, don't just name it."**

## Procedure

### Step 1: Collect Raw Material
Gather:
- Original user request
- Final output/deliverable
- Tool outputs verifying correctness (test results, exit codes, lint)
- User feedback received during task (corrections, "try again")

### Step 2: Score Each Axis Independently
Rate 1-5 with mandatory evidence for scores <5.

### Step 3: Generate Eval Report
```
SELF-EVALUATION REPORT
======================
Task: {brief description}
Overall: {weighted average}/5

CORRECTNESS: {score}/5
  Evidence: {specific finding or "No issues found"}

CLARITY: {score}/5
  Evidence: {specific finding or "No issues found"}

ACTIONABILITY: {score}/5
  Evidence: {specific finding or "No issues found"}

CONCISENESS: {score}/5
  Evidence: {specific finding or "No issues found"}

IMPROVEMENT INSTINCTS:
- {trigger} → {action} (confidence: {0.3-0.9})
```

### Step 4: Feed Learning System
If learning system is active (PR-27+), auto-generate instinct YAML from findings:
```yaml
---
id: eval-{task-slug}-{axis-lowercase}
trigger: "when {task type}"
action: "{specific improvement}"
confidence: 0.6
domain: quality
source: self-eval
scope: project
---
```

## Integration Points
- `/team:verify` invokes self-eval on Layer 2 output before Layer 3 review
- `/gsd-execute-phase` runs self-eval per subagent, aggregates in SUMMARY.md
- High-confidence eval instincts (≥0.8) auto-update team-toolkit.md quality notes
- Low scores (≤2) on correctness trigger automatic re-execution offer
