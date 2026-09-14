---
description: "Run post-output self-evaluation scoring on correctness, clarity, actionability, and conciseness"
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
---

# /self-eval — Agent Output Quality Scoring

Evaluate the most recent agent output or deliverable across four quality axes.

## Usage
```
/self-eval              # Evaluate last output in current session
/self-eval --file <path>  # Evaluate specific file/deliverable
/self-eval --team         # Evaluate last /team pipeline output
```

## What It Does
1. Collects original request + final output + verification evidence
2. Scores each axis (correctness, clarity, actionability, conciseness) 1-5
3. Generates improvement instincts for the learning system
4. Flags scores ≤2 on correctness for automatic re-execution offer

## When to Run
- After any `/team:*` command completes
- After `/gsd-execute-phase` finishes
- When user asks "how did that go?" or "evaluate this"
- Before marking a phase as complete in GSD workflows
