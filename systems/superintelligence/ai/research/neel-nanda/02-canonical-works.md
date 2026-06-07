# Neel Nanda — canonical works

## Foundational papers

### A Mathematical Framework for Transformer Circuits (2021)
- Anthropic, Elhage, Nanda, Olsson, Henighan, et al.
- URL: https://transformer-circuits.pub/2021/framework/index.html
- Neel's first major publication, while at Anthropic under Chris Olah. Establishes the QK/OV decomposition, residual stream as communication channel, and induction-head framing that anchors all subsequent mech interp.

### Progress measures for grokking via mechanistic interpretability (2023)
- Nanda, Chan, Lieberum, Smith, Steinhardt
- URL: https://arxiv.org/abs/2301.05217
- ICLR 2023 (oral). Fully reverse-engineered the algorithm a small transformer learns for modular addition — discrete Fourier transforms + trigonometric identities to convert addition to rotation about a circle. Identified three discrete phases of grokking: memorization → circuit formation → cleanup (weight decay removing memorization). The paper that demonstrated mech interp could produce a *complete* mechanistic explanation, not just suggestive evidence.

### Gemma Scope: Open Sparse Autoencoders Everywhere All At Once on Gemma 2 (2024)
- Lieberum, Rajamanoharan, Conmy, Smith, Sonnerat, Varma, Kramár, Nanda; advised by Rohin Shah and Anca Dragan.
- URL: https://arxiv.org/abs/2408.05147
- DeepMind blog: https://deepmind.google/blog/gemma-scope-helping-the-safety-community-shed-light-on-the-inner-workings-of-language-models/
- Open release of JumpReLU SAEs trained on every layer of Gemma 2 2B / 9B and select layers of 27B. NeurIPS 2024. The largest open SAE artifact at release; intended as community infrastructure.

### Gemma Scope 2 (2025)
- McDougall, Conmy, Kramár, Lieberum, Rajamanoharan, Nanda.
- URL: https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/gemma-scope-2-helping-the-ai-safety-community-deepen-understanding-of-complex-language-model-behavior/Gemma_Scope_2_Technical_Paper.pdf
- 2025-09-16 technical paper. Extends to Gemma 3 (270M, 1B, 4B, 12B, 27B). Continuation of community-infrastructure stance.

### Are Sparse Autoencoders Useful? A Case Study in Sparse Probing (2025)
- ICML 2025; Nanda is co-author.
- URL: https://arxiv.org/abs/2502.16681
- Critical self-examination of SAEs from inside the field. Finding: linear probes outperform SAEs on known concepts; SAEs are valuable for *discovery* of unknown features, not for *detecting* known ones. Important because the lead author was previously bullish on SAEs.

## Tools and infrastructure

### TransformerLens
- URL: https://github.com/TransformerLensOrg/TransformerLens
- Python library for mechanistic interpretability of GPT-2-style language models. Loads 50+ open-source models, exposes activations at any layer, supports activation patching / hooking / caching / editing. Created by Neel after leaving Anthropic to fix the open-source-tooling gap. Current maintainers: Bryce Meyer and Jonah Larson. v3.2.1 released 2026-05-09. ~3.5k GitHub stars, 574 forks.
- Most influential single artifact in the field's recent history. Effectively the de facto interpretability stdlib.

## Pedagogy / community

### 200 Concrete Open Problems in Mechanistic Interpretability (2022-12-28)
- Sequence on LessWrong / AlignmentForum
- URL: https://www.lesswrong.com/posts/LbrPTJ4fmABEdEnLf/200-concrete-open-problems-in-mechanistic-interpretability
- A research-agenda enumeration written explicitly for newcomers — "find a problem that catches your fancy and jump in." Reshaped how junior researchers entered the field.

### Mechanistic Interpretability Quickstart Guide
- URL: https://www.neelnanda.io/mechanistic-interpretability/quickstart
- "How to speedrun your way to maybe doing something useful in mechanistic interpretability in a weekend." Pairs with the 200 Concrete Open Problems sequence as the canonical on-ramp.

### "An Extremely Opinionated Annotated List of My Favourite Mechanistic Interpretability Papers"
- URL: https://www.neelnanda.io/mechanistic-interpretability/favourite-papers-old
- Reading list with commentary; effectively a curriculum.

## Talks

### An Introduction to Mechanistic Interpretability — IASEAI 2025
- URL: https://www.youtube.com/watch?v=0704iLc55Fs
- Pedagogical lecture, the canonical 2025 "what is mech interp" intro.

### Theories of change for mech interp (talk announced 2025-11-14 on X)
- URL: https://x.com/NeelNanda5/status/1989694906231849308
- "By default all research is useless. So we need a story for why our work matters. In this talk I discuss my theories of change for mech interp, different routes to impact, and how it determines what to research."
