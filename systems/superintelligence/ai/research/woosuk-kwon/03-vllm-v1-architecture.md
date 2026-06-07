# vLLM V1 — Architecture Rewrite (Jan 2025)

## Announcement

- Blog: https://blog.vllm.ai/2025/01/27/v1-alpha-release.html (also at vllm.ai/blog/2025-01-27-v1-alpha-release)
- Red Hat Developer summary: https://developers.redhat.com/articles/2025/01/28/vllm-v1-a-major-upgrade-vllms-core-architecture
- Docs: https://docs.vllm.ai/en/stable/usage/v1_guide/

## Why V1

After ~1.5 years of vLLM V0 development, the team identified that features added independently were limiting vertical optimization and accumulating technical debt. Woosuk Kwon initiated V1 and personally implemented the scheduler and model runner. Co-driven by UC Berkeley, Neural Magic (now Red Hat), Anyscale, and Roblox.

## Key architectural changes

**1. Scheduler.** Eliminates the traditional prefill/decode distinction. Scheduling decisions are simple dictionaries mapping request IDs to token counts. Supports chunked prefills, prefix caching, and speculative decoding uniformly.

**2. Execution loop & API server.** Deep multiprocessing integration. An isolated `EngineCore` focuses exclusively on scheduling and model execution. CPU-intensive work (tokenization, multimodal preprocessing, de-tokenization) overlaps with the core loop.

**3. KV cache manager.** Optimized data structures for constant-time cache eviction. Minimized Python object overhead. Prefix-caching CPU overhead is near-zero even at 0% hit rate.

**4. Tensor parallelism.** Moved from co-locating the scheduler with Worker 0 to a clean symmetric architecture. Workers cache request state and transmit only incremental updates.

**5. Input preparation.** Implements a Persistent Batch technique — caches input tensors and applies only diffs each step, using NumPy operations for efficiency.

**6. Integrations.** torch.compile, piecewise CUDA graphs, FlashAttention 3, enhanced multimodal LLM support with offloaded preprocessing and encoder caching.

## Performance

Up to **1.7× higher throughput** than V0. Vision-language models like Qwen2-VL show even larger speedups.

## Migration

Set `VLLM_USE_V1=1`. No API changes. V1 became the default engine through 2025.

## What this tells us about Woosuk

- He is willing to throw away 1.5 years of code when the architecture is the wrong shape.
- He framed the rewrite around eliminating special cases (prefill vs decode) — uniformity > shortcuts.
- He emphasized **near-zero CPU overhead** and **zero-config defaults**. The systems-research instinct: the framework should be invisible.
- He treats the scheduler as the heart of the engine. The scheduler-first reorganization is the persona signal.

## Subsequent (2026)

- **Model Runner V2 (MRV2)**, March 2026 — further reimplementation of the model runner.
- **v0.18 / v0.19**, April 2026 — gRPC serving, GPU-accelerated speculative decoding, Gemma 4 day-one support.
- **v0.21.0**, May 15 2026 — most recent.
