---
name: gsd-do
description: "Use when you know what you want but not which /gsd-* command to run. Routes freeform text to the best matching GSD command, confirms the match, then hands off without doing the work itself."
argument-hint: "<description of what you want to do>"
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
---

<objective>
Analyze freeform natural language input and dispatch to the most appropriate GSD command.

Acts as a smart dispatcher — never does the work itself. Matches intent to the best GSD command using routing rules, confirms the match, then hands off.

Use when you know what you want but don't know which `/gsd-*` command to run.
</objective>

<context>
$ARGUMENTS
</context>

<process>
Execute the do workflow end-to-end.
Route user intent to the best GSD command and invoke it.
</process>
