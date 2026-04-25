---
description: "Draft a reply to a specific email. Usage: /email-reply Project Phase 2 Contract Data"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# /email-reply — Draft a reply

Parse the argument as a subject to find. Use the `/email` skill with subcommand `reply-draft`.

Invoke the Skill tool: `email` with args `reply-draft <subject from argument>`.
