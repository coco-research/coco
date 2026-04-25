# /team present — Presentation Pipeline

> Called by team.md router when action is `present`.
> Activates the presentation specialist team.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | business-analyst, ux-researcher | 2 |
| L2 | narrative-architect, structured-presentation OR apple-presentation, data-viz-specialist | 3-4 |
| L3 | slide-quality, grammar-editor | 2 |
| L4 | principal-pm or principal-ux (if user-facing product presentation) | 1 |

### Style Detection

Parse scope to detect presentation style:
- "ARB" / "architecture review" / "steerco" / "Consulting" → structured-presentation
- "launch" / "demo" / "keynote" / "Apple" / "product" → apple-presentation
- "data" / "analytics" / "metrics" → data-viz-specialist as L2 lead
- Default → structured-presentation (Consulting is the home format)

Both styles always include narrative-architect (storyline) + data-viz-specialist (charts).

## Pipeline Customization

### Layer 1: Audience & Content Research
L1 agents determine:
- Who is the audience? What do they already know?
- What is the core message / ask?
- What data and evidence is available?
- What format constraints exist (time limit, template, pre-read vs live)?

### Layer 2: Deck Creation
Agents work in sequence within L2 (not parallel — narrative must come first):

1. **narrative-architect** (first) → Designs storyline: core message, narrative arc, slide outline with key message per slide, appendix strategy
2. **format specialist** (second, reads narrative) → Structures each slide following format rules (Consulting or Apple style)
3. **data-viz-specialist** (parallel with #2) → Creates chart specifications for all data slides

**Toolkit integration:**
- Check team-toolkit.md for "Architecture Review Decks" if ARB format
- If /pmstudio-arb recommended → use it as starting point, then specialists refine
- Apply quality notes (e.g., "data viz sections need improvement")

**Output format:** HTML slide deck (self-contained, viewable in browser).

### Layer 3: Slide Review
- **slide-quality** → Action titles, one message per slide, source citations, visual consistency
- **grammar-editor** → Text quality, tone for audience

### Layer 4: Narrative Sign-Off
Principal reviews:
- Does the storyline land? Does the audience get to "so what" by slide 3?
- Is the ask clear?
- What slides should be cut or moved to appendix?

## GSD Integration

When `.planning/` exists, presentations pull phase status and metrics from STATE.md and ROADMAP.md.
