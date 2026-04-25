---
description: "Save matching emails to a project folder for sync processing. Usage: /email-save alice to emails/"
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# /email-save — Save emails to project folder

Parse the argument for sender/subject and target folder. Use the `/email` skill with subcommand `save`.

Invoke the Skill tool: `email` with args `save <argument>`.
