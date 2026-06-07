# DeepSeek model release history — through V4 (April 2026)

Sources:
- https://en.wikipedia.org/wiki/DeepSeek
- https://api-docs.deepseek.com/updates
- https://www.cnbc.com/2026/04/24/deepseek-v4-llm-preview-open-source-ai-competition-china.html
- https://techcrunch.com/2026/04/24/deepseek-previews-new-ai-model-that-closes-the-gap-with-frontier-models/

Retrieved: 2026-05-28

## Full release timeline

| Model | Release Date | License | Parameters | Key Architecture |
|-------|--------------|---------|------------|------------------|
| DeepSeek Coder | 2023-11-02 | source-available | 1.3B–33B | Llama-based decoder |
| DeepSeek-LLM | 2023-11-29 | source-available | 7B, 67B | Llama-based decoder |
| DeepSeek-MoE | 2024-01-09 | source-available | 16B (2.7B active) | shared + routed experts |
| DeepSeek-Math | 2024-04 | source-available | 7B | GRPO RL |
| DeepSeek-V2 | 2024-05 | source-available | 15.7B–236B | MLA + MoE + KV caching |
| DeepSeek-V2.5 | 2024-09 | source-available | combined V2+Coder | hybrid |
| DeepSeek-V3 | 2024-12 | **MIT** | 671B (37B active) | multi-token prediction |
| DeepSeek-R1-Lite | 2024-11-20 | proprietary preview | unspecified | reasoning-focused |
| **DeepSeek-R1** | **2025-01-20** | **MIT** | **671B** | **GRPO without SFT (R1-Zero variant)** |
| DeepSeek-R1-0528 | 2025-05-28 | MIT | 671B | enhanced language consistency |
| DeepSeek-V3.1 | 2025-08-21 | MIT | 671B | hybrid thinking/non-thinking ("DeepThink" toggle) |
| DeepSeek-V3.2 | 2025-12-01 | MIT | 671B | sparse attention |
| **DeepSeek-V4 (preview)** | **2026-04-24** | **MIT** | **1.6T (Pro, 49B active); 284B (Flash)** | **1M-token context window** |

## DeepSeek-R1 — the global-impact event (Jan 20, 2025)

- **671B-parameter MoE reasoning model**, released open-weights under **MIT license** (permissive, commercial use allowed).
- Trained with **~2,048 Nvidia H800 GPUs at $5.6M cost** (pretraining-only figure; full infrastructure costs disputed).
- The R1-Zero variant was trained with **Group Relative Policy Optimization (GRPO)** and *no supervised fine-tuning* — a notable architectural claim.
- Matched OpenAI o1 performance on reasoning benchmarks at "1/30th the API cost."
- **January 27, 2025:** Nvidia fell ~17% — $588.8 billion single-day market-cap loss, the largest in US stock-market history. Other AI hardware names also crashed.
- Surpassed ChatGPT as the #1 free app on the US iOS App Store within a week.

## Key technical innovations associated with Liang's lab

1. **Multi-Head Latent Attention (MLA)** — V2, May 2024. Low-rank approximation reduces KV cache. Per Liang's own statement, MLA was developed by a young researcher on a personal-interest initiative inside DeepSeek — an artifact of the bottom-up culture.

2. **Mixture of Experts with shared + routed experts** — DeepSeek-MoE, V2, V3. "Shared experts" always active, "routed experts" conditionally activated.

3. **Group Relative Policy Optimization (GRPO)** — DeepSeek-Math (April 2024), used heavily in R1. PPO variant that drops the critic network and computes advantages within a group of sampled completions.

4. **R1-Zero training without SFT** — the headline-grabbing claim that reasoning behavior emerges from pure RL on verifiable rewards.

5. **Sparse attention** — V3.2, Dec 2025.

6. **1M-token context** — V4, April 2026.

## V4 (April 24, 2026) — the most recent major release

- 1.6 trillion total parameters / 49B active (MoE) for V4-Pro.
- 284 billion parameters for V4-Flash.
- 1M-token context window.
- Both released open-weights under MIT on Hugging Face.
- API pricing: $0.14/$0.28 per M input/output tokens (Flash); $0.145/$3.48 (Pro).
- TechCrunch headline: "closes the gap with frontier models."
- Tom's Hardware reported V4 was trained partly on Huawei chips amid escalating US accusations of IP theft.
- DeepSeek senior researcher Chen Deli posted on X: "484 days later, we humbly share our labour of love. As always, we stay true to long-termism and open source for all." Liang Wenfeng did not appear publicly for the launch.

## R2 status — undelivered

- R2 was originally planned for early May 2025.
- Instead, R1 was updated to R1-0528 on May 28, 2025.
- As of July 2025, R2 was not released; Liang Wenfeng was reportedly not satisfied with its performance.
- As of May 2026, R2 is still not in the official model list. This is one of the few publicly visible signs of internal disagreement about ship/no-ship calls under Liang.

## Strategic license observation

- DeepSeek shifted from "source-available" (custom license) to **MIT** starting with V3 (Dec 2024). The MIT-licensed R1 (Jan 2025) is the canonical artifact — a Chinese frontier lab releasing a frontier reasoning model under one of the most permissive open-source licenses in existence.
- This is widely cited as the moment the open-weights vs closed-frontier debate hit institutional inflection. It is the specific event behind Liang's "open-source is cultural" stance becoming load-bearing.
