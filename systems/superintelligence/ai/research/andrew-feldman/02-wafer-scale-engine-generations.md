# Wafer-Scale Engine — WSE-1, WSE-2, WSE-3, and the CS-3 System

## Sources
- https://en.wikipedia.org/wiki/Cerebras
- https://awesomeagents.ai/hardware/cerebras-wse-3/
- https://arxiv.org/html/2503.11698v1
- https://arxiv.org/pdf/2503.11698
- https://sdk.cerebras.net/computing-with-cerebras
- https://medium.com/@santhosraj14/the-cerebras-wafer-scale-architecture-engineering-the-future-of-extreme-scale-deep-learning-b6f343f41e1a
- https://machine-learning-made-simple.medium.com/why-cerebras-raised-at-56-4-billion-usd-to-attack-nvidias-memory-bottleneck-c11bfe81f417

## Generations at a glance

| Generation | Announced | Process | Transistors | Cores | On-chip SRAM | On-chip bandwidth | System |
|---|---|---|---|---|---|---|---|
| WSE-1 | August 2019 | TSMC 16nm | 1.2 trillion | 400,000 | 18 GB | — | CS-1 |
| WSE-2 | April 2021 | TSMC 7nm | 2.6 trillion | 850,000 | 40 GB | 20 PB/s | CS-2 |
| WSE-3 | March 2024 | TSMC 5nm | 4.0 trillion | 900,000 | 44 GB | 21 PB/s | CS-3 |

All three generations occupy an entire 300mm wafer — 46,225 mm² of silicon, roughly 56× the area of NVIDIA's largest GPU die. Cerebras "skipped the slicing part" of the normal fab process: instead of cutting the wafer into hundreds of separate chips, the entire wafer is treated as one integrated processor with on-wafer die-to-die interconnect.

## Architectural distinctives

1. **On-chip SRAM as the only memory layer for compute.** Unlike GPUs, which rely on off-chip HBM (3.35 TB/s on H100, 8 TB/s on B200) reached over comparatively narrow pipes, WSE-3 holds 44 GB of SRAM directly adjacent to the 900,000 compute cores and delivers 21 PB/s of aggregate memory bandwidth — roughly 2,625× the bandwidth available to a B200 GPU. Feldman's repeated public claim that wafer-scale "attacks NVIDIA's memory bottleneck" stems from this number.

2. **Layer-by-layer dataflow execution.** WSE-3 implements a layer-by-layer flow: the entire wafer is devoted to computing one layer of the model across all data, then advances to the next layer. This is the inverse of the GPU pattern (where many copies of the model are split across many GPUs and data is streamed through them) and the source of Cerebras's "we never multiply by zero" claim on sparse workloads — the dataflow scheduler can skip zero-valued operands at scale.

3. **Single-device programming model.** Cerebras markets the CS-2 / CS-3 as providing "the deep learning compute resources equivalent to hundreds of GPUs, while providing the ease of programming, management and deployment of a single device." This is the user-facing flip side of wafer-scale: the cluster-coordination tax (NCCL, all-reduce, sharding strategy, gradient sync) collapses to zero because there's nothing to coordinate — it is one chip.

4. **No HBM dependency.** Because everything is on-die SRAM, Cerebras systems are insulated from the HBM supply bottleneck that constrained the NVIDIA Hopper / Blackwell ramp through 2024–2025. This is a recurring framing in Feldman's public commentary, especially during the IPO cycle: Cerebras's supply curve does not depend on SK Hynix or Micron HBM allocation.

## Performance claims at WSE-3 launch (March 2024)

- Roughly twice the performance of CS-2 on identical models.
- Up to 24 trillion parameters trainable on a single CS-3 (memory-mapped from external storage).
- Up to 2,048 CS-3 systems can be clustered for a single training job.

## The 2024 academic comparison (arXiv 2503.11698)

An academic comparison of Cerebras wafer-scale integration vs. NVIDIA GPU systems (March 2024) concluded that the wafer-scale architecture's primary advantage shows up on memory-bandwidth-bound workloads — exactly the regime that long-context LLM decode falls into. On compute-bound regimes (large-batch training of dense models), the GPU stack's economic advantage from scale manufacturing and CUDA tooling still dominates. This is the technical version of Feldman's go-to-market framing: "We are not trying to beat GPUs everywhere. We are trying to dominate the regime where GPUs are leaving 50× of performance on the floor."

## Why this matters for the persona

The WSE-3 specifications are the load-bearing concrete artifacts behind every public stance Feldman takes. When he says "GPU was the wrong architecture for AI," he is implicitly pointing at the 21 PB/s vs. 8 TB/s bandwidth ratio. When he says "moving data is expensive in power and time," he is pointing at the fact that WSE-3 doesn't move data off-chip in the first place. The architecture and the rhetoric are coupled — Cerebras's marketing claims and Feldman's strategic claims are both downstream of one number: bandwidth-per-byte-of-model-weight.
