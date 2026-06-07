# Albert Gu — Canonical Works and Publications

## Canonical research papers

These are the works that anchor the persona. Each is a milestone in the state-space-model line of research and is the primary evidence anyone summoning Gu should anchor to.

### HiPPO (2020) — the precursor

- **Title:** HiPPO: Recurrent Memory with Optimal Polynomial Projections
- **Authors:** Albert Gu, Tri Dao, Stefano Ermon, Atri Rudra, Christopher Ré
- **Venue:** NeurIPS 2020
- **Significance:** The mathematical machinery for projecting a continuous signal onto a polynomial basis. HiPPO is the substrate on which S4 is built — without HiPPO's diagonal-plus-low-rank decomposition, the structured matrices that make S4 efficient do not exist.

### S4 (2022) — the canonical SSM paper

- **Title:** Efficiently Modeling Long Sequences with Structured State Spaces
- **Authors:** Albert Gu, Karan Goel, Christopher Ré
- **Venue:** ICLR 2022
- **arXiv:** https://arxiv.org/abs/2111.00396
- **ICLR poster:** https://iclr.cc/virtual/2022/poster/6959
- **Repo:** https://github.com/state-spaces/s4
- **Annotated implementation:** Sasha Rush's "Annotated S4" — https://srush.github.io/annotated-s4/
- **Significance:** Introduced the structured-state-space sequence model. Solved the Path-X task (length 16,384) on the Long Range Arena benchmark — the first model to do so meaningfully. Set state-of-the-art on every LRA task and substantially closed the long-context gap to Transformers on image and language modeling. Achieved 91% accuracy on sequential CIFAR-10. The paper that put SSMs back on the deep-learning map.

### Mamba (2023) — the breakthrough

- **Title:** Mamba: Linear-Time Sequence Modeling with Selective State Spaces
- **Authors:** Albert Gu, Tri Dao
- **Posted:** December 2023, arXiv:2312.00752
- **arXiv:** https://arxiv.org/abs/2312.00752
- **Repo:** https://github.com/state-spaces/mamba
- **Significance:** The selection mechanism — making SSM parameters input-dependent — was the unlock that let SSMs match or exceed Transformers on language modeling at small-to-medium scale. Mamba-3B outperformed Transformers of the same size and matched Transformers twice its size, both in pretraining and downstream evaluation. The paper that turned SSMs from a long-context curiosity into a real architectural competitor.

### Mamba-2 / Transformers are SSMs (2024)

- **Title:** Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality
- **Authors:** Tri Dao, Albert Gu
- **Venue:** ICML 2024
- **arXiv:** https://arxiv.org/abs/2405.21060
- **Significance:** Established the State Space Duality (SSD) framework — a theoretical bridge showing that attention and selective SSMs are two views of the same family of structured semiseparable matrix operations. Introduced Mamba-2, which is 2–8× faster than Mamba-1 by leveraging matrix-multiplication as the primitive (hitting tensor cores on modern GPUs). Brought tensor-parallel, sequence-parallel, and variable-length systems tricks from the Transformer ecosystem into SSM land.

### H-Net / Dynamic Chunking (2025)

- **Title:** Dynamic Chunking for End-to-End Hierarchical Sequence Modeling
- **Authors:** Sukjun Hwang, Brandon Wang, Albert Gu (Goomba Lab)
- **Posted:** July 2025
- **Significance:** A hierarchical, end-to-end-learned chunking mechanism that replaces tokenization. At ~1B parameters, H-Net matches compute-and-data while surpassing tokenized Transformers and discovering word- and superword-like chunks emergently. Gu's framing on launch (X, July 8, 2025, https://x.com/_albertgu/status/1943704103059664966): *"Tokenization is just a special case of 'chunking' — building low-level data into high-level abstractions — which is in turn fundamental to intelligence. Our new architecture, which enables hierarchical *dynamic chunking*, is not only tokenizer-free, but simply scales better."* dnaHNet, a downstream application of H-Net to genomic sequences, was accepted as an ICML 2026 Spotlight.

### Stanford PhD dissertation (2023)

- **Title:** Modeling Sequences with Structured State Spaces
- **Author:** Albert Gu
- **Advisor:** Christopher Ré
- **Stanford Digital Repository:** https://purl.stanford.edu/mb976vf9362
- **Augmented PDF:** https://stacks.stanford.edu/file/druid:mb976vf9362/gu_dissertation-augmented.pdf
- **Significance:** The book-length synthesis of HiPPO → S4 → S5 → H3 as a unified theoretical and computational framework. The thesis frames SSMs as the principled deep-learning instantiation of the classical control-theory state-space formulation, with structured matrix operations as the computational primitive that makes it tractable.

## Cartesia product line — the production-scale evidence

### Sonic (May 2024)

- **Original Sonic launch:** Approximately 135ms model latency. Cartesia's first public SSM-backed voice model.

### Sonic 2.0 (March 2025)

- **Latency:** 90ms full model, 40ms turbo.
- **Coincided with:** $64M Series A from Kleiner Perkins.
- **Added:** Voice changer, audio infill (seamless editing).
- **Source:** https://cartesia.ai/blog/series-a

### Sonic-3 (October 2025)

- **Latency:** 90ms model latency, 190ms end-to-end (time-to-first-audio).
- **Languages:** 42 (up from 15 in Sonic 2.0).
- **Emotional range:** Native laughter, full emotional expressiveness, real-time response shaping.
- **Coincided with:** $100M Series B (Kleiner Perkins, Index Ventures, Lightspeed, NVIDIA).
- **Sources:** https://startupstag.com/investments/cartesia-raises-100m-launches-sonic-3-ai-voice-model/ and https://cartesia.ai/sonic

### Ink-Whisper STT (June 2025)

- Cartesia's fine-tuned Whisper variant purpose-built for real-time voice agent transcription rather than post-processing.

### Line agent platform (August 2025)

- Code-first agent development platform for building voice agents on top of Cartesia's models.

## Talks and lectures (canonical)

- **"On the Tradeoffs of State Space Models"** — Simons Institute, September 27, 2024. https://simons.berkeley.edu/talks/albert-gu-carnegie-mellon-university-2024-09-27. Companion blog post at https://goombalab.github.io/blog/2025/tradeoffs/.
- **"Mamba, Mamba-2 and Post-Transformer Architectures for Generative AI"** — TWIML AI Podcast Episode 693, July 16, 2024. https://twimlai.com/podcast/twimlai/mamba-mamba-2-and-post-transformer-architectures-for-generative-ai/.
- **"The State Space Model Revolution"** — Cognitive Revolution Podcast, July 4, 2024. https://www.cognitiverevolution.ai/the-state-space-model-revolution-with-albert-gu/.
- **"State Space Models and Real-time Intelligence"** — No Priors Podcast, with Karan Goel (joint appearance), 2024.
- **Laude Lounge @ NeurIPS 2025** — Research-to-Startup panel, December 2025.

## Sources

- https://arxiv.org/abs/2111.00396 — S4
- https://arxiv.org/abs/2312.00752 — Mamba
- https://arxiv.org/abs/2405.21060 — Mamba-2 / SSD
- https://github.com/state-spaces/mamba — Mamba repo
- https://github.com/state-spaces/s4 — S4 repo
- https://purl.stanford.edu/mb976vf9362 — Stanford dissertation
- https://cartesia.ai/sonic — Sonic product page
- https://goombalab.github.io/blog/2025/tradeoffs/ — Tradeoffs blog post
- https://simons.berkeley.edu/talks/albert-gu-carnegie-mellon-university-2024-09-27 — Simons talk
- https://x.com/_albertgu/status/1943704103059664966 — H-Net launch post
