# Fix typos and broken commands in README quickstart

**Type:** documentation
**Labels:** `good first issue`, `documentation`
**Estimated time:** 15 minutes

## Problem

A few people following the README quickstart have hit issues because the commands drift slightly from what `scripts/setup.sh` and `scripts/dev.sh` actually do. We need a careful pass that:

- Fixes any typos
- Makes the commands copy-pasteable on a fresh macOS or Linux machine
- Matches the actual flags used by `scripts/dev.sh` and `scripts/start.sh`

## Hint

- Read `README.md` end-to-end and try the quickstart on a fresh shell.
- Cross-reference each command against `scripts/setup.sh`, `scripts/dev.sh`, `scripts/start.sh`.
- Backticks around all commands, file paths, env vars.

## Files

- `README.md`
- (read only) `scripts/setup.sh`, `scripts/dev.sh`, `scripts/start.sh`

## Acceptance criteria

- [ ] Every command in the quickstart copies and runs without modification on a fresh checkout
- [ ] No broken relative links (verify with `grep -nE '\]\(\.\./|\]\(\./'`)
- [ ] Lint clean (no trailing whitespace, consistent fence style)
