# MCP Server: Slack
> Team communication and channel management for AI agents via Model Context Protocol

## Installation
```bash
npm install -g @anthropic/mcp-server-slack
```

## Configuration
Add to your IDE's MCP settings with a Slack Bot Token:

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-bot-token",
        "SLACK_TEAM_ID": "T01234567"
      }
    }
  }
}
```

## Tools Provided
| Tool | Description |
|------|-------------|
| `send_message` | Send a message to a channel or DM |
| `list_channels` | List available channels |
| `get_channel_history` | Get recent messages from a channel |
| `search_messages` | Search across workspace messages |
| `create_channel` | Create a new channel |
| `invite_to_channel` | Invite users to a channel |
| `set_topic` | Set channel topic |
| `add_reaction` | Add emoji reaction to a message |

## Integration with Coco
The Slack MCP server enhances Coco's team communication workflows:
- `/team:communicate` can post updates directly to Slack channels
- `/pmstudio-sync-init` can monitor Slack channels alongside email for project signals
- Brain DB events can be created from Slack thread discussions
- Incident response plans can auto-notify on-call channels

## Security Notes
- Use Bot Tokens (xoxb-) not User Tokens (xoxp-) for server integrations
- Restrict bot permissions to minimum required scopes
- Never commit tokens — use environment variables or secret managers
- Audit bot activity logs regularly
