---
name: learning:evolve
description: "Run pattern detection on session observations to extract and reinforce instincts"
argument-hint: "--project PROJECT_ID"
allowed-tools:
  - Bash
---

Run the Coco learning system evolution cycle to scan observations and detect new patterns.

```bash
cd "$CLAUDE_PROJECT_DIR" && python3 -m coco_learning.cli evolve --project $ARGUMENTS
```

This command:
1. Loads recent observations from `~/.coco/learning/projects/<id>/observations.jsonl`
2. Applies heuristic pattern matching rules across testing, security, workflow, architecture, debugging, and performance domains
3. Creates new candidate instincts for patterns with sufficient evidence (default: 3+ occurrences)
4. Reinforces existing instincts by incrementing evidence count and recomputing confidence
5. Saves all detected/reinforced instincts to disk as YAML files

After running, display the results and suggest:
- For strong instincts (confidence ≥ 0.7): recommend `/learning:promote <id> --from-project <id>`
- For candidates with low evidence: explain they need more observation data
- If no patterns detected: suggest continuing normal work to accumulate observations
