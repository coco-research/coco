# Nathan Lambert — canonical works research

## Interconnects newsletter (interconnects.ai)

The primary canonical artifact. Active since 2022 (post-ChatGPT). 300+ posts as of 2026. Publishes 1–3x/week. Topic mix: RLHF, post-training, reasoning models, Chinese open-source labs, frontier model reviews, RL.

- "DeepSeek R1's recipe to replicate o1 and the future of reasoning LMs" (January 21, 2025) — defining post on R1's training pipeline and the case that RL at scale, not search, drives reasoning. Key claim: "The winds of o1 replication have been blowing strongly away from any sort explicit search (especially at inference time)."
- "The state of post-training in 2025" — taxonomy of post-training into (1) instruction finetuning, (2) preference finetuning, (3) reinforcement finetuning. Documents post-training cost trajectory: LLaMA <<$1M → Llama 2 ~$10–20M → Llama 3.1 >$50M.
- "Towards American Truly Open Models: The ATOM Project" (August 4, 2025) — calls for at least one US lab with 10,000+ leading-edge GPUs dedicated to truly open models within 6–12 months.
- "Olmo 3: America's truly open reasoning models" (November 20, 2025) — release post for Olmo 3 family. Describes 32B base as "our most impactful artifact" and frames Olmo 3 as "one small step towards" ATOM goals.
- "2025 Interconnects year in review" — published December 2025. Notable claim: "slow, consistent progress over the next few years," not dramatic acceleration. Tracks 26 posts on Chinese models in 2025.

## Models / leaderboards / benchmarks

- **Tülu series** — Tulu 2 (2023), Tulu 3 (Nov 2024, arXiv:2411.15124), published at COLM 2025. Lambert is first author on Tulu 3. Introduced **RLVR (Reinforcement Learning with Verifiable Rewards)** as a novel training method.
- **Olmo series** — OLMoE (September 2024, 1.3B active / 6.9B total, MoE), Olmo 2 (2024), **Olmo 3** (November 20, 2025): 7B and 32B variants including Base, Instruct, Think (reasoning), and RL Zero. Includes OlmoTrace tool for tracing outputs to training data. ArXiv:2512.13961.
- **Olmo 3.1** — extends RL training for stronger reasoning benchmarks (post-Olmo-3 update).
- **RewardBench** — first benchmark and leaderboard for reward models in RLHF, arXiv:2403.13787, March 2024. Lambert first author. Published at NAACL 2025 Findings.
- **RewardBench 2** — arXiv:2506.01937, June 2025. New multi-skill reward modeling benchmark; models score ~20 points lower on RB2 than RB1.
- **Open LLM Leaderboard** — community reference for open model evaluation; built while at HuggingFace.
- **Zephyr-Beta** — open fine-tuned model from his HuggingFace era.

## RLHF Book (rlhfbook.com)

- Open online textbook. First draft online version completed April 2025 (X post status 1912582035186602008).
- Manning preorder available November 2025.
- January 2026: major chapter reorganization, code examples library added.
- February 2026: v2 content — direct alignment chapter, RL cheatsheet, appendices, search bar, Kindle support.
- April 2026: final editorial polish for print.
- Coverage: instruction tuning, reward modeling, rejection sampling, RL, on-policy distillation, direct alignment algorithms (DPO and variants), synthetic data, tool-use, character training, evaluation.
- Coming to print via Simon & Schuster / Manning. ISBN 9781633434301.
- arXiv:2504.12501 — "Reinforcement Learning from Human Feedback" (book draft).

## Sources

- https://www.interconnects.ai/p/deepseek-r1-recipe-for-o1
- https://www.interconnects.ai/p/the-state-of-post-training-2025
- https://www.interconnects.ai/p/atom-project
- https://www.interconnects.ai/p/olmo-3-americas-truly-open-reasoning
- https://www.interconnects.ai/p/2025-interconnects-year-in-review
- https://arxiv.org/abs/2411.15124
- https://arxiv.org/abs/2512.13961
- https://arxiv.org/abs/2403.13787
- https://arxiv.org/abs/2506.01937
- https://arxiv.org/abs/2504.12501
- https://rlhfbook.com/
- https://github.com/natolambert/rlhf-book
- https://www.manning.com/books/the-rlhf-book
