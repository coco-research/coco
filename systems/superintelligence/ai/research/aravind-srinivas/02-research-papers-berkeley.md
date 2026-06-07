# Aravind Srinivas — Pre-Perplexity Research Papers

Compiled 2026-05-27 from arXiv.

Aravind's research at UC Berkeley under Pieter Abbeel focused on **self-supervised representation learning and reinforcement learning from pixels**. He is not an author of the original SimCLR paper (Ting Chen et al., Google); the SimCLR-adjacent work was at Berkeley with a different lineage.

## Key papers

### 1. CURL: Contrastive Unsupervised Representations for Reinforcement Learning

- **Authors:** Aravind Srinivas, Michael Laskin, Pieter Abbeel
- **arXiv:** 2004.04136
- **Date:** April 8, 2020
- **URL:** https://arxiv.org/abs/2004.04136
- **Contribution:** Combines unsupervised contrastive representation learning with off-policy RL control. Extracts high-level features from raw pixels using contrastive learning, then performs RL on the learned embeddings. Reports 1.9x and 1.2x performance gains at 100K-step benchmarks on DeepMind Control Suite and Atari. First image-based RL algorithm to nearly match sample-efficiency of state-based feature methods on DMControl.
- **Why it matters for persona:** This is Aravind's signature paper. Establishes his domain identity as a "contrastive representations + RL" researcher pre-LLM. The pattern — *learn a good embedding cheaply, then layer downstream tasks on top* — is precisely what Perplexity does with foundation models on top of a search index.

### 2. Reinforcement Learning with Augmented Data (RAD)

- **Authors:** Michael Laskin, Kimin Lee, Adam Stooke, Lerrel Pinto, Pieter Abbeel, Aravind Srinivas
- **arXiv:** 2004.14990
- **Date:** April 2020
- **Contribution:** Data augmentation (random crops, color jitter) on pixel observations dramatically improves RL sample efficiency. A "no model change, just better data" result that beat CURL on several benchmarks.

### 3. Decision Transformer: Reinforcement Learning via Sequence Modeling

- **Authors:** Lili Chen, Kevin Lu, Aravind Rajeswaran, Kimin Lee, Aditya Grover, Michael Laskin, Pieter Abbeel, Aravind Srinivas, Igor Mordatch
- **arXiv:** 2106.01345
- **Date:** June 2021
- **Contribution:** Recasts offline RL as a sequence-modeling problem solvable by a Transformer conditioned on returns. One of the most cited "RL via LLM-style architectures" papers.
- **Why it matters for persona:** Aravind is on the author list of a paper that prefigures the entire 2023+ "treat everything as sequence prediction" worldview that Perplexity instantiates.

### 4. SUNRISE: A Simple Unified Framework for Ensemble Learning in Deep RL

- **Authors:** Kimin Lee, Michael Laskin, Aravind Srinivas, Pieter Abbeel
- **arXiv:** 2007.04938

### 5. Reinforcement Learning with Latent Flow

- **Authors:** Wenling Shang, Xiaofei Wang, Aravind Srinivas, Aravind Rajeswaran, Yang Gao, Pieter Abbeel, Michael Laskin
- **arXiv:** 2101.01857

## Themes across the corpus

1. **Representation learning before policy learning.** Almost every paper first learns a cheap, self-supervised embedding, then puts the heavy machinery on top. This is exactly Perplexity's product architecture: a cheap, fast retrieval substrate with LLM reasoning on top.
2. **Sample efficiency obsession.** Repeated emphasis on doing more with fewer environment steps / fewer labels.
3. **Pixels-in, decisions-out, end-to-end differentiable.** No hand-engineered features. Bias against ad-hoc pipelines.
4. **Reward sparsity tolerance.** Many of these techniques (CURL, RAD) are specifically motivated by the fact that RL reward signal is thin. This priors his Perplexity thinking: signal scarcity is the dominant variable.

## Sources

- https://arxiv.org/abs/2004.04136
- https://arxiv.org/abs/2004.14990
- https://arxiv.org/abs/2106.01345
- https://arxiv.org/abs/2007.04938
- https://arxiv.org/abs/2101.01857
- https://people.eecs.berkeley.edu/~pabbeel/publications.html
