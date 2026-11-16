# Coco MCP Server (`coco mcp`)

`coco mcp` starts a read-only Model Context Protocol (MCP) server over stdio using Node.js standard libraries only. It requires zero third-party npm packages, makes zero network calls, spawns zero child processes, and never modifies files on disk.

## Quick Start

Add Coco to any MCP client configuration:

```json
{
  "mcpServers": {
    "coco": {
      "command": "npx",
      "args": ["-y", "cocosuperintelligence", "mcp"]
    }
  }
}
```

Or run directly from a local checkout:

```bash
node bin/coco.js mcp
```

## Content Checkout Resolution

At startup, `coco mcp` resolves the read-only Coco content root in order:

1. `$COCO_DIR` (or `--coco-dir <dir>`), when explicitly provided.
2. The package's parent directory, when `skills/INDEX.md` is present (running from a Coco git checkout).
3. `~/.coco/src`, when `skills/` is present.
4. `./coco`, when `skills/` is present.

If none of those locations contains a `skills/` directory, the server still completes MCP handshakes cleanly and returns a tool error (`isError: true`) instructing the caller to run `npx cocosuperintelligence install` or set `COCO_DIR`.

## Tools

| Tool | Arguments | Description |
|---|---|---|
| `coco_search` | `query?: string`, `kind?: "skill" \| "command" \| "agent"`, `limit?: 1..50` | Case-insensitive search across allowlisted Coco skills, commands, and specialist agents. Returns matching names, kinds, and one-line descriptions. |
| `coco_skill` | `name: string` | Returns the `SKILL.md` Markdown body of an allowlisted skill. |

## Resources

| URI / Template | MIME Type | Description |
|---|---|---|
| `coco://skill/{name}` | `text/markdown` | Read an allowlisted Coco skill `SKILL.md` by slug. |

## Security & Trust Boundary

- **Allowlist-only lookups:** Every skill, command, and agent is indexed from verified files inside the resolved `COCO_DIR` root (`realpath` checked). User input is never joined into filesystem paths; `../`, path separators, symlinks escaping `COCO_DIR`, and unknown names are refused.
- **Bounded replies:** Every response is UTF-8 byte-capped (`32768` bytes by default; configurable via `COCO_MCP_MAX_BYTES`) with an explicit truncation notice.
- **Offline & read-only:** No network modules, child processes, or filesystem writes are invoked.
