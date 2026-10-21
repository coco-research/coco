---
allowed-tools: Bash, Read
argument-hint: "<path to a .docx, .xlsx, or .pptx> <what to do>"
description: Read, edit, and render a Word, Excel, or PowerPoint file with officecli
---

# /officecli

Load the `officecli` skill (`skills/officecli/SKILL.md`) and follow it.

1. Run `command -v officecli`. If it is missing, tell the user to run `brew install officecli` and stop. Do not install officecli any other way. Do not run `officecli install`.
2. Run every officecli call as `OFFICECLI_SKIP_UPDATE=1 officecli …`. Prefix each call. The shell environment does not persist between tool calls.
3. Apply the task in $ARGUMENTS: a path to a `.docx`, `.xlsx`, or `.pptx`, and what to do with it.
4. Finish with the render, look, fix loop. Render with `OFFICECLI_SKIP_UPDATE=1 officecli view <file> html`, read the result, fix, and repeat until it looks right.
