---
description: "Use when the user runs /team develop, or the team router picks action develop, to build or fix code through a multi-agent pipeline. Shards files across L2 agents, then reviews with captured regression evidence."
---
# /team develop: Build Pipeline

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

## Stage 1: Brownfield Map

```
python3 ~/.claude/skills/team-gate/scripts/brownfield_map.py --for "<the feature or fix in words>" --repo-root .
```
exit 0: continue; read `.team-ship/BROWNFIELD-MAP.md` before reading any code.
exit 1: not used; a map is not a pass or fail judgement.
exit 2: UNVERIFIED; quote the gate file's summary (gates/handoff-1-map.json).

No develop-pipeline aggregator exists to require this gate file; the map is the first step by instruction.

## Pipeline Customization

### Layer 1: Research
L1 agents focus on the following areas.
- File mapping for the feature scope
- Existing patterns and conventions to follow
- Dependencies and integration points
- Security considerations for the feature

### Layer 2: Execution

1. Run `run_gate.py discover` then `run_gate.py run` for the baseline, before any Layer 2 agent commits.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . discover
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . run
```
exit 0: continue and quote each gate file's summary (gates/7-discover.json, gates/8.json), and record gates/8.json's head field now as the base for the red-green proof; that file is rewritten by the Regression Tests run.
exit 1: BLOCK; for the command that stopped, quote its gate file's summary and loop back to Layer 2 execution.
exit 2: UNVERIFIED; for the command that stopped, quote its gate file's summary; the suite is not confirmed passing until the gate passes or an override receipt names the gate.

L2 agents receive file ownership boundaries (I10), covering the following areas.
- Orchestrator divides scope into non-overlapping file groups
- Each agent's prompt includes the following block.
  ```
  YOUR FILES: [list]
  DO NOT TOUCH: [files owned by other agents]
  ```
- Agents commit atomically per feature/fix

**Architecture context is advisory, not an allocation mechanism.**

```
python3 ~/.claude/skills/team-gate/scripts/arch_gate.py --repo-root .
```
exit 0: continue and quote `.arch/ARCH-GATE.json`; inline the component table from `.arch/INDEX.md` into each L2 prompt (max 25 lines) so agents know where each component's code lives.
exit 1: BLOCK; a REMOVE verdict, quote the reason from `.arch/ARCH-GATE.json`.
exit 2: UNVERIFIED; the index is absent (no .arch/index.json, which the script reports as not found), the pin is behind HEAD, or drift is unreconciled; omit the component-table block from each L2 prompt rather than quoting it.

Do **not** derive `YOUR FILES` from the index. The index sits at C4-Container altitude
while work is sharded at module altitude, and the two do not line up: in this repository
a legal five-component index assigns `skills/`, 1,087 files, to a single component. A
typical feature also spans three components at once. Scope-based splitting stays
authoritative for ownership; the index only tells an agent which boundary it is working
inside.

**Toolkit integration:**
- Check team:toolkit.md for "Code Implementation" entry
- If Superpowers pipeline recommended → agent follows brainstorm → plan → execute pattern
- If GSD active → agent reads `.planning/` context and follows phase conventions

**Permission Mode:** `bypassPermissions`, agents need to create/edit files and run tests.

### Regression Tests

Run after all Layer 2 agents complete, before Layer 3, per the Test Evidence Protocol (`team:evidence.md`).

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . discover
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . run
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . coverage
```
exit 0: continue and quote each gate file's summary (gates/7-discover.json, gates/8.json, gates/10.json).
exit 1: BLOCK; for the command that stopped, quote its gate file's summary and loop back to Layer 2 execution.
exit 2: UNVERIFIED; for `coverage`, no pytest-shaped command gives NOT_APPLICABLE, which still blocks unless an override receipt names gate "coverage"; for any other command that stopped, the suite is not confirmed passing until the gate passes or an override receipt names the gate.

Provision what CI provisions. When something cannot be provisioned, record "override integration: <reason>" in your own words as the human, and run_gate's skip rule decides the rest.

prove_red runs each test added since the base green at HEAD, reverts the implementation paths in a throwaway worktree and proves it goes red for the right reason; a never-red or invalid-red classification is BLOCK with the reason quoted from gates/9.json.

```
python3 ~/.claude/skills/team-gate/scripts/prove_red.py prove --base <the head recorded at the baseline step> --repo-root .
python3 ~/.claude/skills/team-gate/scripts/prove_red.py recheck --repo-root .
```
exit 0: continue and quote each gate file's summary (gates/9.json, gates/9-recheck.json).
exit 1: BLOCK; quote the reason from gates/9.json, or from gates/9-recheck.json for a changed or removed proved test, and loop back to Layer 2 execution.
exit 2: UNVERIFIED; for the command that stopped, quote its gate file's summary; the suite is not confirmed passing until the gate passes or an override receipt names the gate.

```
python3 ~/.claude/skills/team-gate/scripts/run_gate.py --repo-root . evidence
```
exit 0: continue and quote `.team-ship/EVIDENCE.md`.
exit 1: not used; evidence exits 0 or 2.
exit 2: UNVERIFIED; the suite is not confirmed passing until the gate passes or an override receipt names the gate.

Surface skips and failures explicitly in REVIEW-PACKAGE.md (with the skip count and any `UNVERIFIED` surface): never hide them inside a "passed" summary.

### Layer 3: Review
L3 agents focus on the following areas.
- Code correctness and edge cases (domain-accuracy)
- Test coverage adequacy: confirmed by the Regression Tests gate above, via `EVIDENCE.md`, not by reading test descriptions
- Architecture alignment with existing patterns
- Security review of auth, data handling, API boundaries (security-analyst, if selected)

## GSD Integration (C4)

When `.planning/` exists, the following applies.
- Read ROADMAP.md for phase context
- L2 agents follow GSD conventions: atomic commits, SUMMARY.md, STATE.md updates
Output is compatible with `/gsd-verify-work`.
