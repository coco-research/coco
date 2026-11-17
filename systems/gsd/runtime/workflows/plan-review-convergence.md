<purpose>
Cross-AI plan convergence loop — automates the manual chain:
gsd-plan-phase N → gsd-review N --codex → gsd-plan-phase N --reviews → gsd-review N --codex → ...
Each step runs inside an isolated Agent that calls the corresponding Skill.
Orchestrator only does: init, loop control, parse CYCLE_SUMMARY for HIGH count, stall detection, escalation.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.

@$HOME/.claude/get-shit-done/references/revision-loop.md
@$HOME/.claude/get-shit-done/references/gates.md
@$HOME/.claude/get-shit-done/references/agent-contracts.md
</required_reading>

<process>

## 1. Parse and Normalize Arguments

Extract from $ARGUMENTS: phase number, reviewer flags (`--codex`, `--gemini`, `--claude`, `--opencode`, `--ollama`, `--lm-studio`, `--llama-cpp`, `--all`), `--max-cycles N`, `--text`, `--ws`.

```bash
PHASE=$(echo "$ARGUMENTS" | grep -oE '[0-9]+\.?[0-9]*' | head -1)
