<purpose>

Start a new milestone cycle for an existing project. Loads project context, gathers milestone goals (from MILESTONE-CONTEXT.md or conversation), updates PROJECT.md and STATE.md, optionally runs parallel research, defines scoped requirements with REQ-IDs, spawns the roadmapper to create phased execution plan, and commits all artifacts. Brownfield equivalent of new-project.

</purpose>

<required_reading>

Read all files referenced by the invoking prompt's execution_context before starting.

</required_reading>

<available_agent_types>
Valid GSD subagent types (use exact names — do not fall back to 'general-purpose'):
- gsd-project-researcher — Researches project-level technical decisions
- gsd-research-synthesizer — Synthesizes findings from parallel research agents
- gsd-roadmapper — Creates phased execution roadmaps
</available_agent_types>

<process>

## 1. Load Context

Parse `$ARGUMENTS` before doing anything else:
- `--reset-phase-numbers` flag → opt into restarting roadmap phase numbering at `1`
- remaining text → use as milestone name if present

If the flag is absent, keep the current behavior of continuing phase numbering from the previous milestone.

- Read PROJECT.md (existing project, validated requirements, decisions)
- Read MILESTONES.md (what shipped previously)
- Read STATE.md (pending todos, blockers)
- Check for MILESTONE-CONTEXT.md (from /gsd-discuss-milestone)

## 2. Gather Milestone Goals

**If MILESTONE-CONTEXT.md exists:**
- Use features and scope from discuss-milestone
- Present summary for confirmation

**If no context file:**
- Present what shipped in last milestone

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
- Ask inline (freeform, NOT AskUserQuestion): "What do you want to build next?"
- Wait for their response, then use AskUserQuestion to probe specifics
- If user selects "Other" at any point to provide freeform input, ask follow-up as plain text — not another AskUserQuestion

## 2.5. Scan Planted Seeds

Check `.planning/seeds/` for seed files that match the milestone goals gathered in step 2.

```bash
ls .planning/seeds/SEED-*.md 2>/dev/null
```

**If no seed files exist:** Skip this step silently — do not print any message or prompt.

**If seed files exist:** Read each `SEED-*.md` file and extract from its frontmatter and body:
- **Idea** — the seed title (heading after frontmatter, e.g. `# SEED-001: <idea>`)
- **Trigger conditions** — the `trigger_when` frontmatter field and the "When to Surface" section's bullet list
- **Planted during** — the `planted_during` frontmatter field (for context)

Compare each seed's trigger conditions against the milestone goals from step 2. A seed matches when its trigger conditions are relevant to any of the milestone's target features or goals.

**If no seeds match:** Skip silently — do not prompt the user.

**If matching seeds found:**

**`--auto` mode:** Auto-select ALL matching seeds. Log: `[auto] Selected N matching seed(s): [list seed names]`

**Text mode (`TEXT_MODE=true`):** Present matching seeds as a plain-text numbered list:
```
Seeds that match your milestone goals:
1. SEED-001: <idea> (trigger: <trigger_when>)
2. SEED-003: <idea> (trigger: <trigger_when>)

Enter numbers to include (comma-separated), or "none" to skip:
```

**Normal mode:** Present via AskUserQuestion:
```
AskUserQuestion(
  header: "Seeds",
  question: "These planted seeds match your milestone goals. Include any in this milestone's scope?",
  multiSelect: true,
  options: [
    { label: "SEED-001: <idea>", description: "Trigger: <trigger_when> | Planted during: <planted_during>" },
    ...
  ]
)
```

**After selection:**
- Selected seeds become additional context for requirement definition in step 9. Store them in an accumulator (e.g. `$SELECTED_SEEDS`) so step 9 can reference the ideas and their "Why This Matters" sections when defining requirements.
- Unselected seeds remain untouched in `.planning/seeds/` — never delete or modify seed files during this workflow.

## 3. Determine Milestone Version

- Parse last version from MILESTONES.md
- Suggest next version (v1.0 → v1.1, or v2.0 for major)
- Confirm with user

## 3.5. Verify Milestone Understanding

Before writing any files, present a summary of what was gathered and ask for confirmation.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► MILESTONE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Milestone v[X.Y]: [Name]**

**Goal:** [One sentence]

**Target features:**
- [Feature 1]
- [Feature 2]
- [Feature 3]

**Key context:** [Any important constraints, decisions, or notes from questioning]
```

AskUserQuestion:
- header: "Confirm?"
- question: "Does this capture what you want to build in this milestone?"
- options:
  - "Looks good" — Proceed to write PROJECT.md
  - "Adjust" — Let me correct or add details

**If "Adjust":** Ask what needs changing (plain text, NOT AskUserQuestion). Incorporate changes, re-present the summary. Loop until "Looks good" is selected.

**If "Looks good":** Proceed to Step 4.

## 4. Update PROJECT.md

Add/update:

```markdown
## Current Milestone: v[X.Y] [Name]

**Goal:** [One sentence describing milestone focus]

**Target features:**
- [Feature 1]
- [Feature 2]
- [Feature 3]
```

Update Active requirements section and "Last updated" footer.

Ensure the `## Evolution` section exists in PROJECT.md. If missing (projects created before this feature), add it before the footer:

```markdown
## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state
```

## 5. Update STATE.md

Reset STATE.md frontmatter AND body atomically via the SDK. This writes the new
milestone version/name into the YAML frontmatter, resets `status` to
`planning`, zeroes `progress.*` counters, and rewrites the `## Current Position`
section to the new-milestone template. Accumulated Context (decisions,
blockers, todos) is preserved across the switch — symmetric with
`milestone.complete`.

```bash
gsd-sdk query state.milestone-switch --milestone "v[X.Y]" --name "[Name]"
```

The resulting Current Position section looks like:

```markdown
## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: [today] — Milestone v[X.Y] started
```

Bug #2630: a prior version of this workflow rewrote the Current Position body
manually but left the frontmatter pointing at the previous milestone, so every
downstream reader (`state.json`, `getMilestoneInfo`, progress bars) reported the
stale milestone until the first phase advance forced a resync. Always use the
SDK handler above — do not hand-edit STATE.md here.

## 6. Cleanup and Commit

Delete MILESTONE-CONTEXT.md if exists (consumed).

Clear leftover phase directories from the previous milestone:

```bash
gsd-sdk query phases.clear --confirm
```

```bash
gsd-sdk query commit "docs: start milestone v[X.Y] [Name]" --files .planning/PROJECT.md .planning/STATE.md
```

## 7. Load Context and Resolve Models

```bash
INIT=$(gsd-sdk query init.new-milestone)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_RESEARCHER=$(gsd-sdk query agent-skills gsd-project-researcher)
AGENT_SKILLS_SYNTHESIZER=$(gsd-sdk query agent-skills gsd-research-synthesizer)
AGENT_SKILLS_ROADMAPPER=$(gsd-sdk query agent-skills gsd-roadmapper)
```

Extract from init JSON: `researcher_model`, `synthesizer_model`, `roadmapper_model`, `commit_docs`, `research_enabled`, `current_milestone`, `project_exists`, `roadmap_exists`, `latest_completed_milestone`, `phase_dir_count`, `phase_archive_path`, `agents_installed`, `missing_agents`.

**If `agents_installed` is false:** Display a warning before proceeding:
```
⚠ GSD agents not installed. The following agents are missing from your agents directory:
  {missing_agents joined with newline}

Subagent spawns (gsd-project-researcher, gsd-research-synthesizer, gsd-roadmapper) will fail
with "agent type not found". Run the installer with --global to make agents available:

  npx get-shit-done-cc@latest --global

Proceeding without research subagents — roadmap will be generated inline.
```
Skip the parallel research spawn step and generate the roadmap inline.

## 7.5 Reset-phase safety (only when `--reset-phase-numbers`)

If `--reset-phase-numbers` is active:

1. Set starting phase number to `1` for the upcoming roadmap.
2. If `phase_dir_count > 0`, archive the old phase directories before roadmapping so new `01-*` / `02-*` directories cannot collide with stale milestone directories.

If `phase_dir_count > 0` and `phase_archive_path` is available:

```bash
mkdir -p "${phase_archive_path}"
