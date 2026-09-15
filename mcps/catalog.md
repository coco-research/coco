# MCP Server Catalog
> Curated list of Model Context Protocol servers compatible with Coco

## How to Use
Each server file in `mcps/servers/` contains installation instructions, configuration examples, and integration notes specific to Coco's workflow system. Copy the relevant JSON block into your IDE's MCP settings file.

## Available Servers

| Server | File | Primary Use Case | Priority |
|--------|------|------------------|----------|
| Filesystem | [filesystem.md](servers/filesystem.md) | Sandboxed file access for agents | HIGH |
| PostgreSQL | [postgres.md](servers/postgres.md) | Database queries and schema inspection | HIGH |
| GitHub | [github.md](servers/github.md) | PR creation, issue tracking, repo management | HIGH |
| Atlassian | [atlassian.md](servers/atlassian.md) | Jira + Confluence integration | HIGH |
| Slack | [slack.md](servers/slack.md) | Team communication and notifications | MEDIUM |
| Notion | [notion.md](servers/notion.md) | Knowledge base and database sync | MEDIUM |
| Linear | [linear.md](servers/linear.md) | Issue tracking and project management | MEDIUM |
| Supabase | [supabase.md](servers/supabase.md) | Backend-as-a-service DB and auth | MEDIUM |

## Configuration Locations by Adapter

| Adapter | MCP Config Path |
|---------|-----------------|
| Claude Code | `~/.claude/settings.json` → `mcpServers` |
| Cursor | `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global) |
| Windsurf | `~/.codeium/windsurf/mcp.json` |
| VS Code (Continue) | `~/.continue/config.json` → `models[].mcpServers` |
| Cline | `~/.cline/mcp_settings.json` |
| Roo Code | `~/.roo-code/mcp_settings.json` |
| Amazon Q | `~/.aws/amazon-q/mcp.json` |
| Zed | `~/.config/zed/settings.json` → `experimental.mcpServers` |
| Aider | `.aider.conf.yml` → not native; use AGENTS.md references |
| GitHub Copilot CLI | Not supported natively; use AGENTS.md |

## Security Best Practices
1. **Never commit credentials** — use environment variables or secret managers
2. **Use minimum permissions** — fine-grained tokens, read-only DB users, scoped API keys
3. **Audit regularly** — review access logs and rotate keys on schedule
4. **Sandbox filesystem access** — always specify allowed directories explicitly
5. **Prefer OAuth over API keys** when the service supports it

## Adding New Servers
To add a new MCP server to this catalog:
1. Create `mcps/servers/<name>.md` following the existing template
2. Add an entry to the table above
3. Test configuration with at least one adapter
4. Submit as a standalone PR
