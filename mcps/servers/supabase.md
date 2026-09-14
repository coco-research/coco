# MCP Server: Supabase
> Backend-as-a-service database and auth integration for AI agents via Model Context Protocol

## Installation
```bash
npm install -g @anthropic/mcp-server-supabase
```

## Configuration
Add to your IDE's MCP settings:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-supabase"],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      }
    }
  }
}
```

## Tools Provided
| Tool | Description |
|------|-------------|
| `query` | Execute SQL queries via PostgREST |
| `list_tables` | List all tables in the schema |
| `describe_table` | Get column definitions and types |
| `insert_row` | Insert a row into a table |
| `update_rows` | Update rows matching a filter |
| `delete_rows` | Delete rows matching a filter |
| `list_functions` | List edge functions |
| `invoke_function` | Invoke an edge function |

## Integration with Coco
The Supabase MCP server enhances Coco's full-stack development workflows:
- Database architects can inspect and modify schemas directly
- `/team:develop` agents can seed test data via MCP
- Brain DB can sync user/team entities from Supabase Auth
- Code verification can validate against live schema constraints

## Security Notes
- Prefer service role key only for admin operations; use anon key for read-only
- Enable Row Level Security (RLS) on all tables
- Never expose service role keys in client-side code
- Rotate keys regularly and audit access logs in Supabase dashboard
