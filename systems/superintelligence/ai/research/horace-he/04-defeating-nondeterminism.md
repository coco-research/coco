# "Defeating Nondeterminism in LLM Inference" — Connectionism Post

Source: https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/
Date: **September 10, 2025**
Author: Horace He, with collaborators at Thinking Machines Lab
Repo: https://github.com/thinking-machines-lab/batch_invariant_ops
vLLM integration docs: https://docs.vllm.ai/en/latest/features/batch_invariance/
Author tweet announcing it: https://x.com/cHHillee/status/1965828670167331010
Press: https://www.nextbigfuture.com/2025/11/defeating-nondeterminism-in-llm-inference-by-thinking-machines.html
Yahoo Finance: https://finance.yahoo.com/news/thinking-machines-lab-wants-ai-213011412.html

## Central claim — the "common wisdom" is wrong

The widely repeated explanation for LLM nondeterminism is "concurrency + floating-point non-associativity." Horace argues this is **incomplete**. The actual root cause is:

> "Nearly all LLM inference endpoints are nondeterministic [because] the load (and thus batch-size) nondeterministically varies."

The chain of causation: variable load → variable batch size → non-batch-invariant kernels → bitwise-different outputs even at temperature 0.

## The fix — batch invariance

A kernel is **batch-invariant** if it produces bitwise-identical results for a given input regardless of the batch size. He demonstrates batch-invariant implementations of the three operations that break:

- **RMSNorm** — data-parallel strategy assigning batch elements to cores, avoiding cross-batch reduction order shifts.
- **Matrix multiplication** — fixed tile sizes, avoiding split-K optimizations that reorder accumulation.
- **Attention** — fixed split-size (not fixed split-count) strategy for KV caching, so split boundaries don't move with batch shape.

## The empirical proof

> "In testing with 1000 completions at temperature 0, the default generated 80 unique outputs; with batch-invariant kernels, all 1000 were identical."

## Why this is a high-signal stance

1. It identifies a **mechanical, debuggable cause** for a phenomenon the field had handwaved as inherent — classic Horace move (compare to his "tokenization is the cause of disproportionate weirdness" energy from a different domain).
2. It ships an **open-source artifact** (batch_invariant_ops) integrated with vLLM and FlexAttention, not just a paper. "Product + open science."
3. It is the **first Connectionism post** and therefore the move that defines Thinking Machines' research voice. Horace's framing — kernel numerics, reproducibility, batch shape — is now the lab's calling card.
4. It explicitly bridges to **RL training**: bitwise-consistent inference is a precondition for reproducible RL evaluation. Downstream consequences in vLLM Project's November 2025 follow-up ("No More Train-Inference Mismatch: Bitwise Consistent On-Policy RL").

## Author's own framing on X

> "Apologies that I haven't written anything since joining Thinking Machines but I hope this blog post on a topic very near and dear to my heart (reproducible floating point numerics in LLM inference) will make up for it!" — @cHHillee, ~September 2025.

## Signature moves this artifact instantiates

- **First-principles diagnosis** — "the explanation everyone gives is incomplete; here is the actual mechanical cause."
- **Open-source the fix** — drop-in torch.Library replacement; no need to rewrite your model.
- **Tie performance and correctness** — batch invariance is presented not just as a numerics nicety but as a load-bearing property for production RL.
