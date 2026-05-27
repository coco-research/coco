# Add `--version` flag to CLI

**Type:** enhancement
**Labels:** `good first issue`, `enhancement`, `cli`
**Estimated time:** 15 minutes

## Problem

The `coco` CLI currently has no `--version` / `-V` flag. Users have to inspect `pyproject.toml` or git history to know which version they are running, which makes bug reports harder to triage.

## Hint

- The CLI entry point lives in `cli/`. Look for a `main()` or argparse/Click setup.
- Read the version from `cli/__init__.py` (`__version__`) or from `importlib.metadata.version("coco")` so we don't duplicate the literal.
- If you use `argparse`, the one-liner is `parser.add_argument("--version", action="version", version=f"coco {__version__}")`.

## Files

- `cli/__init__.py` (read `__version__`)
- `cli/main.py` or the equivalent entry point under `cli/`

## Acceptance criteria

- [ ] `coco --version` prints `coco <version>` and exits 0
- [ ] `coco -V` works the same way
- [ ] The printed version matches the one declared in `pyproject.toml`
- [ ] No new dependencies added
