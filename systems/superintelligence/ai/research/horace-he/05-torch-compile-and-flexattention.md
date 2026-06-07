# torch.compile, PyTorch 2.0, and FlexAttention — Engineering Legacy

## torch.compile / PyTorch 2.0

Paper: "PyTorch 2: Faster Machine Learning Through Dynamic Python Bytecode Transformation and Graph Compilation"
Venue: ASPLOS 2024
DOI: https://dl.acm.org/doi/10.1145/3620665.3640366
Tech-talk index: https://dev-discuss.pytorch.org/t/torch-compile-tech-talks-at-ptc23/1625

torch.compile is the **defining engineering artifact** Horace He is associated with prior to Thinking Machines. The launch slogan he popularized: **"2–4x faster in one line of code."** Architecturally, the pipeline takes ordinary PyTorch Python code, traces it via dynamic Python bytecode transformation (Dynamo), lowers it through an intermediate representation (FX → Aten → Inductor), and emits Triton kernels — which are themselves still Python — for execution.

His framing of why this matters, paraphrased from his Jane Street talk:

> "If you've written code in CUDA and the CUDA programming model, it must be parallel… parallelism is inherent to the programming model."

The deeper claim is about **programming models, not optimizations**. He argues the field underweights the importance of well-designed APIs and overweights the hope that the compiler will figure it out. torch.compile is engineered to let users predict what the compiler will do — predictability is the contract, performance is the consequence.

## FlexAttention

PyTorch blog: https://pytorch.org/blog/flexattention/ (August 7, 2024, co-authored with Driss Guessous, Yanbo Liang, Joy Dong)
Paper (MLSys 2025): https://proceedings.mlsys.org/paper_files/paper/2025/file/61a9278dfef5f871b5e472389f8d6fa1-Paper-Conference.pdf
arXiv: https://arxiv.org/pdf/2412.05496
Author's tweet thread launching it: https://x.com/cHHillee/status/1821253769147118004 (August 2024)
Part II for inference: https://pytorch.org/blog/flexattention-for-inference/

The pitch (his words):

> "For too long, users have lived under the software lottery tyranny of fused attention implementations. No longer. Introducing FlexAttention, a new PyTorch API allowing for many attention variants to enjoy fused kernels in a few lines of PyTorch."

The technical move: a programming model where the user writes attention modifications (score_mod, mask_mod) in plain Python, and `torch.compile` lowers them into a fused Triton FlashAttention kernel that is competitive with hand-written ones. Sliding window, causal mask, prefix-LM, document mask, ALiBi, soft-cap — all expressed in a few lines, all fused.

His own line on why this could only happen at the PyTorch level:

> "It's not a coincidence that the two most popular ML compilers are closely tied to the two most popular ML frameworks. I don't think FlexAttention could have been done at a different level of abstraction." — @cHHillee, Jan 2025 (https://x.com/cHHillee/status/1876742134482501827).

PagedAttention falls out as a special case of FlexAttention's abstraction — a point he highlights as evidence the abstraction is correct.

## Why this matters for the persona

These artifacts are the proof that he is **not** a blog-post-only systems thinker. He has personally shipped:

- A new compiler stack in the most-used ML framework.
- A new programmable kernel API at MLSys 2025.
- A widely-used open-source inference reference (gpt-fast).
- A drop-in numerics-correctness library (batch_invariant_ops).

The persona's authority on ML systems rests on *both* the canonical brrrr post *and* the artifacts. Critiques he levels carry weight because he has done the work.
