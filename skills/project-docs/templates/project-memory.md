# Project Memory — {{PROJECT_NAME}}

## Overview
- Purpose: {{ONE_LINE_DESCRIPTION}}
- Type: {{PROJECT_TYPE}} (product/consulting/implementation/governance)
- Started: {{DATE}}

## Architecture
- Entry: {{PRIMARY_DELIVERABLE}}
- Structure: See Folder Structure below

## Folder Structure

```
{{PROJECT_NAME}}/
├── CLAUDE.local.md
├── .sync-watch.json
├── Meeting-Notes/
├── Research/
├── Source-Documents/
├── Data/
├── _temp/
│
{{ADDITIONAL_FOLDERS}}
```

### Routing Guide

| "I need..." | Go to |
|-------------|-------|
| Meeting notes | `Meeting-Notes/` |
| Research & analysis | `Research/` |
| The PRD | `PRD/` |
| The main presentation | `Presentations/` |
| Contracts, emails, vendor docs | `Source-Documents/` |
| Stakeholder contacts | `Data/` |
| Old presentation versions | `Presentations/_archive/` |

### File Naming Conventions
- **Meeting notes**: Date-first (`2026-03-10-{Stakeholder}.md`) for chronological sort
- **Research**: No date suffix (dates in content + file history)
- **New files**: Place in the relevant folder, matching sub-folder pattern

## Key Decisions
- [{{DATE}}] Project initialized with {{PROJECT_TYPE}} template

## Recent Changes
- [{{DATE}}] Project scaffolded — initial folder structure created

## Open Questions
-

## Commands
- N/A (documentation project, no build/test commands)

## Quality Protocol
- Verification: All stakeholder names cross-checked against source documents
- All dates verified against meeting timestamps
