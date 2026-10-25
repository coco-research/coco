# MCP Server: agent-qa
> Natural-language web and mobile testing by vostride, with recorded run evidence, advanced memidex memory, and self-improvement.

## Installation

Follow the [agent quickstart](https://vostride.com/docs/agent-qa/agent-quickstart) in the application repository to install agent-qa, initialize the project, and configure its target and model provider.
The commands below run from the directory containing `agent-qa.config.yaml`.
The runtime is distributed separately under its [published license](https://github.com/vostride/agent-qa/blob/main/LICENSE.md).

## Configuration

For Claude Code, register the project-scoped stdio server:

```bash
claude mcp add-json --scope project agent-qa '{"type":"stdio","command":"npx","args":["agent-qa","mcp"],"timeout":6000000}'
```

This writes `.mcp.json` in the project.
Start Claude Code from that project and approve the server when prompted.
The resulting configuration is:

```json
{
  "mcpServers": {
    "agent-qa": {
      "type": "stdio",
      "command": "npx",
      "args": ["agent-qa", "mcp"],
      "timeout": 6000000
    }
  }
}
```

The timeout is 100 minutes, above the default 90-minute limit for one agent-qa test.
Allow additional time for suites.
Other hosts have their own configuration and timeout settings; follow the [coding-agent setup guide](https://vostride.com/docs/agent-qa/coding-agents).
That guide also covers installing the four version-matched agent-qa skills into your host.

## Tools Provided

The server exposes 20 tools, including:

| Tool | Description |
|------|-------------|
| `agent_qa_write_test` | Draft, verify, and run a test from an intent; may execute the application |
| `agent_qa_start_run` | Run tests selected by `patterns` and return a run ID after completion |
| `agent_qa_get_run_overview` | Read a recorded run's verdict, steps, and evidence |
| `agent_qa_get_run_evidence` | Read step evidence or a screenshot |
| `agent_qa_get_run_knowledge` | Inspect memory supplied to a run and changes it produced |
| `agent_qa_preview_run_mark` | Preview the effect of correcting a verdict without applying it |

See the [MCP reference](https://vostride.com/docs/agent-qa/mcp) for all tools and resources.

## Integration with Coco

Use agent-qa alongside Coco's test-generation and debugging workflows to exercise a real user journey and inspect the resulting evidence.
Keep test authoring and execution within the user's requested scope: writing or refining a test can execute checks, while configuration, verdict, and knowledge tools can change project state.
Read the returned run with the overview or digest tools before reporting a result; a run ID or an empty run list is not a passing test.
After a fix, rerun the relevant test before claiming the behavior is verified.

## Security Notes

- Use temporary, limited test credentials and a dedicated test environment.
- Only values declared through `workspace.secretsFile` receive the documented secret masking; screenshots and other artifacts may still contain sensitive data.
- Read runs and knowledge through the supported CLI or MCP tools, not private `.agent-qa/` storage.
- Read `agent-qa-knowledge/AGENTS.md` before changing knowledge records.
