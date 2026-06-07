# vLLM in the Inference Ecosystem (2025–2026)

## Production install base

From the a16z and Inferact materials:
- **400,000+ concurrent GPUs** running vLLM globally at any given moment.
- **2,000+ contributors**, **50+ core developers**.
- **>200 supported model architectures**, including Llama, Qwen, Gemma, Mixtral, DeepSeek-V3, GPT-OSS-120B.

## Production users (named)

Meta, Google, Amazon (AWS Bedrock), Character.ai, Roblox, LinkedIn, Spotify, Mistral AI, Cohere, IBM, Anthropic (vLLM provides an Anthropic Messages API endpoint at /api/vllm/entrypoints/anthropic), Apple (referenced indirectly via the iPhone-apps comment).

## Hardware support

NVIDIA GPUs (primary), AMD GPUs (ROCm), Google TPUs, AWS Trainium, Intel Gaudi, Apple Silicon, x86/ARM/PowerPC CPUs. Quantization: FP8, INT4, INT8, GPTQ, AWQ, GGUF.

## Project governance

- Apache License 2.0.
- Donated to the Linux Foundation in July 2024.
- Became a PyTorch Foundation hosted project in May 2025.
- Latest version: v0.21.0 (May 15, 2026). 94 total releases.

## Competitive position (as of May 2026)

| Engine | Lane | Position vs vLLM |
|---|---|---|
| **SGLang** | Open-source, Berkeley | Closest competitor. RadixAttention tree-structured prefix cache. Commercialized as RadixArk (~$400M val). Both projects come from Ion Stoica's lab — sibling rivalry, not enemy. |
| **TensorRT-LLM** | NVIDIA-only, closed-ish | Sharper low-level NVIDIA kernels; vLLM wins on portability and ease. TensorRT-LLM ~30–50% throughput edge in high-concurrency on H100, but lock-in. |
| **TGI** (Hugging Face) | Open-source | Maintenance mode. HF now recommends vLLM or SGLang. |
| **llama.cpp / Ollama** | Edge / local | Different lane. vLLM is server-side at scale. |
| **Anyscale / Together / Fireworks** | Hosted inference | Use vLLM under the hood. Inferact's "universal layer" framing is meant to complement, not replace. |

## Benchmarks (industry reports, late 2025 – early 2026)

- vLLM consistently the **fastest TTFT** (time-to-first-token) at all concurrency levels.
- SGLang has the most stable per-token latency (4–21 ms).
- TensorRT-LLM wins peak throughput on NVIDIA-only stacks.
- vLLM wins on **portability, model coverage, and operational simplicity** — "good default."

Sources: MarkTechPost https://www.marktechpost.com/2025/11/07/comparing-the-top-6-inference-runtimes-for-llm-serving-in-2025/ ; Yotta Labs https://www.yottalabs.ai/post/best-llm-inference-engines-in-2026-vllm-tensorrt-llm-tgi-and-sglang-compared

## Why Woosuk's position is unique

1. **He owns the dominant runtime in production.** When Meta, Anthropic, OpenAI integrate inference, vLLM is in the loop somewhere.
2. **He bridges academia and industry.** Berkeley PhD, but also vLLM is what actually runs Anthropic and Google's open-weight inference paths.
3. **He's an open-source advocate with a $150M war chest.** Unusual mix.
4. **He's understated.** Less visible than Tri Dao or Horace He on X, but more downstream impact via the engine itself.

## Blind spots / tensions

- Closed-frontier-lab inference (OpenAI's internal serving, Anthropic's internal serving, Google's TPU stack) does NOT use vLLM. The "universal" claim has limits.
- vLLM's complexity ceiling: 200+ model architectures, 50+ core devs, 2k issues, 3k PRs — operational debt is real even after the V1 rewrite.
- Bench leaderboards now favor specialized engines for specific workloads (SGLang for structured outputs, TensorRT-LLM for NVIDIA-locked latency). The "default good" lane is contested.
- Woosuk's systems frame can underweight algorithmic gains (sparse attention, MoE routing, speculative decoding policy) coming out of model-side research.
