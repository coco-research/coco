# "ChatGPT and The Art of Post-Training" — detailed notes

Source: Slide deck for the Jan 28, 2025 Stanford HAI Seminar by Barret Zoph and John Schulman. Synthesized from the FisherAI Chinese-language slide summary (fisherdaddy.com/posts/chatgpt-and-the-art-of-post-traning/) and the qiangtu PDF copy, both of which mirror the original Google Slides deck. Schulman's X thread confirming the slides: https://x.com/johnschulman2/status/1891539960743743756.

The talk was not recorded but Zoph and Schulman released the slides publicly. This is the most consequential single artifact for understanding Zoph's applied post-training thinking; everything else (departure note, Tinker positioning) is downstream.

## Working definition of post-training

> Post-training is the final stage that turns a base model into something that behaves like an assistant, follows the right format, uses tools, refuses appropriately, and has a coherent personality. It is fundamentally smaller in compute than pretraining but enables far faster iteration cycles.

The deck explicitly contrasts pretraining (next-token prediction on raw text) with post-training (RLHF, instruction tuning, tool-use teaching, refusal training, persona shaping).

## Timeline of the work the talk describes

- **Mid-2020:** GPT-3 base released.
- **2021:** WebGPT (RL-trained web browsing). The chat-model research line begins as a WebGPT successor.
- **January 2022:** InstructGPT / GPT-3.5 released — instruction-following completion model.
- **September 2022:** Schulman and Zoph begin collaborating; the initial team is just called "RL" and is a handful of people.
- **Summer 2022:** Closed beta among friends and family.
- **Late 2022:** Leadership decides to ship; product team mobilizes.
- **November/December 2022:** ChatGPT launches as a "low-key research preview," goes viral.
- **2023–2024:** Team grows to 100+; expands to GPT-4, GPT-4o, o1-mini; tools (browsing, code, retrieval); multimodal.
- **May 2024:** OpenAI publishes the Model Spec for transparency and internal consistency.

## The four "famous bugs" the talk uses as case studies

These are critical — they encode Zoph's lessons about what goes wrong.

### 1. Spelling errors

A bug in the annotation system trained the reward model to prefer **misspelled** completions. When human annotators improved versions of model outputs, the pipeline classified the improved versions as highest-scoring examples — but with a flaw that left certain spelling artifacts as correlated features. The reward model learned the artifact. Lesson: **the reward model is exactly as good as the data pipeline that produced its training set, including its silent bugs.**

### 2. Over-refusals

Early GPT-3.5 was excessively preachy in its refusals, while being easily jailbroken. Root cause: fuzzy boundary between harmful and benign queries, inconsistent annotator preferences, lack of refusal specifications. Fix: paired data (matched harmful/harmless prompts), explicit specs, tiered annotator management. Lesson: **specs > vibes for safety-relevant behavior.**

### 3. Political bias

Model exhibited systematic American left-leaning bias. Contributors: PMC writing style, annotator demographics, RL amplification of small initial biases, hard problem of symmetric treatment across views. Lesson: **RL is a bias amplifier on top of whatever the SFT distribution already encoded; small initial skew compounds.**

### 4. Defamation and factual issues

Models traded off informativeness vs accuracy, with autoregressive sampling making things worse by inducing confabulation. Largely solved by paired-prompt data collection.

## Reward modeling is the central bottleneck

The talk treats reward modeling as the hardest open problem in post-training:

- Comparison data (binary or 1–7 scale) plus annotator metadata is the input.
- Reward models become over-optimized or "hacked" — this is presented as the **persistent** failure mode of RLHF.
- Different feedback sources have explicit tradeoffs: **user annotations give prompt authenticity but low label quality**; **expert annotations give correctness but lower alignment with user intent.** Neither is sufficient alone.
- Subjective domains (creative writing, humor), high-effort tasks (programming, math proofs, long docs) are the open frontier where annotation quality is the bottleneck.

## SFT-then-RL is the standard pipeline

- SFT initializes; RL optimizes.
- Human-AI collaboration can produce higher-quality SFT data than humans alone — scalable supervision is the live research direction.

## Direct Zoph attribution in the slides

The deck is presented jointly; no separated solo-Zoph quotes. But the structure of the case studies (bugs first, methodology second) and the emphasis on engineering rigor over algorithmic novelty is recognizably Zoph's framing (consistent with his NAS / Switch Transformer / FLAN style of "show the engineered system, then explain why each piece is necessary"). Schulman's portion typically focuses on the RL algorithmic side.

## Implication for the persona

This talk is the single best primary source for Zoph's applied-ML stances as of 2025. Three signature framings come out of it:

1. **The reward model is the bottleneck. Reward hacking is not a bug to fix once; it is the permanent shape of the failure surface.**
2. **Specs beat vibes for any safety-relevant behavior.** Boundary cases need paired data and explicit written guidelines, not annotator intuition.
3. **Post-training is where the magic happens at the frontier.** Pretraining provides the substrate; post-training is where assistant behavior, tool use, and personality are actually created — and where the most consequential engineering decisions are made on a small fraction of pretraining compute.
