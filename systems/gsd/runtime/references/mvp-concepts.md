# MVP Concepts — index

Cross-reference for the six MVP-related reference files. Each file has a single, narrow purpose. This index exists so future readers (and agents resolving `@`-refs) can find the right file without grepping the directory.

Canonical domain terms for the concepts named below live in [CONTEXT.md](../../CONTEXT.md) under "Domain terms" — start there if you need a precise definition.

## File map

| File | Purpose | Loaded by |
|---|---|---|
| `references/planner-mvp-mode.md` | **Rules.** Vertical-slice planning rules, slice ordering, Walking Skeleton constraints. | `gsd-planner` agent when `MVP_MODE=true` |
| `references/skeleton-template.md` | **Template.** Shape of `SKELETON.md` for new-project Phase 1 under `--mvp`. | `gsd-planner` agent when the Walking Skeleton gate fires |
| `references/user-story-template.md` | **Template.** Format and slot definitions for `As a / I want to / So that`. | `gsd-mvp-phase` workflow during interactive prompting; `gsd-planner` when emitting the `## Phase Goal` header |
| `references/spidr-splitting.md` | **Splitting discipline.** Five-axis decomposition (Spike, Paths, Interfaces, Data, Rules) for stories too large for one phase. | `gsd-mvp-phase` workflow when the user story exceeds size threshold |
| `references/execute-mvp-tdd.md` | **Gate.** MVP+TDD runtime gate semantics: when it fires, what it checks, halt-and-report protocol, end-of-phase blocking escalation, Behavior-Adding Task definition. | `gsd-executor` agent when `MVP_MODE=true && TDD_MODE=true` |
| `references/verify-mvp-mode.md` | **UAT framing.** Three-section UAT structure (user-flow → technical → coverage), anti-patterns, `User Flow Coverage` section in VERIFICATION.md. | `gsd-verifier` agent when the phase under verification has `mode: mvp` |

## Concept-to-file map

