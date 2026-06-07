# Thinking Machines Lab products — Tinker (Oct 2025) and Interaction Models (May 2026)

## Tinker (announced October 1, 2025)

Sources:
- https://thinkingmachines.ai/news/announcing-tinker/
- https://thinkingmachines.ai/tinker/
- https://venturebeat.com/ai/thinking-machines-first-official-product-is-here-meet-tinker-an-api-for
- https://www.deeplearning.ai/the-batch/thinking-machines-new-tinker-api-makes-it-easier-to-fine-tune-models-on-many-gpus

### What it is

Tinker is Thinking Machines Lab's first product. It is a managed fine-tuning API that gives researchers low-level primitives — `forward_backward` and `sample` — across a distributed GPU backend. Most fine-tuning runs use LoRA so that many concurrent tenants can share a single compute pool, which is how TML keeps it economical to operate.

Key design choices, in TML's own words: "abstract the distribution without hiding the knobs." The API exposes the post-training primitives directly instead of wrapping them in a high-level "train this dataset" abstraction. This matches Schulman's long-stated preference, going back to his Berkeley CS294 lectures, for teaching the actual primitives rather than packaging them.

### Models supported

Open-weights only at launch: Llama 70B family, Qwen 235B family, plus smaller open-weights models. Tinker is explicitly not a closed-frontier-model API.

### Adoption signals

Early adopters cited in the launch post: research groups at Princeton, Stanford, Berkeley, and Redwood Research. Use cases: theorem proving, chemistry reasoning, reinforcement learning research, and AI control experiments. Note the alignment-adjacent set (Redwood, AI control) — TML positioned Tinker as RLHF/alignment-research infrastructure as much as product fine-tuning.

### Status updates

- October 1, 2025: launch in private beta with waitlist.
- December 12, 2025: Tinker moved to general availability.

### Schulman's authorial role

The announcement post does not name individual authors. However, Tinker's design — primitives over abstractions, LoRA-first, post-training-research mandate — is fingerprint-identical to Schulman's stated preferences in his Dwarkesh interview and his 2023 RLHF talk. Treating Tinker as a Schulman-driven artifact is the safe reading; TML's own framing of the team as "the people who built RLHF" supports this.

## Interaction Models — TML-Interaction-Small (announced May 11, 2026)

Sources:
- https://thinkingmachines.ai/blog/interaction-models/
- https://techcrunch.com/2026/05/11/thinking-machines-wants-to-build-an-ai-that-actually-listens-while-it-talks/
- https://www.unite.ai/thinking-machines-lab-ships-first-model-with-200ms-real-time-interaction/
- https://siliconangle.com/2026/05/11/thinking-machines-drops-new-highly-responsive-model-designed-humanlike-interactions-real-time/

### What it is

A research preview of "interaction models" — a model class that handles audio, video, and text interaction natively rather than via external scaffolding (push-to-talk, turn-taking, separate STT/TTS pipelines). TML-Interaction-Small is the first such model: 276B parameter Mixture-of-Experts, 12B active parameters at inference, processing inputs in 200ms micro-turn chunks. A parallel asynchronous "background" reasoning model shares context and handles deeper thought without blocking the real-time loop.

### Headline claim

Round-trip response in roughly 0.40 seconds — close to natural human conversational latency and significantly faster than OpenAI's and Google's published comparable models as of May 2026.

### Motivation framing (direct quotes from the blog post)

- "Interactivity should scale alongside intelligence; the way we work with AI should not be treated as an afterthought."
- "Good results benefit from a collaborative process where the human stays in the loop, clarifying and giving feedback along the way."

### Authorship

The post is bylined "Thinking Machines" without individual contributors listed. Cannot confirm or deny Schulman is on the author list from the public artifact alone. Treating this as a TML-wide research output where Schulman is the Chief Scientist of record is appropriate.

### Significance for the persona

- The "human in the loop, clarifying as we go" framing is consistent with Schulman's Dwarkesh stance that the helpful-assistant frame should outlast the autonomous-agent frame near-term.
- The architectural choice — a fast interaction loop plus an async deeper-reasoning model — is conceptually a multi-policy RL setup. It reads as Schulman-influenced architecture even if he is not the principal author of the modeling work.
- This is a 2026 signal that satisfies the post-2025-05-27 recent-signal requirement directly.
