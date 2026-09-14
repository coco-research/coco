---
name: gsd-set-profile
description: "Use when the user wants to switch the GSD model profile for agents: quality, balanced, budget, or inherit. Runs the gsd-tools config-set-model-profile command and shows its output verbatim."
argument-hint: "<profile (quality|balanced|budget|inherit)>"
allowed-tools:
  - Bash
---


Show the following output to the user verbatim, with no extra commentary:

!`node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" config-set-model-profile $ARGUMENTS --raw`
