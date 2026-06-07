# Pieter Abbeel — canonical works, publications, signature papers

**Sources:**
- https://people.eecs.berkeley.edu/~pabbeel/publications.html
- https://dblp.org/pid/a/PieterAbbeel.html
- https://scholar.google.com/citations?user=vtwH6GkAAAAJ&hl=en
- https://ai.stanford.edu/~ang/papers/icml04-apprentice.pdf

**Fetched:** 2026-05-27

## Foundational papers (pre-2020)

### Apprenticeship Learning via Inverse Reinforcement Learning
**Abbeel & Ng, ICML 2004.** The IRL canon. Recovers a reward function from expert demonstrations rather than hand-engineering one. URL: https://ai.stanford.edu/~ang/papers/icml04-apprentice.pdf

### Autonomous Helicopter Aerobatics through Apprenticeship Learning
**Abbeel, Coates, Ng (2010).** The Stanford autonomous helicopter — flips, rolls, tic-tocs — learned from human expert demonstration. A canonical demonstration that RL + IRL is real-world deployable. Sage Journal.

### Trust Region Policy Optimization (TRPO)
**Schulman, Levine, Moritz, Jordan, Abbeel, ICML 2015.** The bridge from policy gradient theory to deep RL. Schulman's PhD-stage paper under Abbeel. Direct ancestor of PPO. https://arxiv.org/abs/1502.05477

### Generative Adversarial Imitation Learning (GAIL)
**Ho & Ermon (Abbeel co-advised lineage), NeurIPS 2016.** Imitation learning recast as GAN. Bridge between Abbeel's IRL roots and the deep-learning generation. Jonathan Ho later founded Ideogram and authored DDPM.

### Domain Randomization
Abbeel lab papers on sim-to-real transfer via domain randomization (~2017). Train in simulation with extreme randomization of textures, lighting, dynamics so policies generalize to real robots zero-shot.

### Hindsight Experience Replay (HER)
**Andrychowicz, Wolski, Ray, ..., Abbeel et al., NeurIPS 2017.** Sample-efficient RL by re-labeling failed trajectories as successes for different goals.

### Soft Actor-Critic (SAC)
**Haarnoja, Zhou, Abbeel, Levine, ICML 2018.** Maximum-entropy off-policy deep RL. State of the art for continuous control for years.

### Model-Agnostic Meta-Learning (MAML)
**Finn, Abbeel, Levine, ICML 2017.** Chelsea Finn PhD thesis cornerstone. Few-shot adaptation via second-order gradients.

### Denoising Diffusion Probabilistic Models (DDPM)
**Ho, Jain, Abbeel, NeurIPS 2020.** Jonathan Ho's PhD work. The paper that launched modern diffusion model generation (Imagen, Stable Diffusion, DALL-E 2 all trace back). Abbeel as co-author on the foundational diffusion model paper.

### Decision Transformer
**Chen, Lu, ..., Abbeel et al., NeurIPS 2021.** Recast RL as sequence modeling on (return, state, action) tuples. Conditioning on desired return rather than running policy gradient. Major reframe.

### Implicit Behavior Cloning, BC-Z, RT-1 ancestors
Various 2020-2023 papers laying groundwork for general-purpose robot transformers.

## 2024 publications

- **HumanoidBench**: Simulated humanoid benchmark for whole-body locomotion + manipulation (RSS 2024).
- **Body Transformer**: Leveraging robot embodiment for policy learning (CoRL 2024).

## 2025 publications

- **MultiGen**: Multimodal generation in simulation to learn multimodal policies in real. CoRL 2025 Best Paper Finalist.
- **VideoMimic**: Visual imitation enables contextual humanoid control. CoRL 2025 Best Student Paper Award. Real2sim2real pipeline reconstructs 3D environments + human motion from single-camera video, retargets to humanoid. https://arxiv.org/abs/2505.03729 — repo at https://github.com/hongsukchoi/VideoMimic
- **Value-Based Deep RL Scales Predictably**: ICML 2025.
- **FastTD3**: Simple, fast, capable RL for humanoid control. 2025.
- **MaxInfoRL**: Boosting exploration in RL through information gain maximization. ICLR 2025.
- **SEMDICE**: Off-policy state entropy maximization via stationary distribution correction. ICLR 2025.

## 2026 publications (in press)

- **TWIST2** (ICRA 2026): Scalable, portable, holistic humanoid data collection. Uses Pico4U VR + custom $250 2-DoF robot neck for egocentric data. 100 demonstrations / 15 minutes / ~100% success rate. https://arxiv.org/abs/2511.02832 (posted late 2025), repo at https://github.com/amazon-far/TWIST2 — note the **amazon-far** GitHub org, signaling Amazon Frontier AI & Robotics.
- **EgoMI** (ICRA 2026): Learning active vision + whole-body manipulation from egocentric demonstrations.
- **Learning to Design Soft Hands using Reward Models** (ICRA 2026).
- **D-REX** (ICLR 2026): Differentiable real-to-sim-to-real engine for dexterous grasping.

## Covariant / Amazon robotic foundation models

- **Covariant Brain**: in-warehouse deployment platform (2020+).
- **RFM-1 (Robotics Foundation Model 1)**: Announced March 11, 2024. Trains on text, images, video, robot actions, sensor data from warehouse operations. Multimodal foundation model for piece-picking and beyond.
- **RFM-2 / successors**: No formal public announcement of "RFM-2" surfaced in May 2026. Likely folded into Amazon Nova + internal robotic models post-acquisition. Open question whether Covariant publishes future model cards or whether all R&D output now ships as Amazon products.

## Citation profile

- Google Scholar h-index: very high (200K+ total citations as of May 2026).
- DDPM, SAC, MAML, TRPO, GAIL, Hindsight Experience Replay, Decision Transformer — each individually has tens of thousands of citations.
