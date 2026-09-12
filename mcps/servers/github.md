# MCP Server: GitHub
> PR creation, issue tracking, and repository management for AI agents via Model Context Protocol

## Installation
```bash
npm install -g @modelcontextprotocol/server-github
```

## Configuration
Add to your IDE's MCP settings with a personal access token:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

## Tools Provided
| Tool | Description |
|------|-------------|
| `create_issue` | Create a new issue in a repository |
| `list_issues` | List issues with filters (state, labels, assignee) |
| `get_issue` | Get details of a specific issue |
| `create_pull_request` | Create a new pull request |
| `list_pull_requests` | List open/closed PRs |
| `get_pull_request` | Get PR details including diff and reviews |
| `search_repositories` | Search across GitHub repositories |
| `get_file_contents` | Read file contents from a repository |
| `create_branch` | Create a new branch |
| `list_commits` | List commits on a branch or path |

## Integration with Coco
The GitHub MCP server integrates with Coco's workflow system:
- `/gsd-ship` can create PRs directly via MCP instead of CLI
- `/team:research` can search repositories for prior art
- Brain DB entities can be linked to GitHub issues and PRs
- Code review agents can fetch PR diffs for analysis

## Security Notes
- Use fine-grained tokens with minimum required permissions
- Never commit tokens to version control — use env vars or secret managers
- Restrict token scope to specific repositories when possible
- Rotate tokens regularly and audit usage logs
