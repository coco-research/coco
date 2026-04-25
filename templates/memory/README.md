# Persistent Memory System

AI assistants start every session with zero context. Persistent memory fixes this by maintaining two markdown files that your AI reads at the start of each session and updates as you work.

## How It Works

1. **Session start** — AI reads both memory files to restore context
2. **During work** — AI updates memory when decisions are made, bugs are fixed, or new context emerges
3. **Session end** — Memory persists for the next session automatically

## Files

| File | Scope | Location | Purpose |
|------|-------|----------|---------|
| Global memory | All projects | `~/.claude/CLAUDE.md` or equivalent | Your role, preferences, tools, lessons learned |
| Project memory | One project | `CLAUDE.local.md` in project root | Tech stack, decisions, active work, recent changes |

## Templates

- [Global Memory Template](global-memory-template.md) — Starting point for `~/.claude/CLAUDE.md`
- [Project Memory Template](project-memory-template.md) — Starting point for `CLAUDE.local.md`

## Deep Dive

- [Memory Guide](guide.md) — Full guide with maintenance habits, what to store, and anti-patterns

## Quick Setup

1. Copy the global template to `~/.claude/CLAUDE.md`
2. Copy the project template to `CLAUDE.local.md` in your project root
3. Fill in your role, tools, and current project context
4. Date all entries with `[YYYY-MM-DD]` format
5. Keep files under 200-300 lines (trim old entries regularly)
