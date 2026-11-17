<purpose>
Clarify WHAT a phase delivers through a Socratic interview loop with quantitative ambiguity scoring.
Produces a SPEC.md with falsifiable requirements that discuss-phase treats as locked decisions.

This workflow handles "what" and "why" — discuss-phase handles "how".
</purpose>

<ambiguity_model>
Score each dimension 0.0 (completely unclear) to 1.0 (crystal clear):

| Dimension         | Weight | Minimum | What it measures                                  |
|-------------------|--------|---------|---------------------------------------------------|
| Goal Clarity      | 35%    | 0.75    | Is the outcome specific and measurable?           |
| Boundary Clarity  | 25%    | 0.70    | What's in scope vs out of scope?                  |
| Constraint Clarity| 20%    | 0.65    | Performance, compatibility, data requirements?    |
| Acceptance Criteria| 20%   | 0.70    | How do we know it's done?                         |

**Ambiguity score** = 1.0 − (0.35×goal + 0.25×boundary + 0.20×constraint + 0.20×acceptance)

**Gate:** ambiguity ≤ 0.20 AND all dimensions ≥ their minimums → ready to write SPEC.md.

A score of 0.20 means 80% weighted clarity — enough precision that the planner won't silently make wrong assumptions.
</ambiguity_model>

<interview_perspectives>
Rotate through these perspectives — each naturally surfaces different blindspots:

**Researcher (rounds 1–2):** Ground the discussion in current reality.
- "What exists in the codebase today related to this phase?"
- "What's the delta between today and the target state?"
- "What triggers this work — what's broken or missing?"

**Simplifier (round 2):** Surface minimum viable scope.
- "What's the simplest version that solves the core problem?"
- "If you had to cut 50%, what's the irreducible core?"
- "What would make this phase a success even without the nice-to-haves?"

**Boundary Keeper (round 3):** Lock the perimeter.
- "What explicitly will NOT be done in this phase?"
- "What adjacent problems is it tempting to solve but shouldn't?"
- "What does 'done' look like — what's the final deliverable?"

**Failure Analyst (round 4):** Find the edge cases that invalidate requirements.
- "What's the worst thing that could go wrong if we get the requirements wrong?"
- "What does a broken version of this look like?"
- "What would cause a verifier to reject the output?"

**Seed Closer (rounds 5–6):** Lock remaining undecided territory.
- "We have [dimension] at [score] — what would make it completely clear?"
- "The remaining ambiguity is in [area] — can we make a decision now?"
- "Is there anything you'd regret not specifying before planning starts?"
</interview_perspectives>

<process>

## Step 1: Initialize

```bash
INIT=$(node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" init phase-op "${PHASE}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Parse JSON for: `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`, `state_path`, `requirements_path`, `roadmap_path`, `planning_path`, `response_language`, `commit_docs`.

**If `response_language` is set:** All user-facing text in this workflow MUST be in `{response_language}`. Technical terms, code, and file paths stay in English.

**If `phase_found` is false:**
```
Phase [X] not found in roadmap.
Use /gsd:progress to see available phases.
```
Exit.

**Check for existing SPEC.md:**
```bash
ls ${phase_dir}/*-SPEC.md 2>/dev/null | grep -v AI-SPEC | head -1 || true
```

If SPEC.md already exists:

**If `--auto`:** Auto-select "Update it". Log: `[auto] SPEC.md exists — updating.`

**Otherwise:** Use AskUserQuestion:
- header: "Spec"
- question: "Phase [X] already has a SPEC.md. What do you want to do?"
- options:
  - "Update it" — Revise and re-score
  - "View it" — Show current spec
  - "Skip" — Exit (use existing spec as-is)

If "View": Display SPEC.md, then offer Update/Skip.
If "Skip": Exit with message: "Existing SPEC.md unchanged. Run /gsd:discuss-phase [X] to continue."
If "Update": Load existing SPEC.md, continue to Step 3.

## Step 2: Scout Codebase

**Read these files before any questions:**
- `{requirements_path}` — Project requirements
- `{state_path}` — Decisions already made, current phase, blockers
- ROADMAP.md phase entry — Phase description, goals, canonical refs

**Grep the codebase** for code/files relevant to this phase goal. Look for:
- Existing implementations of similar functionality
- Integration points where new code will connect
- Test coverage gaps relevant to the phase
- Prior phase artifacts (SUMMARY.md, VERIFICATION.md) that inform current state

**Synthesize current state** — the grounded baseline for the interview:
