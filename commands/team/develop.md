# /team develop — Build Pipeline

> Called by team.md router when action is `develop`.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst, security-analyst | 2 |
| L2 | senior-backend-eng, senior-frontend-eng, senior-cloud-architect, qa-test-architect, senior-data-eng, sre-devops, mcp-integration, performance-eng (if perf-related) | 3-5 (domain-dependent) |
| L3 | domain-accuracy, doc-quality, security-analyst (if api/backend/infrastructure), architecture-reviewer (if `.arch/index.json` exists) | 2-5 |
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

**Architecture context is advisory, not an allocation mechanism.** When
`.arch/index.json` exists and its pin is CURRENT, inline the component table from
`.arch/INDEX.md` into each L2 prompt (max 25 lines) so agents know where each
component's code lives.

Do **not** derive `YOUR FILES` from the index. The index sits at C4-Container altitude
while work is sharded at module altitude, and the two do not line up: in this repository
a legal five-component index assigns `skills/` — 1,087 files — to a single component. A
typical feature also spans three components at once. Scope-based splitting stays
authoritative for ownership; the index only tells an agent which boundary it is working
inside.

If the index is STALE, omit the block rather than quoting it.

**Toolkit integration:**
- Check team:toolkit.md for "Code Implementation" entry
- If Superpowers pipeline recommended → agent follows brainstorm → plan → execute pattern
- If GSD active → agent reads `.planning/` context and follows phase conventions

**Permission Mode:** `bypassPermissions` — agents need to create/edit files and run tests.

### Layer 3: Review
L3 agents focus on:
- Code correctness and edge cases (domain-accuracy)
- Test coverage adequacy verified against `EVIDENCE.md` — confirm the suite actually executed (captured exit 0, skips accounted for), not by reading test descriptions
- Architecture alignment with existing patterns
- Security review of auth, data handling, API boundaries (security-analyst, if selected)

### Regression Tests
Run after Layer 2, before Layer 3, per the Test Evidence Protocol (`team:evidence.md`): run the CI-equivalent authoritative gate with integration dependencies provisioned, capture command + exit code + parsed summary + measured coverage to `EVIDENCE.md`. Surface skips and failures explicitly in REVIEW-PACKAGE.md (with the skip count and any `UNVERIFIED` surface) — never hide them inside a "passed" summary.

## GSD Integration (C4)

When `.planning/` exists:
- Read ROADMAP.md for phase context
- L2 agents follow GSD conventions: atomic commits, SUMMARY.md, STATE.md updates
- Output is compatible with `/gsd:verify-work`
