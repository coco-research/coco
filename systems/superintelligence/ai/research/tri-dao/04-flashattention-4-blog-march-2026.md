# FlashAttention-4 — Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling

Sources:
- https://tridao.me/blog/2026/flash4/
- https://www.together.ai/blog/flashattention-4
- https://www.theneuron.ai/explainer-articles/flashattention-4-explained-the-software-that-makes-every-ai-chatbot-fast-just-got-a-massive-upgrade-tri-dao-blackwell/
- https://pytorch.org/blog/flexattention-flashattention-4-fast-and-flexible/
- https://lambda.ai/blog/flashattention-4-gives-the-nvidia-blackwell-platform-its-most-optimized-attention-kernel-yet

Extracted: 2026-05-27

## Headline

**Released:** March 5, 2026 (Tri Dao's blog), with broader PyPI / PyTorch / Lambda
ecosystem rollout shortly after. **May 27, 2026** — CuTeDSL-based release for Hopper and
Blackwell GPUs (significantly faster install / compile time vs. prior C++ template path).

## Authors

Ted Zadouri (Princeton + Together AI), Markus Hoehnerbach (Meta), Jay Shah (Colfax Research),
Timmy Liu (NVIDIA), Vijay Thakkar (Meta + Georgia Tech), **Tri Dao** (Princeton + Together AI).

Cross-institutional kernel work is itself a persona signature — Princeton + Together AI as
**lead** with NVIDIA, Meta, and Colfax as collaborators.

## Performance claims

- **B200 BF16:** up to **1605 TFLOPs/s**, ~71% utilization.
- **1.1–1.3× faster** than cuDNN 9.13 forward pass.
- **2.1–2.7× faster** than Triton forward pass.
- Backward pass: "consistently outperforms the other baselines for large sequence lengths."

## Central technical thesis (the Dao voice)

> "The main performance bottleneck lies not in how fast the tensor cores can do MMA,
> but rather (a) in the SFU units for softmax exponential during the FWD computation,
> and (b) in the shared-memory traffic during the BWD computation."

This is the recurring move: **the obvious bottleneck (tensor-core throughput) is not the
real bottleneck**. The real bottleneck has moved to **softmax exponential on SFU units**
(forward) and **shared-memory traffic on operand B** (backward). The paper redesigns the
kernel around those new bottlenecks.

## Key design decisions

1. **Ping-pong scheduling with two Q tiles per CTA** — maximize matmul / softmax overlap.
2. **Software-emulated exp() via polynomial approximation on FMA units** — instead of routing
   through the SFU, which is bandwidth-limited. Cody-Waite range reduction + Horner's method
   with polynomial coefficients (p₀=1.0, p₁≈0.6951, p₂≈0.2276, p₃≈0.0771) optimized using the
   **Sollya** numerical software package.
3. **2-CTA MMA mode** — halve shared-memory traffic for backward pass operand B.
4. **Conditional online softmax rescaling** — rescale less frequently to minimize non-matmul
   operations.
5. **Implemented entirely in CuTe-DSL** (CUTLASS' Python kernel DSL). Reduces compile times
   by ~20–30× vs C++ templates. Installation and compilation take seconds rather than
   minutes-to-hours.

## Direct quote on the difficulty of kernel work

> "Optimizing FlashAttention backward can feel like stuffing an oversized rug into a room:
> flatten one corner and another pops up."

This is the **asymmetric hardware scaling** thesis: when tensor-core throughput grows
faster than memory bandwidth and SFU throughput, **every other resource becomes the
bottleneck in turn**, and you cannot solve the problem with a single optimization.

## "FA5 will be written completely by AI"

Per third-party reporting (theneuron.ai explainer), Tri Dao used Claude to help debug a
deadlock in the FA-4 code, and stated a hope that **FlashAttention-5 will be written
completely by AI**. This is a meaningful posture from someone whose research is at the
hardest-to-automate layer of the stack — kernel-level CUDA optimization. It signals he
is **optimistic about coding-agent capability at the kernel layer**, in contrast to
positions like Karpathy's "agents are slop for novel code."

## Why this artifact anchors the persona's 2026 voice

- It is the **single most recent canonical Dao publication** as of 2026-05-27.
- It is the artifact most-cited by inference-engine and serving-stack teams in 2026.
- It restates his core thesis (memory hierarchy + co-design) in language that's directly
  applicable to systems-kernels-serving cell debates (per-provider deadlines, kernel-fused
  pipelines, partial-result tolerance).
