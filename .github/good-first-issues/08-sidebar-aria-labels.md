# Add `aria-label` to icon-only buttons in sidebar

**Type:** enhancement
**Labels:** `good first issue`, `enhancement`, `frontend`, `a11y`
**Estimated time:** 20 minutes

## Problem

The collapsed sidebar shows icon-only buttons (no visible text). Screen readers announce these as "button" with no description, so they're unusable for keyboard/AT users. Lighthouse a11y audit flags these.

## Hint

- Find each `<button>` / `<IconButton>` in the sidebar component that renders only an icon.
- Add `aria-label="<destination or action>"`, e.g. `aria-label="Dashboard"`, `aria-label="Toggle sidebar"`.
- For decorative icons inside labeled buttons (text + icon), add `aria-hidden="true"` to the icon instead.

## Files

- `frontend/src/components/Sidebar.tsx` (or wherever the sidebar lives — search `frontend/src/` for "Sidebar")

## Acceptance criteria

- [ ] Every icon-only sidebar button has a meaningful `aria-label`
- [ ] Decorative icons inside labeled buttons have `aria-hidden="true"`
- [ ] Lighthouse a11y score for the dashboard does not regress (and ideally improves)
- [ ] Visual output is unchanged
