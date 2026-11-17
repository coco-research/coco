<purpose>
Check for GSD updates via npm, display changelog for versions between installed and latest, obtain user confirmation, and execute clean installation with cache clearing.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="get_installed_version">
Detect whether GSD is installed locally or globally by checking both locations and validating install integrity.

First, derive `PREFERRED_CONFIG_DIR` and `PREFERRED_RUNTIME` from the invoking prompt's `execution_context` path:
- If the path contains `/get-shit-done/workflows/update.md`, strip that suffix and store the remainder as `PREFERRED_CONFIG_DIR`
- Path contains `/.codex/` -> `codex`
- Path contains `/.gemini/antigravity/` -> `antigravity`
- Path contains `/.gemini/` -> `gemini`
- Path contains `/.config/kilo/` or `/.kilo/`, or `PREFERRED_CONFIG_DIR` contains `kilo.json` / `kilo.jsonc` -> `kilo`
- Path contains `/.config/opencode/` or `/.opencode/`, or `PREFERRED_CONFIG_DIR` contains `opencode.json` / `opencode.jsonc` -> `opencode`
- Otherwise -> `claude`

Use `PREFERRED_CONFIG_DIR` when available so custom `--config-dir` installs are checked before default locations.
Use `PREFERRED_RUNTIME` as the first runtime checked so `/gsd:update` targets the runtime that invoked it.

Kilo config precedence must match the installer: `KILO_CONFIG_DIR` -> `dirname(KILO_CONFIG)` -> `XDG_CONFIG_HOME/kilo` -> `~/.config/kilo`.

```bash
expand_home() {
  case "$1" in
    "~/"*) printf '%s/%s\n' "$HOME" "${1#~/}" ;;
    *) printf '%s\n' "$1" ;;
  esac
}

# Runtime candidates: "<runtime>:<config-dir>" stored as an array.
# Using an array instead of a space-separated string ensures correct
# iteration in both bash and zsh (zsh does not word-split unquoted
# variables by default). Fixes #1173.
RUNTIME_DIRS=( "claude:.claude" "opencode:.config/opencode" "opencode:.opencode" "antigravity:.gemini/antigravity" "gemini:.gemini" "kilo:.config/kilo" "kilo:.kilo" "codex:.codex" )
ENV_RUNTIME_DIRS=()

# PREFERRED_CONFIG_DIR / PREFERRED_RUNTIME should be set from execution_context
# before running this block.
if [ -n "$PREFERRED_CONFIG_DIR" ]; then
  PREFERRED_CONFIG_DIR="$(expand_home "$PREFERRED_CONFIG_DIR")"
  if [ -z "$PREFERRED_RUNTIME" ]; then
    if [ -f "$PREFERRED_CONFIG_DIR/kilo.json" ] || [ -f "$PREFERRED_CONFIG_DIR/kilo.jsonc" ]; then
      PREFERRED_RUNTIME="kilo"
    elif [ -f "$PREFERRED_CONFIG_DIR/opencode.json" ] || [ -f "$PREFERRED_CONFIG_DIR/opencode.jsonc" ]; then
      PREFERRED_RUNTIME="opencode"
    elif [ -f "$PREFERRED_CONFIG_DIR/config.toml" ]; then
      PREFERRED_RUNTIME="codex"
    fi
  fi
fi

# If runtime is still unknown, infer from runtime env vars; fallback to claude.
if [ -z "$PREFERRED_RUNTIME" ]; then
  if [ -n "$CODEX_HOME" ]; then
    PREFERRED_RUNTIME="codex"
  elif [ -n "$ANTIGRAVITY_CONFIG_DIR" ]; then
    PREFERRED_RUNTIME="antigravity"
  elif [ -n "$GEMINI_CONFIG_DIR" ]; then
    PREFERRED_RUNTIME="gemini"
  elif [ -n "$KILO_CONFIG_DIR" ]; then
    PREFERRED_RUNTIME="kilo"
  elif [ -n "$KILO_CONFIG" ]; then
    PREFERRED_RUNTIME="kilo"
  elif [ -n "$OPENCODE_CONFIG_DIR" ] || [ -n "$OPENCODE_CONFIG" ]; then
    PREFERRED_RUNTIME="opencode"
  elif [ -n "$CLAUDE_CONFIG_DIR" ]; then
    PREFERRED_RUNTIME="claude"
  else
    PREFERRED_RUNTIME="claude"
  fi
fi

# If execution_context already points at an installed config dir, trust it first.
# This covers custom --config-dir installs that do not live under the default
# runtime directories.
if [ -n "$PREFERRED_CONFIG_DIR" ] && { [ -f "$PREFERRED_CONFIG_DIR/get-shit-done/VERSION" ] || [ -f "$PREFERRED_CONFIG_DIR/get-shit-done/workflows/update.md" ]; }; then
  INSTALL_SCOPE="GLOBAL"
  # Normalize a path for comparison: on Windows with Git Bash, pwd returns
  # POSIX-style /c/Users/... but PREFERRED_CONFIG_DIR may carry C:/Users/...
  # Convert Windows drive-letter paths to POSIX form so the comparison works
  # on both Windows (Git Bash) and POSIX systems.
  normalize_path() {
    local p="$1"
    case "$p" in
      [A-Za-z]:/*)
        local drive rest
        drive="${p%%:*}"
        rest="${p#?:}"
        p="/$(printf '%s' "$drive" | tr '[:upper:]' '[:lower:]')$rest"
        ;;
    esac
    printf '%s' "$p"
  }
  normalized_preferred="$(normalize_path "$PREFERRED_CONFIG_DIR")"
  for dir in .claude .config/opencode .opencode .gemini/antigravity .gemini .config/kilo .kilo .codex; do
    resolved_local="$(cd "./$dir" 2>/dev/null && pwd)"
    normalized_local="$(normalize_path "$resolved_local")"
    if [ -n "$normalized_local" ] && [ "$normalized_local" = "$normalized_preferred" ]; then
      INSTALL_SCOPE="LOCAL"
      break
    fi
  done

  if [ -f "$PREFERRED_CONFIG_DIR/get-shit-done/VERSION" ] && grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+' "$PREFERRED_CONFIG_DIR/get-shit-done/VERSION"; then
    INSTALLED_VERSION="$(cat "$PREFERRED_CONFIG_DIR/get-shit-done/VERSION")"
  else
    INSTALLED_VERSION="0.0.0"
  fi

  echo "$INSTALLED_VERSION"
  echo "$INSTALL_SCOPE"
  echo "${PREFERRED_RUNTIME:-claude}"
  # 4-line output contract (#2993 CR): early-return path must also emit
  # GSD_DIR or downstream check_latest_version misreads the install as
  # UNKNOWN. PREFERRED_CONFIG_DIR is the resolved config dir we just
  # validated above (line 95-96); it is the right GSD_DIR value for
  # this fast path.
  echo "$PREFERRED_CONFIG_DIR"
  exit 0
fi

# Absolute global candidates from env overrides (covers custom config dirs).
if [ -n "$CLAUDE_CONFIG_DIR" ]; then
  ENV_RUNTIME_DIRS+=( "claude:$(expand_home "$CLAUDE_CONFIG_DIR")" )
fi
if [ -n "$ANTIGRAVITY_CONFIG_DIR" ]; then
  ENV_RUNTIME_DIRS+=( "antigravity:$(expand_home "$ANTIGRAVITY_CONFIG_DIR")" )
fi
if [ -n "$GEMINI_CONFIG_DIR" ]; then
  ENV_RUNTIME_DIRS+=( "gemini:$(expand_home "$GEMINI_CONFIG_DIR")" )
fi
if [ -n "$KILO_CONFIG_DIR" ]; then
  ENV_RUNTIME_DIRS+=( "kilo:$(expand_home "$KILO_CONFIG_DIR")" )
elif [ -n "$KILO_CONFIG" ]; then
  ENV_RUNTIME_DIRS+=( "kilo:$(dirname "$(expand_home "$KILO_CONFIG")")" )
elif [ -n "$XDG_CONFIG_HOME" ]; then
  ENV_RUNTIME_DIRS+=( "kilo:$(expand_home "$XDG_CONFIG_HOME")/kilo" )
fi
if [ -n "$OPENCODE_CONFIG_DIR" ]; then
  ENV_RUNTIME_DIRS+=( "opencode:$(expand_home "$OPENCODE_CONFIG_DIR")" )
elif [ -n "$OPENCODE_CONFIG" ]; then
  ENV_RUNTIME_DIRS+=( "opencode:$(dirname "$(expand_home "$OPENCODE_CONFIG")")" )
elif [ -n "$XDG_CONFIG_HOME" ]; then
  ENV_RUNTIME_DIRS+=( "opencode:$(expand_home "$XDG_CONFIG_HOME")/opencode" )
fi
if [ -n "$CODEX_HOME" ]; then
  ENV_RUNTIME_DIRS+=( "codex:$(expand_home "$CODEX_HOME")" )
fi

# Reorder entries so preferred runtime is checked first.
ORDERED_RUNTIME_DIRS=()
for entry in "${RUNTIME_DIRS[@]}"; do
  runtime="${entry%%:*}"
  if [ "$runtime" = "$PREFERRED_RUNTIME" ]; then
    ORDERED_RUNTIME_DIRS+=( "$entry" )
  fi
done
ORDERED_ENV_RUNTIME_DIRS=()
for entry in "${ENV_RUNTIME_DIRS[@]}"; do
  runtime="${entry%%:*}"
  if [ "$runtime" = "$PREFERRED_RUNTIME" ]; then
    ORDERED_ENV_RUNTIME_DIRS+=( "$entry" )
  fi
done
for entry in "${ENV_RUNTIME_DIRS[@]}"; do
  runtime="${entry%%:*}"
  if [ "$runtime" != "$PREFERRED_RUNTIME" ]; then
    ORDERED_ENV_RUNTIME_DIRS+=( "$entry" )
  fi
done
for entry in "${RUNTIME_DIRS[@]}"; do
  runtime="${entry%%:*}"
  if [ "$runtime" != "$PREFERRED_RUNTIME" ]; then
    ORDERED_RUNTIME_DIRS+=( "$entry" )
  fi
done

# Check local first (takes priority only if valid and distinct from global)
LOCAL_VERSION_FILE="" LOCAL_MARKER_FILE="" LOCAL_DIR="" LOCAL_RUNTIME=""
for entry in "${ORDERED_RUNTIME_DIRS[@]}"; do
  runtime="${entry%%:*}"
  dir="${entry#*:}"
  if [ -f "./$dir/get-shit-done/VERSION" ] || [ -f "./$dir/get-shit-done/workflows/update.md" ]; then
    LOCAL_RUNTIME="$runtime"
    LOCAL_VERSION_FILE="./$dir/get-shit-done/VERSION"
    LOCAL_MARKER_FILE="./$dir/get-shit-done/workflows/update.md"
    LOCAL_DIR="$(cd "./$dir" 2>/dev/null && pwd)"
    break
  fi
done

GLOBAL_VERSION_FILE="" GLOBAL_MARKER_FILE="" GLOBAL_DIR="" GLOBAL_RUNTIME=""
for entry in "${ORDERED_ENV_RUNTIME_DIRS[@]}"; do
  runtime="${entry%%:*}"
  dir="${entry#*:}"
  if [ -f "$dir/get-shit-done/VERSION" ] || [ -f "$dir/get-shit-done/workflows/update.md" ]; then
    GLOBAL_RUNTIME="$runtime"
    GLOBAL_VERSION_FILE="$dir/get-shit-done/VERSION"
    GLOBAL_MARKER_FILE="$dir/get-shit-done/workflows/update.md"
    GLOBAL_DIR="$(cd "$dir" 2>/dev/null && pwd)"
    break
  fi
done

if [ -z "$GLOBAL_RUNTIME" ]; then
  for entry in "${ORDERED_RUNTIME_DIRS[@]}"; do
    runtime="${entry%%:*}"
    dir="${entry#*:}"
    if [ -f "$HOME/$dir/get-shit-done/VERSION" ] || [ -f "$HOME/$dir/get-shit-done/workflows/update.md" ]; then
      GLOBAL_RUNTIME="$runtime"
      GLOBAL_VERSION_FILE="$HOME/$dir/get-shit-done/VERSION"
      GLOBAL_MARKER_FILE="$HOME/$dir/get-shit-done/workflows/update.md"
      GLOBAL_DIR="$(cd "$HOME/$dir" 2>/dev/null && pwd)"
      break
    fi
  done
fi

# Only treat as LOCAL if the resolved paths differ (prevents misdetection when CWD=$HOME)
IS_LOCAL=false
if [ -n "$LOCAL_VERSION_FILE" ] && [ -f "$LOCAL_VERSION_FILE" ] && [ -f "$LOCAL_MARKER_FILE" ] && grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+' "$LOCAL_VERSION_FILE"; then
  if [ -z "$GLOBAL_DIR" ] || [ "$LOCAL_DIR" != "$GLOBAL_DIR" ]; then
    IS_LOCAL=true
  fi
fi

if [ "$IS_LOCAL" = true ]; then
  INSTALLED_VERSION="$(cat "$LOCAL_VERSION_FILE")"
  INSTALL_SCOPE="LOCAL"
  TARGET_RUNTIME="$LOCAL_RUNTIME"
  RESOLVED_GSD_DIR="$LOCAL_DIR"
elif [ -n "$GLOBAL_VERSION_FILE" ] && [ -f "$GLOBAL_VERSION_FILE" ] && [ -f "$GLOBAL_MARKER_FILE" ] && grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+' "$GLOBAL_VERSION_FILE"; then
  INSTALLED_VERSION="$(cat "$GLOBAL_VERSION_FILE")"
  INSTALL_SCOPE="GLOBAL"
  TARGET_RUNTIME="$GLOBAL_RUNTIME"
  RESOLVED_GSD_DIR="$GLOBAL_DIR"
elif [ -n "$LOCAL_RUNTIME" ] && [ -f "$LOCAL_MARKER_FILE" ]; then
  # Runtime detected but VERSION missing/corrupt: treat as unknown version, keep runtime target
  INSTALLED_VERSION="0.0.0"
  INSTALL_SCOPE="LOCAL"
  TARGET_RUNTIME="$LOCAL_RUNTIME"
  RESOLVED_GSD_DIR="$LOCAL_DIR"
elif [ -n "$GLOBAL_RUNTIME" ] && [ -f "$GLOBAL_MARKER_FILE" ]; then
  INSTALLED_VERSION="0.0.0"
  INSTALL_SCOPE="GLOBAL"
  TARGET_RUNTIME="$GLOBAL_RUNTIME"
  RESOLVED_GSD_DIR="$GLOBAL_DIR"
else
  INSTALLED_VERSION="0.0.0"
  INSTALL_SCOPE="UNKNOWN"
  TARGET_RUNTIME="claude"
  RESOLVED_GSD_DIR=""
fi

echo "$INSTALLED_VERSION"
echo "$INSTALL_SCOPE"
echo "$TARGET_RUNTIME"
echo "$RESOLVED_GSD_DIR"
```

Parse output:
- Line 1 = installed version (`0.0.0` means unknown version)
- Line 2 = install scope (`LOCAL`, `GLOBAL`, or `UNKNOWN`)
- Line 3 = target runtime (`claude`, `opencode`, `gemini`, `kilo`, or `codex`)
- Line 4 = resolved GSD config dir (e.g. `/Users/me/.claude`, `/Users/me/.gemini`); empty if scope is `UNKNOWN`. Capture this as `GSD_DIR` and pass it to subsequent steps so they don't have to re-derive the runtime path.
- If scope is `UNKNOWN`, proceed to install step using `--claude --global` fallback.

If multiple runtime installs are detected and the invoking runtime cannot be determined from execution_context, ask the user which runtime to update before running install.

**If VERSION file missing:**
```
## GSD Update

**Installed version:** Unknown

Your installation doesn't include version tracking.

Running fresh install...
```

Proceed to install step (treat as version 0.0.0 for comparison).
</step>

<step name="check_latest_version">
Check npm for latest version via the deterministic script. **Do NOT run `npm view` or `npm search` directly** — the package name must come from the script, not from a free choice at execution time. (#2992: LLM-driven prescriptions of npm package names produced wrong-package queries; moving the package name into a script constant closes that gap.)

The `GSD_DIR` value emitted by `get_installed_version` (line 4) resolves to the runtime-specific config dir (`~/.claude/`, `~/.gemini/`, `~/.codex/`, etc.), so the script invocation works for every runtime — not just Claude. If `GSD_DIR` is empty (scope `UNKNOWN`), skip this step and go directly to install.

`LATEST_RESULT` is a JSON document with the documented shape `{ ok: bool, version: string, reason: string, detail?: string }`. Parse via `jq` ONLY when the script actually ran. When `GSD_DIR` is empty (scope `UNKNOWN`), skip the check entirely and seed the parsed fields with their no-op values so downstream logic does not mistake an unset `LATEST_RESULT` for a failed network check (#2993 CR feedback):

```bash
if [ -z "$GSD_DIR" ]; then
  # No install detected — fall through to install step; version-check is skipped.
  LATEST_RESULT=""
  LATEST_STATUS=0
  LATEST_OK=false
  LATEST_VERSION=""
  LATEST_REASON="no_install_detected"
else
  LATEST_RESULT="$(node "$GSD_DIR/get-shit-done/bin/check-latest-version.cjs" --json 2>/dev/null)"
  LATEST_STATUS=$?
  # #2993 CR: when node is missing or the script doesn't exist, LATEST_RESULT
  # is empty and piping it to `jq` produces a parse error on stderr while
  # leaving LATEST_OK / LATEST_REASON as empty strings. Fail the check with a
  # meaningful reason instead of a blank diagnostic.
  if [ -n "$LATEST_RESULT" ]; then
    LATEST_OK="$(printf '%s' "$LATEST_RESULT" | jq -r '.ok // false')"
    LATEST_VERSION="$(printf '%s' "$LATEST_RESULT" | jq -r '.version // empty')"
    LATEST_REASON="$(printf '%s' "$LATEST_RESULT" | jq -r '.reason // empty')"
  else
    LATEST_OK=false
    LATEST_VERSION=""
    LATEST_REASON="script_not_found_or_node_unavailable"
  fi
fi
```

**If `LATEST_OK` is not `true`** (or `LATEST_STATUS` is non-zero):

```text
Couldn't check for updates (reason: {LATEST_REASON}, exit: {LATEST_STATUS}).

To update manually: `npx -y --package=get-shit-done-cc@latest -- get-shit-done-cc --global`
```

Exit.
</step>

<step name="compare_versions">
Compare installed vs latest:

**If installed == latest:**
```
## GSD Update

**Installed:** X.Y.Z
**Latest:** X.Y.Z

You're already on the latest version.
```

Exit.

**If installed > latest:**
```
## GSD Update

**Installed:** X.Y.Z
**Latest:** A.B.C

You're ahead of the latest release — this looks like a dev install.

If you see a "⚠ dev install — re-run installer to sync hooks" warning in
your statusline, your hook files are older than your VERSION file. Fix it
by re-running the local installer from your dev branch:

    node bin/install.js --global --claude

Running /gsd:update would install the npm release (A.B.C) and downgrade
your dev version — do NOT use it to resolve this warning.
```

Exit.
</step>

<step name="show_changes_and_confirm">
**If update available**, fetch and show what's new BEFORE updating:

1. Fetch changelog from GitHub raw URL
2. Extract entries between installed and latest versions
3. Display preview and ask for confirmation:

```
## GSD Update Available

**Installed:** 1.5.10
