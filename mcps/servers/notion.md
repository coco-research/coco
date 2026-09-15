# MCP Server: Notion
> Knowledge base and database integration for AI agents via Model Context Protocol

## Installation
```bash
npm install -g @anthropic/mcp-server-notion
```

## Configuration
Add to your IDE's MCP settings with a Notion Integration Token:

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-notion"],
      "env": {
        "NOTION_API_KEY": "secret_your_integration_token"
      }
    }
  }
}
```

## Tools Provided
| Tool | Description |
|------|-------------|
| `search` | Search pages and databases |
| `get_page` | Get page content and properties |
| `create_page` | Create a new page in a database or as child |
| `update_page` | Update page properties |
| `query_database` | Query database with filters and sorts |
| `get_block_children` | Get nested block content |
| `append_block_children` | Add content blocks to a page |

## Integration with Coco
The Notion MCP server complements Coco's documentation and PM workflows:
- `/team:document` can publish deliverables to Notion databases
- Brain DB entities can sync to Notion people/team databases
- PRD generation can pull requirements from Notion specs
- Meeting notes can be auto-created as Notion pages

## Security Notes
- Create internal integrations with minimum required capabilities
- Share only specific pages/databases with the integration
- Never commit API keys — use environment variables
- Review integration access in Notion workspace settings
