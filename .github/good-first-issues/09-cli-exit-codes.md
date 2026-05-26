# Surface CLI exit codes in README

**Type:** documentation
**Labels:** `good first issue`, `documentation`, `cli`
**Estimated time:** 15 minutes

## Problem

People wiring `coco` into shell scripts and cron jobs need to know which exit codes mean what. Currently we use `0` for success and `1` for "any error", but a few commands (`coco verify`, `coco approve`) actually return more granular codes. Nothing is documented.

## Hint

- Grep `cli/` for `sys.exit(` or `raise SystemExit(` and list every distinct exit code.
- Add a "Exit codes" section to the README (or to `docs/cli.md` if one exists, then link from README).
- One row per code: code, meaning, example commands that emit it.

## Files

- `README.md` — add new section, or
- `docs/cli.md` (create if not present, link from README)
- (read only) `cli/`

## Acceptance criteria

- [ ] Every exit code currently emitted by the CLI is documented
- [ ] Table format with code | meaning | example
- [ ] Linked from the README if placed in `docs/`
