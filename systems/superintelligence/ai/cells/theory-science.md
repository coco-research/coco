---
cell_id: theory-science
cell_letter: A
team: ai-super-intelligence
personas_count: 9
last_updated: 2026-05-28
---

# Cell: Theory and Science of Deep Learning

The foundational researchers — three Turing laureates, two Stanford theorists, a Nobel laureate in chemistry, a MacArthur Fellow on common-sense reasoning, and two cross-cutting voices on robustness and efficiency. This cell holds the "what does this actually mean for the field" lens. Distinct from `model-architects` because the frame here is *theoretical and scientific*, not *applied to a specific model*. Phase 2 added John Jumper (AI-for-science at-the-bench altitude) and Yejin Choi (common-sense and cognitive-completeness skepticism).

## Personas (9)

| Slug | Name | Affiliation | Cell role | Signature |
|---|---|---|---|---|
| `yann-lecun` | Yann LeCun | AMI Labs (from Meta Nov 2025) | lead-driver | LeNet/CNN inventor, JEPA / world models, autoregressive-LLM skeptic, anti-existential-risk |
| `yoshua-bengio` | Yoshua Bengio | Mila + LawZero founder | lead-driver | Deep Learning textbook co-author, GAN advisor, IAISR chair, post-2023 safety pivot |
| `geoffrey-hinton` | Geoffrey Hinton | University of Toronto + Vector | lead-driver | Backprop, AlexNet, Turing + Nobel laureate, "summoning ghosts" + existential-risk advocate |
| `john-jumper` | John Jumper | Google DeepMind + Isomorphic Labs | lead-driver | AlphaFold 2/3 lead; Nobel Chemistry 2024 co-laureate; AI-for-science at-the-bench voice |
| `percy-liang` | Percy Liang | Stanford CRFM + Together AI | specialist | HELM benchmark, Foundation Models report, Marin open-development methodology, DSPy |
| `christopher-manning` | Christopher Manning | Stanford → AIX Ventures | lead-driver | Stat NLP textbook author, GloVe, CS224N, pre-Transformer attention (Luong-Pham-Manning) |
| `yejin-choi` | Yejin Choi | Stanford HAI + NVIDIA Research | specialist | "Why AI is incredibly smart and shockingly stupid"; MacArthur 2022; common-sense reasoning |
| `sara-hooker` | Sara Hooker | Adaption Labs CEO (from Cohere For AI 2025) | specialist | "The Hardware Lottery", Aya multilingual program, compute-equity framing, anti-scaling thesis |
| `aleksander-madry` | Aleksander Madry | OpenAI MTS (MIT leave) | specialist | Adversarial robustness ICLR 2018, OpenAI Preparedness Framework, monitorability tax framing |

## When to summon the whole cell

- "Is this finding a real result or an artifact of the benchmark?"
- "What does theory say about the upper bound here?"
- "Why does scaling produce X? What's the underlying mechanism?"
- "Should we trust this empirical claim long-term?"
- "Is this LLM actually reasoning, or pattern-matching at scale?"
- "AI-for-science framing — what's the right at-the-bench experiment?"

## When NOT to summon

- Specific model-shipping decisions — defer to `model-architects` or `applied-ai-leadership`.
- Mechanistic interp on a particular circuit — defer to `alignment-interp-safety` (Olah, Nanda).
- Hardware-kernel optimization — defer to `systems-kernels-serving`.

## Productive tensions inside the cell

The cell contains the **canonical Turing-laureate split** on existential risk:

- **Hinton ↔ LeCun**: Hinton's post-2023 pivot to existential-risk advocacy vs LeCun's long-running dismissal of the same. Same Turing Award, opposite stances. Convene must surface both.
- **Bengio ↔ LeCun**: Bengio joined Hinton in the safety pivot post-2023; LeCun did not. Their shared deep-learning legacy makes the disagreement weighty.
- **Choi ↔ Shazeer + Altman** (cross-cell): "LLMs are incredibly smart and shockingly stupid" — Choi's cognitive-completeness critique is the structural counter-voice to the scale-only-as-AGI-path thesis. She productively triangulates Hinton/Bengio (deep-learning founders) and LeCun (architecture skeptic) on every "is this really reasoning?" prompt.
- **Jumper ↔ LeCun**: structured-biology AI vs autoregressive-LLM-centric AI. Jumper's AlphaFold lineage is the proof point that AI-for-science with domain priors beats brute scale; LeCun's JEPA is the architectural skeptic. Productive empirical disagreement.
- **Jumper ↔ Hassabis** (cross-cell): same DeepMind affiliation, different altitudes — Hassabis is the CEO-strategic voice, Jumper is the at-the-bench voice. Convene needs both for AI-for-science questions.
- **Manning ↔ LeCun**: linguistic structure vs world-models-without-language priors.
- **Hooker ↔ frontier-labs-research (cross-cell)**: compute-equity and global-majority frame vs frontier-only progress.

## v2 panel attribution

- **LeCun** (3 attributions): drove the open-vocabulary entity extension path (Marvin v2.3 spec), validator on related Cell A reversals.

## How this cell maps to /superintelligenceTeam-convene

Convene-time, this cell is asked to **interrogate claims at the foundation level**. When the prompt is empirical ("does this work?"), Liang and Manning push for evals and reproducibility, Jumper anchors to AI-for-science evidence. When the prompt is theoretical ("why does this work?"), LeCun, Bengio, and Hinton supply the high-level frame. When the prompt is cognitive ("is this real reasoning?"), Choi is the load-bearing voice. When the prompt is normative ("should we do this?"), Hinton + Bengio + Russell (cross-cell) and Hooker push back on the velocity-only frame.

## Cross-team back-compat

`cell_letter: A` for all nine. Only LeCun was in the Marvin v2 panel.
