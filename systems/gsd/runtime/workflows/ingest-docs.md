# Ingest Docs Workflow

Scan a repo for mixed planning documents (ADR, PRD, SPEC, DOC), synthesize them into a consolidated context, and bootstrap or merge into `.planning/`.

- `[path]` — optional target directory to scan (defaults to repo root)
- `--mode new|merge` — override auto-detect (defaults: `new` if `.planning/` absent, `merge` if present)
- `--manifest <file>` — YAML file listing `{path, type, precedence?}` per doc; overrides heuristic classification
- `--resolve auto|interactive` — conflict resolution (v1: only `auto` is supported; `interactive` is reserved)

---

<step name="banner">

Display the stage banner:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► INGEST DOCS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

</step>

<step name="parse_arguments">

Parse `$ARGUMENTS`:

- First positional token (if not a flag) → `SCAN_PATH` (default: `.`)
- `--mode new|merge` → `MODE` (default: auto-detect)
- `--manifest <file>` → `MANIFEST_PATH` (optional)
- `--resolve auto|interactive` → `RESOLVE_MODE` (default: `auto`; reject `interactive` in v1 with message "interactive resolution is planned for a future release")

**Validate paths:**

```bash
case "{SCAN_PATH}" in *..*) echo "SECURITY_ERROR: path contains traversal sequence"; exit 1 ;; esac
test -d "{SCAN_PATH}" || echo "PATH_NOT_FOUND"
if [ -n "{MANIFEST_PATH}" ]; then
  case "{MANIFEST_PATH}" in *..*) echo "SECURITY_ERROR: manifest path contains traversal"; exit 1 ;; esac
  test -f "{MANIFEST_PATH}" || echo "MANIFEST_NOT_FOUND"
fi
```

**Containment (required):** After resolving `SCAN_PATH` and `MANIFEST_PATH` relative to the repo root, canonicalize each with `realpath` (or platform equivalent) and assert the result is under `realpath("$REPO_ROOT")`. Reject absolute paths outside the repo (e.g. `/tmp`, `C:\Windows`) even when they do not contain `..`.

If `PATH_NOT_FOUND` or `MANIFEST_NOT_FOUND`: display error and exit.

</step>

<step name="init_and_mode_detect">

Run the init query:

```bash
INIT=$(node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" init ingest-docs)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Parse `project_exists`, `planning_exists`, `has_git`, `git_worktree_root`, `in_nested_subdir`, `project_path` from INIT.

**Auto-detect MODE** if not set:
- `planning_exists: true` → `MODE=merge`
- `planning_exists: false` → `MODE=new`

If user passed `--mode new` but `.planning/` already exists: display warning and require explicit confirm via `AskUserQuestion` (approve-revise-abort from `references/gate-prompts.md`) before overwriting.

Git initialisation (Bug #3491 — never create a nested `.git` inside an existing worktree):

- If `has_git: true` and `in_nested_subdir: true`: do NOT run `git init`. Surface a warning that planning files will be tracked by the outer repo at `git_worktree_root`.
- If `has_git: true` and `in_nested_subdir: false`: already at a worktree root, skip `git init`.
- If `has_git: false` and `MODE=new`: initialize git:

```bash
git init
```

**Detect runtime** using the same pattern as `new-project.md`:
- execution_context path `/.codex/` → `RUNTIME=codex`
- `/.gemini/` → `RUNTIME=gemini`
- `/.opencode/` or `/.config/opencode/` → `RUNTIME=opencode`
- else → `RUNTIME=claude`

Fall back to env vars (`CODEX_HOME`, `GEMINI_CONFIG_DIR`, `OPENCODE_CONFIG_DIR`) if execution_context is unavailable.

</step>

<step name="discover_docs">

Build the doc list from three sources, in order:

**1. Manifest (if provided)** — authoritative:

Read `MANIFEST_PATH`. Expected YAML shape:

```yaml
docs:
  - path: docs/adr/0001-db.md
    type: ADR
    precedence: 0   # optional, lower = higher precedence
  - path: docs/prd/auth.md
    type: PRD
```

Each entry provides `path` (required, relative to repo root) + `type` (required, one of ADR|PRD|SPEC|DOC) + `precedence` (optional integer).

**2. Directory conventions** (skipped when manifest is provided):

```bash
# ADRs
find {SCAN_PATH} -type f \( -path '*/adr/*' -o -path '*/adrs/*' -o -name 'ADR-*.md' -o -regex '.*/[0-9]\{4\}-.*\.md' \) 2>/dev/null

# PRDs
find {SCAN_PATH} -type f \( -path '*/prd/*' -o -path '*/prds/*' -o -name 'PRD-*.md' \) 2>/dev/null

# SPECs / RFCs
find {SCAN_PATH} -type f \( -path '*/spec/*' -o -path '*/specs/*' -o -path '*/rfc/*' -o -path '*/rfcs/*' -o -name 'SPEC-*.md' -o -name 'RFC-*.md' \) 2>/dev/null

# Generic docs (fall-through candidates)
find {SCAN_PATH} -type f -path '*/docs/*' -name '*.md' 2>/dev/null
```

De-duplicate the union (a file matched by multiple patterns is one doc).

**3. Content heuristics** (run during classification, not here) — the classifier handles frontmatter `type:` and H1 inspection for docs that didn't match a convention.

**Cap:** hard limit of 50 docs per invocation (documented v1 constraint). If the discovered set exceeds 50:

```
GSD > Discovered {N} docs, which exceeds the v1 cap of 50.
      Use --manifest to narrow the set to ≤ 50 files, or run
      /gsd:ingest-docs again with a narrower <path>.
```

Exit without proceeding.

**Display discovered set** and request approval (see `references/gate-prompts.md` — `yes-no-pick` pattern works; or `approve-revise-abort`):

```
Discovered {N} documents:
  {N} ADR | {N} PRD | {N} SPEC | {N} DOC | {N} unclassified

  docs/adr/0001-architecture.md       [ADR]    (from manifest|directory|heuristic)
  docs/adr/0002-database.md           [ADR]    (directory)
  docs/prd/auth.md                    [PRD]    (manifest)
  ...
```

**Text mode:** apply the same `--text`/`text_mode` rule as other workflows — replace `AskUserQuestion` with a numbered list.

Use `AskUserQuestion` (approve-revise-abort):
- question: "Proceed with classification of these {N} documents?"
- header: "Approve?"
- options: Approve | Revise | Abort

On Abort: exit cleanly with "Ingest cancelled."
On Revise: exit with guidance to re-run with `--manifest` or a narrower path.

