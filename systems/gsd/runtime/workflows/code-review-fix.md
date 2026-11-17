<purpose>
Auto-fix issues from REVIEW.md. Validates phase, checks config gate, verifies REVIEW.md exists and has fixable issues, spawns gsd-code-fixer agent, handles --auto iteration loop (capped at 3), commits REVIEW-FIX.md once at the end, and presents results.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<available_agent_types>
- gsd-code-fixer: Applies fixes to code review findings
- gsd-code-reviewer: Reviews source files for bugs and issues
</available_agent_types>

<process>

<step name="initialize">
Parse arguments and load project state:

```bash
PHASE_ARG="${1}"
INIT=$(gsd-sdk query init.phase-op "${PHASE_ARG}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Parse from init JSON: `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `padded_phase`, `commit_docs`.

**Input sanitization (defense-in-depth):**
```bash
# Validate PADDED_PHASE contains only digits and optional dot (e.g., "02", "03.1")
if ! [[ "$PADDED_PHASE" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
  echo "Error: Invalid phase number format: '${PADDED_PHASE}'. Expected digits (e.g., 02, 03.1)."
  # Exit workflow
fi
```

**Phase validation (before config gate):**
If `phase_found` is false, report error and exit:
```
Error: Phase ${PHASE_ARG} not found. Run /gsd:progress to see available phases.
```

This runs BEFORE config gate check so user errors are surfaced immediately regardless of config state.

Parse optional flags from $ARGUMENTS:

```bash
FIX_ALL=false
AUTO_MODE=false
for arg in "$@"; do
  if [[ "$arg" == "--all" ]]; then FIX_ALL=true; fi
  if [[ "$arg" == "--auto" ]]; then AUTO_MODE=true; fi
done
```

Compute scope variable:

```bash
if [ "$FIX_ALL" = "true" ]; then
  FIX_SCOPE="all"
else
  FIX_SCOPE="critical_warning"
fi
```

Compute review and fix report paths:

```bash
REVIEW_PATH="${PHASE_DIR}/${PADDED_PHASE}-REVIEW.md"
FIX_REPORT_PATH="${PHASE_DIR}/${PADDED_PHASE}-REVIEW-FIX.md"
```
</step>

<step name="check_config_gate">
Check if code review is enabled via config:

```bash
CODE_REVIEW_ENABLED=$(gsd-sdk query config-get workflow.code_review 2>/dev/null || echo "true")
```

If CODE_REVIEW_ENABLED is "false":
```
Code review fix skipped (workflow.code_review=false in config)
```
Exit workflow.

Default is true — only skip on explicit false. This check runs AFTER phase validation so invalid phase errors are shown first.

Note: This reuses the `workflow.code_review` config key rather than introducing a separate `workflow.code_review_fix` key. Rationale: fixes are meaningless without review, so a single toggle makes sense. If independent control is needed later, a separate key can be added in v2.
</step>

<step name="check_review_exists">
Verify that REVIEW.md exists:

```bash
if [ ! -f "${REVIEW_PATH}" ]; then
  echo "Error: No REVIEW.md found for Phase ${PHASE_ARG}. Run /gsd:code-review ${PHASE_ARG} first."
  exit 1
fi
```

Do NOT auto-run code-review. Require explicit user action to ensure review intent is clear.
</step>

<step name="check_review_status">
Parse REVIEW.md frontmatter to check status and extract context for --auto loop:

```bash
# Parse status field
REVIEW_STATUS=$(REVIEW_PATH="${REVIEW_PATH}" node -e "
  const fs = require('fs');
  const content = fs.readFileSync(process.env.REVIEW_PATH, 'utf-8');
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (match && /status:\s*(\S+)/.test(match[1])) {
    console.log(match[1].match(/status:\s*(\S+)/)[1]);
  } else {
    console.log('unknown');
  }
" 2>/dev/null)
```

If status is "clean" or "skipped":
```
No issues to fix in Phase ${PHASE_ARG} REVIEW.md (status: ${REVIEW_STATUS}).
```
Exit workflow.

If status is "unknown":
```
Warning: Could not parse REVIEW.md status. Proceeding with fix attempt.
```

Extract review depth for --auto re-review:

```bash
REVIEW_DEPTH=$(REVIEW_PATH="${REVIEW_PATH}" node -e "
  const fs = require('fs');
  const content = fs.readFileSync(process.env.REVIEW_PATH, 'utf-8');
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (match && /depth:\s*(\S+)/.test(match[1])) {
    console.log(match[1].match(/depth:\s*(\S+)/)[1]);
  } else {
    console.log('standard');
  }
" 2>/dev/null)
```

Extract original review file list for --auto re-review scope persistence:

```bash
# Extract review file list — portable bash 3.2+ (no mapfile, handles spaces in paths)
REVIEW_FILES_ARRAY=()
while IFS= read -r line; do
  [ -n "$line" ] && REVIEW_FILES_ARRAY+=("$line")
done < <(REVIEW_PATH="${REVIEW_PATH}" node -e "
  const fs = require('fs');
  const content = fs.readFileSync(process.env.REVIEW_PATH, 'utf-8');
  const match = content.match(/^---\n([\s\S]*?)\n---/);
