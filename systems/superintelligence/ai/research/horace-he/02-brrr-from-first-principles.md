# "Making Deep Learning Go Brrrr From First Principles" — Canonical Post

Source: https://horace.io/brrr_intro.html
Hacker News discussion: https://news.ycombinator.com/item?id=37361711
X announcement: https://x.com/cHHillee/status/1503803011843252224 (March 15, 2022)
Karpathy endorsement: https://x.com/karpathy/status/1778841713605525889
External summary: https://www.abhik.ai/papers/deeplearning-go-brr

## Why this post is load-bearing

This is the post that established Horace He's name in the ML systems community and is the single canonical reference cited when explaining why a model is slow. Karpathy publicly recommended it as the standard explanation of GPU performance complexity. It is also the post that names his Substack ("Thonk From First Principles") and his personal brand around "first-principles" performance reasoning.

## Central thesis

> "Everybody wants their models to run faster. However, researchers often cargo cult performance without a solid understanding on the underlying principles." — Horace He, launching the post.

He argues every GPU operation lives in exactly one of three regimes, and that **the first job of a performance engineer is to identify which regime they are in**, because the wrong optimization in the wrong regime is wasted effort.

## The three regimes

1. **Compute-bound** — the FLOPs themselves are the bottleneck. Optimization: better matmul implementations, lower-precision math, kernel fusion that increases arithmetic intensity.
2. **Memory-bandwidth-bound** — the GPU spends its time moving tensors between HBM and SRAM. Optimization: operator fusion, recomputation, smaller dtypes, better tiling.
3. **Overhead-bound** — Python interpreter cost, PyTorch dispatch cost, kernel launch cost. Optimization: CUDA graphs, compilation, batching.

## Key quoted principles

- "In the time that Python can perform a single FLOP, an A100 could have chewed through 9.75 million FLOPS." — the canonical justification for why overhead matters at scale.
- "Modern accelerators grow compute speed faster than memory bandwidth." — the structural reason memory-bandwidth-bound work has gotten harder over time.
- On operator fusion: "Instead of writing our data to global memory just to read it again, we elide the extra memory accesses by performing several computations at once." Called by him "the most important optimization in deep learning compilers."
- The diagnostic frame: "If your training loss is way lower than your test loss, you're in the 'overfitting' regime, and you're wasting your time if you try to increase the capacity of your model." (used as analogy for the performance-regime move.)

## Why it's the right anchor for this persona

The three-regime framework is also the lens he applies to everything downstream — torch.compile, FlexAttention, batch-invariant ops. Each artifact can be explained as "this is what you build once you take the regime seriously." It is the **mental model** in his persona file.
