# MCP Server: PostgreSQL
> Database queries and schema inspection for AI agents via Model Context Protocol

## Installation
```bash
npm install -g @modelcontextprotocol/server-postgres
```

## Configuration
Add to your IDE's MCP settings:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://user:password@localhost:5432/mydb"
      ]
    }
  }
}
```

## Environment Variable (Recommended)
Avoid hardcoding credentials by using an environment variable:
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/mydb"
      }
    }
  }
}
```

## Tools Provided
| Tool | Description |
|------|-------------|
| `query` | Execute SQL queries (SELECT, INSERT, UPDATE, DELETE) |
| `list_tables` | List all tables in the database |
| `describe_table` | Get column names, types, and constraints for a table |
| `list_schemas` | List all schemas in the database |

## Integration with Coco Brain
The Postgres MCP server can complement Coco's SQLite-based Brain DB by:
- Querying production databases for entity data during `/brain-rescan`
- Validating Brain DB decisions against live schema constraints
- Extracting relationships from foreign key constraints
- Syncing task status from project management tables

## Security Notes
- Use read-only database users when possible
- Never store credentials in MCP config files — use env vars or secret managers
- Restrict network access to the database host
- Audit query logs for unexpected patterns
