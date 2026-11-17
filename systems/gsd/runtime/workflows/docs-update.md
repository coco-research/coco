<purpose>
Generate, update, and verify all project documentation — both canonical doc types and existing hand-written docs. The orchestrator detects the project's doc structure, assembles a work manifest tracking every item, dispatches parallel doc-writer and doc-verifier agents across waves, reviews existing docs for accuracy, identifies documentation gaps, and fixes inaccuracies via a bounded fix loop. All state is persisted in a work manifest so no work item is lost between steps. Output: Complete, structure-aware documentation verified against the live codebase.
</purpose>

<available_agent_types>
Valid GSD subagent types (use exact names — do not fall back to 'general-purpose'):
- gsd-doc-writer — Writes and updates project documentation files
- gsd-doc-verifier — Verifies factual claims in docs against the live codebase
</available_agent_types>

<process>

<step name="init_context" priority="first">
Load docs-update context:

```bash
INIT=$(gsd-sdk query docs-init)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS=$(gsd-sdk query agent-skills gsd-doc-writer)
```

Extract from init JSON:
- `doc_writer_model` — model string to pass to each spawned agent (never hardcode a model name)
- `commit_docs` — whether to commit generated files when done
- `existing_docs` — array of `{path, has_gsd_marker}` objects for existing Markdown files
- `project_type` — object with boolean signals: `has_package_json`, `has_api_routes`, `has_cli_bin`, `is_open_source`, `has_deploy_config`, `is_monorepo`, `has_tests`
- `doc_tooling` — object with booleans: `docusaurus`, `vitepress`, `mkdocs`, `storybook`
- `monorepo_workspaces` — array of workspace glob patterns (empty if not a monorepo)
- `project_root` — absolute path to the project root
</step>

<step name="classify_project">
Map the `project_type` boolean signals from the init JSON to a primary type label and collect conditional doc signals.

**Primary type classification (first match wins):**

| Condition | primary_type |
|-----------|-------------|
| `is_monorepo` is true | `"monorepo"` |
| `has_cli_bin` is true AND `has_api_routes` is false | `"cli-tool"` |
| `has_api_routes` is true AND `is_open_source` is false | `"saas"` |
| `is_open_source` is true AND `has_api_routes` is false | `"open-source-library"` |
| (none of the above) | `"generic"` |

**Conditional doc signals (D-02 union rule — check independently after primary classification):**

After determining primary_type, check each signal independently regardless of the primary type. A CLI tool that is also open source with API routes still gets all three conditional docs.

| Signal | Conditional Doc |
|--------|----------------|
| `has_api_routes` is true | Queue API.md |
| `is_open_source` is true | Queue CONTRIBUTING.md |
| `has_deploy_config` is true | Queue DEPLOYMENT.md |

Present the classification result:
```
Project type: {primary_type}
Conditional docs queued: {list or "none"}
```
</step>

<step name="build_doc_queue">
Assemble the complete doc queue from always-on docs plus conditional docs from classify_project.

**Always-on docs (queued for every project, no exceptions):**
1. README
2. ARCHITECTURE
3. GETTING-STARTED
4. DEVELOPMENT
5. TESTING
6. CONFIGURATION

**Conditional docs (add only if signal matched in classify_project):**
- API (if `has_api_routes`)
- CONTRIBUTING (if `is_open_source`)
- DEPLOYMENT (if `has_deploy_config`)

**IMPORTANT: CHANGELOG.md is NEVER queued. The doc queue is built exclusively from the 9 known doc types listed above. Do not derive the queue from `existing_docs` directly — existing_docs is only used in the next step to determine create vs update mode.**

**Doc queue limit:** Maximum 9 docs. Always-on (6) + up to 3 conditional = at most 9.

**CONTRIBUTING.md confirmation (new file only):**

If CONTRIBUTING.md is in the conditional queue AND does NOT appear in the `existing_docs` array from init JSON:

1. If `--force` is present in `$ARGUMENTS`: skip this check, include CONTRIBUTING.md in the queue.

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
2. Otherwise, use AskUserQuestion to confirm:

```
AskUserQuestion([{
  question: "This project appears to be open source (LICENSE file detected). CONTRIBUTING.md does not exist yet. Would you like to create one?",
  header: "Contributing",
  multiSelect: false,
  options: [
    { label: "Yes, create it", description: "Generate CONTRIBUTING.md with project guidelines" },
    { label: "No, skip it", description: "This project does not need a CONTRIBUTING.md" }
  ]
}])
```

If the user selects "No, skip it": remove CONTRIBUTING.md from the doc queue.
If CONTRIBUTING.md already exists in `existing_docs`: skip this prompt entirely, include it for update.

**Existing non-canonical docs (review queue):**

After assembling the canonical doc queue above, scan the `existing_docs` array from init JSON for files that do NOT match any canonical path in the queue (neither primary nor fallback path from the resolve_modes table). These are hand-written docs like `docs/api/endpoint-map.md` or `docs/frontend/pages/not-found.md`.

For each non-canonical existing doc found:
- Add to a separate `review_queue`
- These will be passed to gsd-doc-verifier in the verify_docs step for accuracy checking
- If inaccuracies are found, they will be dispatched to gsd-doc-writer in `fix` mode for surgical corrections

If non-canonical docs are found, display them in the queue presentation:

```
Existing docs queued for accuracy review:
  - docs/api/endpoint-map.md (hand-written)
  - docs/api/README.md (hand-written)
  - docs/frontend/pages/not-found.md (hand-written)
```

If none found, omit this section from the queue presentation.

**Documentation gap detection (missing non-canonical docs):**

After assembling the canonical and review queues, analyze the codebase to identify areas that should have documentation but don't. This ensures the command creates complete project documentation, not just the 9 canonical types.

1. **Scan the codebase for undocumented areas:**
   - Use Glob/Grep to discover significant source directories (e.g., `src/components/`, `src/pages/`, `src/services/`, `src/api/`, `lib/`, `routes/`)
   - Compare against existing docs: for each major source directory, check if corresponding documentation exists in the docs tree
   - Look at the project's existing doc structure for patterns — if the project has `docs/frontend/components/`, `docs/services/`, etc., these indicate the project's documentation conventions

2. **Identify gaps based on project conventions:**
   - If the project has a `docs/` directory with grouped subdirectories, each source module area that has a corresponding docs subdirectory but is missing documentation files represents a gap
   - If the project has frontend components/pages but no component docs, flag this
   - If the project has service modules but no service docs, flag this
   - Skip areas that are already covered by canonical docs (e.g., don't flag missing API docs if `docs/API.md` is already in the canonical queue)

3. **Present discovered gaps to the user:**

```
AskUserQuestion([{
  question: "Found {N} documentation gaps in the codebase. Which should be created?",
  header: "Doc gaps",
  multiSelect: true,
  options: [
    { label: "{area}", description: "{why it needs docs — e.g., '5 components in src/components/ with no docs'}" },
    ...up to 4 options (group related gaps if more than 4)
  ]
}])
```

4. For each gap the user selects:
   - Add to the generation queue with mode = `"create"`
   - Set the output path to match the project's existing doc directory structure
   - The gsd-doc-writer will receive a `doc_assignment` with `type: "custom"` and a description of what to document, using the project's source files as content discovery targets

If no gaps are detected, omit this section entirely.

Present the assembled queue to the user before proceeding:

Present the mode resolution table from resolve_modes (shown above), followed by:

```
{If non-canonical docs found, show as a table:}

Existing docs queued for accuracy review:

| Path | Type |
|------|------|
| {path} | hand-written |
| ... | ... |

CHANGELOG.md: excluded (out of scope)
```

The mode resolution table IS the queue presentation — it shows every doc with its resolved path, mode, and source. Do not duplicate the list in a separate format.

Then confirm with AskUserQuestion:

```
AskUserQuestion([{
  question: "Doc queue assembled ({N} docs). Proceed with generation?",
  header: "Doc queue",
  multiSelect: false,
  options: [
    { label: "Proceed", description: "Generate all {N} docs in the queue" },
    { label: "Abort", description: "Cancel doc generation" }
  ]
}])
```

If the user selects "Abort": exit the workflow. Otherwise continue to resolve_modes.
</step>

<step name="resolve_modes">
For each doc in the assembled queue, determine whether to create (new file) or update (existing file).

**Doc type to canonical path mapping (defaults):**

| Type | Default Path | Fallback Path |
|------|-------------|---------------|
| `readme` | `README.md` | — |
| `architecture` | `docs/ARCHITECTURE.md` | `ARCHITECTURE.md` |
| `getting_started` | `docs/GETTING-STARTED.md` | `GETTING-STARTED.md` |
| `development` | `docs/DEVELOPMENT.md` | `DEVELOPMENT.md` |
| `testing` | `docs/TESTING.md` | `TESTING.md` |
| `api` | `docs/API.md` | `API.md` |
| `configuration` | `docs/CONFIGURATION.md` | `CONFIGURATION.md` |
| `deployment` | `docs/DEPLOYMENT.md` | `DEPLOYMENT.md` |
| `contributing` | `CONTRIBUTING.md` | — |

**Structure-aware path resolution:**

Before applying the default path table, inspect the project's existing docs directory structure to detect whether the project uses **grouped subdirectories** or **flat files**. This determines how ALL new docs are placed.

**Step 1: Detect the project's docs organization pattern.**

List subdirectories under `docs/` from the `existing_docs` paths. If the project has 2+ subdirectories (e.g., `docs/architecture/`, `docs/api/`, `docs/guides/`, `docs/frontend/`), the project uses a **grouped structure**. If docs are only flat files directly in `docs/` (e.g., `docs/ARCHITECTURE.md`), it uses a **flat structure**.

**Step 2: Resolve paths based on the detected pattern.**

**If GROUPED structure detected:**

Every doc type MUST be placed in an appropriate subdirectory — no doc should be left flat in `docs/` when the project organizes into groups. Use the following resolution logic:

| Type | Subdirectory resolution (in priority order) |
|------|----------------------------------------------|
| `architecture` | existing `docs/architecture/` → create `docs/architecture/` if not present |
| `getting_started` | existing `docs/guides/` → existing `docs/getting-started/` → create `docs/guides/` |
| `development` | existing `docs/guides/` → existing `docs/development/` → create `docs/guides/` |
| `testing` | existing `docs/testing/` → existing `docs/guides/` → create `docs/testing/` |
| `api` | existing `docs/api/` → create `docs/api/` if not present |
| `configuration` | existing `docs/configuration/` → existing `docs/guides/` → create `docs/configuration/` |
| `deployment` | existing `docs/deployment/` → existing `docs/guides/` → create `docs/deployment/` |

For each type, check the resolution chain left-to-right. Use the first existing subdirectory. If none exist, create the rightmost option.

The filename within the subdirectory should be contextual — e.g., `docs/guides/getting-started.md`, `docs/architecture/overview.md`, `docs/api/reference.md` — rather than `docs/architecture/ARCHITECTURE.md`. Match the naming style of existing files in that subdirectory (lowercase-kebab, UPPERCASE, etc.).

**If FLAT structure detected (or no docs/ directory):**

Use the default path table above as-is (e.g., `docs/ARCHITECTURE.md`, `docs/TESTING.md`).

**Step 3: Store each resolved path and create directories.**

For each doc type, store the resolved path as `resolved_path`. Then create all necessary directories:
```bash
mkdir -p {each unique directory from resolved paths}
```

**Mode resolution logic:**

For each doc type in the queue:
1. Check if the `resolved_path` appears in the `existing_docs` array from the init JSON
2. If not found at resolved path, check the default and fallback paths from the table
3. If found at any path: mode = `"update"` — use the Read tool to load the current file content (will be passed as `existing_content` in the doc_assignment block). Use the found path as the output path (do not move existing docs).
4. If not found: mode = `"create"` — no existing content to load. Use the `resolved_path`.

**Ensure docs/ directory exists:**
Before proceeding to the next step, create the `docs/` directory and any resolved subdirectories if they do not exist:
```bash
mkdir -p docs/
```

**Output a mode resolution table:**

Present a table showing the resolved path, mode, and source for every doc in the queue:

```
Mode resolution:

| Doc | Resolved Path | Mode | Source |
|-----|---------------|------|--------|
| readme | README.md | update | found at README.md |
| architecture | docs/architecture/overview.md | create | new directory |
| getting_started | docs/guides/getting-started.md | update | found, hand-written |
| development | docs/guides/development.md | create | matched docs/guides/ |
| testing | docs/guides/testing.md | create | matched docs/guides/ |
| configuration | docs/guides/configuration.md | create | matched docs/guides/ |
| api | docs/api/reference.md | create | new directory |
| deployment | docs/guides/deployment.md | update | found, hand-written |
```

This table MUST be shown to the user — it is the primary confirmation of where files will be written and whether existing files will be updated. It appears as part of the queue presentation BEFORE the AskUserQuestion confirmation.

Track the resolved mode and file path for each queued doc. For update-mode docs, store the loaded file content — it will be passed to the agent in the next steps.

**CRITICAL: Persist the work manifest.**

After resolve_modes completes, write ALL work items to `.planning/tmp/docs-work-manifest.json`. This is the single source of truth for every subsequent step — the orchestrator MUST read this file at each step instead of relying on memory.

```bash
mkdir -p .planning/tmp
```

Write the manifest using the Write tool:

```json
{
  "canonical_queue": [
    {
      "type": "readme",
      "resolved_path": "README.md",
      "mode": "create|update|supplement",
      "preservation_mode": null,
      "wave": 1,
      "status": "pending"
    }
  ],
  "review_queue": [
    {
      "path": "docs/frontend/components/button.md",
      "type": "hand-written",
      "status": "pending_review"
    }
  ],
  "gap_queue": [
    {
      "description": "Frontend components in src/components/",
      "output_path": "docs/frontend/components/overview.md",
      "status": "pending"
    }
  ],
  "created_at": "{ISO timestamp}"
}
```

Every subsequent step (dispatch, collect, verify, fix_loop, report) MUST begin by reading `.planning/tmp/docs-work-manifest.json` and update the `status` field for items it processes. This prevents the orchestrator from "forgetting" any work item across the multi-step workflow.
</step>

<step name="preservation_check">
Check for hand-written docs in the queue and gather user decisions before dispatch.

**Skip conditions (check in order):**

1. If `--force` is present in `$ARGUMENTS`: treat all docs as mode: regenerate, skip to detect_runtime_capabilities.
2. If `--verify-only` is present in `$ARGUMENTS`: skip to verify_only_report (do not continue to detect_runtime_capabilities).
3. If no docs in the queue have `has_gsd_marker: false` in the `existing_docs` array: skip to detect_runtime_capabilities.

**For each queued doc where `has_gsd_marker` is false (hand-written doc detected):**

Present the following choice using `AskUserQuestion` if available, or inline prompt otherwise:

```
{filename} appears to be hand-written (no GSD marker found).

How should this file be handled?
  [1] preserve    -- Skip entirely. Leave unchanged.
  [2] supplement  -- Append only missing sections. Existing content untouched.
  [3] regenerate  -- Overwrite with a fresh GSD-generated doc.
```

Record each decision. Update the doc queue:
- `preserve` decisions: remove the doc from the queue entirely
- `supplement` decisions: set mode to `supplement` in the doc_assignment block; include `existing_content` (full file content)
- `regenerate` decisions: set mode to `create` (treat as a fresh write)

**Fallback when AskUserQuestion is unavailable:** Default all hand-written docs to `preserve` (safest default). Display message:

```
AskUserQuestion unavailable — hand-written docs preserved by default.
Use --force to regenerate all docs, or re-run in Claude Code to get per-file prompts.
```

After all decisions recorded, continue to detect_runtime_capabilities.
</step>

<!-- If Task tool is unavailable at runtime, skip dispatch/collect waves and use sequential_generation instead. -->

<step name="dispatch_wave_1" condition="Task tool is available">
**Read the work manifest first:** `Read .planning/tmp/docs-work-manifest.json` — use `canonical_queue` items with `wave: 1` for this step.

Spawn 3 parallel gsd-doc-writer agents for Wave 1 docs: README, ARCHITECTURE, CONFIGURATION.

These are foundational docs with no cross-references needed, making them ideal for parallel generation.

Use `run_in_background=true` for all three to enable parallel execution.

**Agent 1: README**

```
Agent(
  subagent_type="gsd-doc-writer",
  model="{doc_writer_model}",
  run_in_background=true,
  description="Generate README.md for target project",
  prompt="<doc_assignment>
type: readme
mode: {create|update|supplement}
preservation_mode: {preserve|supplement|regenerate|null}
project_context: {INIT JSON}
{existing_content: | (include full file content here if mode is update or supplement, else omit this line)}
</doc_assignment>

{AGENT_SKILLS}

Write the doc file directly. Return confirmation only — do not return doc content."
)
```

**Agent 2: ARCHITECTURE**

```
Agent(
  subagent_type="gsd-doc-writer",
  model="{doc_writer_model}",
  run_in_background=true,
  description="Generate ARCHITECTURE.md for target project",
  prompt="<doc_assignment>
type: architecture
mode: {create|update|supplement}
preservation_mode: {preserve|supplement|regenerate|null}
project_context: {INIT JSON}
{existing_content: | (include full file content here if mode is update or supplement, else omit this line)}
</doc_assignment>

{AGENT_SKILLS}

Write the doc file directly. Return confirmation only — do not return doc content."
)
```

**Agent 3: CONFIGURATION**

```
Agent(
  subagent_type="gsd-doc-writer",
  model="{doc_writer_model}",
  run_in_background=true,
  description="Generate CONFIGURATION.md for target project",
  prompt="<doc_assignment>
type: configuration
mode: {create|update|supplement}
preservation_mode: {preserve|supplement|regenerate|null}
project_context: {INIT JSON}
{existing_content: | (include full file content here if mode is update or supplement, else omit this line)}
note: Apply VERIFY markers to any infrastructure claim not discoverable from the repository.
</doc_assignment>

{AGENT_SKILLS}

Write the doc file directly. Return confirmation only — do not return doc content."
)
```

**CRITICAL:** Agent prompts must contain ONLY the `<doc_assignment>` block, the `${AGENT_SKILLS}` variable, and the return instruction. Do not include project planning context, workflow prose, or any internal tooling references in agent prompts.

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling all Wave 1 Agent() calls above with `run_in_background=true`, do NOT generate any documentation independently while the subagents are active. Wait for all Wave 1 agents to complete before proceeding. This prevents duplicate work and wasted context.

Continue to collect_wave_1.
</step>

<step name="collect_wave_1">
**Read the work manifest first:** `Read .planning/tmp/docs-work-manifest.json` — update `status` to `"completed"` or `"failed"` for each Wave 1 item after collection. Write the updated manifest back to disk.

Wait for all 3 Wave 1 agents to complete using the TaskOutput tool.

Call TaskOutput for all 3 agents in parallel (single message with 3 TaskOutput calls):

```
TaskOutput tool:
  task_id: "{task_id from README agent result}"
  block: true
  timeout: 300000

TaskOutput tool:
  task_id: "{task_id from ARCHITECTURE agent result}"
  block: true
  timeout: 300000

TaskOutput tool:
  task_id: "{task_id from CONFIGURATION agent result}"
  block: true
  timeout: 300000
```

**Expected confirmation format from each agent:**
```
## Doc Generation Complete
**Type:** {type}
**Mode:** {mode}
**File written:** `{path}` ({N} lines)
Ready for orchestrator summary.
```

**After collection, verify the Wave 1 files exist on disk** using the `resolved_path` from each manifest entry:
```bash
ls -la {resolved_path_1} {resolved_path_2} {resolved_path_3} 2>/dev/null
```

If any agent failed or its file is missing:
- Note the failure
- Continue with the successful docs (do NOT halt Wave 2 for a single failure)
- The missing doc will be noted in the final report

Continue to dispatch_wave_2.
</step>

<step name="dispatch_wave_2" condition="Task tool is available">
**Read the work manifest first:** `Read .planning/tmp/docs-work-manifest.json` — use `canonical_queue` items with `wave: 2` for this step.

Spawn agents for all queued Wave 2 docs: GETTING-STARTED, DEVELOPMENT, TESTING, and any conditional docs (API, DEPLOYMENT, CONTRIBUTING) that were queued in build_doc_queue.

Wave 2 agents can reference Wave 1 outputs for cross-referencing — include the `wave_1_outputs` field in each doc_assignment block.

Use `run_in_background=true` for all Wave 2 agents to enable parallel execution within the wave.

**Agent: GETTING-STARTED**

```
Agent(
  subagent_type="gsd-doc-writer",
