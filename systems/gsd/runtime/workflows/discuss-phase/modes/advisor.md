# Advisor mode — research-backed comparison tables

> **Lazy-loaded and gated.** The parent `workflows/discuss-phase.md` Reads
> this file ONLY when `ADVISOR_MODE` is true (i.e., when
> `$HOME/.claude/get-shit-done/USER-PROFILE.md` exists). Skip the Read
> entirely when no profile is present — that's the inverse of the
> `--advisor` flag from #2174 (don't pay the cost when unused).

## Activation

```bash
PROFILE_PATH="$HOME/.claude/get-shit-done/USER-PROFILE.md"
if [ -f "$PROFILE_PATH" ]; then
  ADVISOR_MODE=true
else
  ADVISOR_MODE=false
fi
```

If `ADVISOR_MODE` is false, do **not** Read this file — proceed with the
standard `default.md` discussion flow.

## Calibration tier

Resolve `vendor_philosophy` calibration tier:
1. **Priority 1:** Read `config.json` > `preferences.vendor_philosophy`
   (project-level override)
2. **Priority 2:** Read USER-PROFILE.md `Vendor Choices/Philosophy` rating
   (global)
3. **Priority 3:** Default to `"standard"` if neither has a value or value
   is `UNSCORED`

Map to calibration tier:
- `conservative` OR `thorough-evaluator` → `full_maturity`
- `opinionated` → `minimal_decisive`
- `pragmatic-fast` OR any other value OR empty → `standard`

Resolve advisor model:
```bash
ADVISOR_MODEL=$(gsd-sdk query resolve-model gsd-advisor-researcher --raw)
```

## Non-technical owner detection

Read USER-PROFILE.md and check for product-owner signals:

```bash
PROFILE_CONTENT=$(cat "$HOME/.claude/get-shit-done/USER-PROFILE.md" 2>/dev/null || true)
```

Set `NON_TECHNICAL_OWNER = true` if ANY of the following are present:
- `learning_style: guided`
- The word `jargon` appears in a `frustration_triggers` section
- `explanation_depth: practical-detailed` (without a technical modifier)
- `explanation_depth: high-level`

**Tie-breaker / precedence (when signals conflict):**
1. An explicit `technical_background: true` (or any `explanation_depth` value
   tagged with a technical modifier such as `practical-detailed:technical`)
   **overrides** all inferred non-technical signals — set
   `NON_TECHNICAL_OWNER = false`.
2. Otherwise, ANY single matching signal is sufficient to set
   `NON_TECHNICAL_OWNER = true` (signals are OR-aggregated, not weighted).
3. Contradictory `explanation_depth` values: the most recent entry wins.

Log the resolved value and the matched/overriding signal so the user can
audit why a given framing was used.

When `NON_TECHNICAL_OWNER` is true, reframe gray area labels and
descriptions in product-outcome language before presenting them. Preserve
the same underlying decision — only change the framing:

- Technical implementation term → outcome the user will experience
  - "Token architecture" → "Color system: which approach prevents the dark theme from flashing white on open"
  - "CSS variable strategy" → "Theme colors: how your brand colors stay consistent in both light and dark mode"
  - "Component API surface area" → "How the building blocks connect: how tightly coupled should these parts be"
  - "Caching strategy: SWR vs React Query" → "Loading speed: should screens show saved data right away or wait for fresh data"

This reframing applies to:
1. Gray area labels and descriptions in `present_gray_areas`
2. Advisor research rationale rewrites in the synthesis step below

## advisor_research step

After the user selects gray areas in `present_gray_areas`, spawn parallel
research agents.

1. Display brief status: `Researching {N} areas...`

2. For EACH user-selected gray area, spawn a `Agent()` in parallel:

   ```
   Agent(
     prompt="First, read @~/.claude/agents/gsd-advisor-researcher.md for your role and instructions.

     <gray_area>{area_name}: {area_description from gray area identification}</gray_area>
     <phase_context>{phase_goal and description from ROADMAP.md}</phase_context>
     <project_context>{project name and brief description from PROJECT.md}</project_context>
     <calibration_tier>{resolved calibration tier: full_maturity | standard | minimal_decisive}</calibration_tier>

     Research this gray area and return a structured comparison table with rationale.
     ${AGENT_SKILLS_ADVISOR}",
     subagent_type="general-purpose",
     model="{ADVISOR_MODEL}",
     description="Research: {area_name}"
   )
   ```

   All `Agent()` calls spawn simultaneously — do NOT wait for one before
   starting the next.

   > **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling all Agent() calls above to spawn research agents, do NOT independently research or analyze any of the gray areas while the subagents are active. Wait for all subagents to return before synthesizing results. This prevents duplicate work and wasted context.

3. After ALL agents return, **synthesize results** before presenting:

   For each agent's return:
   a. Parse the markdown comparison table and rationale paragraph
   b. Verify all 5 columns present (Option | Pros | Cons | Complexity | Recommendation) — fill any missing columns rather than showing broken table
   c. Verify option count matches calibration tier:
      - `full_maturity`: 3-5 options acceptable
      - `standard`: 2-4 options acceptable
