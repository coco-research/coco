# MCP Server: Filesystem
> Sandboxed file access for AI agents via Model Context Protocol

## Installation
```bash
npm install -g @modelcontextprotocol/server-filesystem
```

## Configuration
Add to your IDE's MCP settings (e.g., `~/.claude/settings.json`, `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/allowed/directory"
      ]
    }
  }
}
```

## Allowed Directories
Specify one or more directories the server can access:
```json
"args": [
  "-y",
  "@modelcontextprotocol/server-filesystem",
  "/home/user/projects",
  "/tmp/workspace"
]
```

## Tools Provided
| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `write_file` | Write/create files |
| `list_directory` | List directory contents |
| `search_files` | Search for files by pattern |
| `get_file_info` | Get file metadata (size, modified, etc.) |
| `move_file` | Move/rename files |

## Security Notes
- Server runs in sandboxed mode — only specified directories are accessible
- No path traversal outside allowed directories
- Read-only mode available via `--readonly` flag
- Use with Coco's Brain system for persistent project knowledge storage

## Integration with Coco
The filesystem MCP server complements Coco's Brain DB by providing:
- Direct file read/write for document generation skills
- Project directory scanning for `/brain-rescan`
- Template file access for PRD and architecture workflows
