<purpose>
Zero-friction idea capture. One Write call, one confirmation line. No questions, no prompts.

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
Runs inline — no Task, no AskUserQuestion, no Bash.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="storage_format">
**Note storage format.**

Notes are stored as individual markdown files:

- **Project scope**: `.planning/notes/{YYYY-MM-DD}-{slug}.md` — used when `.planning/` exists in cwd
- **Global scope**: `~/.claude/notes/{YYYY-MM-DD}-{slug}.md` — fallback when no `.planning/`, or when `--global` flag is present

Each note file:

```markdown
---
date: "YYYY-MM-DD HH:mm"
promoted: false
---

{note text verbatim}
```

**`--global` flag**: Strip `--global` from anywhere in `$ARGUMENTS` before parsing. When present, force global scope regardless of whether `.planning/` exists.

**Important**: Do NOT create `.planning/` if it doesn't exist. Fall back to global scope silently.
</step>

<step name="parse_subcommand">
**Parse subcommand from $ARGUMENTS (after stripping --global).**

| Condition | Subcommand |
|-----------|------------|
| Arguments are exactly `list` (case-insensitive) | **list** |
