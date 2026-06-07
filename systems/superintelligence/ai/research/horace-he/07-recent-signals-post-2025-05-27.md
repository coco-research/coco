# Recent Signals (post 2025-05-27)

Window: 2025-05-27 → 2026-05-27. Required by persona schema: at least three entries.

## 1. Departure from Meta → Thinking Machines Lab, announced publicly

- **Date**: 2025-03-04 (note: this is technically pre-window, so listed for context — the actual *operational* effects unfold in the window).
- **URL**: https://www.thonking.ai/p/why-pytorch-is-an-amazing-place-to
- **Takeaway**: He is no longer at Meta. As of mid-2025 forward he is a founding-team ML-systems researcher at Thinking Machines Lab (Mira Murati's startup). The window-relevant signal is that his entire 2025-06-onwards output now sits behind Thinking Machines' deliberately quiet release cadence.

## 2. "Defeating Nondeterminism in LLM Inference" — Connectionism launch post

- **Date**: 2025-09-10
- **URL**: https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/
- **Takeaway**: He authors the first post on Thinking Machines' research blog. Argues the "concurrency + floating point" common-wisdom explanation for LLM nondeterminism is wrong; the real cause is non-batch-invariant kernels under variable load. Ships `batch_invariant_ops` (https://github.com/thinking-machines-lab/batch_invariant_ops) integrated with vLLM via FlexAttention. **In testing, 1000 completions at temperature 0 went from 80 unique outputs to 1000 bitwise-identical outputs.**

## 3. Author's own X thread announcing the post

- **Date**: ~2025-09-10
- **URL**: https://x.com/cHHillee/status/1965828670167331010
- **Takeaway**: First publicly observable output since joining Thinking Machines. He explicitly frames it as "a topic very near and dear to my heart (reproducible floating point numerics in LLM inference)" — confirming that kernel-level numerics is the lens he is bringing into the new lab.

## 4. Downstream adoption — vLLM's batch_invariance feature lands

- **Date**: 2025-09 / 2025-11
- **URLs**:
  - vLLM docs: https://docs.vllm.ai/en/latest/features/batch_invariance/
  - vLLM blog post: https://blog.vllm.ai/2025/11/10/bitwise-consistent-train-inference.html ("No More Train-Inference Mismatch: Bitwise Consistent On-Policy RL with vLLM and TorchTitan")
- **Takeaway**: Within two months, the production inference stack the open-source community uses ships first-class support for his abstraction. The vLLM blog explicitly credits the Horace He / Thinking Machines work as the unlock for bitwise-consistent on-policy RL — a major win for reproducible RL training.

## 5. Downstream adoption — SGLang follows

- **Date**: 2025-09-22
- **URL**: https://www.lmsys.org/blog/2025-09-22-sglang-deterministic/
- **Takeaway**: LMSYS SGLang ships its own deterministic-inference path inspired by the Thinking Machines work. Two of the three major open-source LLM serving stacks (vLLM, SGLang) adopt the batch-invariance frame within a month.

## 6. Thinking Machines Lab's strategic posture — Interaction Models preview

- **Date**: 2026-05-11
- **URLs**:
  - Blog: https://thinkingmachines.ai/blog/ ("Interaction Models: A Scalable Approach to Human-AI Collaboration")
  - VentureBeat: https://venturebeat.com/technology/thinking-machines-shows-off-preview-of-near-realtime-ai-voice-and-video-conversation-with-new-interaction-models
  - TechCrunch: https://techcrunch.com/2026/05/11/thinking-machines-wants-to-build-an-ai-that-actually-listens-while-it-talks/
- **Takeaway**: Thinking Machines previews **TML-Interaction-Small** (~400ms response, real-time voice/video). Horace's stated focus area at the lab is "collaborative AI products over purely autonomous agents" — this direction now has a public artifact, even though authorship credit for the model itself is not individually attributed to Horace. The substrate (low-latency, predictable inference with bitwise-consistent kernels) maps directly onto his prior work.

## 7. Thinking Machines × NVIDIA strategic partnership

- **Date**: 2026-03-10
- **URL**: covered in https://thinkingmachines.ai/news/ index
- **Takeaway**: TML and NVIDIA announce a gigawatt-scale strategic compute partnership. Relevant to Horace's portfolio because his work is the layer that turns NVIDIA hardware into reproducible product-grade inference.

## Notes

- Confirmed three or more entries dated **after 2025-05-27**: items #2, #3, #4, #5, #6, #7 all post-date the cutoff. Item #1 is pre-window context.
- Caveat: Thinking Machines has been deliberately quiet on a per-person basis since launch. Horace's individual publishing cadence in this window is one Connectionism post + supporting X thread + the substrate behind a lab-level launch — not a flood of blog output like 2022–2024. This is reflected in the persona's blind-spot field.
