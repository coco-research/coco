# sync-skills — Cross-Runtime GSD Skill Sync

**Command:** `/gsd-sync-skills`

Sync managed `gsd-*` skill directories from one canonical runtime's skills root to one or more destination runtime skills roots. Keeps multi-runtime installs aligned after a `gsd-update` on one runtime.

---

## Arguments

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--from <runtime>` | Yes | *(none)* | Source runtime — the canonical runtime to copy from |
| `--to <runtime\|all>` | Yes | *(none)* | Destination runtime or `all` supported runtimes |
| `--dry-run` | No | *on by default* | Preview changes without writing anything |
| `--apply` | No | *off* | Execute the diff (overrides dry-run) |

If neither `--dry-run` nor `--apply` is specified, dry-run is the default.

**Supported runtime names:** `claude`, `codex`, `grok`, `copilot`, `cursor`, `windsurf`, `opencode`, `gemini`, `kilo`, `augment`, `trae`, `qwen`, `codebuddy`, `cline`, `antigravity` (grok uses the `~/.agents` layout)

---

## Step 1: Parse Arguments

```bash
FROM_RUNTIME=""
TO_RUNTIMES=()
IS_APPLY=false

# Parse --from
if [[ "$@" == *"--from"* ]]; then
  FROM_RUNTIME=$(echo "$@" | grep -oP '(?<=--from )\S+')
fi

# Parse --to
if [[ "$@" == *"--to all"* ]]; then
  TO_RUNTIMES=(claude codex grok copilot cursor windsurf opencode gemini kilo augment trae qwen codebuddy cline antigravity)
elif [[ "$@" == *"--to"* ]]; then
  TO_RUNTIMES=( $(echo "$@" | grep -oP '(?<=--to )\S+') )
fi

# Parse --apply
if [[ "$@" == *"--apply"* ]]; then
  IS_APPLY=true
fi
```

**Validation:**
- If `--from` is missing or unrecognized: print error and exit
- If `--to` is missing or unrecognized: print error and exit
- If `--from` == `--to` (single destination): print `[no-op: source and destination are the same runtime]` and exit

---

## Step 2: Resolve Skills Roots

Use `install.js --skills-root` to resolve paths — this reuses the single authoritative path table rather than duplicating it:

