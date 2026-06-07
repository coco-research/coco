# Persona Schema — Source of Truth

This file defines the schema every persona profile under `superintelligenceTeam/personas/<slug>.md` must conform to. The schema is consumed by the slash commands (`/superintelligenceTeam-summon`, `/superintelligenceTeam-cell`, `/superintelligenceTeam-convene`) and by `registry.json`.

A persona file has two parts: a YAML frontmatter block (machine-readable), and a Markdown narrative (human-readable, used by `convene` to draw voice from).

## Required YAML frontmatter

```yaml
---
slug: andrej-karpathy                # kebab-case, unique across the roster

teams:                               # which Super Intelligence Teams this persona belongs to;
                                     # one persona may belong to multiple teams.
                                     # Known teams: ai-super-intelligence, cloud-super-intelligence,
                                     # finance-super-intelligence, coding-super-intelligence,
                                     # design-super-intelligence, product-super-intelligence,
                                     # memory-systems-super-intelligence (future).
  - ai-super-intelligence

cell: model-architects               # functional cell slug. Known cells for ai-super-intelligence:
                                     #   frontier-labs-research
                                     #   applied-ai-leadership
                                     #   model-architects
                                     #   reasoning-rl-agents
                                     #   alignment-interp-safety
                                     #   theory-science
                                     #   multimodal-embodied
                                     #   systems-kernels-serving
cell_letter: A                       # optional; preserved for back-compat with Marvin v2 panel
                                     # (A = AI/research, B = memory, C = cloud, D = data/security,
                                     #  E = obs/ops/privacy). Skip if not in v2 panel.
cell_role: lead-driver               # lead-driver | validator | specialist | swing
                                     #   lead-driver = drove a v2 reversal/decision
                                     #   validator   = co-signed a lead-driver's call
                                     #   specialist  = narrow deep-domain expert
                                     #   swing       = bridges two cells

real_name: Andrej Karpathy
archetype: First-principles deep-learning teacher
status: active                       # active | retired | archetype
                                     #   archetype = deceased or no longer publishing;
                                     #   profile is drawn from canonical published work

affiliations_2026: [Eureka Labs]
past_affiliations:
  - OpenAI (founding member, returned 2023-2024)
  - Tesla (Director of AI, 2017-2022)
  - Stanford (CS231n instructor)

domains:
  - LLM internals
  - training dynamics
  - evals
  - scaling
  - education

signature_moves:                     # how this persona attacks a problem; >=5
  - Build it from scratch in 200 lines to prove you understand it
  - Read the loss curve like a book
  - Tokenization is half of every LLM bug you'll ever hit
  # ...

canonical_works:                     # blog posts, repos, talks; >=5
  - title: "Let's build GPT from scratch, in code, spelled out"
    kind: video                      # video | blog | repo | talk | tweet
    url: https://www.youtube.com/...
    one_liner: "Annotated walkthrough of a GPT trained from zero in a Jupyter notebook."
  # ...

key_publications:                    # formal papers / books; may be empty for non-academic personas
  - title: "Software 2.0"
    kind: essay                      # paper | book | essay | chapter
    venue: Medium
    year: 2017
    url: https://karpathy.medium.com/software-2-0-a64152b37c35
    one_liner: "Neural nets as a new kind of software stack."

recent_signal_12mo:                  # things they said / shipped in the last 12 months; >=3
                                     # for `status: active`. For `status: archetype` (e.g. deceased
                                     # or no longer publishing), set this to `[]` and use the
                                     # `persistent_signals:` field below instead.
  - title: "..."
    date: 2025-XX-XX
    url: https://...
    takeaway: "..."
  # ...

persistent_signals:                  # OPTIONAL — for archetype personas only. Replaces
                                     # recent_signal_12mo when recency cannot apply (deceased,
                                     # long-retired, or no longer publicly active). >=5 entries.
                                     # Each entry uses the same shape as recent_signal_12mo
                                     # but the `date` can be historical (e.g., 1976-2011 for
                                     # Steve Jobs, plus posthumous archive material).
  - title: "Stanford Commencement Address"
    date: 2005-06-12
    url: https://news.stanford.edu/...
    takeaway: "Stay hungry. Stay foolish. Connecting the dots backwards."
  # ...

public_stances:                      # claims they consistently advance; >=3; every claim cited
  - claim: "Software 3.0 — natural language is the new code"
    evidence_url: https://...
  # ...

mental_models:                       # the lenses they think through; >=3
  - "..."
  # ...

v2_panel_attribution:                # GOLD FIELD — actual stances mined from the
                                     # Marvin Memory v2 panel synthesis on 2026-05-26.
                                     # Anchors persona to real panel material, not
                                     # inferred opinion. Cite source artifact.
                                     # Empty list if persona didn't speak in panel.
  - stance: "Make the right thing the default. Hot path = L4 floor + L1 drill-up + L5 NER-gated, not full 5-layer fan-out."
    panel_document: marvin-memory-master-phased-plan.html
    panel_section: "Reversal 2 — Full 5-layer hot path → 3-tier"
    co_signers: [adrian-cockcroft]
  - stance: "L4 is the floor; everything else is silent fallback with 50ms deadline."
    panel_document: marvin-memory-old-vs-new.html
    panel_section: "v2.2 Final architecture diagram"
    co_signers: [adrian-cockcroft, werner-vogels]

when_to_summon:                      # >=5
  - "Designing eval suites for an LLM-heavy system"
  - "Debugging silent training-loss anomalies"
  # ...

when_not_to_summon:                  # >=2
  - "Pure infra cost optimization with no model touchpoint"
  # ...

pairs_well_with: [tri-dao, jason-wei]              # rosters they amplify
productive_conflict_with: [yann-lecun, charles-packer]   # rosters they sharpen by disagreeing with

blind_spots:                         # >=2; what they tend to under-weight
  - "Tends to favor from-scratch over off-the-shelf even when wrong call"
  # ...

voice_style: "Plain English, no jargon. Analogies from physics/optics. Drops one-liner heuristics."

sample_prompts:                      # exact phrases a caller could use; >=2
  - "Karpathy, audit this training curve — what's the smell?"
  # ...

confidence: 0.95                     # 0.00–1.00; identifier certainty + profile depth
last_verified: 2026-05-27            # YYYY-MM-DD when sources were last checked

sources:                             # >=8 cited URLs; >=3 from last 12 months
  - https://karpathy.ai/...
  - https://twitter.com/karpathy/status/...
  # ...
---
```

## Required Markdown narrative

After the frontmatter, the file MUST include these sections in order. Convene templates draw on them for voice.

```markdown
# {Real Name} — narrative profile

## How they think
3–5 paragraphs synthesizing the YAML into a readable persona. Paraphrase in plain prose — use verbatim quotation marks only for text from a verified primary source; otherwise no quotes, and never invent wording. Anchor to canonical_works and recent_signal_12mo.

## What they would push back on
Bulleted list. What this persona would NOT accept in a proposal. Tie each item to a public stance or blind-spot inverse.

## What they would build first
Bulleted list. Their default first move when handed a greenfield version of the problem in their domain.

## How they phrase a critique
2–4 example phrasings of how this persona delivers pushback. In their voice. Cite the voice_style field.

## Example transcript
3–5 lines of dialogue, in their voice, responding to a generic prompt relevant to their domain. Show signature_moves and mental_models in action.

## Anchor quotes from the v2 panel
For personas who participated in the Marvin Memory v2 panel synthesis (2026-05-26 / 2026-05-27): direct quotes or attributions from the source artifacts (`marvin-memory-master-phased-plan.html`, `marvin-memory-v3-merged-spec.html`, `marvin-memory-old-vs-new.html`, etc). Skip this section for archetype personas who did not participate.
```

## Constraints

### Verification gate (READ FIRST — these personas describe real, identifiable people)

- **Verify or omit. Never fabricate to fill a field.** Every quote, stance, affiliation, role, date, and figure must trace to a real source that (a) resolves and (b) actually supports the claim. If you cannot verify it, leave it out — an empty field is correct; an invented one is a defect that can defame a real person.
- **No invented `evidence_url`s.** A citation counts only if you fetched it and it supports the exact claim. A URL that 404s, or that does not state the claim, fails the gate — drop the claim. "Has a URL" is not "is true."
- **No verbatim quotes unless sourced.** Use quotation marks only for text copied from a cited primary source you verified. Otherwise paraphrase in plain prose with no quotation marks. Never invent wording and attribute it to a person.
- **No unverified claims — but recent, dated facts are fine when cited.** A new role, a funding round, an IPO, a recent talk is welcome WHEN a resolving source supports it. What is banned is asserting such things without verification, or projecting future/speculative events as fact. If you cannot cite it, omit it; when unsure of a current role, describe the durable archetype rather than guess a dated specific.
- **Quotas are ceilings, not floors.** Where a field below says `>=N`, read it as "up to N, only as many as you can verify." Fewer well-sourced entries beat N fabricated ones. Quality over quota.

### Mechanical

- Identifier slugs use lower-case-kebab-case of the real name (e.g., `andrej-karpathy`, `joseph-gonzalez`).
- If identification fails for an UNCONFIRMED slug, do NOT write a persona file — surface top-3 candidates with evidence in the user-facing chat instead.
- Raw research excerpts MUST be saved under `<team>/research/<slug>/` as plain Markdown so future re-syntheses do not re-crawl — and so every claim is auditable against its excerpt.
- File encoding: UTF-8, LF newlines, no trailing whitespace.

## Why this schema

- **Frontmatter is the contract** consumed by `registry.json` and all slash commands.
- **v2_panel_attribution anchors personas to actual panel material**, not Claude's inference of what a famous person "would" say. Per user instruction: "anchor each persona to what they actually said in the v2 panel."
- **cell_role distinguishes lead-driver from validator** so convene synthesis can correctly cite "Hamilton drove the substrate reversal; Hightower validated" rather than collapsing all four Cell C members into one voice.
- **key_publications separated from canonical_works** because formal papers (Kleppmann's DDIA, Hellerstein's "Building a Bw-Tree") need to surface differently from videos/repos/tweets.
- **last_verified date stamp** lets future re-syntheses know which profiles need recrawling.

## See also

- `superintelligenceTeam/templates/convene.md` — multi-persona session template.
- `superintelligenceTeam/registry.json` — machine-readable roster derived from these files.
- `superintelligenceTeam/SKILL.md` — user-facing entry point.
