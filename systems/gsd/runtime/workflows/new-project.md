<purpose>
Initialize a new project through unified flow: questioning, research (optional), requirements, roadmap. This is the most leveraged moment in any project — deep questioning here means better plans, better execution, better outcomes. One workflow takes you from idea to ready-for-planning.
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

<auto_mode>

## Auto Mode Detection

Check if `--auto` flag is present in $ARGUMENTS.

**If auto mode:**

- Skip brownfield mapping offer (assume greenfield)
- Skip deep questioning (extract context from provided document)
- Config: YOLO mode is implicit (skip that question), but ask granularity/git/agents FIRST (Step 2a)
- After config: run Steps 6-9 automatically with smart defaults:
  - Research: Always yes
  - Requirements: Include all table stakes + features from provided document
  - Requirements approval: Auto-approve
  - Roadmap approval: Auto-approve

**Document requirement:**
Auto mode requires an idea document — either:

- File reference: `/gsd:new-project --auto @prd.md`
- Pasted/written text in the prompt

If no document content provided, error:

```
Error: --auto requires an idea document.

Usage:
  /gsd:new-project --auto @your-idea.md
  /gsd:new-project --auto [paste or write your idea here]

The document should describe what you want to build.
```

</auto_mode>

<process>

## 1. Setup

**MANDATORY FIRST STEP — Execute these checks before ANY user interaction:**

```bash
INIT=$(gsd-sdk query init.new-project)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_RESEARCHER=$(gsd-sdk query agent-skills gsd-project-researcher)
AGENT_SKILLS_SYNTHESIZER=$(gsd-sdk query agent-skills gsd-research-synthesizer)
AGENT_SKILLS_ROADMAPPER=$(gsd-sdk query agent-skills gsd-roadmapper)
```

Parse JSON for: `researcher_model`, `synthesizer_model`, `roadmapper_model`, `commit_docs`, `project_exists`, `has_codebase_map`, `planning_exists`, `has_existing_code`, `has_package_file`, `is_brownfield`, `needs_codebase_map`, `has_git`, `git_worktree_root`, `in_nested_subdir`, `project_path`, `agents_installed`, `missing_agents`, `agent_runtime`, `agents_dir`, `required_agents`, `required_agents_installed`, `missing_required_agents`, `agent_skill_payloads_available`, `agent_skill_payload_agents`.

**If `agents_installed` is false:** Display a warning before proceeding:
```text
⚠ GSD agents not installed. The following agents are missing from your agents directory:
  {missing_agents joined with newline}

Runtime checked: {agent_runtime}
Agents directory checked: {agents_dir}
Required new-project agents missing:
  {missing_required_agents joined with newline, or "none"}

Agent skill payloads available: {agent_skill_payloads_available}
Agent skill payload agents:
  {agent_skill_payload_agents joined with newline, or "none"}

Skill payloads only provide prompt context. Named subagent spawns still require agent
definitions to be installed for this runtime.

Subagent spawns (gsd-project-researcher, gsd-research-synthesizer, gsd-roadmapper) will fail
with "agent type not found" if `required_agents_installed` is false. Run the installer with --global to make agents available:

  npx get-shit-done-cc@latest --global

Proceeding without research subagents — roadmap will be generated inline.
```
Skip Steps 6–7 (parallel research and synthesis) and proceed directly to roadmap creation in Step 8.

**Detect runtime and set instruction file name:**

Derive `RUNTIME` from the invoking prompt's `execution_context` path:
- Path contains `/.codex/` → `RUNTIME=codex`
- Path contains `/.gemini/` → `RUNTIME=gemini`
- Path contains `/.config/opencode/` or `/.opencode/` → `RUNTIME=opencode`
- Otherwise → `RUNTIME=claude`

If `execution_context` path is not available, fall back to env vars:
```bash
if [ -n "$CODEX_HOME" ]; then RUNTIME="codex"
elif [ -n "$GEMINI_CONFIG_DIR" ]; then RUNTIME="gemini"
elif [ -n "$OPENCODE_CONFIG_DIR" ] || [ -n "$OPENCODE_CONFIG" ]; then RUNTIME="opencode"
else RUNTIME="claude"; fi
```

Set the instruction file variable:
```bash
if [ "$RUNTIME" = "codex" ]; then INSTRUCTION_FILE="AGENTS.md"; else INSTRUCTION_FILE="CLAUDE.md"; fi
```

All subsequent references to the project instruction file use `$INSTRUCTION_FILE`.

**If `project_exists` is true:** Error — project already initialized. Use `/gsd:progress`.

**Git init (#3491 — never nest `.git` inside an existing worktree):**

- If `has_git` true and `in_nested_subdir` true: skip `git init`; warn `⚠ Initializing inside existing worktree (${git_worktree_root}); planning files will track to outer repo.`
- If `has_git` true and `in_nested_subdir` false: skip `git init` (already at worktree root).
- If `has_git` false: `git init`.

## 2. Brownfield Offer

**If auto mode:** Skip to Step 4 (assume greenfield, synthesize PROJECT.md from provided document).

**If `needs_codebase_map` is true** (from init — existing code detected but no codebase map):


**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
Use AskUserQuestion:

- header: "Codebase"
- question: "I detected existing code in this directory. Would you like to map the codebase first?"
- options:
  - "Map codebase first" — Run /gsd:map-codebase to understand existing architecture (Recommended)
  - "Skip mapping" — Proceed with project initialization

**If "Map codebase first":**

```
Run `/gsd:map-codebase` first, then return to `/gsd:new-project`
```

Exit command.

**If "Skip mapping" OR `needs_codebase_map` is false:** Continue to Step 3.

## 2a. Auto Mode Config (auto mode only)

**If auto mode:** Collect config settings upfront before processing the idea document.

YOLO mode is implicit (auto = YOLO). Ask remaining config questions:

**Round 1 — Core settings (3 questions, no Mode question):**

```
AskUserQuestion([
  {
    header: "Granularity",
    question: "How finely should scope be sliced into phases?",
    multiSelect: false,
    options: [
      { label: "Coarse (Recommended)", description: "Fewer, broader phases (3-5 phases, 1-3 plans each)" },
      { label: "Standard", description: "Balanced phase size (5-8 phases, 3-5 plans each)" },
      { label: "Fine", description: "Many focused phases (8-12 phases, 5-10 plans each)" }
    ]
  },
  {
    header: "Execution",
    question: "Run plans in parallel?",
    multiSelect: false,
    options: [
      { label: "Parallel (Recommended)", description: "Independent plans run simultaneously" },
      { label: "Sequential", description: "One plan at a time" }
    ]
  },
  {
    header: "Git Tracking",
    question: "Commit planning docs to git?",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Planning docs tracked in version control" },
      { label: "No", description: "Keep .planning/ local-only (add to .gitignore)" }
    ]
  }
])
```

**Round 2 — Workflow agents (same as Step 5):**

```
AskUserQuestion([
  {
    header: "Research",
    question: "Research before planning each phase? (adds tokens/time)",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Investigate domain, find patterns, surface gotchas" },
      { label: "No", description: "Plan directly from requirements" }
    ]
  },
  {
    header: "Plan Check",
    question: "Verify plans will achieve their goals? (adds tokens/time)",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Catch gaps before execution starts" },
      { label: "No", description: "Execute plans without verification" }
    ]
  },
  {
    header: "Verifier",
    question: "Verify work satisfies requirements after each phase? (adds tokens/time)",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Confirm deliverables match phase goals" },
      { label: "No", description: "Trust execution, skip verification" }
    ]
  },
  {
    header: "AI Models",
    question: "Which AI models for planning agents?",
    multiSelect: false,
    options: [
      { label: "Balanced (Recommended)", description: "Sonnet for most agents — good quality/cost ratio" },
      { label: "Quality", description: "Opus for research/roadmap — higher cost, deeper analysis" },
      { label: "Budget", description: "Haiku where possible — fastest, lowest cost" },
      { label: "Inherit", description: "Use the current session model for all agents (OpenCode /model)" }
    ]
  }
])
```

**Round 3 — PR body onboarding:**

Ask which optional PRD-style sections `/gsd:ship` should append to generated PR bodies. These map to `ship.pr_body_sections`; selected sections are written with `"enabled": true`, unselected seeded sections are written with `"enabled": false` so the project can enable them later without editing `ship.md`.

Prefer lean/agile PRD sections that make the delivered increment clear: user stories, acceptance criteria, Definition of Done or release criteria, risks, dependencies, and stakeholder review.

```
AskUserQuestion([
  {
    header: "PR Body",
    question: "Which optional PRD-style sections should /gsd:ship include in PR bodies?",
    multiSelect: true,
    options: [
      { label: "User Stories & Acceptance Criteria", description: "Append user-facing stories and acceptance checks from REQUIREMENTS.md" },
      { label: "Risks & Dependencies", description: "Append rollout risks, dependencies, and rollback notes from PLAN.md" },
      { label: "Success Metrics & Release Criteria", description: "Append measurable Definition of Done and release checks for stakeholder review" },
      { label: "Stakeholder Review & Approval", description: "Append approval checklist for projects that need sign-off traceability" }
    ]
  }
])
```

Build `ship.pr_body_sections` from those choices. For selected options, set `enabled: true`; for seeded but unselected options, set `enabled: false`. If the user selects none, use `"ship":{"pr_body_sections":[]}`.

Create `.planning/config.json` with all settings (CLI fills in remaining defaults automatically):

```bash
mkdir -p .planning
gsd-sdk query config-new-project '{"mode":"yolo","granularity":"[selected]","parallelization":true|false,"commit_docs":true|false,"model_profile":"quality|balanced|budget|inherit","workflow":{"research":true|false,"plan_check":true|false,"verifier":true|false,"nyquist_validation":true|false,"auto_advance":true},"ship":{"pr_body_sections":[{"heading":"User Stories & Acceptance Criteria","enabled":true|false,"source":"REQUIREMENTS.md ## User Stories || REQUIREMENTS.md ## Acceptance Criteria","fallback":"- Acceptance criteria are covered by the linked requirements and verification evidence."},{"heading":"Risks & Dependencies","enabled":true|false,"source":"PLAN.md ## Risks || PLAN.md ## Dependencies","fallback":"- No known high-risk rollout dependencies."},{"heading":"Success Metrics & Release Criteria","enabled":true|false,"source":"REQUIREMENTS.md ## Definition of Done || VERIFICATION.md ## Release Criteria","fallback":"- Release when automated verification and required manual checks pass."},{"heading":"Stakeholder Review & Approval","enabled":true|false,"template":"- Product owner approval pending for {phase_name}."}]}}'
```

**If commit_docs = No:** Add `.planning/` to `.gitignore`.

**Commit config.json:**

```bash
mkdir -p .planning
gsd-sdk query commit "chore: add project config" --files .planning/config.json
```

**Persist auto-advance chain flag to config (survives context compaction):**

```bash
gsd-sdk query config-set workflow._auto_chain_active true
```

Proceed to Step 4 (skip Steps 3 and 5).

## 2b. Prior Spike/Sketch Detection

Check for existing spike and sketch work that should inform project setup:

```bash
# Check for spike findings skill (project-local)
SPIKE_SKILL=$(ls ./.claude/skills/spike-findings-*/SKILL.md 2>/dev/null | head -1 || true)

# Check for sketch findings skill (project-local)
SKETCH_SKILL=$(ls ./.claude/skills/sketch-findings-*/SKILL.md 2>/dev/null | head -1 || true)

# Check for raw spikes/sketches in .planning/
HAS_SPIKES=$(ls .planning/spikes/MANIFEST.md 2>/dev/null)
HAS_SKETCHES=$(ls .planning/sketches/MANIFEST.md 2>/dev/null)
```

If any of these exist, surface them before questioning:

```
⚡ Prior exploration detected:
{if SPIKE_SKILL}  ✓ Spike findings skill: {path} — validated patterns from experiments
{if SKETCH_SKILL}  ✓ Sketch findings skill: {path} — validated design decisions
{if HAS_SPIKES && !SPIKE_SKILL}  ◆ Raw spikes in .planning/spikes/ — consider `/gsd:spike --wrap-up` to package findings
{if HAS_SKETCHES && !SKETCH_SKILL}  ◆ Raw sketches in .planning/sketches/ — consider `/gsd:sketch --wrap-up` to package findings

These findings will be incorporated into project context and available to planning agents.
```

If spike/sketch findings skills exist, read their SKILL.md files to inform the questioning phase — they contain validated patterns, constraints, and design decisions that should shape the project definition.

## 3. Deep Questioning

**If auto mode:** Skip (already handled in Step 2a). Extract project context from provided document instead and proceed to Step 4.

**Display stage banner:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► QUESTIONING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Open the conversation:**

Ask inline (freeform, NOT AskUserQuestion):

"What do you want to build?"

Wait for their response. This gives you the context needed to ask intelligent follow-up questions.

**Research-before-questions mode:** Check if `workflow.research_before_questions` is enabled in `.planning/config.json` (or the config from init context). When enabled, before asking follow-up questions about a topic area:

1. Do a brief web search for best practices related to what the user described
2. Mention key findings naturally as you ask questions (e.g., "Most projects like this use X — is that what you're thinking, or something different?")
3. This makes questions more informed without changing the conversational flow

When disabled (default), ask questions directly as before.

**Follow the thread:**

Based on what they said, ask follow-up questions that dig into their response. Use AskUserQuestion with options that probe what they mentioned — interpretations, clarifications, concrete examples.

Keep following threads. Each answer opens new threads to explore. Ask about:

- What excited them
- What problem sparked this
- What they mean by vague terms
- What it would actually look like
- What's already decided

Consult `questioning.md` for techniques:

- Challenge vagueness
- Make abstract concrete
- Surface assumptions
- Find edges
- Reveal motivation

**Check context (background, not out loud):**

As you go, mentally check the context checklist from `questioning.md`. If gaps remain, weave questions naturally. Don't suddenly switch to checklist mode.

**Decision gate:**

When you could write a clear PROJECT.md, use AskUserQuestion:

- header: "Ready?"
- question: "I think I understand what you're after. Ready to create PROJECT.md?"
- options:
  - "Create PROJECT.md" — Let's move forward
  - "Keep exploring" — I want to share more / ask me more

If "Keep exploring" — ask what they want to add, or identify gaps and probe naturally.

Loop until "Create PROJECT.md" selected.

## 4. Write PROJECT.md

**If auto mode:** Synthesize from provided document. No "Ready?" gate was shown — proceed directly to commit.

Synthesize all context into `.planning/PROJECT.md` using the template from `templates/project.md`.

**For greenfield projects:**

Initialize requirements as hypotheses:

```markdown
## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] [Requirement 1]
- [ ] [Requirement 2]
- [ ] [Requirement 3]

### Out of Scope

- [Exclusion 1] — [why]
- [Exclusion 2] — [why]
```

All Active requirements are hypotheses until shipped and validated.

**For brownfield projects (codebase map exists):**

Infer Validated requirements from existing code:

1. Read `.planning/codebase/ARCHITECTURE.md` and `STACK.md`
2. Identify what the codebase already does
3. These become the initial Validated set

```markdown
## Requirements

### Validated

- ✓ [Existing capability 1] — existing
- ✓ [Existing capability 2] — existing
- ✓ [Existing capability 3] — existing

### Active

- [ ] [New requirement 1]
- [ ] [New requirement 2]

### Out of Scope

- [Exclusion 1] — [why]
```

**Key Decisions:**

Initialize with any decisions made during questioning:

```markdown
## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| [Choice from questioning] | [Why] | — Pending |
```

**Last updated footer:**

```markdown
---
*Last updated: [date] after initialization*
```

**Evolution section** (include at the end of PROJECT.md, before the footer):

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

Do not compress. Capture everything gathered.

**Commit PROJECT.md:**

```bash
mkdir -p .planning
gsd-sdk query commit "docs: initialize project" --files .planning/PROJECT.md
```

## 5. Workflow Preferences

**If auto mode:** Skip — config was collected in Step 2a. Proceed to Step 5.5.

**Check for global defaults** at `~/.gsd/defaults.json`. If the file exists, read and display its contents before asking:

```bash
DEFAULTS_RAW=$(cat ~/.gsd/defaults.json 2>/dev/null)
```

Format the JSON into human-readable bullets using these label mappings:
- `mode` → "Mode"
- `granularity` → "Granularity"
- `parallelization` → "Execution" (`true` → "Parallel", `false` → "Sequential")
- `commit_docs` → "Git Tracking" (`true` → "Yes", `false` → "No")
- `model_profile` → "AI Models"
- `workflow.research` → "Research" (`true` → "Yes", `false` → "No")
- `workflow.plan_check` → "Plan Check" (`true` → "Yes", `false` → "No")
- `workflow.verifier` → "Verifier" (`true` → "Yes", `false` → "No")

Display above the prompt:

```text
Your saved defaults (~/.gsd/defaults.json):
  • Mode: [value]
  • Granularity: [value]
  • Execution: [Parallel|Sequential]
  • Git Tracking: [Yes|No]
  • AI Models: [value]
  • Research: [Yes|No]
  • Plan Check: [Yes|No]
  • Verifier: [Yes|No]
```

Then ask:

```text
AskUserQuestion([
  {
    question: "Use these saved defaults?",
    header: "Defaults",
    multiSelect: false,
    options: [
      { label: "Use as-is (Recommended)", description: "Proceed with the defaults shown above" },
      { label: "Modify some settings", description: "Keep defaults, change a few" },
      { label: "Configure fresh", description: "Walk through all questions from scratch" }
    ]
  }
])
```

**If "Use as-is":** use the defaults values for config.json and skip directly to **Commit config.json** below.

**If "Modify some settings":** present a selection of every setting with its current saved value.

**If TEXT_MODE is active** (non-Claude runtimes): display a numbered list and ask the user to type the numbers of settings they want to change (comma-separated). Parse the response and proceed.

```text
Which settings do you want to change? (enter numbers, comma-separated)

  1. Mode — Currently: [value]
  2. Granularity — Currently: [value]
  3. Execution — Currently: [Parallel|Sequential]
  4. Git Tracking — Currently: [Yes|No]
  5. AI Models — Currently: [value]
  6. Research — Currently: [Yes|No]
  7. Plan Check — Currently: [Yes|No]
  8. Verifier — Currently: [Yes|No]
```

**Otherwise** (Claude runtime with AskUserQuestion): use multiSelect:

```text
AskUserQuestion([
  {
    question: "Which settings do you want to change?",
    header: "Change Settings",
    multiSelect: true,
    options: [
      { label: "Mode", description: "Currently: [value]" },
      { label: "Granularity", description: "Currently: [value]" },
      { label: "Execution", description: "Currently: [Parallel|Sequential]" },
      { label: "Git Tracking", description: "Currently: [Yes|No]" },
      { label: "AI Models", description: "Currently: [value]" },
      { label: "Research", description: "Currently: [Yes|No]" },
      { label: "Plan Check", description: "Currently: [Yes|No]" },
      { label: "Verifier", description: "Currently: [Yes|No]" }
    ]
  }
])
```

For each selected setting, ask only that question using the option set from Round 1 / Round 2 below. Merge user answers over the saved defaults — unchanged settings retain their saved values. Then skip to **Commit config.json**.

**If "Configure fresh" or `~/.gsd/defaults.json` doesn't exist:** proceed with the questions below.

**Round 1 — Core workflow settings (4 questions):**

```
questions: [
  {
    header: "Mode",
    question: "How do you want to work?",
    multiSelect: false,
    options: [
      { label: "YOLO (Recommended)", description: "Auto-approve, just execute" },
      { label: "Interactive", description: "Confirm at each step" }
    ]
  },
  {
    header: "Granularity",
    question: "How finely should scope be sliced into phases?",
    multiSelect: false,
    options: [
      { label: "Coarse", description: "Fewer, broader phases (3-5 phases, 1-3 plans each)" },
      { label: "Standard", description: "Balanced phase size (5-8 phases, 3-5 plans each)" },
      { label: "Fine", description: "Many focused phases (8-12 phases, 5-10 plans each)" }
    ]
  },
  {
    header: "Execution",
    question: "Run plans in parallel?",
    multiSelect: false,
    options: [
      { label: "Parallel (Recommended)", description: "Independent plans run simultaneously" },
      { label: "Sequential", description: "One plan at a time" }
    ]
  },
  {
    header: "Git Tracking",
    question: "Commit planning docs to git?",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Planning docs tracked in version control" },
      { label: "No", description: "Keep .planning/ local-only (add to .gitignore)" }
    ]
  }
]
```

**Round 2 — Workflow agents:**

These spawn additional agents during planning/execution. They add tokens and time but improve quality.

| Agent | When it runs | What it does |
|-------|--------------|--------------|
| **Researcher** | Before planning each phase | Investigates domain, finds patterns, surfaces gotchas |
| **Plan Checker** | After plan is created | Verifies plan actually achieves the phase goal |
| **Verifier** | After phase execution | Confirms must-haves were delivered |

All recommended for important projects. Skip for quick experiments.

```
questions: [
  {
    header: "Research",
    question: "Research before planning each phase? (adds tokens/time)",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Investigate domain, find patterns, surface gotchas" },
      { label: "No", description: "Plan directly from requirements" }
    ]
  },
  {
    header: "Plan Check",
    question: "Verify plans will achieve their goals? (adds tokens/time)",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Catch gaps before execution starts" },
      { label: "No", description: "Execute plans without verification" }
    ]
  },
  {
    header: "Verifier",
    question: "Verify work satisfies requirements after each phase? (adds tokens/time)",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Confirm deliverables match phase goals" },
      { label: "No", description: "Trust execution, skip verification" }
    ]
  },
  {
