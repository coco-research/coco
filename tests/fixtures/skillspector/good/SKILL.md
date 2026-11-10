---
name: skillspector-good-fixture
description: Clean fixture for the skill-scan workflow. Never installed, never indexed.
---

# Good fixture: read a changelog and summarise it

This file exists only for `.github/workflows/skill-scan.yml` and
`tests/fixtures/skillspector/`. It is not a Coco skill: no manifest lists it, no adapter
installs it, and `scripts/build-index.py` does not index it.

## What it does

1. Read the changelog at the repository root.
2. Group the entries under Added, Changed, Fixed and Removed.
3. Print the grouped list to the terminal.

## How

Read the file with an editor or a pager. Nothing here downloads, installs, executes or
publishes anything, which is why the scan must report no finding for this folder.
