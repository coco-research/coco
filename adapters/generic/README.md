# Generic adapter (AGENTS.md)

Produces a single `AGENTS.md` for any AI tool that follows the [AGENTS.md spec](https://agents.md/) — Continue, Windsurf, Cline, and others.

**Aider is not on that list:** it does not load `AGENTS.md` on its own. Use the dedicated `aider` adapter (`bash install.sh --adapter aider`), which also writes a `.aider.conf.yml` with `read: AGENTS.md`. With `generic`, load the file yourself: `aider --read AGENTS.md`.

## Install

```bash
cd path/to/your/project
bash /path/to/coco/adapters/generic/install.sh
```

Internally this delegates to the codex adapter (same output format).

## Why this exists

Codex CLI is the canonical AGENTS.md consumer. This adapter exists to give a discoverable name for users of other AGENTS.md-compatible tools.
