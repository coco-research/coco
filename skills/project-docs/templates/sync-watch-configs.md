# .sync-watch.json Templates by Project Type

## Product

```json
{
  "project_name": "{{PROJECT_NAME}}",
  "watch_dirs": [
    "Meeting-Notes",
    "Research",
    "PRD",
    "Architecture"
  ],
  "target_docs": {
    "tier1": [
      {
        "path": "PRD/{{PRD_FILE}}",
        "name": "Product Requirements",
        "update_from": ["Meeting-Notes", "Research"],
        "what": "Requirements, user stories, decisions, architecture changes"
      },
      {
        "path": "CLAUDE.local.md",
        "name": "Project Memory",
        "update_from": ["*"],
        "what": "New files, folder changes, key decisions, recent changes log"
      }
    ],
    "tier2": [
      {
        "path": "PRD/PRD-Presentation.html",
        "name": "PRD Presentation",
        "update_from": ["PRD"],
        "what": "Sync with PRD changes"
      }
    ]
  },
  "ignore_patterns": [".*", "*.tmp", "~$*"],
  "file_types": [".md", ".html", ".docx", ".xlsx", ".pdf"]
}
```

## Consulting

```json
{
  "project_name": "{{PROJECT_NAME}}",
  "watch_dirs": [
    "Meeting-Notes",
    "Research",
    "Source-Documents"
  ],
  "target_docs": {
    "tier1": [
      {
        "path": "Presentations/{{DECK_FILE}}",
        "name": "Main Presentation",
        "update_from": ["Meeting-Notes", "Research"],
        "what": "New stakeholders, decisions, findings, status updates"
      },
      {
        "path": "CLAUDE.local.md",
        "name": "Project Memory",
        "update_from": ["*"],
        "what": "New files, folder changes, key decisions, recent changes log"
      }
    ],
    "tier2": [
      {
        "path": "Data/Stakeholder-Directory.xlsx",
        "name": "Stakeholder Directory",
        "update_from": ["Meeting-Notes"],
        "what": "New contacts mentioned in meetings"
      }
    ]
  },
  "ignore_patterns": [".*", "*.tmp", "~$*"],
  "file_types": [".md", ".html", ".docx", ".xlsx", ".pdf"]
}
```

## Implementation

```json
{
  "project_name": "{{PROJECT_NAME}}",
  "watch_dirs": [
    "Meeting-Notes",
    "Research",
    "PRD",
    "Architecture",
    "Verification",
    "Source-Documents"
  ],
  "target_docs": {
    "tier1": [
      {
        "path": "PRD/{{PRD_FILE}}",
        "name": "Product Requirements",
        "update_from": ["Meeting-Notes", "Research", "Verification"],
        "what": "Requirements, design decisions, verification findings"
      },
      {
        "path": "Presentations/{{DECK_FILE}}",
        "name": "Main Presentation",
        "update_from": ["Meeting-Notes", "Research", "PRD"],
        "what": "Stakeholders, decisions, timeline, architecture"
      },
      {
        "path": "CLAUDE.local.md",
        "name": "Project Memory",
        "update_from": ["*"],
        "what": "New files, folder changes, key decisions, recent changes log"
      }
    ],
    "tier2": [
      {
        "path": "PRD/PRD-Presentation.html",
        "name": "PRD Presentation",
        "update_from": ["PRD"],
        "what": "Sync with PRD changes"
      },
      {
        "path": "Data/Stakeholder-Directory.xlsx",
        "name": "Stakeholder Directory",
        "update_from": ["Meeting-Notes"],
        "what": "New contacts mentioned in meetings"
      }
    ]
  },
  "ignore_patterns": [".*", "*.tmp", "~$*"],
  "file_types": [".md", ".html", ".docx", ".xlsx", ".pdf"]
}
```

## Governance

```json
{
  "project_name": "{{PROJECT_NAME}}",
  "watch_dirs": [
    "Meeting-Notes",
    "Research",
    "Framework/Controls",
    "Framework/Risks",
    "Framework/Policies"
  ],
  "target_docs": {
    "tier1": [
      {
        "path": "Framework/{{FRAMEWORK_FILE}}",
        "name": "Governance Framework",
        "update_from": ["Meeting-Notes", "Research", "Framework"],
        "what": "Controls, risks, policies, regulatory changes"
      },
      {
        "path": "CLAUDE.local.md",
        "name": "Project Memory",
        "update_from": ["*"],
        "what": "New files, folder changes, key decisions, recent changes log"
      }
    ],
    "tier2": [
      {
        "path": "Presentations/{{DECK_FILE}}",
        "name": "Governance Deck",
        "update_from": ["Meeting-Notes", "Framework"],
        "what": "Status updates, risk changes, compliance progress"
      }
    ]
  },
  "ignore_patterns": [".*", "*.tmp", "~$*"],
  "file_types": [".md", ".html", ".docx", ".xlsx", ".pdf"]
}
```
