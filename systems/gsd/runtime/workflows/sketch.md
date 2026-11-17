<purpose>
Explore design directions through throwaway HTML mockups before committing to implementation.
Each sketch produces 2-3 variants for comparison. Saves artifacts to `.planning/sketches/`.
Companion to `/gsd:sketch --wrap-up`.

Supports two modes:
- **Idea mode** (default) — user describes a design idea to sketch
- **Frontier mode** — no argument or "frontier" / "what should I sketch?" — analyzes existing sketch landscape and proposes consistency and frontier sketches
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.

@~/.claude/get-shit-done/references/sketch-theme-system.md
@~/.claude/get-shit-done/references/sketch-variant-patterns.md
@~/.claude/get-shit-done/references/sketch-interactivity.md
@~/.claude/get-shit-done/references/sketch-tooling.md
</required_reading>

<process>

<step name="banner">
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► SKETCHING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Parse `$ARGUMENTS` for:
- `--quick` flag → set `QUICK_MODE=true`
- `--text` flag → set `TEXT_MODE=true`
- `frontier` or empty → set `FRONTIER_MODE=true`
- Remaining text → the design idea to sketch

**Text mode:** If TEXT_MODE is enabled, replace AskUserQuestion calls with plain-text numbered lists.
</step>

<step name="route">
## Routing

- **FRONTIER_MODE is true** → Jump to `frontier_mode`
- **Otherwise** → Continue to `setup_directory`
</step>

<step name="frontier_mode">
## Frontier Mode — Propose What to Sketch Next

### Load the Sketch Landscape

If no `.planning/sketches/` directory exists, tell the user there's nothing to analyze and offer to start fresh with an idea instead.

Otherwise, load in this order:

**a. MANIFEST.md** — the design direction, reference points, and sketch table with winners.

**b. Findings skills** — glob `./.claude/skills/sketch-findings-*/SKILL.md` and read any that exist, plus their `references/*.md`. These contain curated design decisions from prior wrap-ups.

**c. All sketch READMEs** — read `.planning/sketches/*/README.md` for design questions, winners, and tags.

### Analyze for Consistency Sketches

Review winning variants across all sketches. Look for:

- **Visual consistency gaps:** Two sketches made independent design choices that haven't been tested together.
- **State combinations:** Individual states validated but not seen in sequence.
- **Responsive gaps:** Validated at one viewport but the real app needs multiple.
- **Theme coherence:** Individual components look good but haven't been composed into a full-page view.

If consistency risks exist, present them as concrete proposed sketches with names and design questions. If no meaningful gaps, say so and skip.

### Analyze for Frontier Sketches

Think laterally about the design direction from MANIFEST.md and what's been explored:

- **Unsketched screens:** UI surfaces assumed but unexplored.
- **Interaction patterns:** Static layouts validated but transitions, loading, drag-and-drop need feeling.
- **Edge case UI:** 0 items, 1000 items, errors, slow connections.
- **Alternative directions:** Fresh takes on "fine but not great" sketches.
- **Polish passes:** Typography, spacing, micro-interactions, empty states.

Present frontier sketches as concrete proposals numbered from the highest existing sketch number.

### Get Alignment and Execute

Present all consistency and frontier candidates, then ask which to run. When the user picks sketches, update `.planning/sketches/MANIFEST.md` and proceed directly to building them starting at `build_sketches`.
</step>

<step name="setup_directory">
Create `.planning/sketches/` and themes directory if they don't exist:

```bash
mkdir -p .planning/sketches/themes
```

Check for existing sketches to determine numbering:
```bash
ls -d .planning/sketches/[0-9][0-9][0-9]-* 2>/dev/null | sort | tail -1
```

Check `commit_docs` config:
```bash
COMMIT_DOCS=$(gsd-sdk query config-get commit_docs 2>/dev/null || echo "true")
```
</step>

<step name="mood_intake">
**If `QUICK_MODE` is true:** Skip mood intake. Use whatever the user provided in `$ARGUMENTS` as the design direction. Jump to `load_spike_context`.

**Otherwise:**

Before sketching anything, explore the design intent through conversation. Ask one question at a time — using AskUserQuestion in normal mode, or a plain-text numbered list if TEXT_MODE is active.

**Questions to cover (adapt to what the user has already shared):**

1. **Feel:** "What should this feel like? Give me adjectives, emotions, or a vibe."
2. **References:** "What apps, sites, or products have a similar feel to what you're imagining?"
3. **Core action:** "What's the single most important thing a user does here?"

