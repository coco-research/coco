# Replace inline hex colors with Tailwind tokens in `KnowledgeStats`

**Type:** enhancement
**Labels:** `good first issue`, `enhancement`, `frontend`, `design-system`
**Estimated time:** 30 minutes

## Problem

`KnowledgeStats` has a handful of inline hex colors (e.g. `style={{ color: "#1a73e8" }}`) that bypass the Tailwind 4 theme tokens. This drifts from the rest of the app and breaks future theming (dark mode, branding).

## Hint

- Identify each hex code in the component.
- Map them to the closest semantic token in `frontend/tailwind.config.*` or `frontend/src/index.css` (`@theme` block).
  - Brand blue `#1a73e8` → `text-primary` / `bg-primary`
  - Greys → `text-muted-foreground`, `text-foreground`, `border-border`
- Remove `style={{ color: ... }}` props in favor of `className` utilities.

## Files

- `frontend/src/components/KnowledgeStats.tsx` (or path under `frontend/src/`)
- (read only) `frontend/tailwind.config.*` and `frontend/src/index.css`

## Acceptance criteria

- [ ] No hex literals remain in the file
- [ ] Visual output matches before/after (compare in browser)
- [ ] No new dependencies
- [ ] `pnpm lint` passes
