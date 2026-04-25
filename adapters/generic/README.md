# Generic adapter (AGENTS.md)

Produces a single `AGENTS.md` for any AI tool that follows the [AGENTS.md spec](https://agents.md/) — Aider, Continue, Windsurf, Cline, and others.

## Install

```bash
cd path/to/your/project
bash /path/to/coco/adapters/generic/install.sh
```

Internally this delegates to the codex adapter (same output format).

## Why this exists

Codex CLI is the canonical AGENTS.md consumer. This adapter exists to give a discoverable name for users of other AGENTS.md-compatible tools.
