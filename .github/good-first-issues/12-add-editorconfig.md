# Add `.editorconfig` to repo root

**Type:** enhancement
**Labels:** `good first issue`, `enhancement`, `tooling`
**Estimated time:** 15 minutes

## Problem

Contributors using different editors (VS Code, Cursor, JetBrains, Vim) end up producing files with mixed indentation, trailing-whitespace, and line-ending styles. A repo-root `.editorconfig` makes this consistent automatically across editors that support it (most do).

## Hint

Create `.editorconfig` with sensible defaults:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

Match the existing style — if Python files in this repo use 4 spaces (they do), reflect that.

## Files

- `.editorconfig` (new, repo root)

## Acceptance criteria

- [ ] File exists at the repo root with `root = true`
- [ ] Python override uses 4 spaces
- [ ] No existing files reformatted in this PR (the config only affects new edits)
