---
description: "Set up automated sync for a new project folder: email monitoring (Outlook), file change detection, and auto-update of all documents (PRD, presentations, etc.) every 2 hours via cron. Run this in any project folder to get the same automation as other projects."
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
  - Skill
  - AskUserQuestion
---

# /pmstudio-sync-init — Set Up Automated Sync for a New Project Folder

This is an alias for `/project-sync init`. Run it inside any project folder to set up:

1. **Email extraction** — Searches Outlook via AppleScript (Legacy Outlook, primary) for project-specific emails by keywords, stakeholders, and subject patterns. Falls back to MIME cache + HxStore binary extraction if AppleScript fails (New Outlook).
2. **File monitoring** — Detects new meeting notes, research docs, source files in watched directories
3. **Sync report** — Generates `.sync-report.md` listing what changed and which docs need updating
4. **Auto-update** — Claude CLI (`claude -p`, Sonnet, $2 budget cap) reads new content and updates all structured documents (PRD, presentations, architecture, roadmap, etc.)
5. **Persistent cron job** — Runs every 2 hours in background, persists across terminal closes and reboots

## The 4-Step Pipeline (every 2 hours)

```
Step 1: Email Search (AppleScript → Outlook inbox/sent)
  ↓ new emails saved to project emails folder
Step 2: File Detection (scan watched dirs for new/modified files)
  ↓ changes detected
Step 3: Sync Report (.sync-report.md generated)
  ↓ lists changed files + which docs need updating
Step 4: Auto-Update (Claude CLI reads changes, updates all target docs)
  ↓ documents updated, sync report deleted
```

## What it creates

| File | Location | Purpose |
|------|----------|---------|
| `.sync-watch.json` | Project root | Config: keywords, senders, watch dirs, target docs, auto-update budget |
| `run-sync-<name>.sh` | `~/.claude/scripts/` | Wrapper script (avoids OneDrive `&` path issues in launchd XML) |
| `com.claude.project-sync.<name>.plist` | `~/Library/LaunchAgents/` | launchd cron job (every 2 hours) |
| State cache | `~/.claude/state/<project>/` | Timestamps, logs, cached config, auto-update logs |

## `.sync-watch.json` Full Schema

```json
{
  "project_name": "Project Name",
  "watch_dirs": ["emails", "docs", "Meeting-Notes"],
  "target_docs": {
    "tier1": [
      {
        "path": "docs/PRD.html",
        "name": "PRD",
        "update_from": ["emails", "Meeting-Notes"],
        "what": "New requirements, stakeholder feedback, decisions"
      }
    ],
    "tier2": [
      {
        "path": "docs/Presentation.html",
        "name": "Stakeholder Deck",
        "update_from": ["PRD"],
        "what": "Sync with PRD changes"
      }
    ]
  },
  "email_search": {
    "enabled": true,
    "keywords": ["project name", "jira-id", "product name"],
    "senders": ["stakeholder_name", "another_name"],
    "subject_patterns": ["RE: Known Thread Subject"],
    "dest_dir": "emails",
    "format": "txt"
  },
  "auto_update": {
    "enabled": true,
    "model": "sonnet",
    "max_budget_usd": 2.00
  },
  "ignore_patterns": [".*", "*.tmp", "~$*"],
  "file_types": [".md", ".html", ".docx", ".xlsx", ".pdf", ".eml", ".txt"]
}
```

## Init Process

### Step 1: Gather project info
Ask the user for (or infer from existing files like CLAUDE.local.md, existing emails, folder structure):
1. **Project name**
2. **Email search keywords** — project-specific terms (product names, Jira IDs, codenames)
3. **Key stakeholders/senders** — names to filter emails by
4. **Subject patterns** — known email thread subjects
5. **Watch directories** — folders to monitor (emails, meeting notes, research, etc.)
6. **Target documents** — tier1 (critical) and tier2 (secondary) docs to auto-update
7. **Email destination folder** — where to save discovered emails
8. **Email format** — `txt` (default) or `eml`
9. **Auto-update settings** — model (`sonnet` default), budget ($2.00 default)

### Step 2: Create `.sync-watch.json` in project root

### Step 3: Create wrapper script
Write `~/.claude/scripts/run-sync-<safe-name>.sh`:
```bash
#!/bin/bash
exec /bin/bash $HOME/.claude/scripts/project-sync-orchestrator.sh "/full/path/to/project"
```
**CRITICAL:** Use absolute paths (no `~`), quote the path (handles `&` in OneDrive paths).

### Step 4: Create launchd plist
Write `~/Library/LaunchAgents/com.claude.project-sync.<safe-name>.plist` with:
- ProgramArguments pointing to the wrapper script (NOT the project dir directly)
- StartInterval: 7200 (2 hours)
- RunAtLoad: true
- HOME env var set explicitly
- Log paths under `~/.claude/logs/`

### Step 5: Activate & cache
```bash
mkdir -p ~/.claude/logs ~/.claude/state
launchctl load ~/Library/LaunchAgents/com.claude.project-sync.<safe-name>.plist
```
Then run manually once to cache config:
```bash
/bin/bash ~/.claude/scripts/run-sync-<safe-name>.sh
```

### Step 6: Verify
`launchctl list | grep project-sync` — expect exit code 0.

## Email Search Details

**Primary: AppleScript (Legacy Outlook)**
- Full inbox + sent items access
- Searches by sender name/address, subject keywords, subject patterns
- Saves matching emails as `.txt` files with headers (Subject, From, Date)
- Deduplicates by checking if message date already exists in file
- Searches last 2000 messages per folder (messages are date-sorted, stops at timestamp)

**Fallback: MIME + HxStore (New Outlook)**
- Parses `~/Library/Group Containers/UBF8T346G9.Office/Outlook/.../MimeFiles/` for clean email files
- Scans `HxStore.hxd` binary for subject awareness (logged, not dumped)
- Used automatically if AppleScript fails

## Email Commands (also available)

These `/email-*` commands work alongside the sync cron:

| Command | What it does |
|---------|-------------|
| `/email-read <name>` | Show latest emails from a person |
| `/email-unread` | Show unread emails (count + top 20) |
| `/email-search <keywords>` | Search by subject keywords |
| `/email-today` | Today's emails grouped by hour |
| `/email-summary` | AI summary — decisions, action items |
| `/email-thread <subject>` | Full thread by subject |
| `/email-save <query> to <folder>` | Save emails to project folder |
| `/email-reply <subject>` | Draft a reply |

## Managing After Setup

- `/project-sync status` — Check last run, pending changes, auto-update results
- `/project-sync configure` — Edit keywords, senders, budget, watch dirs
- `/project-sync list` — Show all active sync jobs across projects
- `/project-sync teardown` — Remove cron job, plist, wrapper script

## Known Issues & Workarounds

1. **OneDrive `&` in path**: launchd XML chokes on `&` characters in folder names — solved by wrapper scripts
2. **launchd can't access OneDrive**: Config cached to `~/.claude/state/` — run manually once after config changes
3. **`~` doesn't expand in launchd**: All paths must be absolute
4. **HOME not set in launchd**: Must set HOME env var in plist
5. **Legacy Outlook sync delay**: After switching from New Outlook, full mailbox sync takes 30-60 min
6. **AppleScript sender access**: Use `set s to sender of msg` then `name of s` / `address of s` — NOT `name of sender of msg`
7. **Budget errors**: If Claude CLI says "Exceeded USD budget", increase `max_budget_usd` and re-cache config

---

Now invoke the `/project-sync` skill with the `init` subcommand:

Use the Skill tool to call `project-sync` with args `init`.
