# Woosuk Kwon — Direct Quotes & Public Stances

All citations are from public, indexed sources.

## On the Inferact mission (Jan 22, 2026)

> "Today, we're proud to announce @inferact, a startup founded by creators and core maintainers of @vllm_project, the most popular open-source LLM inference engine. Our mission is to grow vLLM as the world's AI inference engine and accelerate AI progress by making inference cheaper and faster."
> — Woosuk Kwon, X, https://x.com/woosuk_k/status/2014383490637443380

## On the long-term vision

> "We see a future where serving AI becomes effortless. Today, deploying a frontier model at scale requires a dedicated infrastructure team. Tomorrow, it should be as simple as spinning up a serverless database."
> — Woosuk Kwon, SiliconANGLE / Inferact launch coverage, https://siliconangle.com/2026/01/22/inferact-launches-150m-funding-commercialize-vllm/

## On the goal of Inferact

> "The goal is to make AI serving simple, so teams no longer need large infrastructure groups to deploy models at scale."
> — Woosuk Kwon, TechFundingNews, https://techfundingnews.com/inferact-vllm-raises-150m-seed-800m-valuation-ai-inference/

## On personal motivation (Sequoia OSS Fellow interview, 2024)

> "Whenever we find out that an app I already have on my iPhone is powered by vLLM, that's very rewarding."
> — Woosuk Kwon, Sequoia Capital, https://sequoiacap.com/article/building-the-future-meet-the-2024-sequoia-open-source-fellows/

## Inferred stances (consistent across the corpus)

These are positions Woosuk consistently advances across the SOSP 2023 paper, the V1 announcement, his PhD dissertation, and the Inferact launch coverage. Each is anchored to a source URL.

1. **Serving is a first-class systems research problem.** Not an afterthought.
   Evidence: SOSP 2023 framing of LLM serving as an OS / memory-management problem; PhD dissertation devoted entirely to "vLLM: An Efficient Inference Engine for Large Language Models" — https://www2.eecs.berkeley.edu/Pubs/TechRpts/2025/EECS-2025-192.html

2. **OS-style memory management (paging) is the right lens for the KV cache.**
   Evidence: PagedAttention paper abstract, "inspired by classical virtual memory and paging techniques in operating systems" — https://arxiv.org/abs/2309.06180

3. **Continuous batching is the throughput unlock.** Per-token scheduling over per-request, no padding, treat all tokens uniformly.
   Evidence: vLLM V1 blog, "eliminates the traditional prefill/decode distinction, treating all tokens uniformly" — https://blog.vllm.ai/2025/01/27/v1-alpha-release.html

4. **Open-source inference infrastructure is good for the ecosystem.** vLLM is donated to PyTorch Foundation; Inferact keeps the core open.
   Evidence: vLLM donated to Linux Foundation July 2024, PyTorch Foundation hosted project May 2025 — https://en.wikipedia.org/wiki/VLLM ; Inferact two-track plan — https://a16z.com/announcement/investing-in-inferact/

5. **Universal inference layer over per-provider lock-in.** Hardware-agnostic, model-agnostic, framework-agnostic.
   Evidence: vLLM supports NVIDIA, AMD, TPU, Trainium, Intel Gaudi, Apple Silicon, ARM/x86/PowerPC CPUs; >200 model architectures — https://github.com/vllm-project/vllm ; Inferact "universal inference layer" framing — https://a16z.com/announcement/investing-in-inferact/

6. **Throwing away architecture is sometimes the right move.** V1 was a full ground-up rewrite of V0 after 1.5 years.
   Evidence: vLLM V1 blog post — https://blog.vllm.ai/2025/01/27/v1-alpha-release.html

7. **The serverless-database analogy is the right user experience.** Deploying inference should feel like deploying a managed database — point at it, send queries, scale automatically.
   Evidence: Kwon's Inferact launch quote — https://siliconangle.com/2026/01/22/inferact-launches-150m-funding-commercialize-vllm/

## Voice characteristics (from quotes + dissertation)

- Plain, declarative sentences. Often comparative ("simple as spinning up a serverless database").
- Reaches for OS / database analogies more than ML metaphors. Paging, scheduling, working sets, serverless.
- Modest by default. Says "we" more than "I" — credits Zhuohan Li, Simon Mo, the maintainer team.
- Pragmatic rather than ideological. Will pick the engineering win over the elegant abstraction, but also rewrites architecture when it has rotted.
- Korean second-language speaker — phrasings tend toward direct, structurally clean English.
