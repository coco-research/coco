# MCP Server: Linear
> Issue tracking and project management for AI agents via Model Context Protocol

## Installation
```bash
npm install -g @anthropic/mcp-server-linear
```

## Configuration
Add to your IDE's MCP settings with a Linear API Key:

```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-linear"],
      "env": {
        "LINEAR_API_KEY": "lin_api_your_key_here"
      }
    }
  }
}
```

## Tools Provided
| Tool | Description |
|------|-------------|
| `get_issue` | Get issue details by ID or identifier |
| `search_issues` | Search issues with filters |
| `create_issue` | Create a new issue |
| `update_issue` | Update issue status, assignee, priority |
| `list_teams` | List teams in the workspace |
| `list_projects` | List active projects |
| `get_project` | Get project details and progress |
| `create_comment` | Add comment to an issue |
| `list_cycles` | List current and past cycles |

## Integration with Coco
The Linear MCP server integrates with Coco's task and team workflows:
- Brain DB tasks can sync bidirectionally with Linear issues
- `/gsd-add-todo` can create Linear issues directly
- Team feedback entries can be linked to Linear issue identifiers
- Sprint planning agents can query cycle velocity and capacity

## Security Notes
- Generate API keys from Linear settings → API → Personal API Keys
- Use team-scoped keys when possible instead of workspace-wide keys
- Never commit keys — use environment variables or secret managers
- Audit key usage in Linear admin settings
