# SmolLM3 and the Ultra-Scale Playbook — Hugging Face's 2025 open-weights canon

These are the two technical artifacts that prove the Wolf thesis: that the open-weights ecosystem can produce competitive frontier-adjacent models *and* publish the full recipe, not just the artifact.

## SmolLM3

- Release date: July 8, 2025
- Models: `HuggingFaceTB/SmolLM3-3B-Base` and `HuggingFaceTB/SmolLM3-3B`
- Lead authors: Elie Bakouch, Loubna Ben Allal, Anton Lozhkov + 30+ Hugging Face contributors (Thomas Wolf is listed in the SmolLM3 paper authorship and was the institutional sponsor)
- Parameters: 3B
- Training tokens: 11.2T
- Context: 128k (via YARN extrapolation beyond 64k training)
- Languages: 6 (English, French, Spanish, German, Italian, Portuguese)

### Architectural choices that matter for the Wolf thesis

1. **Grouped Query Attention (GQA)** — 4 groups; reduces KV cache without hurting quality (ablated on 100B tokens)
2. **NoPE (No Rotary Position Embeddings on every 4th layer)** — from the "RoPE to NoRoPE and Back Again" paper (Yang et al., 2025). Improves long-context without hurting short-context.
3. **Intra-document masking** — prevents cross-document attention bleed within a packed sequence
4. **Embedding stability via no-weight-decay-on-embeddings** (from OLMo 2)

These are *specific, ablation-provable design deltas* — the same epistemic stance Raschka takes about isolating the delta from the previous generation. SmolLM3 is the practical manifestation of that stance inside Hugging Face.

### Three-stage training curriculum

- Stage 1 (0→8T tokens): web 85% / code 12% / math 3%
- Stage 2 (8T→10T): web 75% / code 15% / math 10%, higher-quality math/code mix
- Stage 3 (10T→11.1T): decay phase, web 63% / code 24% / math 13%, upsampling

### Post-training pipeline (the part most labs hide)

- ~140B-token reasoning mid-training on OpenThoughts3-1.2M and NVIDIA Llama-Nemotron-Post-Training-Dataset
- SFT on ~1.8B tokens with both reasoning and non-reasoning modes (`/think` and `/no_think` flags)
- Anchored Preference Optimization (APO) — an off-policy variant of DPO with more stable optimization
- MergeKit-based model merging: 0.9 × APO soup + 0.1 × mid-training checkpoint = optimal recovery of 128k context performance

### What Hugging Face released alongside

- Base + instruct checkpoints, quantized versions
- **Exact nanotron training configs** with data weights
- Training scripts
- Pretraining data mixture specifications
- SmolTalk2 mid-training and SFT datasets
- Preference data for APO
- Synthetic data generation methodology (Qwen3-32B as source)
- Public WandB training logs with intermediate checkpoints

This is the Wolf doctrine in artifact form. The model is the *exhibit*; the data, code, configs, recipe, and logs are the *proof*. Closed-frontier-lab releases give you the model only.

### Performance positioning

- Outperforms Llama-3.2-3B and Qwen2.5-3B
- Competitive with Qwen3-4B and Gemma3-4B
- AIME 2025: 36.7% with reasoning mode vs 9.3% without
- LiveCodeBench: 30.0% with reasoning vs 15.2% without
- GPQA Diamond: 41.7% with reasoning vs 35.7% without

## The Ultra-Scale Playbook

- Published: February 2025 by Hugging Face (nanotron team)
- Format: ~100-page, ~30,000-word free open guide
- Source data: 4,000+ scaling experiments using up to 512 GPUs
- Effort: ~6 months of writing + ~1 year of GPU compute
- Hosted at: huggingface.co/spaces/nanotron/ultrascale-playbook

### What it covers

- 5D parallelism (data / tensor / pipeline / sequence / context)
- ZeRO partitioning
- CUDA kernel patterns
- Mixed-precision and FP8 trade-offs
- Real-world case studies: how DeepSeek trained for ~$5.5M, why Mistral chose MoE, what Meta did differently for Llama 3
- Companion code repos: `picotron` (educational) and `nanotron` (production-ready)

### Why it matters for the persona

The Ultra-Scale Playbook is the open analogue of internal frontier-lab training notebooks. Frontier labs guard this knowledge as competitive IP; Hugging Face wrote it down and gave it away. This grounds the Wolf claim that the open ecosystem's competitive edge is *information density* — publishing what you learned so the next team can move faster. Closed labs hoard knowledge; the open ecosystem compounds it.

## Sources used in this file

- https://huggingface.co/blog/smollm3
- https://huggingface.co/spaces/nanotron/ultrascale-playbook
- https://the-decoder.com/hugging-face-explains-how-train-large-ai-models-in-the-ultra-scale-playbook/
- https://ssojet.com/news/news-2025-03-huggingface-ultra-scale-playbook
- https://www.infoq.com/news/2025/03/huggingface-ultra-scale-playbook/
- https://huggingface.co/papers/2501.18795 (RoPE → NoRoPE paper, Yang et al., 2025)
- https://huggingface.co/papers/2402.13991 (intra-document masking paper)
- https://github.com/huggingface/nanotron
- https://huggingface.co/collections/HuggingFaceTB/smollm3-686d33c1fdffe8e635317e23
- https://wandb.ai/huggingface/SmolLM3-training-logs
