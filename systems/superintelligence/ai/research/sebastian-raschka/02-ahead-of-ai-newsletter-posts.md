# Ahead of AI — newsletter post catalog and framings

Source: https://magazine.sebastianraschka.com/archive, https://magazine.sebastianraschka.com/p/workflow-for-understanding-llms

The Ahead of AI newsletter is the single best signal for what Raschka actively thinks. Roughly two long-form posts per month, each 30–90 minute read, heavy on diagrams and code references.

## Confirmed posts (2026)

- **May 16, 2026 — "Recent Developments in LLM Architectures: KV Sharing, mHC, and Compressed Attention" / "From Gemma 4 to DeepSeek V4, How New Open-Weight LLMs Are Reducing Long-Context Costs"** — architectural innovations for cost reduction in long context.
- **April 18, 2026 — "My Workflow for Understanding LLM Architectures"** — how Raschka personally analyzes new open-weight releases.
- **April 4, 2026 — "Components of A Coding Agent"** — tools, memory systems, repo context for coding agents.
- **March 22, 2026 — "A Visual Guide to Attention Variants in Modern LLMs"** — MHA, GQA, MLA, sparse attention, hybrid architectures.
- **March 14, 2026 — "New LLM Architecture Gallery"** — companion to the llm-architecture-gallery GitHub repo.
- **February 25, 2026 — "A Dream of Spring for Open-Weight LLMs: 10 Architectures from Jan–Feb 2026"** — comparative analysis of ten open-weight LLM releases.
- **January 24, 2026 — "Categories of Inference-Time Scaling for Improved LLM Reasoning"** — taxonomy of inference scaling methods.

## Confirmed posts (2025)

- **December 30, 2025 — "The State Of LLMs 2025: Progress, Problems, and Predictions"** plus "LLM Research Papers: The 2025 List (July to December)" — annual review; covers DeepSeek R1, benchmarks, 2026 predictions.
- **December 8, 2025 — ML/AI "Hello World" examples** — onboarding patterns.
- **December 3, 2025 — "From DeepSeek V3 to V3.2: Architecture, Sparse Attention, and RL Updates"** — DeepSeek architecture evolution.
- **November 12, 2025 — Tips for reading technical books** — pedagogy-meta post.
- **November 4, 2025 — "Beyond Standard LLMs"** — linear-attention hybrids, text diffusion, code world models.
- **October 29, 2025 — DGX Spark and Mac Mini benchmarks** — small-form-factor ML hardware.
- **October 5, 2025 — "Understanding the 4 Main Approaches to LLM Evaluation (From Scratch)"** — benchmarks, verifiers, leaderboards, LLM judges.
- **September 6, 2025 — "Understanding and Implementing Qwen3 From Scratch"** — detailed Qwen3 walkthrough.

## Key framings extracted

### From "My Workflow for Understanding LLM Architectures" (April 18, 2026)

> "I usually start with the official technical reports, but these days, papers are often less detailed than they used to be"

> "if the weights are shared on the Hugging Face Model Hub and the model is supported in the Python transformers library, we can usually inspect the config file and the reference implementation directly"

> "And 'working' code doesn't lie."

His framing: papers have become less detailed, so reading the actual implementation code is the most reliable path to understanding. He describes it as "one of the best exercises" for understanding architectures. **Critical caveat: this only works for open-weight models.** Proprietary systems like ChatGPT or Claude can't be inspected this way.

### Recurring stances visible across the archive

- **Open-weight LLMs deserve close architectural reading** — almost every month has a post comparing the latest open-weight releases (Llama, Qwen, DeepSeek, Mistral, Gemma).
- **Reasoning is the 2025–2026 frontier** — multiple posts on inference-time scaling, GRPO, RLVR, self-refinement, distillation for reasoning.
- **From-scratch implementation is the test of understanding** — recurring article structure: take a new model, re-implement key components in ~hundreds of lines of PyTorch, show them working.
- **Evaluation matters more than people admit** — October 2025 piece on "4 main approaches" pushes back on benchmark-only reporting; verifiers, LLM judges, leaderboards each have failure modes.
