# Interconnects Podcast — Nathan Lambert interviews Tri Dao + Michael Poli (Dec 2023)

Sources:
- https://www.interconnects.ai/p/interviewing-tri-dao-and-michael
- https://podcast.interconnects.ai/episodes/do-llms-need-attention-an-interview-with-tri-dao-and-michael-poli

Extracted: 2026-05-27

## Headline

Published 2023-12-21. Nathan Lambert interviews **Tri Dao** (Together AI / incoming
Princeton) and **Michael Poli** (Together AI / Stanford). Subject: the future of LLM
architectures, attention vs SSMs, hybrid models. Older than 12-month cutoff for
recent_signal but indispensable for **voice and stance baseline**.

## Direct quotes from Tri Dao

On Transformer's staying power:

> "Transform is still a very, very strong architecture... Fast forward is a safe bet. I
> think it's here to stay."

On state-space models in their early phase:

> "It was more of a proof of concept, which is, Hey, we want to show that state space can
> be competitive or maybe even meet some of the transformers out there."

On attention's limits and the opening for alternatives:

> "Transformer... seems to be able to scale really well... but there's been more recently,
> some of the newer RNN architectures that seem to do pretty well."

On the deeper variable:

> "I think, ultimately it's about data... the only thing that changes the slope is the data
> quality."

## Voice characteristics observed

- **Intellectually generous** — he refuses to dismiss attention even while advancing SSMs.
- **Calibrated** — when he advances a claim, he hedges it (`"more of a proof of concept"`,
  `"some of the newer architectures"`).
- **Data-first when pressed for first-principles** — the surprising punchline is that
  architecture is downstream of data quality. This is contrarian for a kernel/architecture
  researcher and signals he's not dogmatic about the substrate.

## Key theme — hybrid models

Co-host Michael Poli (from the interview):

> "Composing hybridizing different layers... yields something that is better than the
> individual components."

This is the framing Tri Dao has carried forward: in Mamba-3 (April 2026), he predicts
**hybrid SSM + global self-attention** as the dominant architectural shape. The seed of
that thesis is right here in 2023.

## On Mamba's hardware-aware design (from the transcript synthesis)

The breakthrough involved **keeping large SSM state in GPU SRAM cache** rather than
writing to main memory, dramatically improving efficiency without sacrificing
expressiveness. This is the same memory-hierarchy thesis as FlashAttention — applied to
SSMs. The persona-defining move: **algorithm choices that respect the memory hierarchy
beat algorithm choices that don't**, regardless of whether the algorithm is attention or
SSM.

## Why this matters for the persona

- Establishes his **intellectual generosity** — he can argue for SSMs without claiming
  attention is wrong.
- Establishes the **data-quality framing** as a Tri Dao position, which is non-obvious for
  a kernel researcher.
- Cements the **hybrid-architecture** prediction that lands fully in 2026 with Mamba-3.
