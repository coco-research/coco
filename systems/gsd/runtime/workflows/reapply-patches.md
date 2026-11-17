# Reapply Local Patches Workflow

Invoked by `/gsd:update --reapply` (`commands/gsd/update.md`).

After a GSD update wipes and reinstalls files, this workflow merges user's previously saved local modifications back into the new version. Uses three-way comparison (pristine baseline, user-modified backup, newly installed version) to reliably distinguish user customizations from version drift.

**Critical invariant:** Every file in `gsd-local-patches/` was backed up because the installer's hash comparison detected it was modified. The workflow must NEVER conclude "no custom content" for any backed-up file — that is a logical contradiction. When in doubt, classify as CONFLICT requiring user review, not SKIP.

<process>

## Step 1: Detect backed-up patches

Check for local patches directory:

```bash
expand_home() {
  case "$1" in
    "~/"*) printf '%s/%s\n' "$HOME" "${1#~/}" ;;
    *) printf '%s\n' "$1" ;;
  esac
}

PATCHES_DIR=""

# Env overrides first — covers custom config directories used with --config-dir
if [ -n "$KILO_CONFIG_DIR" ]; then
  candidate="$(expand_home "$KILO_CONFIG_DIR")/gsd-local-patches"
  if [ -d "$candidate" ]; then
    PATCHES_DIR="$candidate"
  fi
elif [ -n "$KILO_CONFIG" ]; then
  candidate="$(dirname "$(expand_home "$KILO_CONFIG")")/gsd-local-patches"
  if [ -d "$candidate" ]; then
    PATCHES_DIR="$candidate"
  fi
elif [ -n "$XDG_CONFIG_HOME" ]; then
  candidate="$(expand_home "$XDG_CONFIG_HOME")/kilo/gsd-local-patches"
  if [ -d "$candidate" ]; then
    PATCHES_DIR="$candidate"
  fi
fi

if [ -z "$PATCHES_DIR" ] && [ -n "$OPENCODE_CONFIG_DIR" ]; then
  candidate="$(expand_home "$OPENCODE_CONFIG_DIR")/gsd-local-patches"
  if [ -d "$candidate" ]; then
    PATCHES_DIR="$candidate"
  fi
elif [ -z "$PATCHES_DIR" ] && [ -n "$OPENCODE_CONFIG" ]; then
  candidate="$(dirname "$(expand_home "$OPENCODE_CONFIG")")/gsd-local-patches"
  if [ -d "$candidate" ]; then
    PATCHES_DIR="$candidate"
  fi
elif [ -z "$PATCHES_DIR" ] && [ -n "$XDG_CONFIG_HOME" ]; then
  candidate="$(expand_home "$XDG_CONFIG_HOME")/opencode/gsd-local-patches"
  if [ -d "$candidate" ]; then
    PATCHES_DIR="$candidate"
  fi
fi

if [ -z "$PATCHES_DIR" ] && [ -n "$GEMINI_CONFIG_DIR" ]; then
  candidate="$(expand_home "$GEMINI_CONFIG_DIR")/gsd-local-patches"
  if [ -d "$candidate" ]; then
    PATCHES_DIR="$candidate"
  fi
fi

if [ -z "$PATCHES_DIR" ] && [ -n "$CODEX_HOME" ]; then
  candidate="$(expand_home "$CODEX_HOME")/gsd-local-patches"
  if [ -d "$candidate" ]; then
    PATCHES_DIR="$candidate"
  fi
fi

if [ -z "$PATCHES_DIR" ] && [ -n "$CLAUDE_CONFIG_DIR" ]; then
  candidate="$(expand_home "$CLAUDE_CONFIG_DIR")/gsd-local-patches"
  if [ -d "$candidate" ]; then
    PATCHES_DIR="$candidate"
  fi
fi

# Global install — detect runtime config directory defaults
if [ -z "$PATCHES_DIR" ]; then
  if [ -d "$HOME/.config/kilo/gsd-local-patches" ]; then
    PATCHES_DIR="$HOME/.config/kilo/gsd-local-patches"
  elif [ -d "$HOME/.config/opencode/gsd-local-patches" ]; then
    PATCHES_DIR="$HOME/.config/opencode/gsd-local-patches"
  elif [ -d "$HOME/.opencode/gsd-local-patches" ]; then
    PATCHES_DIR="$HOME/.opencode/gsd-local-patches"
  elif [ -d "$HOME/.gemini/gsd-local-patches" ]; then
    PATCHES_DIR="$HOME/.gemini/gsd-local-patches"
  elif [ -d "$HOME/.codex/gsd-local-patches" ]; then
    PATCHES_DIR="$HOME/.codex/gsd-local-patches"
  else
    PATCHES_DIR="$HOME/.claude/gsd-local-patches"
  fi
fi
# Local install fallback — check all runtime directories
if [ ! -d "$PATCHES_DIR" ]; then
  for dir in .config/kilo .kilo .config/opencode .opencode .gemini .codex .claude; do
    if [ -d "./$dir/gsd-local-patches" ]; then
      PATCHES_DIR="./$dir/gsd-local-patches"
      break
    fi
  done
fi
```

Read `backup-meta.json` from the patches directory.

**If no patches found:**
```
No local patches found. Nothing to reapply.

Local patches are automatically saved when you run /gsd:update
after modifying any GSD workflow, command, or agent files.
```
Exit.

## Step 2: Determine baseline for three-way comparison

The quality of the merge depends on having a **pristine baseline** — the original unmodified version of each file from the pre-update GSD release. This enables three-way comparison:
- **Pristine baseline** (original GSD file before any user edits)
- **User's version** (backed up in `gsd-local-patches/`)
- **New version** (freshly installed after update)

Check for baseline sources in priority order:

### Option A: Pristine hash from backup-meta.json + git history (most reliable)
If the config directory is a git repository:
```bash
CONFIG_DIR=$(dirname "$PATCHES_DIR")
if git -C "$CONFIG_DIR" rev-parse --git-dir >/dev/null 2>&1; then
  HAS_GIT=true
fi
```
When `HAS_GIT=true`, use the `pristine_hashes` recorded in `backup-meta.json` to locate the correct baseline commit. For each file, iterate commits that touched it and find the one whose blob SHA-256 matches the recorded pristine hash:
```bash
# Get the expected pristine SHA-256 from backup-meta.json
PRISTINE_HASH=$(jq -r ".pristine_hashes[\"${file_path}\"] // empty" "$PATCHES_DIR/backup-meta.json")

BASELINE_COMMIT=""
if [ -n "$PRISTINE_HASH" ]; then
  # Walk commits that touched this file, pick the one matching the pristine hash
  while IFS= read -r commit_hash; do
    blob_hash=$(git -C "$CONFIG_DIR" show "${commit_hash}:${file_path}" 2>/dev/null | sha256sum | cut -d' ' -f1)
    if [ "$blob_hash" = "$PRISTINE_HASH" ]; then
      BASELINE_COMMIT="$commit_hash"
      break
    fi
  done < <(git -C "$CONFIG_DIR" log --format="%H" -- "${file_path}")
fi

# Fallback: if no pristine hash in backup-meta (older installer), use first-add commit
if [ -z "$BASELINE_COMMIT" ]; then
  BASELINE_COMMIT=$(git -C "$CONFIG_DIR" log --diff-filter=A --format="%H" -- "${file_path}" | tail -1)
fi
```
Extract the pristine version from the matched commit:
```bash
git -C "$CONFIG_DIR" show "${BASELINE_COMMIT}:${file_path}"
```

**Why this matters:** `git log --diff-filter=A` returns the commit that *first added* the file, which is the wrong baseline on repos that have been through multiple GSD update cycles. The `pristine_hashes` field in `backup-meta.json` records the SHA-256 of the file as it existed in the pre-update GSD release — matching against it finds the correct baseline regardless of how many updates have occurred.

### Option B: Pristine snapshot directory
Check if a `gsd-pristine/` directory exists alongside `gsd-local-patches/`:
```bash
PRISTINE_DIR="$CONFIG_DIR/gsd-pristine"
```
If it exists, the installer saved pristine copies at install time. Use these as the baseline.

### Option C: No baseline available (two-way fallback)
If neither git history nor pristine snapshots are available, fall back to two-way comparison — but with **strengthened heuristics** (see Step 3).

## Step 3: Show patch summary

```
## Local Patches to Reapply

**Backed up from:** v{from_version}
