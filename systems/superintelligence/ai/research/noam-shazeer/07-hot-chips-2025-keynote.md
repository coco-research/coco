# Hot Chips 2025 Keynote — "Predictions for the Next Phase of AI" (August 2025)

Sources:
- https://hc2025.hotchips.org/assets/program/conference/day1/k1_GoogleDeepMind_Shazeer.pdf (deck, 1.1MB PDF)
- https://www.servethehome.com/thank-you-for-the-supercomputers-google-predictions-for-the-next-phase-of-ai-at-hot-chips-2025/
- https://www.youtube.com/watch?v=v0beJQZQIGA (talk video)
- https://x.com/hotchipsorg/status/1968176742151159967
- https://semiengineering.com/what-do-llms-want-from-hardware/

Day 1 keynote at Hot Chips 2025 in Silicon Valley, August 2025. This was Shazeer's first major external technical talk after returning to Google in 2024.

## Title and framing

**"Predictions for the Next Phase of AI"** — pitched as a thank-you to the hardware community, then a road map of what frontier LLMs will need next.

## The three core slides

### 1. "Language Modeling [is the] Best Problem Ever"

A slide dedicated to this thesis. Shazeer's stance: language modeling is the natural objective for general intelligence because it subsumes reasoning, code, math, multi-modality, and tool use, and because the data is essentially free (the internet + synthetic).

### 2. "What LLMs Want"

- More parameters
- More depth
- More nonlinearities
- More information flow (i.e. attention + skip connections)
- More good training data

Each item maps to a hardware requirement.

### 3. "What LLMs Want From Hardware"

Four explicit asks:
1. **More compute (FLOPS)** — "more FLOPS are more better"
2. **More memory capacity**
3. **More memory bandwidth**
4. **More network bandwidth**

Plus two qualitative asks:
- **Lower precision** — FP8 today, smaller tomorrow. Bf16 is overkill for most ops.
- **Determinism** — same inputs should produce same outputs across runs and machines. Non-determinism is the bane of debugging and reproducibility.

## Historical arc (2015 → 2025)

Shazeer walked the audience through a decade of training-scale evolution:
- **2015:** "It was a big deal to train on 32 GPUs."
- **2018:** Google built dedicated TPU pods for AI.
- **2025:** Frontier training runs use "hundreds of thousands of GPUs" (or TPUs).

His gratitude framing — *"Thank you for the supercomputers"* — is real but also a setup. He is telling chip designers: we've absorbed every order-of-magnitude you've shipped, and we need more, faster.

## Implicit predictions

- The next phase of AI is still **scaling-bound**, not algorithm-bound. He does not claim a new paradigm is needed.
- **MoE will keep mattering** because it decouples model capacity from per-token FLOPS.
- **Inference compute is the next frontier** — explicit echo of his Dwarkesh framing that "we're going to see an explosion" in inference-time compute.
- **Bandwidth-to-the-accelerator and inter-accelerator bandwidth** are the bottlenecks, not raw FLOPS.

## Why this matters for the persona

- This is his **public manifesto for the 2025–2027 scaling phase**: more, faster, sparser, lower precision, deterministic.
- It clarifies his disagreement with the Yann LeCun "scaling is hitting a wall, need world models" camp: he is publicly betting another decade of returns on essentially the current paradigm with architecture refinements.
- It also clarifies his agreement-with-engineering posture: he treats the relationship with chip designers as a collaboration, not a customer-supplier dynamic. He pairs naturally with Bryan Catanzaro (NVIDIA, Megatron) and the Google TPU team.
