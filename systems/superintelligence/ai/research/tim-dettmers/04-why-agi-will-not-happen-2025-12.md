# Tim Dettmers — "Why AGI Will Not Happen" (2025-12-10)

Sources: blog post at `timdettmers.com/2025/12/10/why-agi-will-not-happen/`; coverage in The Register (2025-12-11), TechStory, daily.dev, and a Techmeme summary.

This is the most-quoted Dettmers essay of 2025–2026. It is the foundation for any persona claim about his stance on AGI, scaling, or the physical limits of compute.

## Core thesis

> "The thinking around AGI and superintelligence is not just optimistic, but fundamentally flawed."

The essay grounds the AGI critique in **physics, not philosophy**:

> "Computation is physical."

Memory movement scales quadratically with distance, larger caches are inherently slower, and the transformer architecture already sits near the floor of what silicon physics will tolerate.

## Scaling runway

> "We have maybe one, maybe two more years of scaling left [before] further improvements become physically infeasible."

He locates the prior peak of GPU performance-per-cost around 2018:

> "GPUs maxed out in performance per cost around 2018 — after that, we added one off features that exhaust quickly."

Subsequent gains came from precision drops (16-bit → BF16 → FP8 → FP4), HBM, Tensor Cores — features that are now individually exhausted.

## Rack-level last frontier

> "The only way to gain an advantage is by having slightly better rack-level hardware optimizations, but that will also run out quickly — maybe 2026, maybe 2027."

This pins the practical hardware-ceiling date that Dettmers is willing to commit to in public.

## The AGI definition

He defines AGI specifically:

> "intelligence that can do all things humans can do, including economically meaningful physical tasks."

Robotics-grade physical work is the gating constraint, and it is "unsolved, resource-prohibitive."

## Silicon Valley narrative critique

> Predictions of AGI persist "not because they are well founded but because they serve as a compelling narrative."

He frames U.S. labs as prioritising the AGI race over practical economic diffusion — what he describes as a "short-sighted perspective" — and contrasts that with the Chinese ecosystem emphasis on integration and application.

## Anchored claims for the persona file

The essay produces several stances clean enough to use as `public_stances` evidence:

1. **AGI is not coming on the current trajectory.** Evidence URL: the blog post.
2. **Hardware-ceiling year ~2026–2027.** Same source.
3. **Scaling has ~1–2 years left.** Same source.
4. **Quantization gains are exhausted.** Reinforces the November 2024 Interconnects framing.

The Register coverage at https://www.theregister.com/2025/12/11/ai_superintelligence_fantasy is the cleanest third-party citation if a non-self URL is needed.

## Sources

- https://timdettmers.com/2025/12/10/why-agi-will-not-happen/
- https://www.theregister.com/2025/12/11/ai_superintelligence_fantasy
- https://techstory.in/ai-superintelligence-is-a-fantasy-says-leading-ai2-researcher/
- https://www.techmeme.com/251211/p10
