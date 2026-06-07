# Mamba-3 — Improved Sequence Modeling using State Space Principles

Sources:
- https://tridao.me/blog/2026/mamba3-part1/
- https://pli.princeton.edu/blog/2026/mamba-3-improved-sequence-modeling-using-state-space-principles
- https://venturebeat.com/technology/open-source-mamba-3-arrives-to-surpass-transformer-architecture-with-nearly
- OpenReview / ICLR 2026: https://openreview.net/pdf?id=HwCvaJOiCj

Extracted: 2026-05-27

## Headline

**Mamba-3** — released March/April 2026, accepted at **ICLR 2026** as a conference paper.

Authors: Aakash Lahoti, Kevin Y. Li, Berlin Chen, Caitlin Wang, Aviv Bick, J. Zico Kolter,
**Tri Dao**, **Albert Gu**.

Affiliations: Carnegie Mellon, Princeton, Together AI, Cartesia AI.

License: **Apache 2.0** — fully open source.

## The pivot — "inference-first"

Tri Dao's framing question on his personal blog (Mamba-3 Part 1):

> "What would an SSM designed with **inference** in mind look like?"

This explicitly inverts the prior Mamba and Mamba-2 framings, which were
training-throughput-driven. Mamba-3 is the first family member designed top-down for the
**deployment** profile.

## The "cold GPU" problem

> "Linear architectures like Mamba-2, though optimized for training speed, leave the
> inference step 'too simple' and squarely memory-bound — the GPUs aren't brr-ing but
> moving memory most of the time. Each token update performs very little compute relative
> to memory movement, leaving hardware underutilized."

This is the inverse of FlashAttention's framing. There, attention was compute-cheap but
memory-blocked, so you optimize the kernel. Here, SSM decode is **already** compute-cheap
— so cheap that the GPU sits idle while waiting on memory. Mamba-3's answer is to
**increase per-token compute density** so the GPU stops being cold.

## Three technical innovations

1. **Exponential-trapezoidal discretization** — more expressive recurrence than the
   simpler ZOH (zero-order-hold) or bilinear schemes used in Mamba-1/2.
2. **Complex-valued SSM** — extends state-tracking capability; lets the system represent
   oscillations and rotations that real-valued SSMs cannot.
3. **MIMO (Multi-Input, Multi-Output) SSMs** — apply recurrence to vector inputs rather
   than scalars, **without increasing state size**. Increases per-step compute per token.

## Performance

- **1.5B-parameter MIMO variant**: 57.6% average accuracy across benchmarks.
- **Nearly 4% relative improvement** in language modeling capability vs. Transformer
  baseline at the same scale.
- **Matches strong LLM perplexities at half the decoding cost.**

## Strategic framing on attention vs SSMs

> "Linear layers will be predominantly used in **conjunction** with global self-attention
> layers."

This is significant: Dao explicitly **does not** claim SSMs will fully displace attention.
Instead, he predicts a **hybrid** future where SSMs handle the bulk of sequence compression
and attention layers are inserted where retrieval-heavy operations demand them.

The Princeton PLI blog reinforces this:
> "Linear SSM architectures are fundamentally different from Transformers due to their
> fixed state size constraint. While this enables linear computational scaling, it forces
> information compression versus Transformers' continuously growing state (the KV cache)."

So the SSM advantage is **decode efficiency**; the SSM weakness is **retrieval**. The
honest position is: combine them.

## Why this matters for the persona's panel voice

When asked about retrieval-system substrate (HNSW, vector indexes, KV cache management,
quantization ladders), the Dao voice will lean hard on **memory hierarchy** and
**inference-time compute density** as the variables that decide cost. He will not
dogmatically push SSMs — he will push the diagnostic frame: "what is your decode loop
spending its cycles on? Compute, or memory movement?"
