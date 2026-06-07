# PagedAttention Paper — SOSP 2023

## Citation

Kwon, Woosuk; Li, Zhuohan; Zhuang, Siyuan; Sheng, Ying; Zheng, Lianmin; Yu, Cody Hao; Gonzalez, Joseph E.; Zhang, Hao; Stoica, Ion. "Efficient Memory Management for Large Language Model Serving with PagedAttention." SOSP 2023.

- arXiv: https://arxiv.org/abs/2309.06180
- Submitted: September 12, 2023
- Venue: ACM SOSP 2023

## Abstract (verbatim)

> "High throughput serving of large language models (LLMs) requires batching sufficiently many requests at a time. However, existing systems struggle because the key-value cache (KV cache) memory for each request is huge and grows and shrinks dynamically. When managed inefficiently, this memory can be significantly wasted by fragmentation and redundant duplication, limiting the batch size. To address this problem, we propose PagedAttention, an attention algorithm inspired by the classical virtual memory and paging techniques in operating systems. On top of it, we build vLLM, an LLM serving system that achieves (1) near-zero waste in KV cache memory and (2) flexible sharing of KV cache within and across requests to further reduce memory usage."

## The core insight

KV cache for each request is huge, dynamic, and conventionally allocated as one contiguous block per request → massive fragmentation. The OS paging analogy: treat KV cache like virtual memory. Break it into fixed-size blocks (pages). Maintain a block table per request. Allocate blocks on demand, share blocks across requests when possible (e.g. shared system prompt prefixes).

This is the persona's archetypal move: **OS-style memory management applied to attention**. Woosuk's framing is that the KV cache problem was treated as a model-side concern when it is really a systems / memory-management concern.

## Performance claim

> "vLLM improves the throughput of popular LLMs by 2–4× with the same level of latency" compared to FasterTransformer and Orca. Gains scale with longer sequences, larger models, and complex decoding (beam search, parallel sampling).

## Why this matters for the persona

- It is the single most-cited LLM serving paper. The phrase "PagedAttention" is now industry-standard vocabulary.
- It established that **serving is a first-class systems research problem**, not just an engineering afterthought downstream of model training.
- It made the OS-mindset the dominant lens for inference: think in pages, blocks, schedulers, working sets — not just tensors and FLOPs.
- Co-authors include Zhuohan Li (close collaborator), Joseph E. Gonzalez (RISElab faculty), and Ion Stoica (his advisor and Databricks/Anyscale co-founder).
