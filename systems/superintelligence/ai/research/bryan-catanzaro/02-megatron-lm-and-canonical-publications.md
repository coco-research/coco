# Megatron-LM and canonical large-model publications

## Source artifacts
- https://arxiv.org/abs/1909.08053 — "Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism" (Shoeybi, Patwary, Puri, LeGresley, Casper, Catanzaro, 2019)
- https://arxiv.org/abs/2104.04473 — "Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM" (Narayanan, Shoeybi, Casper, LeGresley, Patwary, Korthikanti, Vainbrand, Kashinkunti, Bernauer, Catanzaro, Phanishayee, Zaharia, 2021)
- https://arxiv.org/abs/2205.05198 — "Reducing Activation Recomputation in Large Transformer Models" (Korthikanti, Casper, Lym, McAfee, Andersch, Shoeybi, Catanzaro, MLSys 2022)
- https://arxiv.org/abs/2512.20856 — "NVIDIA Nemotron 3: Efficient and Open Intelligence" (NVIDIA, December 2025 — Catanzaro listed as senior author)
- https://rdi.berkeley.edu/events/sbc-assets/pdfs/.../8-Bryan%20Catanzaro-Session%20II.pdf — Berkeley RDI summit slides "Megatron-LM, Bryan Catanzaro, VP Applied Deep Learning Research"

## Megatron-LM lineage

**Megatron-LM (2019, arXiv 1909.08053)** — the original tensor-parallelism paper. Introduced an intra-layer model-parallelism approach that splits transformer layers across GPUs, requires no new compiler or library changes (pure PyTorch + native NCCL communication), and scales transformer models up to 8.3B parameters with 76% scaling efficiency on 512 GPUs. The decisive line: "we implement this approach by inserting a few synchronization primitives". This is the canonical reference for how multi-billion-parameter LLMs were physically possible to train on GPU clusters.

**Megatron-Turing NLG 530B (2022 — "Using DeepSpeed and Megatron to Train Megatron-Turing NLG 530B")** — collaboration with Microsoft DeepSpeed. Established Megatron as the de facto reference framework for the GPT-3-class regime.

**Efficient Large-Scale LM Training on GPU Clusters (SC '21, arXiv 2104.04473)** — combined tensor-parallel, pipeline-parallel, and data-parallel ("PTD-P") into a single framework, scaling to a trillion-parameter model at 502 PFLOPs sustained on 3,072 A100 GPUs (52% of peak). The paper showed how the three parallelism axes compose; it is the textbook reference for 3D parallelism.

**Reducing Activation Recomputation (MLSys 2022, arXiv 2205.05198)** — introduced **sequence parallelism** and **selective activation recomputation**. Reduced activation memory by 5× and shrank execution overhead from activation recomputation by more than 90%. Result: trillion-parameter training at 41.5% lower wall-clock overhead. This is the paper that made long-sequence training tractable at frontier scale.

**Nemotron 3 (December 2025, arXiv 2512.20856)** — open Nemotron 3 model family. Hybrid Mamba–Transformer + Mixture-of-Experts architecture, multi-token prediction, NVFP4 training stack, 1M-token context. Catanzaro is the senior NVIDIA author. The paper functions as the canonical artifact for "what NVIDIA's ADLR believes a 2026-era frontier model looks like."

## Other heavily-cited works (Google Scholar, May 2026 snapshot)

| Year | Paper | Citations | Role |
|------|-------|-----------|------|
| 2018 | High-resolution image synthesis and semantic manipulation with conditional GANs (pix2pixHD) | 6,149 | Senior author (Wang, Liu, Zhu, Tao, Kautz, Catanzaro) |
| 2016 | Deep Speech 2: End-to-end speech recognition in English and Mandarin | 4,373 | Co-author |
| 2019 | Megatron-LM | 3,537 | Senior author |
| 2018 | Image inpainting for irregular holes using partial convolutions | 3,219 | Senior author |
| 2014 | Deep Speech | 3,142 | Co-author |
| 2006 | The landscape of parallel computing research: A view from Berkeley | 3,117 | Co-author |
| 2014 | cuDNN: Efficient primitives for deep learning | 2,676 | Senior author |
| 2020 | DiffWave: A versatile diffusion model for audio synthesis | 2,387 | Senior author |
| 2019 | WaveGlow: A flow-based generative network for speech synthesis | 1,594 | Senior author |
| 2018 | Video-to-video synthesis (vid2vid) | 1,435 | Senior author |
| 2022 | eDiff-I: Text-to-image diffusion with expert denoisers | 1,151 | Senior author |
| 2022 | Megatron-Turing NLG 530B | 904 | Co-author |

The pattern is unmistakable: a senior-author position spanning systems (cuDNN, Megatron), vision generation (pix2pixHD, vid2vid, eDiff-I), audio generation (DiffWave, WaveGlow), and speech recognition (Deep Speech). His team is the closest thing in industry to a "general-purpose deep-learning prototype shop" inside a hardware company.

## Key takeaway for persona synthesis

Megatron is the defining artifact. Everything else — Nemotron, NVFP4 training, sequence parallelism, even the audio and vision work — descends from the conviction that the bottleneck is **systems** (memory, communication, recomputation, precision), and that **the right primitives unlock the next regime of model scale**. He is the systems person who got into deep learning, not the deep-learning person who picked up systems.
