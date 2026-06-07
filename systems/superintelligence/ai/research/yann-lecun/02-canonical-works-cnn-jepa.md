# Yann LeCun — Canonical Works

## Convolutional Networks (1988–1998)

LeCun developed the convolutional neural network architecture at Bell Labs in the late 1980s, building on Fukushima's Neocognitron but adding gradient-based training.

- **LeNet (1989)** — First practical CNN trained end-to-end with backpropagation on handwritten digit recognition.
- **LeNet-5 (1998)** — Mature version used in commercial bank check reading systems.
- Canonical paper: **"Gradient-based learning applied to document recognition"** (LeCun, Bottou, Bengio, Haffner — Proceedings of the IEEE, vol. 86, no. 11, November 1998).
- CNNs went on to become the foundation of computer vision (ImageNet 2012, ResNet, etc.) and influence sequence models.

## Energy-Based Models

- "A Tutorial on Energy-Based Learning" (LeCun, Chopra, Hadsell, Ranzato, Huang — 2006) — Predicting on Structured Data.
- LeCun has consistently argued that EBMs are a more general framework than probabilistic models for unsupervised learning.

## DjVu Image Compression
- Developed at AT&T Labs (with Léon Bottou and Vladimir Vapnik).
- Used by the Internet Archive for scanned document storage.

## "A Path Towards Autonomous Machine Intelligence" (2022)
Source: https://openreview.net/forum?id=BZ5a1r-kVsf
- Submitted 2022 to OpenReview as a position paper, not a peer-reviewed journal article.
- Three central questions:
  1. How could machines learn as efficiently as humans and animals?
  2. How could machines learn to reason and plan?
  3. How could machines learn representations of percepts and action plans at multiple levels of abstraction?
- Three core architectural proposals:
  1. **Configurable predictive world models** — systems that simulate future states
  2. **Intrinsic motivation** — behavior driven by internal reward signals
  3. **Hierarchical joint embedding architectures** — multi-level representation systems trained through self-supervised learning
- This paper is the canonical source for the JEPA family of architectures.

## JEPA Family

### I-JEPA (Image JEPA) — January 2023
Source: https://arxiv.org/abs/2301.08243
- Title: "Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture"
- Authors: Assran, Duval, Misra, Bojanowski, Vincent, Rabbat, LeCun, Ballas
- Submission date: January 19, 2023; final version April 13, 2023
- Non-generative self-supervised learning. Predicts representations of masked target blocks from a context block. **No hand-crafted data augmentation.**
- Trained ViT-Huge/14 on ImageNet in <72 hours on 16 A100 GPUs.
- Meta AI blog: https://ai.meta.com/blog/yann-lecun-ai-model-i-jepa/

### V-JEPA (Video JEPA) — February 2024
- Extends JEPA to spatiotemporal patches in video.

### V-JEPA 2 — June 11, 2025
Source: https://ai.meta.com/blog/v-jepa-2-world-model-benchmarks/
- 1.2 billion parameter model.
- Two components: Encoder (raw video → semantic embeddings) + Predictor (embeddings + context → predicted embeddings).
- Two-stage self-supervised training:
  - Stage 1 (pre-training): 1M+ hours of video and 1M images, no human labels.
  - Stage 2 (action-conditioning): 62 hours of robot data.
- State-of-the-art on Something-Something v2 and Epic-Kitchens-100 action anticipation.
- Robot pick-and-place: 65–80% success on novel objects in unseen environments, **zero-shot**.
- Outperformed Nvidia's Cosmos by up to 30× in inference speed.
- Released three new benchmarks: IntPhys 2, MVPBench, CausalVQA. Human performance 85–95%, current models trail significantly.

## V-JEPA 2's Significance
- Released **5 months before** LeCun's announced Meta departure.
- Widely viewed as LeCun's final flagship research artifact at Meta.
- Operationalizes the world-models vision from the 2022 "Path Towards AMI" position paper.
- AMI Labs is now picking up this research thread post-Meta.
