# Add `prefers-reduced-motion` guard to wiki animations

**Type:** enhancement
**Labels:** `good first issue`, `enhancement`, `frontend`, `a11y`
**Estimated time:** 20 minutes

## Problem

Several wiki / knowledge pages use CSS transitions and Framer Motion animations (fade-in cards, slide-in panels). Users with `prefers-reduced-motion: reduce` set in their OS still see them, which is an accessibility regression.

## Hint

- For CSS: wrap animation rules in `@media (prefers-reduced-motion: no-preference) { ... }` or add a global `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }` in `frontend/src/index.css`.
- For Framer Motion: use the `useReducedMotion()` hook and skip animation variants when it returns `true`.

## Files

- `frontend/src/index.css` (or equivalent global stylesheet)
- Any wiki page components using Framer Motion — search `frontend/src/` for `from "framer-motion"`.

## Acceptance criteria

- [ ] With `prefers-reduced-motion: reduce` enabled in macOS Accessibility settings (or DevTools rendering tab), wiki pages render without animation
- [ ] Default (no preference) behavior is unchanged
- [ ] No console warnings
