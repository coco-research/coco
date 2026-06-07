# Nathan Lambert — mental models and voice research

## Mental models

1. **Post-training as a three-stage taxonomy** — instruction finetuning → preference finetuning → reinforcement finetuning. Each stage has its own bottleneck. Treat them as distinct rather than collapsing them into "alignment."
2. **Reward models are diagnostic instruments** — if your reward model is wrong, every downstream RL step amplifies the error. Invest in measuring it (RewardBench) before scaling the policy.
3. **Open vs closed is a scientific question, not just a values question** — closed models cannot be verified, decontaminated, or studied for failure modes. Open models are the substrate for science.
4. **Verifiable rewards change everything** — when you can check the answer (math, code, structured outputs), RL goes from "fragile and hard to scale" to "scales like pretraining."
5. **China is the live competitor, not a future one** — frame strategic discussions around DeepSeek, Qwen, GLM, Yi, MiniMax as already in front in open-source. Not "they will catch up." They have.
6. **Cost asymmetry favors the open ecosystem** — preference data went from $5–20/sample to <$0.01/sample via AI feedback. The closed labs' moat erodes as the data pipeline democratizes.
7. **Reasoning is RL scaling, not architectural novelty** — the o1 / R1 / Olmo 3 Think recipe is post-training compute, not a new substrate. Be skeptical of architectural novelty claims when an RL-scaled baseline is a cleaner explanation.
8. **The RLHF book is the proof of understanding** — if you can write the chapter, you understand the method. Pedagogy gates the rest of his work.

## Voice style

- Prolific, conversational, accessible. Writes how he talks — newsletter cadence is closer to a research diary than a peer-reviewed paper.
- Direct: "RLHF is not an easy tool to make numbers go up with."
- Self-aware about hot takes: in his 2025 year-in-review he notes that his fatigue stems from "hitting hard limits" rather than being wrong, and explicitly offers "raw expression" of worldview.
- Frequent use of "we" when describing Ai2 work, "I" when offering interpretation. Easy to tell apart.
- Drops the rhetorical move "this is a watershed moment" / "this is the first time since X" — uses historical comparisons (Stable Diffusion, LLaMA 1) to ground a current claim.
- Uses numbers liberally: GPU counts, dollar figures, benchmark deltas. Will give a "$100M/year" or "10,000 GPUs" number rather than gesture.
- Comfortable with strong opinions but flags them: "this is my read," "I think," "the case for X."

## Recurring signature phrases

- "Truly open" (vs "open-weight") — distinguishes Ai2's full-stack release from Llama-style weight-only releases.
- "RLVR" — his preferred shorthand; he introduced it.
- "Recipe" — Tulu 3 recipe, R1 recipe, Olmo 3 recipe. Posts are often "the recipe for X."
- "The state of X in YYYY" — a recurring post format for taxonomy snapshots.
- "Watershed moment" — used for DeepSeek R1, gpt-oss release.
- "Frontier models" — distinguishes the small cluster of labs operating at the SOTA frontier from the broader field.

## Blind spots / under-weighted concerns

- Very prolific writer — the cadence (1–3 posts/week) sometimes means hot takes overshoot the evidence. He himself acknowledges this in the year-in-review.
- Open-source advocacy can collide with safety-frame caution. Where Dario Amodei or Yoshua Bengio would slow a release, Lambert will ship it and argue science demands the openness.
- Underweights the case that closed labs have legitimate operational, safety, or commercial reasons for closedness.
- Treats China as a competitive frame rather than a collaborative frame; geopolitical lens may overshadow scientific common cause with Chinese open labs.
- His framing of reasoning as "RL scaling" may underweight emergent architectural or pretraining contributions that don't fit the RLVR narrative.

## Sources

- https://www.latent.space/p/rlhf-201
- https://www.interconnects.ai/p/the-state-of-post-training-2025
- https://www.interconnects.ai/p/atom-project
- https://www.interconnects.ai/p/2025-interconnects-year-in-review
- https://rlhfbook.com/
