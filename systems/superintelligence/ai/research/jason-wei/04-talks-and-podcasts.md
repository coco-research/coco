# Jason Wei — Talks, Podcasts, Lectures

## Stanford CS25 — "Scaling LLMs and emergent abilities"

- **Venue:** Stanford CS25 lecture series, "Transformers United"
- **Year:** 2023 (referenced repeatedly in subsequent talks)
- **YouTube:** https://www.youtube.com/watch?v=fnE_2sJqp0o (Stanford CS25 official channel — recording of Wei's lecture)
- **Takeaway:** The slide deck where Wei publicly walked through Chain-of-Thought, emergent abilities, and instruction tuning as one connected research program. The "three pillars" framing of his early career originates here.

## MIT — Guest lecture on RL and reasoning

- **Venue:** MIT EECS / CSAIL guest lecture circuit
- **Year:** 2024
- **Takeaway:** Public lecture defending the emergence framing against the "mirage" critique. Argued that the choice of metric (exact-match vs. token-level loss) determines whether you see a phase transition, and exact-match is the metric users actually experience.

## Latent Space podcast (Swyx + Alessio Fanelli)

- **Episode:** "Jason Wei on the next decade of scaling"
- **URL:** https://www.latent.space/p/jason-wei (canonical Latent Space episode page)
- **Year:** 2024 / 2025 (Wei has appeared multiple times)
- **Takeaway:** Most-cited interview for Wei's public statements on RL, verifiability, and the OpenAI → Anthropic move. He explicitly says "verification is the new scaling axis" and frames CoT as "giving the model space to think."

## NeurIPS 2024 / 2025 panel appearances

- Panelist at NeurIPS on emergent abilities (2024) and on inference-time scaling (2025).
- 2025 panel quote (paraphrased from a recap thread): "The next 10x in capability comes from inference compute, not pretraining."

## YC AI Startup School (June 2025)

Wei appeared alongside Karpathy at the YC AI Startup School in June 2025 — the same event where Karpathy delivered the "Software is changing (again)" / Software 3.0 keynote. Wei's slot focused on post-training and verifiable rewards.

- **Reference:** https://www.ycombinator.com/library (YC library, AI Startup School video index)

## Recurring talking points across talks

1. **Chain-of-thought works because the model needs room to compute intermediate states.** Not because the words are special. The autoregressive substrate plus extra tokens equals more compute.
2. **Emergence is real and load-bearing for capability planning.** Don't extrapolate smooth log-linear curves through phase-transition points.
3. **Verifiability is the new scaling axis.** Math, code, theorem proving, structured games — these get crushed first because verification is cheap. Long-form writing, taste, judgment — these stay hard.
4. **The right path to AGI is "give the model more compute at inference time."** Test-time compute scaling is the second scaling law.
5. **Research taste matters more than research effort.**

## Voice in talks

In talks Wei is conversational, fast, and uses concrete benchmarks more than analogies. He references specific arithmetic tasks (GSM8K, MATH), specific LM checkpoints (PaLM-540B, FLAN-T5-XXL), and specific emergence thresholds (often "~10^22 FLOPs"). He resists rhetorical flourish — closer to a benchmark-numbers researcher than a metaphor-driven communicator. This is a meaningful contrast with Karpathy, who reaches for physics analogies; Wei reaches for citation numbers.

## Sources

- Stanford CS25: https://web.stanford.edu/class/cs25/
- Latent Space: https://www.latent.space/
- YC AI Startup School index: https://www.ycombinator.com/library
- NeurIPS proceedings 2024/2025: https://neurips.cc/
