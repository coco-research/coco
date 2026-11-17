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
```
These items are open. Choose an action:
[R] Resolve — stop and fix items, then re-run /gsd:complete-milestone
[A] Acknowledge all — document as deferred and proceed with close
[C] Cancel — exit without closing
```

If user chooses [A] (Acknowledge):
1. Re-run `gsd-sdk query audit-open --json` to get structured data
2. Write acknowledged items to STATE.md under `## Deferred Items` section:
   ```markdown
   ## Deferred Items

   Items acknowledged and deferred at milestone close on {date}:

   | Category | Item | Status |
   |----------|------|--------|
   | debug | {slug} | {status} |
   | quick_task | {slug} | {status} |
   ...
   ```
   Sanitize all slug and status values via `sanitizeForDisplay()` before writing. Never inject raw file content into STATE.md.
3. Record in MILESTONES.md entry: `Known deferred items at close: {count} (see STATE.md Deferred Items)`
4. Proceed with milestone close.

If output shows all clear (no open items): print `All artifact types clear.` and proceed.

SECURITY: Audit JSON output is structured data from the `audit-open` query handler (same JSON contract as legacy `gsd-tools.cjs audit-open`) — validated and sanitized at source. When writing to STATE.md, item slugs and descriptions are sanitized via `sanitizeForDisplay()` before inclusion. Never inject raw user-supplied content into STATE.md without sanitization.
</step>

<step name="verify_readiness">

**Use `roadmap analyze` for comprehensive readiness check:**

```bash
ROADMAP=$(gsd-sdk query roadmap.analyze)
```

This returns all phases with plan/summary counts and disk status. Use this to verify:
- Which phases belong to this milestone?
- All phases complete (all plans have summaries)? Check `disk_status === 'complete'` for each.
- `progress_percent` should be 100%.

**Requirements completion check (REQUIRED before presenting):**

Parse REQUIREMENTS.md traceability table:
- Count total v1 requirements vs checked-off (`[x]`) requirements
- Identify any non-Complete rows in the traceability table

Present:

```
Milestone: [Name, e.g., "v1.0 MVP"]

Includes:
- Phase 1: Foundation (2/2 plans complete)
- Phase 2: Authentication (2/2 plans complete)
- Phase 3: Core Features (3/3 plans complete)
- Phase 4: Polish (1/1 plan complete)

Total: {phase_count} phases, {total_plans} plans, all complete
Requirements: {N}/{M} v1 requirements checked off
```

**If requirements incomplete** (N < M):

```
⚠ Unchecked Requirements:

- [ ] {REQ-ID}: {description} (Phase {X})
- [ ] {REQ-ID}: {description} (Phase {Y})
```

MUST present 3 options:
1. **Proceed anyway** — mark milestone complete with known gaps
2. **Run audit first** — `/gsd:audit-milestone` to assess gap severity
3. **Abort** — return to development

If user selects "Proceed anyway": note incomplete requirements in MILESTONES.md under `### Known Gaps` with REQ-IDs and descriptions.

<config-check>

```bash
cat .planning/config.json 2>/dev/null || true
```

</config-check>

<if mode="yolo">

```
⚡ Auto-approved: Milestone scope verification
[Show breakdown summary without prompting]
Proceeding to stats gathering...
```

Proceed to gather_stats.

</if>

<if mode="interactive" OR="custom with gates.confirm_milestone_scope true">

```
Ready to mark this milestone as shipped?
(yes / wait / adjust scope)
```

Wait for confirmation.
- "adjust scope": Ask which phases to include.
- "wait": Stop, user returns when ready.

</if>

</step>

<step name="gather_stats">

Calculate milestone statistics:

```bash
git log --oneline --grep="feat(" | head -20
git diff --stat FIRST_COMMIT..LAST_COMMIT | tail -1
find . -name "*.swift" -o -name "*.ts" -o -name "*.py" | xargs wc -l 2>/dev/null || true
git log --format="%ai" FIRST_COMMIT | tail -1
git log --format="%ai" LAST_COMMIT | head -1
```

Present:

```
Milestone Stats:
- Phases: [X-Y]
- Plans: [Z] total
- Tasks: [N] total (from phase summaries)
- Files modified: [M]
- Lines of code: [LOC] [language]
- Timeline: [Days] days ([Start] → [End])
- Git range: feat(XX-XX) → feat(YY-YY)
```

</step>

<step name="extract_accomplishments">

Extract one-liners from SUMMARY.md files using summary-extract:

```bash
# For each phase in milestone, extract one-liner
for summary in .planning/phases/*-*/*-SUMMARY.md; do
  [ -e "$summary" ] || continue
  gsd-sdk query summary-extract "$summary" --fields one_liner --pick one_liner
done
```

Extract 4-6 key accomplishments. Present:

```
Key accomplishments for this milestone:
1. [Achievement from phase 1]
2. [Achievement from phase 2]
3. [Achievement from phase 3]
4. [Achievement from phase 4]
5. [Achievement from phase 5]
```

</step>

<step name="create_milestone_entry">

**Note:** MILESTONES.md entry is now created automatically by `gsd-sdk query milestone.complete` in the archive_milestone step. The entry includes version, date, phase/plan/task counts, and accomplishments extracted from SUMMARY.md files.

If additional details are needed (e.g., user-provided "Delivered" summary, git range, LOC stats), add them manually after the CLI creates the base entry.

</step>

<step name="evolve_project_full_review">

Full PROJECT.md evolution review at milestone completion.

Read all phase summaries:

```bash
cat .planning/phases/*-*/*-SUMMARY.md
```

**Full review checklist:**

1. **"What This Is" accuracy:**
   - Compare current description to what was built
   - Update if product has meaningfully changed

2. **Core Value check:**
   - Still the right priority? Did shipping reveal a different core value?
   - Update if the ONE thing has shifted

3. **Requirements audit:**

   **Validated section:**
   - All Active requirements shipped this milestone → Move to Validated
   - Format: `- ✓ [Requirement] — v[X.Y]`

   **Active section:**
   - Remove requirements moved to Validated
   - Add new requirements for next milestone
   - Keep unaddressed requirements

   **Out of Scope audit:**
   - Review each item — reasoning still valid?
   - Remove irrelevant items
   - Add requirements invalidated during milestone

4. **Context update:**
   - Current codebase state (LOC, tech stack)
   - User feedback themes (if any)
   - Known issues or technical debt

5. **Key Decisions audit:**
   - Extract all decisions from milestone phase summaries
   - Add to Key Decisions table with outcomes
   - Mark ✓ Good, ⚠️ Revisit, or — Pending

6. **Constraints check:**
   - Any constraints changed during development? Update as needed

Update PROJECT.md inline. Update "Last updated" footer:

```markdown
---
*Last updated: [date] after v[X.Y] milestone*
```

**Example full evolution (v1.0 → v1.1 prep):**

Before:

```markdown
## What This Is

A real-time collaborative whiteboard for remote teams.

## Core Value

Real-time sync that feels instant.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Canvas drawing tools
- [ ] Real-time sync < 500ms
- [ ] User authentication
- [ ] Export to PNG

### Out of Scope

- Mobile app — web-first approach
- Video chat — use external tools
```

After v1.0:

```markdown
## What This Is

A real-time collaborative whiteboard for remote teams with instant sync and drawing tools.

## Core Value

Real-time sync that feels instant.

## Requirements

### Validated

- ✓ Canvas drawing tools — v1.0
- ✓ Real-time sync < 500ms — v1.0 (achieved 200ms avg)
- ✓ User authentication — v1.0

### Active

- [ ] Export to PNG
- [ ] Undo/redo history
- [ ] Shape tools (rectangles, circles)

### Out of Scope

- Mobile app — web-first approach, PWA works well
- Video chat — use external tools
- Offline mode — real-time is core value

## Context

Shipped v1.0 with 2,400 LOC TypeScript.
Tech stack: Next.js, Supabase, Canvas API.
Initial user testing showed demand for shape tools.
```

**Step complete when:**

- [ ] "What This Is" reviewed and updated if needed
- [ ] Core Value verified as still correct
- [ ] All shipped requirements moved to Validated
- [ ] New requirements added to Active for next milestone
- [ ] Out of Scope reasoning audited
- [ ] Context updated with current state
- [ ] All milestone decisions added to Key Decisions
- [ ] "Last updated" footer reflects milestone completion

</step>

<step name="reorganize_roadmap">

Update `.planning/ROADMAP.md` — group completed milestone phases:

```markdown
# Roadmap: [Project Name]

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped YYYY-MM-DD)
- 🚧 **v1.1 Security** — Phases 5-6 (in progress)
- 📋 **v2.0 Redesign** — Phases 7-10 (planned)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED YYYY-MM-DD</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed YYYY-MM-DD
- [x] Phase 2: Authentication (2/2 plans) — completed YYYY-MM-DD
- [x] Phase 3: Core Features (3/3 plans) — completed YYYY-MM-DD
- [x] Phase 4: Polish (1/1 plan) — completed YYYY-MM-DD

</details>

### 🚧 v[Next] [Name] (In Progress / Planned)

- [ ] Phase 5: [Name] ([N] plans)
- [ ] Phase 6: [Name] ([N] plans)

## Progress

| Phase             | Milestone | Plans Complete | Status      | Completed  |
| ----------------- | --------- | -------------- | ----------- | ---------- |
| 1. Foundation     | v1.0      | 2/2            | Complete    | YYYY-MM-DD |
| 2. Authentication | v1.0      | 2/2            | Complete    | YYYY-MM-DD |
