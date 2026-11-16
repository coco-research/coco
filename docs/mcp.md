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

Or generate / merge configuration automatically for your harness:

```bash
node bin/coco.js connect --list
node bin/coco.js connect codex --write
node bin/coco.js connect claude-code --write
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
| `coco_persona` | `department?: string`, `name?: string`, `query?: string`, `limit?: 1..20` | Look up or search Super Intelligence personas and specialist agents with mandatory AI-persona attribution. |
| `coco_board` | `question: string`, `departments?: string[]`, `size?: 1..16` | Assemble conflict-balanced persona cards across departments plus the structured 4-round debate protocol (zero server model calls). |

## Prompts

`prompts/list` and `prompts/get` expose:
- Cross-department Super Intelligence commands (`SI`, `SI-Orchestrate`, `SI-Decide`, `SI-Analyse`, `SI-Review`, `SI-Tradeoff`, `SI-Pre-Mortem`, `SI-Post-Mortem`, `SI-Full-Cycle`, `SI-Re-Analyse`, `SI-Plan`, `SI-Design`, `SI-Vote`, `SI-Debug`, `SI-Stress-Test`, `SI-Defend`, `SI-Roast`).
- Per-department Super Intelligence commands (`SI-Eng-Review`, `SI-AI-Decide`, `SI-GTM-Decide`, etc.).
- Core Coco skills and shipped slash commands.

## Resources

| URI / Template | MIME Type | Description |
|---|---|---|
| `coco://skill/{name}` | `text/markdown` | Read an allowlisted Coco skill `SKILL.md` by slug. |
| `coco://persona/{department}/{name}` | `text/markdown` | Read an allowlisted Super Intelligence persona card by department and slug. |

## Security & Trust Boundary

- **Allowlist-only lookups:** Every skill, command, and agent is indexed from verified files inside the resolved `COCO_DIR` root (`realpath` checked). User input is never joined into filesystem paths; `../`, path separators, symlinks escaping `COCO_DIR`, and unknown names are refused.
- **Bounded replies:** Every response is UTF-8 byte-capped (`32768` bytes by default; configurable via `COCO_MCP_MAX_BYTES`) with an explicit truncation notice.
- **Offline & read-only:** No network modules, child processes, or filesystem writes are invoked.
