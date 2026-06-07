# π₀ and π₀.5 — Robot Foundation Model Papers (extracted 2026-05-27)

Sources:
- π₀ paper (arXiv 2410.24164) — https://arxiv.org/html/2410.24164v1
- π₀.5 paper (arXiv 2504.16054) — https://arxiv.org/abs/2504.16054
- Blog announcement π₀ — https://www.pi.website/blog/pi0
- TWIML interview "π0: A Foundation Model for Robotics with Sergey Levine" — https://www.youtube.com/watch?v=5mY71rGXAkM

## π₀ (pi-zero)

- **Title:** "π₀: A Vision-Language-Action Flow Model for General Robot Control"
- **Released:** October–November 2024.
- **Authors:** Physical Intelligence team. Levine is a senior co-author; Chelsea Finn and Karol Hausman among the core author list.
- **Architecture:** 3B-parameter transformer built on top of **PaliGemma** (Google's open vision-language model). Extended with a robot-specific **action expert** that outputs continuous joint commands using a **flow-matching** generative head.
- **Training data:** Over **10,000 hours of real-world robot teleoperation data**, collected across **7 robot embodiments** and **68 tasks**. This is the largest single corpus of cross-embodiment manipulation data publicly described as of late 2024.
- **Capabilities demonstrated at launch:** folding laundry, assembling cardboard boxes, bussing tables, basic kitchen manipulation.
- **Stance the paper takes:** that a **single generalist policy** trained on diverse cross-embodiment data can match or exceed specialist policies on each individual robot — the empirical bet that defines Physical Intelligence as a company.

## π₀-FAST

- Distillation / efficient-inference variant of π₀ released in early 2025. Same model family; trades some quality for lower latency.

## π₀.5 (pi-zero-point-five)

- **Title:** "π₀.5: a Vision-Language-Action Model with Open-World Generalization"
- **Submitted:** April 22, 2025 (arXiv 2504.16054).
- **Authors:** Roughly 36 named authors from Physical Intelligence; includes Sergey Levine, Chelsea Finn, Brian Ichter, and the broader team.
- **Capabilities demonstrated:** Long-horizon and dexterous manipulation tasks — **cleaning a kitchen** and **cleaning a bedroom** — performed in **homes the model has never been trained on**. This is the first publicly reported VLA result demonstrating substantial open-world generalization out of the training distribution.
- **Key methodological additions over π₀:**
  - **Co-training on heterogeneous tasks** across multiple robots.
  - Explicit **semantic subtask prediction** — the model predicts an intermediate language label ("put dishes in sink") that grounds the action policy.
  - Use of **web data** alongside robot data, treated as auxiliary pretraining rather than substitute.
  - **Object-detection signals** as an additional modality.
- **Stance the paper advances:** the bottleneck on generalization is not architecture but **diversity of training data**, and co-training with explicit semantic targets unlocks transfer to unseen environments.

## π₁ (pi-one)

The user brief mentions π₁ as a forthcoming or recently launched model. As of public sources on 2026-05-27, the canonical π₁ launch artifact has not been independently confirmed by arXiv or pi.website search results. Treat π₁ as on the roadmap / in development.

## Why these papers matter for the persona

- They are the empirical evidence that backs every Levine claim about "generalist over specialist", "data over algorithm", and "real-world over simulation."
- π₀.5 in particular is the demonstration that the data-flywheel thesis produces concrete open-world capability — not just better in-distribution scores.
- The flow-matching action expert is technically distinctive in a landscape mostly dominated by diffusion-based action heads, and is now widely imitated in the broader robotics-foundation-model community.

## Independent reproductions / community impact

- `lucidrains/pi-zero-pytorch` — community PyTorch reimplementation, indicates the architecture has crossed into reference-implementation territory.
- Multiple 2025 paper reviews ("Pi0, Pi0.5, Pi0-FAST — Tracing the Path of Physical Intelligence") trace the model family in detail.
