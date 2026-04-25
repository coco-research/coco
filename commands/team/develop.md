# /team develop — Build Pipeline

> Called by team.md router when action is `develop`.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst, security-analyst | 2 |
| L2 | senior-backend-eng, senior-frontend-eng, senior-cloud-architect, qa-test-architect, senior-data-eng, sre-devops, mcp-integration, performance-eng (if perf-related) | 3-5 (domain-dependent) |
| L3 | domain-accuracy, doc-quality, security-analyst (if api/backend/infrastructure) | 2-4 |
| L4 | principal-architect | 1 |

### Domain-Specific Selection

- `backend` only → senior-backend-eng + qa-test-architect + (senior-cloud-architect if `infrastructure`)
- `frontend` only → senior-frontend-eng + qa-test-architect + (senior-ux-designer if `product`)
- `backend` + `frontend` → senior-backend-eng + senior-frontend-eng + qa-test-architect
- `data` → senior-data-eng + senior-backend-eng
- `mobile` → senior-mobile-eng + qa-test-architect
- `infrastructure` → senior-cloud-architect + sre-devops
- `integrations` → mcp-integration + senior-backend-eng

## Pipeline Customization

### Layer 1: Research
L1 agents focus on:
- File mapping for the feature scope
- Existing patterns and conventions to follow
- Dependencies and integration points
- Security considerations for the feature

### Layer 2: Execution
L2 agents receive file ownership boundaries (I10):
- Orchestrator divides scope into non-overlapping file groups
- Each agent's prompt includes:
  ```
  YOUR FILES: [list]
  DO NOT TOUCH: [files owned by other agents]
  ```
- Agents commit atomically per feature/fix

**Toolkit integration:**
- Check team-toolkit.md for "Code Implementation" entry
- If Superpowers pipeline recommended → agent follows brainstorm → plan → execute pattern
- If GSD active → agent reads `.planning/` context and follows phase conventions

**Permission Mode:** `bypassPermissions` — agents need to create/edit files and run tests.

### Layer 3: Review
L3 agents focus on:
- Code correctness and edge cases (domain-accuracy)
- Test coverage adequacy (doc-quality reviewing test descriptions)
- Architecture alignment with existing patterns
- Security review of auth, data handling, API boundaries (security-analyst, if selected)

### Regression Tests
Run after Layer 2, before Layer 3. Include results in REVIEW-PACKAGE.md.

## GSD Integration (C4)

When `.planning/` exists:
- Read ROADMAP.md for phase context
- L2 agents follow GSD conventions: atomic commits, SUMMARY.md, STATE.md updates
- Output is compatible with `/gsd:verify-work`
