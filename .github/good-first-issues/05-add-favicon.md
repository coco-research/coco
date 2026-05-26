# Add favicon to frontend

**Type:** enhancement
**Labels:** `good first issue`, `enhancement`, `frontend`
**Estimated time:** 15 minutes

## Problem

The CoCo Platform frontend currently shows the default Vite favicon in the browser tab. We want a proper CoCo favicon so the app is identifiable when users have multiple tabs open.

## Hint

- Drop a 32x32 (and ideally 192x192 + apple-touch-icon 180x180) PNG into `frontend/public/`.
- Update `frontend/index.html` `<link rel="icon" ...>` entries.
- If you don't have a design, use a simple monogram "C" on the brand color. Any free CC0 icon is fine for the first draft.

## Files

- `frontend/public/favicon.png` (new) — and `apple-touch-icon.png` if you want to be thorough
- `frontend/index.html`

## Acceptance criteria

- [ ] `pnpm dev` shows the new favicon in the tab
- [ ] No 404s in DevTools network panel for icon files
- [ ] Old `vite.svg` reference removed from `index.html`
