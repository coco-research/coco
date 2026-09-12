---
name: gsd-explore
description: "Use when the user wants to think through an idea before committing to a plan, e.g. /gsd-explore auth strategy. Runs a Socratic session, optionally spawns research, then routes output to notes, seeds, requirements, or new phases."
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
  - Task
  - AskUserQuestion
---

<objective>
Open-ended Socratic ideation session. Guides the developer through exploring an idea via
probing questions, optionally spawns research, then routes outputs to the appropriate GSD
artifacts (notes, todos, seeds, research questions, requirements, or new phases).

Accepts an optional topic argument: `/gsd-explore authentication strategy`
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/explore.md
</execution_context>

<process>
Execute the explore workflow from @$HOME/.claude/get-shit-done/workflows/explore.md end-to-end.
</process>
