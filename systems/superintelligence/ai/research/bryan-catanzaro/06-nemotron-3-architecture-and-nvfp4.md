# Nemotron 3 architecture and NVFP4 training stack (Dec 2025)

## Source artifacts
- https://arxiv.org/abs/2512.20856 — "NVIDIA Nemotron 3: Efficient and Open Intelligence" technical report (Dec 2025)
- https://arxiv.org/pdf/2509.25149 — "Pretraining Large Language Models with NVFP4" (Sep 2025)
- https://developer.nvidia.com/blog/3-ways-nvfp4-accelerates-ai-training-and-inference/ — NVIDIA Technical Blog on NVFP4
- https://www.nvidia.com/en-us/ai-data-science/foundation-models/nemotron/ — Nemotron product page
- https://blogs.nvidia.com/blog/neurips-open-source-digital-physical-ai/ — NeurIPS 2025 announcement
- https://www.thedeepview.com/articles/why-nvidia-threw-its-weight-behind-open-source-ai — "Why NVIDIA threw its weight behind open source AI"
- https://www.trendingtopics.eu/nvidia-bets-26-billion-on-open-source-ai-to-build-a-new-moat-next-to-cuda/ — "Nvidia Bets $26 Billion on Open-Source AI to Build a New Moat Next to CUDA"

## Architecture summary

**Nemotron 3 model family** (announced Dec 2025):
- **Nano** — 30B parameters with 3B active (30B-3A MoE)
- **Super** — coming Q1 2026
- **Ultra** — coming H1 2026

**Architecture:**
- Hybrid **Mamba (state-space)** + **Transformer** blocks
- **Mixture-of-Experts** routing for parameter efficiency
- **Native multi-token prediction** — predicts multiple tokens per forward pass, enabling effectively-free speculative decoding (the first token is accepted as the output; subsequent tokens are used as draft predictions and verified)
- Context length up to **1 million tokens**
- Trained with **NVFP4** (NVIDIA's 4-bit floating-point format)

## NVFP4 — the precision moat

NVFP4 is NVIDIA's 4-bit floating-point format implemented in hardware starting with the Blackwell architecture. The Nemotron 3 paper claims:

- 4× memory bandwidth advantage over BF16
- 2× over FP8
- Maintains accuracy on par with FP8/BF16 at frontier scale
- **"No one outside NVIDIA has ever pre-trained a model at this scale using four-bit math."** (Catanzaro)

This is the architectural claim that ties hardware (Blackwell tensor cores supporting FP4) to software (Megatron's training stack) to model artifact (Nemotron 3). It is the exact pattern Catanzaro means by "GPU + software co-design as the moat."

## The 26B-dollar open-source moat strategy

The trendingtopics analysis frames NVIDIA's open-source posture as a deliberate moat-extension play:

- 20 years and ~$26B built the **CUDA moat** (low-level GPU compute primitives).
- The next 5 years and another ~$26B are being directed at building an **open-model moat** alongside CUDA. The pattern is Google's Android strategy applied to LLMs: open weights, open data, open techniques — but every byte of revenue happens on NVIDIA silicon.

Quote from Catanzaro on the strategy: **"Many people don't know this, but Nvidia has more software engineers than hardware engineers."**

## What this implies for his stances

- **Open models are not a charity move.** They are the moat extension.
- **4-bit training is the new precision regime.** Anyone designing for FP16/BF16 at scale will be slower per-watt and per-FLOP than NVIDIA's stack.
- **Hybrid architectures (Mamba + Transformer + MoE) are the bet for the next regime.** Dense Transformer-only is being deprecated even at NVIDIA's flagship release.
- **Multi-token prediction inside the architecture** subsumes external speculative decoding. He will critique inference stacks that bolt speculative decoding on top of a single-token-prediction model as "missing the architecture-level fix."
- **1M-token context is now the table-stakes target** for frontier-open models. The Megatron + selective recomputation + sequence parallelism lineage is what makes this physically tractable.

## Bottom line for synthesis

The Nemotron 3 release is the most important single artifact in his 2025–2026 record. It is the proof that the systems-kernels-serving cell argument — co-design hardware, precision, kernels, parallelism, and architecture together — produces models that the rest of the industry cannot match per-FLOP. Every persona stance about "GPU + software co-design is the moat" should anchor to this paper.
