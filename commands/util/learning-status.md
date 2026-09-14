---
name: learning:status
description: "Show Coco learning system status — instinct counts, observation stats, and detection summary"
argument-hint: "[--project PROJECT_ID]"
allowed-tools:
  - Bash
---

Run the Coco learning system status command to display current instinct inventory and observation statistics.

```bash
cd "$CLAUDE_PROJECT_DIR" && python3 -m coco_learning.cli status $ARGUMENTS
```

If no `--project` is specified, shows global instincts only.
Pass a project ID to include project-scoped instincts and observation file stats.

After displaying status, suggest next actions:
- If observations exist but no instincts: recommend `/learning:evolve --project <id>`
- If candidate instincts have high evidence: recommend `/learning:promote <id> --from-project <id>`
- If no observations: explain that the observe.sh hook captures data automatically during sessions
