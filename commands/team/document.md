# /team document — Documentation Pipeline

> Called by team.md router when action is `document`.
> Creates any document type: PRD, guide, runbook, architecture doc, etc.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | business-analyst, technical-analyst | 2 |
| L2 | senior-pm, technical-writer, confluence-specialist (if Confluence target) | 2-3 |
| L3 | doc-quality, grammar-editor, standards-reviewer | 3 |
| L4 | principal-pm | 1 |

### Document Type Detection

Parse scope to detect document type:
- "PRD" / "requirements" → senior-pm as L2 lead, use prd-generator from toolkit
- "architecture" / "design doc" → this action WRITES UP an architecture for an audience;
  it does not decide one. Put technical-writer + solution-architect in L2. Add
  architecture-reviewer and domain-accuracy to the L3 roster, because the default roster
  of doc-quality, grammar-editor, and standards-reviewer checks structure, tone, and
  template conformance only — none of them can tell whether the architecture being
  described is technically sound. If `.arch/index.json` is absent, offer `/team arch build`
  first, so the document rests on a validated component map rather than an improvised one.
  For a formal published document, prefer /util:create-architecture-documentation, which
  produces C4, arc42, ADR, PlantUML, and Structurizr output.
- "runbook" / "playbook" → sre-devops in L2
- "API docs" → technical-writer + senior-backend-eng in L2
- "onboarding" / "guide" → technical-writer + ux-researcher in L1
- "DR plan" → sre-devops + senior-cloud-architect in L2, use /pmstudio-dr from toolkit
- "IRP" / "incident" → sre-devops in L2, use /pmstudio-irp from toolkit
- Default → technical-writer lead in L2

## Pipeline Customization

### Layer 1: Context Gathering
L1 agents collect:
- Existing documentation on the topic
- Source material (code, configs, meeting notes)
- Stakeholder requirements for the document
- Template requirements (consulting format, Confluence structure, etc.)

### Layer 2: Document Creation
- **Mode:** `default` (creates documents but doesn't modify code)
- Primary author (role depends on document type) writes the document
- Secondary roles contribute specialized sections

**Toolkit integration:**
- Check team:toolkit.md for the relevant document type
- If a PM Studio skill is recommended → invoke it, then L3 reviews the output
- Apply all quality notes from previous runs
- If toolkit says "skip tool" for this case → write directly

### Layer 3: Quality Review (Heavy)
This is where the document gets polished:
- **doc-quality** → Structure, completeness, flow
- **grammar-editor** → Tone, grammar, readability, consulting voice
- **standards-reviewer** → Template conformance, formatting

L3 is intentionally heavy for document actions because document quality
directly impacts stakeholder perception.

### Layer 4: Final Polish
Principal reviews for:
- Does this serve the audience?
- Is the core message clear?
- What should be cut?
- Is this ready for distribution?

## GSD Integration

When `.planning/` exists, documents reference phase context from ROADMAP.md. PRDs align with GSD requirements.
