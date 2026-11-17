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

