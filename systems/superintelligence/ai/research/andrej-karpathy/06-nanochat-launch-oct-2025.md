# Karpathy — nanochat launch (October 2025)

Sources:
- https://www.cxodigitalpulse.com/andrej-karpathy-launches-nanochat-an-open-source-chatgpt-style-model-training-pipeline/
- https://analyticsindiamag.com/ai-news-updates/andrej-karpathy-releases-nanochat-a-minimal-chatgpt-clone/
- https://aidailypost.com/news/andrej-karpathy-releases-nanochat-open-source-chatgpt-clone

## What it is

Open-source framework that trains, fine-tunes, and serves a ChatGPT-style language model end-to-end. Builds on nanoGPT (pretraining only). Adds tokenizer training, SFT, optional RL via GRPO, and a ChatGPT-style web UI — all in ~8,000 lines of readable code.

## Karpathy's announcement (X)

> "You boot up a cloud GPU box, run a single script and in as little as 4 hours later you can talk to your own LLM in a ChatGPT-like web UI."

## Cost claims

| Budget | Time | Hardware | Output |
|---|---|---|---|
| ~$100 | 4 hours | 8×H100 GPU node | Basic ChatGPT clone |
| ~$1,000 | 42 hours | 8×H100 GPU node | Model solving elementary math + coding problems |

## Stack composition

- Tokenizer training in **Rust** (custom efficient BPE, "vibe-coded" by Karpathy)
- Transformer-based LLM pretraining on FineWeb
- Supervised fine-tuning
- Optional reinforcement learning via GRPO (DeepSeek's approach)
- ChatGPT-style web UI

## Eureka Labs / LLM101n integration

Nanochat is the **capstone project** for LLM101n at Eureka Labs. Course covers full LLM lifecycle: data prep → pretraining → SFT → RL.

## Why it matters

- **Educational artifact:** every stage of LLM creation visible in 8,000 readable lines.
- **Democratization:** $100 minimum gets a working ChatGPT-style model.
- **Signature move expression:** "build it from scratch in ~8,000 lines to prove you understand it."
