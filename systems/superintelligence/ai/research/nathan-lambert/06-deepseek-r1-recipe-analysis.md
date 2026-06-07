# Nathan Lambert — DeepSeek R1 recipe analysis (close-read)

Source: https://www.interconnects.ai/p/deepseek-r1-recipe-for-o1 — January 21, 2025.

The single most-read Interconnects post of 2025, the canonical Lambert artifact on reasoning models, and the piece that defined how the open community would read R1.

## Core claim

R1 demonstrates that reasoning capabilities emerge primarily through **reinforcement learning at scale**, not through any explicit inference-time search mechanism. This contradicts a widespread early reading of o1 as "model + MCTS-style search."

> "The winds of o1 replication have been blowing strongly away from any sort explicit search (especially at inference time)."

## The four-stage R1 recipe (Lambert's reconstruction)

1. SFT cold start on a small high-quality reasoning corpus.
2. Large-scale RL with verifiable rewards on math + code.
3. Rejection sampling + supervised fine-tuning on the best RL traces.
4. A second round of RL covering broader, less-verifiable domains.

## RLVR — three reward components in R1

- **Accuracy bonus** — correct answer on a checkable problem. "The first reward here drives the majority of the learning."
- **Format reward** — proper use of reasoning-chain tags.
- **Language consistency penalty** — discourages mid-trace code-switching.

## Strategic framings in the same post

- DeepSeek's pricing undercuts OpenAI by roughly 10x — signals an imminent price war.
- "This again confirms that new technical recipes normally aren't moats — the motivation of a proof of concept or leaks normally get the knowledge out."
- "The first time since Stable Diffusion's release that the most relevant and discussed AI model is released with a very friendly license."

## Why this post matters for the persona

It is the moment Lambert's frame ("open recipes will catch up; RLVR is the engine; reward models are the bottleneck") became the consensus open-source narrative for 2025. Every subsequent Olmo / Tulu release and ATOM Project argument traces back to this read.

## Sources

- https://www.interconnects.ai/p/deepseek-r1-recipe-for-o1
- https://arxiv.org/abs/2411.15124 (Tulu 3 — RLVR origin)
