<purpose>
Spike an idea through experiential exploration — build focused experiments to feel the pieces
of a future app, validate feasibility, and produce verified knowledge for the real build.
Saves artifacts to `.planning/spikes/`. Companion to `/gsd:spike --wrap-up`.

Supports two modes:
- **Idea mode** (default) — user describes an idea to spike
- **Frontier mode** — no argument or "frontier" / "what should I spike?" — analyzes existing spike landscape and proposes integration and frontier spikes
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="banner">
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► SPIKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Parse `$ARGUMENTS` for:
- `--quick` flag → set `QUICK_MODE=true`
- `--text` flag → set `TEXT_MODE=true`
- `frontier` or empty → set `FRONTIER_MODE=true`
- Remaining text → the idea to spike

**Text mode:** If TEXT_MODE is enabled, replace AskUserQuestion calls with plain-text numbered lists.
</step>

<step name="route">
## Routing

- **FRONTIER_MODE is true** → Jump to `frontier_mode`
- **Otherwise** → Continue to `setup_directory`
</step>

<step name="frontier_mode">
## Frontier Mode — Propose What to Spike Next

### Load the Spike Landscape

If no `.planning/spikes/` directory exists, tell the user there's nothing to analyze and offer to start fresh with an idea instead.

Otherwise, load in this order:

**a. MANIFEST.md** — the overall idea, requirements, and spike table with verdicts.

**b. Findings skills** — glob `./.claude/skills/spike-findings-*/SKILL.md` and read any that exist, plus their `references/*.md`. These contain curated knowledge from prior wrap-ups.

**c. CONVENTIONS.md** — read `.planning/spikes/CONVENTIONS.md` if it exists. Established stack and patterns.

**d. All spike READMEs** — read `.planning/spikes/*/README.md` for verdicts, results, investigation trails, and tags.

### Analyze for Integration Spikes

Review every pair and cluster of VALIDATED spikes. Look for:

- **Shared resources:** Two spikes that both touch the same API, database, state, or data format but were tested independently.
- **Data handoffs:** Spike A produces output that Spike B consumes. The formats were assumed compatible but never proven.
- **Timing/ordering:** Spikes that work in isolation but have sequencing dependencies in the real flow.
- **Resource contention:** Spikes that individually work but may compete for connections, memory, rate limits, or tokens when combined.

If integration risks exist, present them as concrete proposed spikes with names and Given/When/Then validation questions. If no meaningful integration risks exist, say so and skip this category.

### Analyze for Frontier Spikes

Think laterally about the overall idea from MANIFEST.md and what's been proven so far. Consider:

- **Gaps in the vision:** Capabilities assumed but unproven.
- **Discovered dependencies:** Findings that reveal new questions.
- **Alternative approaches:** Different angles for PARTIAL or INVALIDATED spikes.
- **Adjacent capabilities:** Things that would meaningfully improve the idea if feasible.
- **Comparison opportunities:** Approaches that worked but felt heavy.

Present frontier spikes as concrete proposals numbered from the highest existing spike number with Given/When/Then and risk ordering.

### Get Alignment and Execute

Present all integration and frontier candidates, then ask which to run. When the user picks spikes, write definitions into `.planning/spikes/MANIFEST.md` (appending to existing table) and proceed directly to building them starting at `research`.
</step>

<step name="setup_directory">
Create `.planning/spikes/` if it doesn't exist:

```bash
mkdir -p .planning/spikes
```

Check for existing spikes to determine numbering:
```bash
ls -d .planning/spikes/[0-9][0-9][0-9]-* 2>/dev/null | sort | tail -1
```

Check `commit_docs` config:
```bash
COMMIT_DOCS=$(gsd-sdk query config-get commit_docs 2>/dev/null || echo "true")
```
</step>

<step name="detect_stack">
Check for the project's tech stack to inform spike technology choices.

**Check conventions first.** If `.planning/spikes/CONVENTIONS.md` exists, follow its stack and patterns — these represent validated choices the user expects to see continued.

**Then check the project stack:**
```bash
ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null
```

Use the project's language/framework by default. For greenfield projects with no conventions and no existing stack, pick whatever gets to a runnable result fastest.

Avoid unless the spike specifically requires it:
- Complex package management beyond `npm install` or `pip install`
- Build tools, bundlers, or transpilers
- Docker, containers, or infrastructure
- Env files or config systems — hardcode everything
</step>

<step name="load_prior_context">
If `.planning/spikes/` has existing content, load context in this priority order:

**a. Conventions:** Read `.planning/spikes/CONVENTIONS.md` if it exists.

**b. Findings skills:** Glob for `./.claude/skills/spike-findings-*/SKILL.md` and read any that exist, plus their `references/*.md` files.

**c. Manifest:** Read `.planning/spikes/MANIFEST.md` for the index of all spikes.

**d. Related READMEs:** Based on the new idea, identify which prior spikes are related by matching tags, names, technologies, or domain overlap. Read only those `.planning/spikes/*/README.md` files. Skip unrelated ones.

Cross-reference against this full body of prior work:
- **Skip already-validated questions.** Note the prior spike number and move on.
- **Build on prior findings.** Don't repeat failed approaches. Use their Research and Results sections.
- **Reuse prior research.** Carry findings forward rather than re-researching.
- **Follow established conventions.** Mention any deviation.
- **Call out relevant prior art** when presenting the decomposition.

If no `.planning/spikes/` exists, skip this step.
</step>

<step name="decompose">
**If `QUICK_MODE` is true:** Skip decomposition and alignment. Take the user's idea as a single spike question. Assign it the next available number. Jump to `research`.

Break the idea into 2-5 independent questions. Frame each as Given/When/Then. Present as a table:

```
| # | Spike | Type | Validates (Given/When/Then) | Risk |
|---|-------|------|-----------------------------|------|
| 001 | websocket-streaming | standard | Given a WS connection, when LLM streams tokens, then client receives chunks < 100ms | **High** |
| 002a | pdf-parse-pdfjs | comparison | Given a multi-page PDF, when parsed with pdfjs, then structured text is extractable | Medium |
| 002b | pdf-parse-camelot | comparison | Given a multi-page PDF, when parsed with camelot, then structured text is extractable | Medium |
```

**Spike types:**
- **standard** — one approach answering one question
- **comparison** — same question, different approaches. Shared number with letter suffix.

Good spikes: specific feasibility questions with observable output.
Bad spikes: too broad, no observable output, or just reading/planning.

Order by risk — most likely to kill the idea runs first.
</step>

<step name="align">
**If `QUICK_MODE` is true:** Skip.

╔══════════════════════════════════════════════════════════════╗
║  CHECKPOINT: Decision Required                               ║
╚══════════════════════════════════════════════════════════════╝

{spike table from decompose step}

──────────────────────────────────────────────────────────────
→ Build all in this order, or adjust the list?
──────────────────────────────────────────────────────────────
</step>

<step name="research">
## Research and Briefing Before Each Spike

This step runs **before each individual spike**, not once at the start.

**a. Present a spike briefing:**

> **Spike NNN: Descriptive Name**
> [2-3 sentences: what this spike is, why it matters, key risk or unknown.]

**b. Research the current state of the art.** Use context7 (resolve-library-id → query-docs) for libraries/frameworks. Use web search for APIs/services without a context7 entry. Read actual documentation.

**c. Surface competing approaches** as a table:

| Approach | Tool/Library | Pros | Cons | Status |
|----------|-------------|------|------|--------|
| ... | ... | ... | ... | ... |

**Chosen approach:** [which one and why]

If 2+ credible approaches exist, plan to build quick variants within the spike and compare them.

**d. Capture research findings** in a `## Research` section in the README.

**Skip when unnecessary** for pure logic with no external dependencies.
</step>

<step name="create_manifest">
Create or update `.planning/spikes/MANIFEST.md`:

```markdown
# Spike Manifest

## Idea
[One paragraph describing the overall idea being explored]

## Requirements
[Design decisions that emerged from the user's choices during spiking. Non-negotiable for the real build. Updated as spikes progress.]

- [e.g., "Must use streaming JSON output, not single-response"]
- [e.g., "Must support reconnection on network failure"]

## Spikes

| # | Name | Type | Validates | Verdict | Tags |
|---|------|------|-----------|---------|------|
```

**Track requirements as they emerge.** When the user expresses a preference during spiking, add it to the Requirements section immediately.
</step>

<step name="reground">
## Re-Ground Before Each Spike

Before starting each spike (not just the first), re-read `.planning/spikes/MANIFEST.md` and `.planning/spikes/CONVENTIONS.md` to prevent drift within long sessions. Check the Requirements section — make sure the spike doesn't contradict any established requirements.
</step>

<step name="build_spikes">
## Build Each Spike Sequentially

**Depth over speed.** The goal is genuine understanding, not a quick verdict. Never declare VALIDATED after a single happy-path test. Follow surprising findings. Test edge cases. Document the investigation trail, not just the conclusion.
