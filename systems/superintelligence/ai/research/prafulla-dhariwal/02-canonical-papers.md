# Prafulla Dhariwal — Canonical Publications

Source: https://prafulladhariwal.com/ and https://scholar.google.com/citations?user=0pOgVVAAAAAJ

## Top-cited papers (Google Scholar, as of 2026-05-27)

1. **Language Models are Few-Shot Learners** (Brown et al., 2020) — 85,799 citations. Dhariwal is a named co-author of the foundational GPT-3 paper. NeurIPS 2020.

2. **Proximal Policy Optimization Algorithms** (Schulman, Wolski, Dhariwal, Radford, Klimov, 2017) — 40,097 citations. The PPO paper. Foundational RL algorithm still used in RLHF pipelines.

3. **Diffusion Models Beat GANs on Image Synthesis** (Dhariwal & Nichol, 2021) — 14,480 citations. *His defining first-author work.* Introduced classifier guidance; demonstrated diffusion surpasses GANs on ImageNet at FID 2.97 (128x128), 4.59 (256x256), 7.72 (512x512). NeurIPS 2021 Spotlight. arXiv: 2105.05233.

4. **Hierarchical Text-Conditional Image Generation with CLIP Latents (DALL-E 2)** (Ramesh, Dhariwal, Nichol, Chu, Chen, 2022) — 11,168 citations.

5. **Improved Denoising Diffusion Probabilistic Models** (Nichol & Dhariwal, 2021) — 6,818 citations. ICML 2021.

6. **GLIDE: Towards Photorealistic Image Generation and Editing with Text-Guided Diffusion Models** (Nichol, Dhariwal et al., 2021) — 5,636 citations. arXiv: 2112.10741.

7. **GPT-4o System Card** (2024) — 5,558 citations.

## Other significant works

- **Jukebox: A Generative Model for Music** (2020) — Dhariwal et al. Generative model for raw audio music.
- **Glow: Generative Flow with Invertible 1x1 Convolutions** (Kingma & Dhariwal, NeurIPS 2018) — Normalizing flow paper.
- **Consistency Models** (2023) — co-authored. Distillation approach to diffusion sampling speed.
- **Improved Techniques for Training Consistency Models** (2023) — co-authored.
- **Point-E** (2022) — text-to-3D point cloud generator. Co-authored.
- **DALL-E 3 paper** ("Improving Image Generation with Better Captions") — co-authored.
- **Scaling Laws for Autoregressive Generative Modeling** (Henighan et al., 2020) — multimodal scaling laws.
- **Variational Lossy Autoencoder** (ICLR 2017) — Dhariwal as MIT undergrad co-author.
- **OpenAI Baselines** — the canonical RL implementation repository, Dhariwal as core contributor.

## Pattern of authorship

Dhariwal is **rarely the public face** of papers (Aditya Ramesh on DALL-E; Tim Brooks/Bill Peebles on Sora; Sam Altman on GPT-4o announcements) but his name appears as **first author or core contributor** across the highest-impact OpenAI generative model papers from 2018–2024. He is the canonical "second-in-command engineer-researcher" pattern: low public output, extraordinarily high research footprint.

## Diffusion contribution specifically

His 2021 papers established three things that every modern image/video/audio diffusion system uses:
1. **Classifier guidance** — using a separately trained classifier to steer reverse-diffusion sampling toward conditional outputs.
2. **Improved DDPM training** — variance learning, cosine noise schedule, hybrid losses. Made diffusion competitive.
3. **Architectural improvements** to the U-Net backbone (attention heads, BigGAN-style residual blocks).

These predate Stable Diffusion and the Sora-era latent diffusion transformers but provide their foundation.
