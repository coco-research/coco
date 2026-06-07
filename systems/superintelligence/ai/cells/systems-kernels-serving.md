---
cell_id: systems-kernels-serving
cell_letter: A
team: ai-super-intelligence
personas_count: 7
last_updated: 2026-05-28
---

# Cell: Systems, Kernels, and Serving

Training kernels, inference serving, distributed training, GPU programming, and non-NVIDIA silicon. This cell holds the "how do we make this run fast and at scale" lens. Internally split between *training kernels + algorithms* (Dao, Gu, Catanzaro, He), *inference serving + accessibility* (Kwon, Dettmers), and *anti-NVIDIA silicon* (Feldman). Phase 2 added Feldman as the canonical wafer-scale-integration voice — the cell needed a non-NVIDIA pole to balance Catanzaro.

## Personas (7)

| Slug | Name | Affiliation | Cell role | Signature |
|---|---|---|---|---|
| `tri-dao` | Tri Dao | Princeton + Together AI CSO | lead-driver | FlashAttention 1-4, Mamba/Mamba-2/Mamba-3, IO-aware kernel design, ATLAS inference |
| `bryan-catanzaro` | Bryan Catanzaro | NVIDIA VP Applied DL Research | lead-driver | Megatron-LM, NeMo framework, cuDNN-origin story, GPU + software co-design |
| `andrew-feldman` | Andrew Feldman | Cerebras Systems co-founder + CEO | lead-driver | Wafer-Scale Engine; anti-NVIDIA dataflow argument; Cerebras IPO May 2026 (Nasdaq: CBRS) |
| `albert-gu` | Albert Gu | CMU + Cartesia CSO | specialist | S4 / Mamba state space models, H-Net hierarchical chunking, Cartesia voice gen |
| `horace-he` | Horace He | Thinking Machines Lab (from Meta March 2025) | specialist | torch.compile, "Make Deep Learning Go Brrrr From First Principles," Defeating Nondeterminism |
| `woosuk-kwon` | Woosuk Kwon | Inferact CTO + co-founder (from Berkeley/TML/DeepMind) | specialist | vLLM / PagedAttention, "OS-style memory management for KV-cache," 400K+ GPU production scale |
| `tim-dettmers` | Tim Dettmers | CMU (Fall 2025) + Ai2 | specialist | QLoRA (NeurIPS 2023 Oral), bitsandbytes, LLM.int8, GPU buying guide, accessible ML thesis |

## When to summon the whole cell

- "Why is this slow / how do we speed it up?"
- "Memory bandwidth or compute bound — what's the roofline?"
- "Quantization / serving / batching — what's the right architecture?"
- "Sub-quadratic attention or stay with attention — what's the tradeoff?"
- "NVIDIA stack or alternative silicon — what's the real cost?"
- "Inference at scale — what does production look like beyond a benchmark demo?"

## When NOT to summon

- Algorithmic / capability research — defer to `model-architects`.
- Alignment or safety — defer to `alignment-interp-safety`.
- Product UX — defer to `applied-ai-leadership`.

## Productive tensions inside the cell

- **Catanzaro ↔ Feldman**: the canonical NVIDIA-vs-wafer-scale split. Catanzaro carries the "GPU + software co-design is the moat" frame; Feldman carries the "the industry took a wrong turn by accepting GPU dataflow" frame. Both technically respect each other; convene must surface this as the central architectural disagreement on AI silicon.
- **Dao ↔ Shazeer** (cross-cell): IO-aware kernels + SSM hybrids vs attention-only at scale.
- **Dao + Gu vs Shazeer + Wei** (cross-cell): SSM/hybrid architectural bet vs pure-attention bet — both camps respect each other and the disagreement is empirical.
- **Catanzaro ↔ Kwon**: closed NVIDIA stack vs open vLLM serving — vendor-customer dynamic but technical respect on both sides.
- **Feldman ↔ Musk** (cross-cell): two custom-silicon poles. Feldman's wafer-scale vs Musk's Tesla Dojo. Convene benefits from both when the prompt is "what silicon should we bet on?"
- **Dettmers ↔ Catanzaro**: democratized-access via quantization vs frontier-scale-only via NVIDIA.

## v2 panel attribution

- **Dao** (3 attributions): drove D17 quantization ladder (f32 → int8 → binary+int8 rerank, panel co-owner with Garcia), v4.5 HNSW ghost-edge SLA + eviction policy, validator on D5 tri-temporal time model.

## How this cell maps to /superintelligenceTeam-convene

Convene-time, this cell is asked **after** the architecture / algorithm question lands. Its three lead-drivers (Dao, Catanzaro, Feldman) ratify whether the design is actually feasible at the latency, cost, and memory budget required — and now from three architectural poles (kernel-level on GPU, full-stack NVIDIA, anti-GPU wafer-scale). Kwon brings the production-scale inference voice (vLLM running on 400K+ GPUs makes him the authority on "what real serving looks like"). Dettmers is the accessibility conscience — when a design only works on H100/Blackwell, he'll surface the cost.

## Cross-team back-compat

All seven carry `cell_letter: A`. Only Tri Dao participated in the Marvin v2 panel.
