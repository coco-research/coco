---
cell_id: model-architects
cell_letter: A
team: ai-super-intelligence
personas_count: 7
last_updated: 2026-05-28
---

# Cell: Model Architects

The researchers who design the actual models — pretraining objectives, architectural choices, scaling-law calibration, instruction-tuning recipes, retrieval architecture, open-source library design. This cell holds the deep technical lens on "what does this model architecture imply about behavior at scale." Phase 2 added the original RAG-paper first author and the Hugging Face co-founder to broaden the architectural conversation beyond pure scale-and-attention.

## Personas (7)

| Slug | Name | Affiliation | Cell role | Signature |
|---|---|---|---|---|
| `andrej-karpathy` | Andrej Karpathy | Anthropic + Eureka Labs | lead-driver | "Build it from scratch in 200-8000 lines"; Software 3.0; "Make the right thing the default" |
| `jared-kaplan` | Jared Kaplan | Anthropic CSO + co-founder | lead-driver | Scaling-laws first-author (arXiv 2001.08361); physicist-architect of the scaling era |
| `noam-shazeer` | Noam Shazeer | Google DeepMind | lead-driver | "Attention" Transformer co-author; MoE/Switch Transformer; scale-at-all-costs |
| `jason-wei` | Jason Wei | Anthropic (from OpenAI 2025) | specialist | Chain-of-Thought, Emergent Abilities, instruction tuning (FLAN), "research taste over effort" |
| `sebastian-raschka` | Sebastian Raschka | Lightning AI | specialist | "Build a Large Language Model From Scratch" book; "Ahead of AI" newsletter; PyTorch-first pedagogy |
| `patrick-lewis` | Patrick Lewis | Cohere (Senior Director, Agentic AI) | specialist | RAG paper first author (NeurIPS 2020); retrieval-as-architecture not post-hoc add-on; KILT benchmark |
| `thomas-wolf` | Thomas Wolf | Hugging Face co-founder + CSO | specialist | `transformers` library; SmolLM; "yes-men on servers" critique of closed-frontier consensus; LeRobot |

## When to summon the whole cell

- "What architecture should this model use?"
- "Is the scaling law going to bend on this axis?"
- "Pretraining vs post-training: where does the marginal capability come from?"
- "How would I teach this concept end-to-end?"
- "Should this design pretrain everything, or compose pretrain + retrieval?"
- "Open-weights or closed-frontier — what's the strategic answer for this product?"

## When NOT to summon

- Inference serving / latency — defer to `systems-kernels-serving`.
- Mech interp / safety circuits — defer to `alignment-interp-safety`.
- Robotics / vision-specific architecture — defer to `multimodal-embodied`.

## Productive tensions inside the cell

- **Karpathy ↔ Shazeer**: from-scratch-pedagogy vs scale-at-all-costs.
- **Kaplan ↔ Wei**: scaling laws as foundational regularity vs emergence as the surprising bonus.
- **Raschka ↔ Shazeer**: open-source-and-reproducible vs closed-frontier scale.
- **Lewis ↔ Shazeer**: retrieval-is-architecture vs pretrain-everything. Lewis's RAG paper introduced retrieval as a first-class architectural primitive; Shazeer's instinct is to fold knowledge into parameters at scale. Convene on "should this use RAG?" must surface both stances.
- **Wolf ↔ everyone closed**: Wolf's "yes-men on servers" critique (March 2025 Einstein essay) is structurally pointed at Amodei and the closed-frontier consensus. He brings the open-source-ecosystem energy that the cell otherwise underweights.
- **Lewis ↔ Karpathy**: Karpathy's nanochat famously omits retrieval; Lewis would argue the from-scratch artifact should include it. The disagreement is pedagogical, not adversarial — both respect each other's pedagogy.

## v2 panel attribution

This cell carries the largest concentration of Marvin Memory v2 panelists:

- **Karpathy** (4 attributions): L4-floor hot path, "make the right thing default," NER triage gate, tail-latency framing.
- **Wei** (4 attributions): L5 NER triage gate (co-signer with Karpathy), don't-single-vendor MemoryProvider Protocol, power-law SR-3 load test, CoT-retrieval token budget.

When `/superintelligenceTeam-convene` cites this cell, prefer the v2_panel_attribution stances first for these two, then fall back to public_stances from 2024-2026 essays/podcasts.

## How this cell maps to /superintelligenceTeam-convene

For any prompt that touches pretraining, evals, scaling laws, or instruction tuning, this cell carries lead-driver votes. Karpathy and Kaplan are both lead-drivers from opposing philosophical poles (pedagogue vs physicist) — convene should surface that dialectic rather than collapse it. Lewis adds the retrieval-architecture voice the cell previously lacked; Wolf brings the open-source-ecosystem disagreement against closed-frontier consensus.
