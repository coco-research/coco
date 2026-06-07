# FlashAttention — NeurIPS 2022 Paper

Sources:
- https://arxiv.org/abs/2205.14135
- https://proceedings.neurips.cc/paper_files/paper/2022/hash/67d57c32e20fd0a7a302cb81d36e40d5-Abstract-Conference.html

Extracted: 2026-05-27

## Citation

Tri Dao, Daniel Y. Fu, Stefano Ermon, Atri Rudra, Christopher Ré.
**"FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness."**
Advances in Neural Information Processing Systems (NeurIPS), 2022.

- Submitted to arXiv: 2022-05-27
- Revised: 2022-06-23
- arXiv: 2205.14135

## Central thesis (paraphrase + quote)

> "A missing principle is making attention algorithms IO-aware — accounting for reads
> and writes between levels of GPU memory."

Standard attention algorithms ignore data movement between **GPU high-bandwidth memory (HBM)** and **on-chip SRAM**. FlashAttention's contribution is not a new mathematical form of attention — it's the same exact attention, computed in a way that respects the memory hierarchy.

## Key technical claims

- **Tiling** to reduce memory reads/writes between HBM and SRAM.
- **Fewer HBM accesses** than standard attention; the paper proves the algorithm is **IO-optimal** for certain SRAM configurations.
- **Exact** — no approximation, no quality loss vs. standard attention.

## Performance numbers reported in the paper

- **15%** speedup on BERT-large (sequence length 512).
- **3×** speedup on GPT-2 (1K tokens).
- **2.4×** speedup on long-range arena (1K–4K tokens).
- Enables sequence lengths (16K, 64K) that were previously impossible at the same model scale.

## GPU memory hierarchy reference numbers (used in the paper for A100)

- HBM: 40–80 GB, ~1.5–2.0 TB/s bandwidth.
- On-chip SRAM: 192 KB per SM × 108 SMs, ~19 TB/s bandwidth.
- SRAM is roughly **10× faster** than HBM but **many orders of magnitude smaller**.
- This asymmetry is the "missing variable" the paper centers on.

## Why this paper anchors the persona

This is the **defining kernel-optimization paper of the modern LLM era**. Every subsequent FlashAttention version (FA-2, FA-3, FA-4) and a large swath of LLM inference engines either build on this contribution or contend with it. When Tri Dao argues a position, it is almost always rooted in a version of this paper's claim: "your algorithm's compute count is not the variable that matters; your algorithm's HBM-access count is."

## Recognition

- ICML 2022 Hardware-Aware Efficient Training (HAET) Workshop **Best Paper**.
- Stanford OSS Prize, 2024.
- One of the most-cited systems-for-ML papers of the 2022–2024 period.
