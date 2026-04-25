# Brain — Project Knowledge Tracker

SQLite-based local knowledge layer. Tracks entities, relationships, decisions, tasks, threads, and events per project. Auto-generates a slim CLAUDE.local.md from the DB.

## Install

```bash
bash adapters/<your-ide>/install.sh --systems brain
```

This wires 6 brain skills (`brain`, `brain-init`, `brain-export`, `brain-rescan`, `brain-update`, `brain-wiki`) into your IDE.

## What it does

- **`brain`** — query entities, relationships, threads
- **`brain-init`** — create `project_brain.db` in current directory
- **`brain-update`** — end-of-session flush (extract entities, decisions, events)
- **`brain-export`** — regenerate CLAUDE.local.md auto section from DB
- **`brain-rescan`** — incremental rescan of project files for new/changed content
- **`brain-wiki`** — generate Wikipedia-style knowledge articles from DB

## State

`project_brain.db` (SQLite) lives in the project root. Add to `.gitignore` if you don't want to share team brain content.

## Why a separate system

Brain is opinionated about its data model and workflow. Users who don't want a local knowledge DB can skip it without losing core framework value.
