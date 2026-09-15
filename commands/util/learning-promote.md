---
name: learning:promote
description: "Promote a project-scoped instinct to global scope for cross-project reuse"
argument-hint: "INSTINCT_ID --from-project PROJECT_ID"
allowed-tools:
  - Bash
---

Promote a project-scoped instinct to the global learning store so it applies across all projects.

```bash
cd "$CLAUDE_PROJECT_DIR" && python3 -m coco_learning.cli promote $ARGUMENTS
```

Promotion eligibility (per instinct-schema.md):
- confidence ≥ 0.7
- evidence_count ≥ 10
- Observed in ≥ 2 distinct projects
- Not domain-specific to a single project's tooling

The CLI enforces the save and flag update; manual review of cross-project evidence is recommended before promoting.

After running, confirm the promotion and suggest `/learning:list` to verify the instinct now appears in global scope.
