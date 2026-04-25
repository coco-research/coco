---
description: "Show latest emails from a specific person. Usage: /email-read alice"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# /email-read — Read emails from a person

Parse the argument as a sender name. Use the `/email` skill with subcommand `read` and the provided name.

Invoke the Skill tool: `email` with args `read <name from argument>`.
