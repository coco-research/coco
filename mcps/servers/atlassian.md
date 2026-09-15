# MCP Server: Atlassian (Jira + Confluence)
> Project management and knowledge base integration for AI agents via Model Context Protocol

## Installation
```bash
npm install -g mcp-atlassian
```

## Configuration
Add to your IDE's MCP settings:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "mcp-atlassian"],
      "env": {
        "ATLASSIAN_URL": "https://your-domain.atlassian.net",
        "ATLASSIAN_USERNAME": "your-email@example.com",
        "ATLASSIAN_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

## Tools Provided
| Tool | Description |
|------|-------------|
| `jira_get_issue` | Get Jira issue details |
| `jira_search` | Search issues using JQL |
| `jira_create_issue` | Create a new Jira issue |
| `jira_update_issue` | Update issue fields, status, assignee |
| `jira_list_projects` | List available projects |
| `confluence_get_page` | Get Confluence page content |
| `confluence_search` | Search Confluence pages |
| `confluence_create_page` | Create a new Confluence page |
| `confluence_update_page` | Update existing page content |
| `confluence_list_spaces` | List available spaces |

## Integration with Coco
The Atlassian MCP server enhances Coco's PM and documentation workflows:
- `/pmstudio-sync-init` can monitor Jira issues alongside email for project updates
- Team roles (Jira Specialist, Confluence Specialist) can use MCP tools directly
- Brain DB decisions can reference Jira issue keys for traceability
- `/team:document` can publish deliverables to Confluence automatically

## Security Notes
- Generate API tokens from Atlassian account settings — never use passwords
- Store credentials in environment variables or secret managers
- Use OAuth 2.0 when available for better security
- Restrict API token permissions to required scopes only
