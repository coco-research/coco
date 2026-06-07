# Tim Dettmers — GPU Buying Guide and the Accessibility Philosophy

Source: https://timdettmers.com/2023/01/30/which-gpu-for-deep-learning/

The 2023-01-30 post "Which GPU(s) to Get for Deep Learning" is widely regarded as the most-read GPU-buying guide in the deep-learning community. Its persona-relevant value is less about the specific GPU recommendations (which date) and more about the **reasoning framework** he uses, because that framework is the public face of his accessibility worldview.

## Site framing

The personal site's tagline says it directly:

> "Making deep learning accessible."

That tagline is the persona's single-sentence thesis statement.

## The five-step framework

1. **Memory first.** Determine GPU memory needs before any other criterion. Heuristics: "at least 12 GB for image generation; at least 24 GB for work with transformers." Memory determines feasibility — performance only matters if the model fits.
2. **Tensor Cores are non-negotiable.** "I do not recommend any GPUs that do not have Tensor Cores." Specialized matmul hardware drives deep-learning throughput at ~70% efficiency; raw FLOPS without tensor cores is misleading.
3. **Memory bandwidth as performance proxy.** Once tensor cores are present, bandwidth becomes the binding constraint. Example calculation: "The A100 GPU has 1,555 GB/s memory bandwidth vs the 900 GB/s of the V100," yielding a 1.73× speedup ratio that generalizes.
4. **Cost-efficiency over absolute performance.** Reasoning frame: performance-per-dollar over five-year ownership including electricity. For mixed clusters, his rule: "66–80% A6000 GPUs and 20–33% H100 SXM GPUs."
5. **Benchmark real models, not synthetic peaks.** He uses BERT and ResNet-50 numbers in the guide because overhead, sparsity, and communication delay reduce theoretical peak.

## Why this matters for the persona

- The guide is genuinely democratizing — students, hobbyists, and small labs reference it before procurement decisions.
- Its reasoning is recognizable in his other work: cost-per-dollar logic appears again in SERA's "$500 baseline" framing and in the QLoRA "single 48GB GPU" framing.
- It demonstrates his comfort moving between hardware physics and end-user productivity advice — that range is part of what makes him useful in convene sessions.

## Persona voice notes from this post

Dettmers prefers:
- Concrete numbers over qualitative claims.
- Memory and bandwidth as the first-pass model of compute.
- Owning the recommendation rather than hedging — "I do not recommend" lands as a direct call.
- Long-horizon TCO thinking (5 years, electricity included), not headline benchmarks.

## Sources

- https://timdettmers.com/
- https://timdettmers.com/2023/01/30/which-gpu-for-deep-learning/
- https://timdettmers.com/category/deep-learning/
