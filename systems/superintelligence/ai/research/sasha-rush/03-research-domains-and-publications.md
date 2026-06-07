# Sasha Rush — Research Domains and Key Publications

Rush is unusual in modern NLP for having sustained three durable research tracks in parallel — structured prediction, efficient architectures (including SSMs), and open-source LLM ecosystem work — without abandoning any of them when the field pivoted to scaling. The current Cursor chapter has added a fourth: post-training of coding agents via RL.

## Track 1 — Structured Prediction in NLP

Rush's pre-Transformer identity. He wrote his PhD at MIT (advised by Michael Collins) on structured prediction. The interest survived the deep-learning transition because he reframed it: differentiable structured prediction in PyTorch via pytorch-struct.

Representative work:
- "A Neural Attention Model for Abstractive Sentence Summarization" (EMNLP 2015) — Rush, Chopra, Weston. The first widely-cited neural summarization paper; predates the Transformer by two years.
- "OpenNMT" (ACL 2017 demo) — production NMT with structured decoding.
- pytorch-struct (2020) — CRFs, dependency parsers, HMMs as PyTorch primitives.

His durable stance: **structure is a feature, not a bug**. Pure-sequence transformer baselines can be beaten by structurally-aware models for tasks where the structure is real.

## Track 2 — Efficient Architectures and State Space Models

Rush has been one of the loudest academic voices arguing that **attention is not the only game in town**. He runs a public bet at IsAttentionAllYouNeed.com on whether non-attention architectures will outperform transformers by a deadline.

Representative work:
- "The Annotated S4" (2022) — see canonical-works file.
- "Pretraining Without Attention" (BiGS, 2022) — Wang, Karamcheti, Rush. SSM-based pretraining at scale; argued SSMs could be competitive with attention for masked LM pretraining.
- "The Mamba in the Llama: Distilling and Accelerating Hybrid Models" (NeurIPS 2024) — Wang, Paliotta, May, Rush, Dao. Distills large Transformers (Llama3-8B-Instruct) into hybrid Mamba-attention models that keep ~25% attention and get competitive AlpacaEval / MT-Bench. https://arxiv.org/abs/2408.15237
- "The Illusion of State in State-Space Models" (ICLR 2024) — Merrill, Petty, Sabharwal, Rush. Argues SSMs as commonly deployed cannot in fact maintain richer state than transformers — a sober theory result from the SSM-enthusiast camp. https://arxiv.org/pdf/2404.08819
- "Simple and Effective Masked Diffusion Language Models" (NeurIPS 2024).

His durable stance: **SSMs are a real alternative substrate, not a fad. But theory matters — measure what each architecture can actually express before declaring victory.**

## Track 3 — Open-Source LLM Ecosystem

Rush's Hugging Face co-authorship and his role in shaping the open-publication norms of LLM research.

Representative work:
- Transformers library co-authorship (EMNLP 2020).
- "Zephyr: Direct Distillation of LM Alignment" (COLM 2024).
- "Contextual Document Embeddings" (ICLR 2025).
- Co-founding **COLM** in 2024 to give language-modeling work a dedicated venue with norms set by people who actually do it.

His durable stance: **open source is the engine of progress in LM research, and venue/community design is itself a research contribution.**

## Track 4 — Post-Training, Reasoning, Coding Agents (2025–present)

The Cursor chapter.

Representative work:
- "Speculations on Test-Time Scaling" (Rush & Daniel Ritter, 2024–2025) — public tutorial PDF on o1-style models, RL for reasoning, and test-time compute. https://srush.github.io/awesome-o1/o1-tutorial.pdf
- **Cursor Composer 1** (October 2025) — Cursor's first proprietary frontier coding model. MoE, trained with RL on in-IDE coding sessions. Rush's quoted stance: "Our primary focus is on RL post-training. We think that is the best way to get the model to be a strong interactive agent." https://simonwillison.net/2025/Oct/29/cursor-composer/
- **Cursor Composer 2 technical report** (March 27, 2026) — https://cursor.com/blog/composer-2-technical-report — two-phase training (continued pretraining on Kimi K2.5 base, then large-scale RL), custom MXFP8 MoE kernels on Blackwell GPUs, Anyrun sandboxed-environment platform, fully async RL pipeline. CursorBench 61.3 (37% better than 1.5), SWE-bench Multilingual 73.7. Rush authored the report.
- Public stance from April 2026 Information Bottleneck podcast: agents should be evaluated on whether they can take a *terse, ambiguous, long-horizon* problem and solve it, not just a clean prompt — and ~35% of Cursor's internal PRs are now produced by their cloud agent.

His durable stance: **coding is the cleanest RL substrate available** because correctness is checkable, and post-training (not pretraining) is where the gains now sit for agent quality. He pushes back against binary-only rewards: "arbitrary rewards" offer richer signal for coding.

## Sources

- http://rush-nlp.com/rawpapers/ (full publication list)
- https://arxiv.org/abs/2408.15237 (Mamba in the Llama)
- https://arxiv.org/pdf/2404.08819 (Illusion of State in SSMs)
- https://srush.github.io/awesome-o1/o1-tutorial.pdf (Test-Time Scaling)
- https://cursor.com/blog/composer-2-technical-report
- https://simonwillison.net/2025/Oct/29/cursor-composer/
- https://www.the-information-bottleneck.com/the-future-of-coding-agents-with-sasha-rush-cursorcornell/
