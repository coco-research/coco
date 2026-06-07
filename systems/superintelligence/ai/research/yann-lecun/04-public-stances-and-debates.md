# Yann LeCun — Public Stances and Public Debates

## Core Stances (as of May 2026)

### 1. LLMs are a dead end for superintelligence
- "LLMs basically are a dead end when it comes to superintelligence." (Jan 2026, FT-relayed)
- "The breakthroughs are not going to come from scaling up LLMs." (Jan 2026, MIT Tech Review)
- Predictions about LLM limits made in 2023–2024 have been partly contradicted by 2024–2025 scaling progress — a known blind spot.

### 2. World models + JEPA + planning are the path
- Position paper "A Path Towards Autonomous Machine Intelligence" (2022, OpenReview).
- JEPA family: I-JEPA (Jan 2023), V-JEPA (Feb 2024), V-JEPA 2 (June 11, 2025).
- Quote: "If your goal is to train a world model for recognition or planning, using pixel predictions is a terrible idea." — frequently repeated, including around V-JEPA 2 launch.
- Cite: https://ai.meta.com/research/vjepa/

### 3. Autoregressive next-token prediction is fundamentally limited
- The error compounds geometrically with sequence length.
- This is a separate argument from #1: even if LLMs become powerful, AR generation introduces an irreducible reasoning ceiling.
- Defended consistently in talks 2023–2025 (Lex Fridman podcast March 7, 2024; Latent Space discussions).

### 4. Video is the data source for world models, not text
- "A four-year-old child receives ~10^15 bytes through visual input alone" vs. ~2×10^13 bytes of all internet text.
- This bandwidth gap is mathematical, not opinion.
- Hence V-JEPA 2's 1M+ hours of video.

### 5. AI existential risk is overstated
Source: https://x.com/ylecun/status/1816823628098425096 (Awesome piece on AI existential risk, or lack thereof)
- "Premature, preposterous, complete B.S."
- Two fallacies he names:
  1. "Just because a system is intelligent it will want to take over"
  2. "The minute we turn on a slightly flawed super-intelligent system, it will take over and destroy humanity"
- Notable contrast: Hinton (Turing co-laureate) has moved toward x-risk concern; LeCun has not.
- Notable contrast: Dario Amodei's "Machines of Loving Grace" framing — LeCun is dismissive of those timelines.

### 6. Open-source AI is the right path
- "Open research and open source are the best ways to understand and mitigate risks." (Oct 2023, X)
- "Open source AI models will soon become unbeatable."
- Vocal supporter of Llama-2 / Llama-3 / Llama-4 open weights.
- Lobbied successfully against restrictive open-source provisions in EU AI Act final text.

### 7. We have not built cat-and-dog intelligence yet
- LeCun repeatedly cites that current AI cannot match the world-modeling capacity of a domestic cat.
- This is the **floor benchmark** he uses to deflate AGI hype.
- Used in Lex Fridman March 2024 conversation and reiterated through 2025.

## Productive Conflicts

### vs. Andrej Karpathy (autoregressive scaling vs. world models)
- Karpathy is invested in the LLM autoregressive paradigm but acknowledges its limits ("we're summoning ghosts, not building animals" — Oct 2025 Dwarkesh appearance).
- LeCun goes further: he says the entire AR / next-token-prediction frame is incompatible with planning.
- Both are Cell A AI/research personas in the Marvin v2 panel — but they disagree on whether to fix LLMs or replace them.

### vs. Ilya Sutskever (pre-training as path)
- LeCun: "Pre-training is this crappy evolution" (paraphrased from Path Towards AMI framing).
- Sutskever: famously sees scaling pre-training as a generalized fitness-landscape optimizer.
- Sutskever's November 2025 Dwarkesh appearance softened the "scale is all" position somewhat — partial convergence.

### vs. Dario Amodei (x-risk timelines)
- Amodei: "Machines of Loving Grace" (October 2024) sketches an AGI timeline within 2–3 years.
- LeCun: dismissive of these timelines as marketing-driven.
- "I'm not wrong" frame from the Jan 2026 quotes is partly directed at Anthropic's framing.

### vs. Geoffrey Hinton (existential risk)
- Hinton left Google in 2023 to speak freely about x-risk concerns; came around to the doomer side.
- LeCun has remained skeptical throughout, including direct on-X exchanges.
- Notable because they share the 2018 Turing Award and are longtime collaborators.

## Productive Collaborations

### Yoshua Bengio (Turing co-laureate)
- Three-way Turing Award (2018) for deep learning.
- Long collaboration history including the 1998 "Gradient-based learning applied to document recognition" paper.
- Diverge on x-risk now (Bengio is more concerned) but converge on fundamental research priorities.

### Pieter Abbeel (RL / robot learning)
- World-models thesis intersects with Abbeel's robot-learning research at UC Berkeley.
- V-JEPA 2's robot fine-tuning resonates with Abbeel's approach.

### Chelsea Finn (meta-learning / world models)
- Stanford / Google DeepMind robot learning + world models research.
- Productive complementarity with JEPA approach.

## Communication Style

- **Combative on X/Twitter (@ylecun)** — known for direct rebuttals to other AI researchers, regulators, and journalists.
- Highly active poster (often dozens of posts per week).
- Uses analogies from physics (gravity, fitness landscapes) and biology (cats, babies, evolution).
- Will say "I don't know" on technical points but **will not back down on positions** he believes are well-grounded.
- French-American — switches between English and French in talks; cultural pride in moving AMI Labs to Paris.
