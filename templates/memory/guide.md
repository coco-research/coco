# Persistent Memory Guide

> Give your AI assistant institutional knowledge so it never starts from zero.

## Why Memory Matters

Every AI session begins with a blank slate. Without memory, you re-explain your project, your stack, your naming conventions, and your past decisions every single time. This is the single biggest source of wasted time when working with AI assistants.

Persistent memory solves this by giving the AI two files it reads at the start of every session: one that knows who you are across all projects, and one that knows everything about the current project.

**The ROI is immediate.** After one session of setup, every future session skips the first 5-10 minutes of context-setting. Over weeks and months, this compounds into hours saved and dramatically better output quality because the AI grounds its responses in your actual decisions, not generic assumptions.

## Two Layers of Memory

### Global Memory (Cross-Project)

A single file that travels with you across every project. It stores:

- **Your preferences** — coding style, communication style, frameworks you prefer
- **Common commands** — the shell commands you run in every project
- **Patterns and conventions** — naming conventions, architecture patterns, formatting rules
- **Lessons learned** — mistakes you or the AI made that should never be repeated

This file lives outside any project directory (e.g., `~/.claude/CLAUDE.md`) so every project session can access it.

### Project Memory (Project-Specific)

A file in each project root that stores everything specific to that project:

- **Overview** — what the project does, what stack it uses, when it started
- **Architecture** — entry points, folder structure, key dependencies
- **Key decisions** — every significant choice with the date and rationale
- **Recent changes** — a running log of what files changed and why
- **Open questions** — unresolved items that need future attention
- **Commands** — dev, build, test, deploy commands for this specific project

This file lives in the project root (e.g., `CLAUDE.local.md`) and is typically gitignored since it contains personal workflow notes.

## What to Store

The most valuable things to put in memory are:

1. **Decisions with dates and rationale.** Not just "we use PostgreSQL" but "[2026-01-15] Chose PostgreSQL over DynamoDB — need complex joins for reporting, team has SQL expertise, cost is predictable." When the AI sees this, it stops suggesting DynamoDB alternatives.

2. **Architecture choices.** Where the entry point is, how folders are organized, what each key module does. This prevents the AI from creating files in the wrong place or misunderstanding the project structure.

3. **Lessons learned.** "useEffect dependency arrays must include all referenced state variables — we had a stale data bug on 2026-02-17 from a missing dep." The AI will check dependency arrays carefully after reading this.

4. **Common commands.** The AI can run your build, test, and lint commands without asking if they are in memory.

5. **Recent changes.** A timestamped log of what changed and why. This gives the AI a "what happened recently" context that prevents it from undoing recent work or duplicating effort.

## What NOT to Store

- **Secrets, API keys, passwords, or tokens.** Memory files can be accidentally shared or committed. Use environment variables for all credentials.
- **Entire file contents.** Memory should be a summary and index, not a mirror of your codebase.
- **Stale information.** Review and prune monthly. Outdated decisions are worse than no decisions because they actively mislead.

## Maintenance Habits

- **Update after every session.** If the AI made a decision, changed architecture, or learned something, it should be in memory before the session ends.
- **Date every entry.** Use `[YYYY-MM-DD]` format so you can tell at a glance how fresh the information is.
- **Review monthly.** Delete entries that are no longer relevant. Move completed open questions to decisions. Archive old recent changes.
- **Keep it concise.** Memory files that grow beyond 200-300 lines become noisy. Summarize older entries and keep only what the AI needs to make good decisions today.

## Tool-Specific Setup

Memory works across AI coding tools, but the setup differs slightly:

- **Cursor setup:** See `cursor/README.md` for Cursor-specific memory configuration, including rules that auto-read and auto-update memory files.
- **Claude Code setup:** See `claude-code/README.md` for Claude Code configuration. Claude Code auto-loads `~/.claude/CLAUDE.md` and `CLAUDE.local.md` natively — no extra setup needed.

## Templates

Ready-to-copy templates are available in this directory:

- `global-memory-template.md` — Copy to `~/.claude/CLAUDE.md` and fill in your preferences
- `project-memory-template.md` — Copy to your project root as `CLAUDE.local.md` and fill in project details
