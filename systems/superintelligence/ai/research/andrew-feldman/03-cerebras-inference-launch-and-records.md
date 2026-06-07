# Cerebras Inference — August 2024 Launch and Subsequent Records

## Sources
- https://www.cerebras.ai/press-release/cerebras-launches-the-worlds-fastest-ai-inference
- https://www.cerebras.ai/press-release/cerebras-inference-llama-405b
- https://www.cerebras.ai/blog/llama-405b-inference
- https://www.cerebras.ai/blog/mistral-le-chat
- https://simonwillison.net/2025/Feb/10/cerebras-mistral/
- https://www.cerebras.ai/press-release/llama4PR
- https://www.cerebras.ai/press-release/maverick
- https://www.businesswire.com/news/home/20250528123694/en/Cerebras-Beats-NVIDIA-Blackwell-in-Llama-4-Maverick-Inference
- https://www.hpcwire.com/off-the-wire/cerebras-leads-llm-inference-race-with-fastest-llama-4-maverick-performance/
- https://news.ycombinator.com/item?id=44141728
- https://www.cerebras.ai/blog/2026Insights

## The August 27, 2024 launch

Cerebras Inference launched on August 27, 2024 as a hosted inference service running customer Llama-class models on CS-3 systems. The launch claims:

- 1,800 tokens/sec on Llama 3.1 8B.
- 450 tokens/sec on Llama 3.1 70B.
- 20× faster than NVIDIA-GPU-based inference solutions in hyperscale clouds.
- Pricing starting at $0.10 per million tokens — explicitly framed as undercutting incumbent providers.

The press release notably **did not include a quote from Andrew Feldman** — quotes came from Artificial Analysis (Micah Hill-Smith), DeepLearning.AI (Andrew Ng), GlaxoSmithKline, LiveKit, Perplexity, and Meter. This is a tell: Cerebras chose to front the launch with customer voices and a third-party benchmark, not its CEO. Feldman has historically saved his strongest first-person commentary for the strategy / IPO / industry-framing register, leaving the product-marketing register to the team.

## The November 18, 2024 Llama 3.1 405B record

In November 2024 Cerebras posted a new record for Meta's largest open model: **969 output tokens/sec on Llama 3.1 405B** with a 240ms time-to-first-token. The framing in the announcement was that wafer-scale inference now extended to frontier-scale dense models, not just the 8B/70B sweet spot.

## The February 10, 2025 Mistral Le Chat integration

Mistral integrated Cerebras Inference into Le Chat's "Flash Answers" feature, achieving **over 1,100 tokens/sec on Mistral Large 2 (123B)**. The framing was explicit: "10× faster than ChatGPT 4o, Claude Sonnet 3.5, and DeepSeek R1." This was Cerebras's first major consumer-facing chat deployment — Le Chat is a general-public product, not a developer API. Coding prompts that take competing assistants up to 50 seconds were claimed to complete instantly.

The technical credit is shared: speculative-decoding techniques were developed in collaboration with Mistral researchers, layered on top of WSE-3's SRAM-based inference.

## The April 2025 Meta Llama API partnership

Meta selected Cerebras as the inference partner for the Llama API, achieving **2,600 tokens/sec on Llama 4 Scout**. Meta's framing was that the Llama API would run 18× faster than the OpenAI API for the equivalent model class. This partnership was strategically consequential: it made Cerebras the official inference path for Meta's first-party model service, not just a third-party provider.

## The May 28, 2025 Llama 4 Maverick record vs. NVIDIA Blackwell

The Maverick benchmark is the pivotal head-to-head moment. On May 27, 2025 NVIDIA announced that 8 Blackwell GPUs in a DGX B200 had crossed 1,000 TPS/user on Llama 4 Maverick (400B parameters). One day later, on May 28, 2025, Artificial Analysis published a benchmark showing Cerebras at **2,522 TPS/user on the same model** — more than double NVIDIA's flagship result. The comparison ranked vendors as:

| Vendor | Llama 4 Maverick TPS/user |
|---|---|
| Cerebras | 2,522 |
| NVIDIA Blackwell DGX B200 (8 GPU) | 1,038 |
| SambaNova | 794 |
| Groq | 549 |
| Amazon | 290 |
| Google | 125 |
| Microsoft Azure | 54 |

Cerebras's positioning at the time emphasized that the Cerebras endpoint was generally available, while the NVIDIA Blackwell result was a benchmark on hardware not yet shipping at scale.

## The 2026 Insights blog (January 2026)

Cerebras's January 2026 blog post "Fast Inference Finds Its Groove" formalized the thesis Feldman had been pitching publicly: inference speed, not parameter count, is now the primary product constraint. Quoting the post:

> "inference speed is not a bragging point. It is the real constraint that determines what AI systems can do."

The post also reframes the architectural argument:

> "GPU systems were never designed for this phase of AI."

And introduces what Cerebras calls "The Cerebras Scaling Law":

> "models that can think more in the same amount of time produce better results."

This is the company-position framing of the chain-of-thought / reasoning-token inflection — if reasoning consumes orders of magnitude more inference tokens than answering, then inference throughput per dollar becomes the binding constraint on what's economically deployable. Feldman's verbal version of this on No Priors and CNBC: "Inference time computes — improving the quality of the answer based on additional use of tokens through reasoning is an extremely powerful tool."

## Why this matters for the persona

The cadence of records from August 2024 through May 2025 is the empirical basis for Feldman's "we are winning inference" stance during the 2026 IPO roadshow. He is not claiming Cerebras will catch NVIDIA on training scale or on the CUDA developer ecosystem — he is claiming Cerebras has already won the inference-throughput regime, and that regime is the regime that matters as the industry pivots from pre-training-led scaling to inference-led reasoning. Every public framing of his from late 2024 onward rests on this body of benchmark evidence.
