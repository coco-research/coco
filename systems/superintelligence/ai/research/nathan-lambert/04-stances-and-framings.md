# Nathan Lambert — public stances and framings research

Each stance paired with the evidence URL that grounds it. These feed directly into `public_stances` in the persona YAML.

## Stance 1: RLVR is a genuinely new training paradigm, not RL relabeled
- "Reinforcement Learning with Verifiable Rewards (RLVR)" introduced as a named method in the Tulu 3 paper, November 2024.
- The accuracy bonus on checkable answers is "the first reward... drives the majority of the learning."
- Evidence: https://www.interconnects.ai/p/deepseek-r1-recipe-for-o1 ; https://arxiv.org/abs/2411.15124

## Stance 2: Reward models are the bottleneck, not the policy
- Long-running thesis across RewardBench, RewardBench 2, and most of his Interconnects RLHF posts.
- RewardBench 2 results — models score ~20 points lower than on RB1 — confirm reward modeling remains the weakest evaluated link.
- Evidence: https://arxiv.org/abs/2506.01937 ; https://allenai.org/blog/rewardbench-the-first-benchmark-leaderboard-for-reward-models-used-in-rlhf-1d4d7d04a90b

## Stance 3: America must build truly open frontier models or lose the open-source ecosystem to China
- Core thesis of the ATOM Project. "America needs to maintain at least one lab focused on training open models with 10,000+ leading-edge GPUs."
- Evidence: https://www.interconnects.ai/p/atom-project ; https://www.atomproject.ai/

## Stance 4: Reasoning models work primarily through RL scaling, not explicit inference-time search
- DeepSeek R1 framing: "The winds of o1 replication have been blowing strongly away from any sort explicit search (especially at inference time)."
- Evidence: https://www.interconnects.ai/p/deepseek-r1-recipe-for-o1

## Stance 5: Chinese open labs are catching up faster than the US discourse acknowledges
- "Top 10 open models on LMArena are all created by Chinese organizations" as of August 2025.
- "Top 3 open models on ArtificialAnalysis are of Chinese origin" (August 2025).
- Evidence: https://www.interconnects.ai/p/atom-project ; https://thenewstack.io/nathan-lamberts-atom-project-seeks-american-open-source-ai-models/

## Stance 6: RLHF is not a numbers-go-up tool; it is a behavior-shaping tool
- "RLHF is not an easy tool to make numbers go up with. It's a powerful tool to change your language model."
- "It doesn't mean that the model believes these things. It's just trained to prioritize these things."
- Evidence: https://www.latent.space/p/rlhf-201

## Stance 7: Open post-training recipes are necessary for scientific progress
- Tulu 3 ethos: release weights, data, code, training recipes, decontamination tools. "Fully open" is non-negotiable.
- Olmo 3 ethos: ship the entire model flow, base → instruct → think → RL Zero, with OlmoTrace for output-to-training-data traceability.
- Evidence: https://arxiv.org/abs/2411.15124 ; https://www.interconnects.ai/p/olmo-3-americas-truly-open-reasoning

## Stance 8: Progress in 2026 will be steady, not explosive
- Year-in-review prediction: "slow, consistent progress over the next few years."
- Evidence: https://www.interconnects.ai/p/2025-interconnects-year-in-review

## Stance 9: AI feedback (synthetic data) has collapsed costs and democratized RLHF
- "$5–20 per preference point" of human data has been replaced by "AI feedback that is <$0.01 per sample."
- Evidence: https://www.interconnects.ai/p/the-state-of-post-training-2025

## Stance 10: Character training, elicitation, and sycophancy are under-studied post-training dimensions
- Year-in-review framing: post-training has moved past DPO-vs-PPO debates and into shaping model character.
- Evidence: https://www.interconnects.ai/p/2025-interconnects-year-in-review

## Sources

All inline above. Cross-referenced for `public_stances` field.
