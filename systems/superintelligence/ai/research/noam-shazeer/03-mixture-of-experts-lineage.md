# Shazeer's Mixture-of-Experts lineage — from MoE 2017 to GLaM to Gemini

Sources:
- https://arxiv.org/abs/1701.06538 — "Outrageously Large Neural Networks: The Sparsely-Gated Mixture-of-Experts Layer" (Shazeer et al., 2017)
- https://arxiv.org/abs/2006.16668 — "GShard" (Lepikhin, Lee, Xu, Chen, Firat, Huang, Krikun, Shazeer, Chen, 2020)
- https://arxiv.org/abs/2101.03961 — "Switch Transformers" (Fedus, Zoph, Shazeer, 2021/2022 JMLR)
- https://arxiv.org/abs/2112.06905 — "GLaM: Efficient Scaling of Language Models with Mixture-of-Experts" (2021)
- https://arxiv.org/abs/2002.05202 — "GLU Variants Improve Transformer" (Shazeer, 2020)
- https://newsletter.maartengrootendorst.com/p/a-visual-guide-to-mixture-of-experts
- https://cameronrwolfe.substack.com/p/conditional-computation-the-birth

## The single thread through Shazeer's career

Shazeer's defining technical thesis is that **conditional computation — activate only the parameters you need on each token — is the only path to keep scaling beyond the limits of dense compute**. He has spent ~10 years proving variations of this claim.

### 2017 — Sparsely-Gated MoE

- "Outrageously Large Neural Networks." First-author Shazeer.
- Introduced the modern MoE layer for deep nets: per-token routing through a learned gating function to a sparse subset of expert sub-networks.
- Trained models up to **137 billion parameters** at a time when dense models were under 1B.
- Introduced **Noisy Top-k Gating** to add stochasticity and prevent expert collapse.

### 2018 — Mesh-TensorFlow

- Shazeer's framework for splitting models across mesh-organized accelerator pools.
- First practical system for training very large Transformers (>1B params) on TPU pods.

### 2019 — T5

- Shazeer was a major contributor to the T5 text-to-text transformer line at Google Research.

### 2020 — GLU Variants Improve Transformer

- Shazeer single-author paper.
- Showed that Gated Linear Unit (GLU) variants — SwiGLU, GeGLU — in the feed-forward block beat the original ReLU FFN on T5 quality.
- **SwiGLU is now the default in Llama, Mistral, Gemini, and most modern open and closed LLMs.** This is a one-author paper that quietly retrained a generation of models.

### 2020 — GShard

- Shazeer co-author. Scaled MoE to **>600B parameters** on >2048 TPUs in 4 days.
- Introduced advanced routing and overflow handling needed for production-scale sparse models.

### 2021 — Switch Transformer

- Shazeer co-author with William Fedus and Barret Zoph.
- Simplified MoE routing to **Top-1** (one expert per token), reducing communication cost.
- Demonstrated **4× faster pretraining than T5-XXL** at matching quality.
- First MoE model to hit the trillion-parameter mark.

### 2021 — GLaM

- Google MoE language model with 1.2T params total but only ~97B active per token.
- About 7× the parameter count of GPT-3 with roughly 1/3 the training energy.

### 2024-2026 — Gemini

- Gemini 1.5 Pro and the entire Gemini 2.x family use MoE architectures internally.
- Shazeer's Hot Chips 2025 keynote explicitly credited MoE as one of the four hardware-relevant levers (more compute, more memory, more bandwidth, more sparsity).

## Why this matters for the persona

- Almost every important architectural decision in modern frontier models — multi-head attention, scaled dot-product, MoE, SwiGLU, GShard sharding — has Shazeer's name on it.
- He is the **most credentialed pro-scaling-through-architecture voice inside Google**. He believes the path forward is not "make the dense model bigger" but "make the architecture sparser and the hardware faster, then make both bigger."
- His Hot Chips slides are essentially the public version of his case: more FLOPS, more memory, more bandwidth, lower precision, determinism, plus sparsity tricks like MoE = continued scaling returns.
