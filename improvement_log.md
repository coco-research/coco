# Wiki UI Improvement Log

## Iteration 1
- change: Redesigned ProgramHealthBar from vertical list (8 rows with progress bars) to compact 3-column grid (6 cards with colored dots and borders). Reduced from ~40% viewport to ~15%.
- result: Briefing page now shows Program Health, What Changed, Attention Needed, Key Metrics, Upcoming, Highlights, AND Decision Timeline all visible in one scroll. Critical "Attention Needed" section moved from below-the-fold to prominently visible.
- next: Program names are raw slug prefixes ("Audit", "3pi", "AM1") — not human-readable. Also the Attention Badge says "2 attention" but the flyout interaction can't be tested via static screenshots.

## Iteration 2
- change: Fixed `entity_type` → `type` column name in 3 queries (project dashboard people, person card entity lookup, person card related people). Column was renamed in global_entities schema but new code used the old name.
- result: AB2 dashboard now shows 20 people with clickable name chips. Person card endpoint also fixed for entity lookup and related people queries.
- next: The empty state for decisions/tasks is prominent but the page still looks sparse. The Explore tab article list could benefit from attention.

## Iteration 3
- change: De-emphasized zero-value stat cards in ProjectDashboard — dimmed text/borders for 0-value stats (Decisions, Tasks) while keeping non-zero stats (People, Articles) at full brightness. Removed "0 pending" / "0 open" sub-labels that added noise.
- result: PM's eye now drawn to what the dashboard has (20 people, 194 articles) not what it lacks. Visual hierarchy improved.
- next: Decision Timeline on the Briefing page shows entries but dates say "Mon, Apr 5" style — should check if timeline date headers render correctly for grouping.

## Iteration 4
- change: Tightened DailyBriefing vertical spacing — section card padding reduced (p-5→p-4), header icon size (w-8→w-6), item spacing (space-y-3→space-y-1.5), outer padding (p-6→p-4), grid gap (gap-4→gap-3), section heading text (text-sm→text-xs).
- result: All 6 critical sections (Program Health, What Changed, Attention Needed, Key Metrics, Upcoming, Highlights) now fit above the fold in 1440×900 viewport. Decision Timeline visible just below. Information density dramatically improved — PM can see everything critical without scrolling.
- next: The Explore tab and People tab haven't been checked since the initial build. Final iteration should verify cross-view navigation works.

## Iteration 5
- change: Verified Explore tab (article list with filter bar), People tab (sortable table with importance bars), type-check (0 errors), backend (25 routes), and console errors (0). No code changes needed — all views render cleanly.
- result: All 4 tabs render correctly. Zero type errors, zero console errors, 25 backend routes load. Anti-Corruption project dashboard shows 20 people + 156 articles with proper visual hierarchy.
- next: (loop complete)

---

## Summary

5 iterations over the continuous improvement loop:
1. **Compact health bars** — vertical list → 3-column grid (viewport usage: 40% → 15%)
2. **Fixed people query** — entity_type → type column name (0 people → 20 people on AB2)
3. **Visual hierarchy** — dimmed zero-value stats so PM sees what exists, not what's missing
4. **Information density** — tightened spacing so all critical sections visible above the fold
5. **Verification** — zero type errors, zero console errors, all views rendering correctly

Before-and-after: The Briefing page went from a loading skeleton with 27 health bars dominating the viewport to a compact, information-dense dashboard where a PM can see program health, attention items, metrics, upcoming decisions, highlights, and a cross-project decision timeline — all in one scroll.

---

## Product Articles Pipeline (2026-04-14)

### Iteration 6 (Team Tags)
- change: Added `infobox_json` to articles list API + rendered team name as colored badge on product cards
- result: Product articles show team tags (Anti-Corruption, Privacy, Regulatory Compliance) for visual scanning
- next: Generate remaining 9 products

### Iteration 7 (25/25 Complete)
- change: Generated all 25 product articles — 16 from PRDs/docs, 4 from web research, 5 from overview slides
- result: 25/25 products in knowledge.db, all visible in wiki under Product filter with team tags
- next: Verify article detail view renders sections correctly

### Iteration 8 (Detail View Verified)
- change: None needed — verified article detail split view renders correctly
- result: TPI Tracker article shows full structured content: architecture sections, key features, workflows, wiki links highlighted in blue. All body_json sections render with proper heading hierarchy. Split panel layout works (list left, detail right).
- next: (loop complete — goal achieved)
