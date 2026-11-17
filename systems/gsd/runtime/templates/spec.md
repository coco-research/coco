# Phase Spec Template

Template for `.planning/phases/XX-name/{phase_num}-SPEC.md` — locks requirements before discuss-phase.

**Purpose:** Capture WHAT a phase delivers and WHY, with enough precision that requirements are falsifiable. discuss-phase reads this file and focuses on HOW to implement (skipping "what/why" questions already answered here).

**Key principle:** Every requirement must be falsifiable — you can write a test or check that proves it was met or not. Vague requirements like "improve performance" are not allowed.

**Downstream consumers:**
- `discuss-phase` — reads SPEC.md at startup; treats Requirements, Boundaries, and Acceptance Criteria as locked; skips "what/why" questions
- `gsd-planner` — reads locked requirements to constrain plan scope
- `gsd-verifier` — uses acceptance criteria as explicit pass/fail checks

---

## File Template

```markdown
# Phase [X]: [Name] — Specification

**Created:** [date]
**Ambiguity score:** [score] (gate: ≤ 0.20)
**Requirements:** [N] locked

## Goal

[One precise sentence — specific and measurable. NOT "improve X" — instead "X changes from A to B".]

## Background

[Current state from codebase — what exists today, what's broken or missing, what triggers this work. Grounded in code reality, not abstract description.]

## Requirements

1. **[Short label]**: [Specific, testable statement.]
   - Current: [what exists or does NOT exist today]
   - Target: [what it should become after this phase]
   - Acceptance: [concrete pass/fail check — how a verifier confirms this was met]

2. **[Short label]**: [Specific, testable statement.]
   - Current: [what exists or does NOT exist today]
   - Target: [what it should become after this phase]
   - Acceptance: [concrete pass/fail check]

[Continue for all requirements. Each must have Current/Target/Acceptance.]

## Boundaries

**In scope:**
- [Explicit list of what this phase produces]
- [Each item is a concrete deliverable or behavior]

**Out of scope:**
- [Explicit list of what this phase does NOT do] — [brief reason why it's excluded]
- [Adjacent problems excluded from this phase] — [brief reason]

## Constraints

[Performance, compatibility, data volume, dependency, or platform constraints.
If none: "No additional constraints beyond standard project conventions."]

## Acceptance Criteria

- [ ] [Pass/fail criterion — unambiguous, verifiable]
- [ ] [Pass/fail criterion]
- [ ] [Pass/fail criterion]

[Every acceptance criterion must be a checkbox that resolves to PASS or FAIL.
No "should feel good", "looks reasonable", or "generally works" — those are not checkboxes.]

## Ambiguity Report

| Dimension          | Score | Min  | Status | Notes                              |
|--------------------|-------|------|--------|------------------------------------|
| Goal Clarity       |       | 0.75 |        |                                    |
| Boundary Clarity   |       | 0.70 |        |                                    |
| Constraint Clarity |       | 0.65 |        |                                    |
| Acceptance Criteria|       | 0.70 |        |                                    |
| **Ambiguity**      |       | ≤0.20|        |                                    |

Status: ✓ = met minimum, ⚠ = below minimum (planner treats as assumption)

## Interview Log

[Key decisions made during the Socratic interview. Format: round → question → answer → decision locked.]

| Round | Perspective    | Question summary         | Decision locked                    |
|-------|----------------|-------------------------|------------------------------------|
| 1     | Researcher     | [what was asked]        | [what was decided]                 |
| 2     | Simplifier     | [what was asked]        | [what was decided]                 |
| 3     | Boundary Keeper| [what was asked]        | [what was decided]                 |

[If --auto mode: note "auto-selected" decisions with the reasoning Claude used.]

---

*Phase: [XX-name]*
*Spec created: [date]*
*Next step: /gsd:discuss-phase [X] — implementation decisions (how to build what's specified above)*
```

<good_examples>

**Example 1: Feature addition (Post Feed)**

```markdown
# Phase 3: Post Feed — Specification

**Created:** 2025-01-20
**Ambiguity score:** 0.12
**Requirements:** 4 locked

## Goal

Users can scroll through posts from accounts they follow, with new posts available after pull-to-refresh.

## Background

The database has a `posts` table and `follows` table. No feed query or feed UI exists today. The home screen shows a placeholder "Your feed will appear here." This phase builds the feed query, API endpoint, and the feed list component.

## Requirements

1. **Feed query**: Returns posts from followed accounts ordered by creation time, descending.
   - Current: No feed query exists — `posts` table is queried directly only from profile pages
   - Target: `GET /api/feed` returns paginated posts from followed accounts, newest first, max 20 per page
   - Acceptance: Query returns correct posts for a user who follows 3 accounts with known post counts; cursor-based pagination advances correctly

2. **Feed display**: Posts display in a scrollable card list.
   - Current: Home screen shows static placeholder text
   - Target: Home screen renders feed cards with author, timestamp, post content, and reaction count
   - Acceptance: Feed renders without error for 0 posts (empty state shown), 1 post, and 20+ posts

3. **Pull-to-refresh**: User can refresh the feed manually.
   - Current: No refresh mechanism exists
   - Target: Pull-down gesture triggers refetch; new posts appear at top of list
   - Acceptance: After a new post is created in test, pull-to-refresh shows the new post without full app restart

4. **New posts indicator**: When new posts arrive, a banner appears instead of auto-scrolling.
   - Current: No such mechanism
   - Target: "3 new posts" banner appears when refetch returns posts newer than the oldest visible post; tapping banner scrolls to top and shows new posts
   - Acceptance: Banner appears for ≥1 new post, does not appear when no new posts, tap navigates to top

## Boundaries

**In scope:**
- Feed query (backend) — posts from followed accounts, paginated
- Feed list UI (frontend) — post cards with author, timestamp, content, reaction counts
- Pull-to-refresh gesture
- New posts indicator banner
