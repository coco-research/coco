---
description: "Check status, change context window, restart, or troubleshoot this machine's local LLM setup (LM Studio + mlx-dspark). Usage: /eng-local-llm [status|set-context <n>|restart|troubleshoot]"
allowed-tools:
  - Read
  - Bash
---

# /eng-local-llm — Local LLM Ops

Read `skills/local-llm/SKILL.md` first for full background (architecture, the
prefill trick, RAM/speed cheatsheets, idle-unload behavior) before acting on
any subcommand below -- this command is the action layer on top of that
knowledge, not a replacement for it.

Parse `$ARGUMENTS`: first token is the subcommand (`status`, `set-context`,
`restart`, `troubleshoot`). No arguments -> show the quick reference table
below and stop.

## Quick reference (no-args output)

| Command | Purpose |
|---|---|
| `/eng-local-llm status` | One-shot health/metrics/RAM snapshot of both backends |
| `/eng-local-llm set-context <n>` | Safely change mlx-dspark's context window and restart |
| `/eng-local-llm restart` | Safe restart of the mlx-dspark server with health verification |
| `/eng-local-llm troubleshoot` | Walk the troubleshooting playbook interactively |

## `status`

Run all of the following and present a combined summary (loaded/unloaded
state, context window, RAM estimate, both launchd agents' status):

```bash
echo "--- mlx-dspark health ---"
curl -s http://127.0.0.1:8090/health
echo
echo "--- mlx-dspark metrics ---"
curl -s http://127.0.0.1:8090/metrics
echo
echo "--- LM Studio ---"
lms ps
echo
echo "--- launchd agents ---"
launchctl list | grep -i dspark
```

Interpret the output for the user:
- `/health`'s `status` field: `ok` = loaded and ready, `no_model` = currently
  idle-unloaded (expect a ~7-40s cold-load delay on the next request, not a
  hang).
- `context_window` should read 65536 unless it was deliberately changed.
- `/metrics`'s `memory.active_bytes`/`peak_bytes` give the live RAM footprint.
- If LM Studio also shows a loaded model, flag that as extra RAM (~16GB) not
  needed by `build_local.py`'s pipeline (it only talks to mlx-dspark).
- Both `com.local.mlx-dspark` and `com.local.mlx-dspark-idle-watcher` should
  appear in the launchd list; a missing one means that LaunchAgent isn't
  loaded (`launchctl load ~/Library/LaunchAgents/<name>.plist` to fix).

## `set-context <n>`

`<n>` is the new context window token count (e.g. `set-context 131072`). Before
changing anything:

1. **Show the RAM math first** using the cheatsheet table from
   `skills/local-llm/SKILL.md` (KV cache per request x `--max-batch 4`) and
   confirm with the user this is what they want, especially for anything
   above 65536 -- don't silently apply a large jump.
2. Edit `~/.config/mlx-dspark/start.sh`: change `--context-window <old>` to
   `--context-window <n>`.
3. Find and kill the running process to trigger a `launchd`-managed restart:
   ```bash
   ps aux | grep mlx_dspark | grep -v grep   # find the PID
   kill <pid>
   ```
4. Poll `/health` until `status` is `"ok"` again, and confirm `context_window`
   in the response equals `<n>`:
   ```bash
   for i in $(seq 1 30); do
     r=$(curl -s http://127.0.0.1:8090/health)
     echo "$r"
     echo "$r" | grep -q '"status": "ok"' && break
     sleep 3
   done
   ```
5. Report the new RAM math and confirm the change is live.

## `restart`

Safe restart without changing any config:

1. `ps aux | grep mlx_dspark | grep -v grep` to find the current PID.
2. `kill <pid>` -- `launchd`'s `KeepAlive(Crashed)` will restart it
   automatically within seconds.
3. Poll `/health` (same loop as above) until `status` is `"ok"`.
4. Confirm `context_window` and `mode` match what's expected before declaring
   success.

## `troubleshoot`

Walk the user through `skills/local-llm/SKILL.md`'s troubleshooting playbook
interactively:
1. Ask what symptom they're seeing (hang, 503, YAML/formatting slip, context
   truncation, server unresponsive, something else).
2. Match it to the relevant playbook entry and walk through the diagnostic
   steps live (run the actual `curl`/`launchctl`/`ps` commands, don't just
   describe them).
3. If none of the documented symptoms match, gather `/health`, `/metrics`,
   and the actual error message/traceback before speculating on a cause.
