# Mamba — Linear-Time Sequence Modeling with Selective State Spaces

Sources:
- https://arxiv.org/abs/2312.00752
- https://github.com/state-spaces/mamba
- COLM 2024 Outstanding Paper

Extracted: 2026-05-27

## Citation

Albert Gu, Tri Dao.
**"Mamba: Linear-Time Sequence Modeling with Selective State Spaces."**
First arXiv: 2023-12-01.
COLM 2024 — **Outstanding Paper Award**.

## Core innovation

**Selective state spaces** — SSM parameters that vary based on **input content**, so the
model can "selectively propagate or forget information along the sequence length dimension
depending on the current token."

This addresses the historical weakness of SSMs: prior structured SSMs (S4, H3) were
input-independent — they couldn't decide whether the current token is information-worthy.
Selective SSMs add that gate.

## Key claims

- **Linear-time** complexity with **5× higher throughput** than Transformers at
  comparable scale.
- **Mamba-3B performs comparably to Transformer-6B** — half the parameters, comparable
  language modeling quality.
- Handles **million-length sequences** while continuing to improve performance — Transformers
  with attention cannot.
- **No attention, no MLP block** — the entire model is selective SSM layers.
- Works across modalities: language, audio, genomics.

## Hardware-aware design (the Dao signature)

The paper specifically argues that prior SSMs failed in part because they tried to
materialize state in HBM. Mamba's contribution is keeping the large SSM state
**resident in SRAM** during the parallel scan, which is the same memory-hierarchy
discipline as FlashAttention applied to a different sequence-modeling architecture.

> "Hardware-aware parallel algorithm" — paper's own framing.

This is the persona's recurring thesis: a clever algorithm that ignores the memory
hierarchy will lose to a less clever one that respects it.

## Why SSMs matter as an alternative to attention

The paper's framing:

- Prior SSMs underperformed attention on language — because they lacked content-based
  reasoning.
- Selective SSMs close that gap **and** retain the linear-time inference profile.
- This makes SSMs viable as a serious alternative substrate, not just a curiosity.

This is the v2-panel-relevant framing: **attention is not the only path to capable
sequence models**. Tri Dao co-owns this stance with Albert Gu.

## Follow-on work (already absorbed into the persona)

- **Mamba-2 / Transformers are SSMs** (ICML 2024) — Dao & Gu show a **structural duality**
  between attention and SSMs through a shared "Structured State Space Duality" frame.
  Attention and SSMs become two faces of the same matrix decomposition.
- **Mamba-3** (ICLR 2026) — "inference-first" SSM; complex-valued state; MIMO recurrence;
  cited as 4% improvement over Transformer baseline at 1.5B; matches strong LLM perplexity
  at **half the decoding cost**. Predicts hybrid SSM + global self-attention as the dominant
  shape going forward.

## Recognition

- COLM 2024 Outstanding Paper.
- One of the most-discussed alternative-architecture papers of the post-2022 LLM era.
- Direct inspiration for IBM Granite Hybrid, NVIDIA Hymba, AI21 Jamba, and other hybrid SSM
  models.
