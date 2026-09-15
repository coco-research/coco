---
name: gsd-pr-branch
description: "Use when opening a pull request and the diff is cluttered with .planning/ commits. Creates a clean branch filtered of GSD planning artifacts so reviewers see only code changes."
argument-hint: "[target branch, default: main]"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---


<objective>
Create a clean branch suitable for pull requests by filtering out .planning/ commits
from the current branch. Reviewers see only code changes, not GSD planning artifacts.

This solves the problem of PR diffs being cluttered with PLAN.md, SUMMARY.md, STATE.md
changes that are irrelevant to code review.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/pr-branch.md
</execution_context>

<process>
Execute the pr-branch workflow from @$HOME/.claude/get-shit-done/workflows/pr-branch.md end-to-end.
</process>
