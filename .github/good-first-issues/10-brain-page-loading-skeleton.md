# Add loading skeleton to `BrainPage`

**Type:** enhancement
**Labels:** `good first issue`, `enhancement`, `frontend`, `ux`
**Estimated time:** 30 minutes

## Problem

`BrainPage` fetches entities, decisions, and events on mount. While the queries are in flight (often 200–600ms on cold start), the page shows a blank screen, which feels broken. We want a Tailwind shimmer skeleton matching the eventual layout (header, stats row, list rows).

## Hint

- TanStack Query's `isPending` / `isLoading` flags identify the loading state.
- Use a simple `animate-pulse bg-muted rounded h-N` block per skeleton item.
- If a `<Skeleton>` primitive already exists under `frontend/src/components/ui/`, reuse it (shadcn convention).

## Files

- `frontend/src/pages/BrainPage.tsx`
- Possibly `frontend/src/components/ui/skeleton.tsx` if a primitive already exists

## Acceptance criteria

- [ ] On a cold page load, a skeleton renders instead of a blank area
- [ ] Skeleton roughly matches the final layout dimensions (no layout shift on data arrival)
- [ ] Skeleton respects `prefers-reduced-motion` (no shimmer if user prefers reduced motion)
