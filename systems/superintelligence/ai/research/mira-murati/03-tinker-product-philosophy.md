# Tinker — Thinking Machines Lab's First Product (Oct 1, 2025)

Sources: thinkingmachines.ai/news/announcing-tinker, thinkingmachines.ai/tinker, VentureBeat, MarkTechPost, InfoQ, DeepLearning.ai The Batch, LessWrong AI Control post.

## What Tinker is

A managed fine-tuning API for open-weight LLMs. Researchers write training loops; Tinker handles distributed GPU scheduling, failure recovery, and infrastructure orchestration.

## Four primitives — Tinker's core abstraction

```
forward_backward(...)   # run forward + backward, accumulate gradients
optim_step(...)         # apply optimizer step
sample(...)             # generate tokens (for eval, interaction, RL rollouts)
save_state(...)         # checkpoint
```

That's the entire API surface. Everything else is up to the researcher — the algorithm, the data, the eval, the reward function, the schedule. Tinker deliberately does not own those choices.

## Design philosophy (the meta-product statement)

> "We empower researchers and hackers to experiment with models by giving them control over the algorithms and data while we handle the complexity of distributed training."

Three explicit choices:

1. **LoRA-only** — Tinker shares one GPU pool across many concurrent training runs by training low-rank adapters. Justified publicly via the "LoRA Without Regret" Connectionism post (Schulman et al., Sept 29 2025) showing LoRA matches full-finetune performance on relevant workloads.
2. **Low-level primitives, not high-level recipes** — researchers can express SFT, DPO, RLHF, GRPO, on-policy distillation, multi-agent setups themselves. No opinionated wrappers.
3. **Open-source Tinker Cookbook** — a separate GitHub repo with ready-to-use reference implementations (3-stage RLHF, math-reasoning reward modeling, tool-use, prompt distillation). Production-quality examples, not a framework.

## Supported model catalog (30+ models)

- **Qwen** 3.5-4B → 3.5-397B-A17B (dense and MoE)
- **Meta Llama** 3.2-1B → 3.1-70B
- **DeepSeek** V3.1 and variants
- **Moonshot Kimi** K2-Thinking, K2.6
- **NVIDIA Nemotron** Nano-30B → Super-120B
- **OpenAI gpt-oss** 20B, 120B

Context lengths 32K–256K depending on model. Switching base model is a single string argument.

## Pricing model

Per-million-token, three tracks:
- **Prefill** (input processing)
- **Sample** (output generation)
- **Train** (fine-tuning ops)

Example: Qwen3.5-4B at $0.22/$0.67/$0.67. Qwen3.5-397B-A17B at $2.00/$5.00/$6.00. Storage $0.10/GB-month. NVIDIA model discount (50%) during launch.

## Strategic read

Tinker is **not** the typical "first product" for a frontier lab. Anthropic's first product was Claude; OpenAI's was GPT-3 API; xAI's was Grok. TML's first product is **a fine-tuning API for other labs' models**.

What this tells us about Murati's strategy:

- **Revenue while researching.** Tinker monetizes the multi-thousand-GPU compute footprint TML had to acquire to train its own model. Beta is free; usage pricing kicks in to amortize Nvidia/Google compute spend.
- **Researcher distribution.** Early users (Princeton, Stanford, Berkeley, Redwood Research) become an evangelist network for TML's later in-house models.
- **AI-control alignment narrative.** The LessWrong AI-control community wrote favorably about Tinker as "good news for AI control" because it democratizes the techniques (LoRA-based fine-tuning) that control researchers need to do their work — a deliberate audience signal from TML.
- **Customization as the productized form of "human-AI collaboration."** Tinker is the operational expression of the homepage thesis: AI that works for *your* unique needs requires giving you the tools to bend a foundation model to those needs.

## Researcher testimonials (from product page)

- Berkeley (Tyler Griggs): "Tinker lets researchers focus on datasets, algorithms, and environments without the complexities of compute and infrastructure."
- Stanford (Jason Liu): "The training infrastructure has been abstracted away, which makes focusing on our data and evals far easier."
- Princeton: "Tinker lets us focus on the research, rather than spending time on engineering overhead."
- Redwood Research (Eric Gan): "Tinker has been reliable for quickly iterating without worrying about hardware or infrastructure."

The chosen testimonials are notable: three academic labs and an AI-safety research org. Zero enterprise testimonials. That positioning is deliberate.
