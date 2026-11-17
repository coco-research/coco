<purpose>

Mark a shipped version (v1.0, v1.1, v2.0) as complete. Creates historical record in MILESTONES.md, performs full PROJECT.md evolution review, reorganizes ROADMAP.md with milestone groupings, and tags the release in git.

</purpose>

<required_reading>

1. templates/milestone.md
2. templates/milestone-archive.md
3. `.planning/ROADMAP.md`
4. `.planning/REQUIREMENTS.md`
5. `.planning/PROJECT.md`

</required_reading>

<archival_behavior>

When a milestone completes:

1. Extract full milestone details to `.planning/milestones/v[X.Y]-ROADMAP.md`
2. Archive requirements to `.planning/milestones/v[X.Y]-REQUIREMENTS.md`
3. Update ROADMAP.md — overwrite in place with milestone grouping (preserve Backlog section)
4. Safety commit archive files + updated ROADMAP.md, then `git rm REQUIREMENTS.md` (fresh for next milestone)
5. Perform full PROJECT.md evolution review
6. Offer to create next milestone inline
7. Archive UI artifacts (`*-UI-SPEC.md`, `*-UI-REVIEW.md`) alongside other phase documents
8. Clean up `.planning/ui-reviews/` screenshot files (binary assets, never archived)

**Context Efficiency:** Archives keep ROADMAP.md constant-size and REQUIREMENTS.md milestone-scoped.

**ROADMAP archive** uses `templates/milestone-archive.md` — includes milestone header (status, phases, date), full phase details, milestone summary (decisions, issues, tech debt).

**REQUIREMENTS archive** contains all requirements marked complete with outcomes, traceability table with final status, notes on changed requirements.

</archival_behavior>

<process>

<step name="pre_close_artifact_audit">
Before proceeding with milestone close, run the comprehensive open artifact audit.

```bash
gsd-sdk query audit-open
```

If the output contains open items (any section with count > 0):

Display the full audit report to the user.

Then ask:
