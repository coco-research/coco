# Document `~/.coco/` directory layout

**Type:** documentation
**Labels:** `good first issue`, `documentation`
**Estimated time:** 30 minutes

## Problem

CoCo writes a handful of files under `~/.coco/` (`brain.json`, `queue.json`, `config.json`, `sessions/`, `events.jsonl`, `platform.db`, `.qb-gateway-key`). New contributors keep asking what each file does, when it's written, and whether it's safe to delete. There's no single doc.

## Hint

- Create `docs/coco-directory.md` (new file).
- For each path: 1-line purpose, who writes it, who reads it, whether it's safe to delete, atomic-write notes.
- Use the bullets in `CLAUDE.local.md` ("Existing Data Stores") as the starting point — but expand each with a short explanation.

## Files

- `docs/coco-directory.md` (new)
- `docs/README.md` or top-level `README.md` — add a link to the new page

## Acceptance criteria

- [ ] New doc covers every file/directory under `~/.coco/`
- [ ] Each entry says: purpose, writer, reader, safe-to-delete?
- [ ] Linked from the docs index
- [ ] Markdown lints clean
