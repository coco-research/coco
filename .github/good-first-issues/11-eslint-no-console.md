# Enable `no-console` in frontend ESLint config

**Type:** enhancement
**Labels:** `good first issue`, `enhancement`, `frontend`, `tooling`
**Estimated time:** 20 minutes

## Problem

Stray `console.log(...)` calls keep landing in PRs because our ESLint config doesn't flag them. We want to enable `no-console` as a warning (not error — error blocks dev), allow `warn`/`error` for legitimate logging, and clean up existing offenders.

## Hint

- Edit `frontend/eslint.config.*` (flat config). Add:
  ```js
  rules: {
    "no-console": ["warn", { allow: ["warn", "error"] }],
  }
  ```
- Run `pnpm lint` and either remove the flagged `console.log` calls or replace with a more specific level.
- Don't suppress with `eslint-disable` unless the call is intentional debug-only behind a flag.

## Files

- `frontend/eslint.config.js` (or `.ts`)
- Any file emitting `console.log` (cleanup pass)

## Acceptance criteria

- [ ] `pnpm lint` passes with the new rule enabled
- [ ] No `eslint-disable-next-line no-console` added without a trailing comment explaining why
- [ ] Production build still works
