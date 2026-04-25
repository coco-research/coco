# Recommended plugins

Coco focuses on the artifacts you'd write yourself: skills, agents, commands, workflows, rules. The wider ecosystem provides excellent third-party plugins that complement Coco. These are **not bundled** with Coco — install them separately if useful.

## Anthropic / Claude Code official

| Plugin | What | Where |
|--------|------|-------|
| anthropic-skills (xlsx, docx, pdf, pptx) | Document I/O | Claude Code marketplace |
| anthropic-skills (skill-creator) | Build new skills | Claude Code marketplace |
| anthropic-skills (consolidate-memory) | Memory hygiene | Claude Code marketplace |
| anthropic-skills (schedule) | Scheduled tasks / cron | Claude Code marketplace |
| code-review | PR review skill | Claude Code marketplace |
| feature-dev | Guided feature development | Claude Code marketplace |
| pdf-viewer | Interactive PDF viewer | Claude Code marketplace |

## Domain packs

| Plugin | What |
|--------|------|
| design pack | UX, accessibility, design-system audits |
| engineering pack | Code review, architecture, debugging |
| product-management pack | PRD, roadmap, sprint planning |
| finance pack | Journal entries, reconciliation, SOX |

These provide namespaced skills (`/design:user-research`, `/engineering:code-review`, `/product-management:write-spec`, `/finance:reconciliation`, etc.) that complement Coco's foundational + personal layers.

## Quality-of-life

| Plugin | What |
|--------|------|
| caveman | Compress AI output to terse style (token saver) |
| hookify | Create hooks to prevent unwanted AI behavior |
| ralph-loop | Long-running iterative agent loops |
| frontend-design | Distinctive frontend with strong design opinions |

## Setup

In Claude Code:

```
/plugin install <plugin-name>
```

In Cursor: see Cursor's official plugin docs.

In Codex / generic: most plugins are Claude Code-specific. Check each plugin's README for cross-IDE support.

## MCP servers

Coco does not bundle MCP servers. The public ecosystem covers everything:

- **Server registry**: https://github.com/modelcontextprotocol/servers
- **Anthropic curated catalog**: in your IDE settings
- **AGENTS.md spec**: https://agents.md/

Common picks:
- `@modelcontextprotocol/server-postgres` — SQL access
- `@modelcontextprotocol/server-filesystem` — sandboxed filesystem
- `mcp-atlassian` — Jira + Confluence
- `slack-mcp-server` — Slack channels + DMs

Wire them in your IDE's MCP config (`~/.claude/mcp.json`, `~/.cursor/mcp.json`, etc.) — not in Coco.
