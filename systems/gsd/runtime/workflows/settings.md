<purpose>
Interactive configuration of GSD workflow agents (research, plan_check, verifier) and model profile selection via multi-question prompt. Updates .planning/config.json with user preferences. Optionally saves settings as global defaults (~/.gsd/defaults.json) for future projects.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="ensure_and_load_config">
Ensure config exists and load current state:

```bash
gsd-sdk query config-ensure-section
INIT=$(gsd-sdk query state.load)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
# `state.load` returns STATE frontmatter JSON from the SDK — it does not include `config_path`. Orchestrators may set `GSD_CONFIG_PATH` from init phase-op JSON; otherwise resolve the same path gsd-tools uses for flat vs active workstream (#2282).
if [[ -z "${GSD_CONFIG_PATH:-}" ]]; then
  if [[ -f .planning/active-workstream ]]; then
    WS=$(tr -d '\n\r' < .planning/active-workstream)
    GSD_CONFIG_PATH=".planning/workstreams/${WS}/config.json"
  else
    GSD_CONFIG_PATH=".planning/config.json"
  fi
fi
```

Creates `config.json` (at the resolved path) with defaults if missing. `INIT` still holds `state.load` output for any step that needs STATE fields.
Store `$GSD_CONFIG_PATH` — all subsequent reads and writes use this path, not a hardcoded `.planning/config.json`, so active-workstream installs target the correct file (#2282).
</step>

<step name="read_current">
```bash
cat "$GSD_CONFIG_PATH"
```

Parse current values (default to `true` if not present):
- `workflow.research` — spawn researcher during plan-phase
- `workflow.plan_check` — spawn plan checker during plan-phase
- `workflow.verifier` — spawn verifier during execute-phase
- `workflow.nyquist_validation` — validation architecture research during plan-phase (default: true if absent)
- `workflow.pattern_mapper` — run gsd-pattern-mapper between research and planning (default: true if absent)
- `workflow.ui_phase` — generate UI-SPEC.md design contracts for frontend phases (default: true if absent)
- `workflow.ui_safety_gate` — prompt to run /gsd:ui-phase before planning frontend phases (default: true if absent)
- `workflow.ai_integration_phase` — framework selection + eval strategy for AI phases (default: true if absent)
- `workflow.tdd_mode` — enforce RED/GREEN/REFACTOR gate sequence during execute-phase (default: false if absent)
- `workflow.code_review` — enable /gsd:code-review and /gsd:code-review --fix commands (default: true if absent)
- `workflow.code_review_depth` — default depth for /gsd:code-review: `quick`, `standard`, or `deep` (default: `"standard"` if absent; only relevant when `code_review` is on)
- `workflow.ui_review` — run visual quality audit (/gsd:ui-review) in autonomous mode (default: true if absent)
- `commit_docs` — whether `.planning/` files are committed to git (default: true if absent)
- `intel.enabled` — enable queryable codebase intelligence (/gsd:map-codebase --query) (default: false if absent)
- `graphify.enabled` — enable project knowledge graph (/gsd:graphify) (default: false if absent)
- `graphify.auto_update` — opt-in: auto-rebuild graph after main HEAD advances (#3347) (default: `false`)
- `model_profile` — which model each agent uses (default: `balanced`)
- `git.branching_strategy` — branching approach (default: `"none"`)
- `workflow.use_worktrees` — whether parallel executor agents run in worktree isolation (default: `true`)
</step>

<step name="present_settings">

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.

**Non-Claude runtime note:** If `TEXT_MODE` is active (i.e. the runtime is non-Claude), prepend the following notice before the model profile question:

```
Note: Quality, Balanced, Budget, and Adaptive profiles assign semantic tiers
(Opus/Sonnet/Haiku) to each agent. When `runtime` is set in .planning/config.json,
tiers resolve to runtime-native model IDs — on Codex that's gpt-5.4 / gpt-5.3-codex /
gpt-5.4-mini with appropriate reasoning effort. See "Runtime-Aware Profiles" in
docs/CONFIGURATION.md.

If `runtime` is unset on a non-Claude runtime, the profile tiers have no effect on
actual model selection — agents use the runtime's default model. Choose "Inherit" to
force session-model behavior, set `runtime` + a profile to get tiered models, or
configure `model_overrides` manually in .planning/config.json to target specific
models per agent.
```

Use AskUserQuestion with current values pre-selected. Questions are grouped into six visual sections; the first question in each section carries the section-denoting `header` field (AskUserQuestion renders abbreviated section tags for grouping, max 12 chars).

Section layout:

### Planning
Research, Plan Checker, Pattern Mapper, Nyquist, UI Phase, UI Gate, AI Phase

### Execution
Verifier, TDD Mode, Code Review, Code Review Depth _(conditional — only when code_review=on)_, UI Review

### Docs & Output
Commit Docs, Skip Discuss, Worktrees

### Features
Intel, Graphify, Graph auto-update _(conditional — only when graphify=on)_

### Model & Pipeline
Model Profile, Auto-Advance, Branching

### Misc
Context Warnings, Research Qs

**Conditional visibility — code_review_depth:** This question is shown only when the user's chosen `code_review` value (after they answer that question, or the pre-selected value if unchanged) is on. If `code_review` is off, omit the `code_review_depth` question from the AskUserQuestion block and preserve the existing `workflow.code_review_depth` value in config (do not overwrite). Implementation: ask the Model + Planning + Execution-up-to-Code-Review questions first; if `code_review=on`, include `code_review_depth` in the same batch; otherwise skip it. Conceptually this is a one-branch split on the `code_review` answer.

**Conditional visibility — graphify.auto_update:** This question is shown only when the user's chosen `graphify.enabled` value is on. If `graphify.enabled` is off, omit the `graphify.auto_update` question and preserve the existing `graphify.auto_update` value in config (do not overwrite). Implementation: ask Graphify first; only ask Graph auto-update when Graphify is enabled.

```
AskUserQuestion([
  {
    question: "Which model profile for agents?",
    header: "Model",
    multiSelect: false,
    options: [
      { label: "Quality", description: "Opus everywhere except verification (highest cost) — Claude only" },
      { label: "Balanced (Recommended)", description: "Opus for planning, Sonnet for research/execution/verification — Claude only" },
      { label: "Budget", description: "Sonnet for writing, Haiku for research/verification (lowest cost) — Claude only" },
      { label: "Inherit", description: "Use current session model for all agents (required for non-Claude runtimes: Codex, Gemini CLI, OpenRouter, local models)" }
    ]
  },
  {
    question: "Spawn Plan Researcher? (researches domain before planning)",
    header: "Research",
    multiSelect: false,
    options: [
      { label: "Yes", description: "Research phase goals before planning" },
      { label: "No", description: "Skip research, plan directly" }
    ]
  },
  {
    question: "Spawn Plan Checker? (verifies plans before execution)",
    header: "Plan Check",
    multiSelect: false,
    options: [
      { label: "Yes", description: "Verify plans meet phase goals" },
      { label: "No", description: "Skip plan verification" }
    ]
  },
  {
    question: "Spawn Execution Verifier? (verifies phase completion)",
    header: "Verifier",
    multiSelect: false,
    options: [
      { label: "Yes", description: "Verify must-haves after execution" },
      { label: "No", description: "Skip post-execution verification" }
    ]
  },
  {
    question: "Enable TDD Mode? (RED/GREEN/REFACTOR gates for eligible tasks)",
    header: "TDD",
    multiSelect: false,
    options: [
      { label: "No (Recommended)", description: "Execute tasks normally. Tests written alongside implementation." },
      { label: "Yes", description: "Planner applies type:tdd to business logic/APIs/validations; executor enforces gate sequence. End-of-phase review checks compliance." }
    ]
  },
  {
    question: "Enable Code Review? (/gsd:code-review and /gsd:code-review --fix commands)",
    header: "Code Review",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Enable /gsd:code-review commands for reviewing source files changed during a phase." },
      { label: "No", description: "Commands exit with a configuration gate message. Use when code review is handled externally." }
    ]
  },
  // Conditional: include the following code_review_depth question ONLY when the user's
  // chosen code_review value is "Yes". If code_review is "No", omit this question from
  // the AskUserQuestion call and do not touch the existing workflow.code_review_depth value.
  {
    question: "Code Review Depth? (default depth for /gsd:code-review — override per-run with --depth=)",
    header: "Review Depth",
    multiSelect: false,
    options: [
      { label: "Standard (Recommended)", description: "Per-file analysis. Balanced cost and signal." },
      { label: "Quick", description: "Pattern-matching only. Fastest, lowest cost." },
      { label: "Deep", description: "Cross-file analysis with import graphs. Highest cost, highest signal." }
    ]
  },
  {
    question: "Enable UI Review? (visual quality audit via /gsd:ui-review in autonomous mode)",
    header: "UI Review",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Run visual quality audit after phase execution in autonomous mode." },
      { label: "No", description: "Skip the UI audit step. Good for backend-only projects." }
    ]
  },
  {
    question: "Auto-advance pipeline? (discuss → plan → execute automatically)",
    header: "Auto",
    multiSelect: false,
    options: [
      { label: "No (Recommended)", description: "Manual /clear + paste between stages" },
      { label: "Yes", description: "Chain stages via Agent() subagents (same isolation)" }
    ]
  },
  {
    question: "Run Pattern Mapper? (maps new files to existing codebase analogs between research and planning)",
    header: "Pattern Mapper",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "gsd-pattern-mapper runs between research and plan steps. Surfaces conventions so new code follows house style." },
      { label: "No", description: "Skip pattern mapping. Faster; lose consistency hinting for new files." }
    ]
  },
  {
    question: "Enable Nyquist Validation? (researches test coverage during planning)",
    header: "Nyquist",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Research automated test coverage during plan-phase. Adds validation requirements to plans. Blocks approval if tasks lack automated verify." },
      { label: "No", description: "Skip validation research. Good for rapid prototyping or no-test phases." }
