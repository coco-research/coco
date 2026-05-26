# Add empty-state illustration to DraftsPage

**Type:** enhancement
**Labels:** `good first issue`, `enhancement`, `frontend`, `ux`
**Estimated time:** 30 minutes

## Problem

`DraftsPage` currently shows a bare "No drafts" string when the drafts list is empty. New users land here and aren't sure if something is broken or just empty. We want a friendly empty state with:

- A small illustration or icon (use an existing Lucide icon, e.g. `FileText` or `Inbox`)
- A one-line headline ("No drafts yet")
- A one-line subtitle hinting at what creates drafts
- A primary CTA button linking to the relevant action (or, if no action exists, omit it)

## Hint

- Look at how other pages render empty states (search `frontend/src/` for `"empty"` or `EmptyState`).
- If a reusable `<EmptyState>` component exists, use it. Otherwise inline a simple `flex flex-col items-center` block.
- Match the existing Radix + Tailwind styling — no new dependencies.

## Files

- `frontend/src/pages/DraftsPage.tsx` (or `.jsx`)
- Possibly `frontend/src/components/EmptyState.tsx` if reusing/creating one

## Acceptance criteria

- [ ] When `drafts.length === 0`, the page renders the new empty state
- [ ] Layout is centered vertically in the content area, not jammed against the top
- [ ] No console warnings; no a11y violations (`aria-label` on icons that aren't decorative)
- [ ] Renders on light theme and looks good
