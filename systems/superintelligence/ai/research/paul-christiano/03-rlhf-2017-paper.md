# Deep Reinforcement Learning from Human Preferences (NeurIPS 2017)

Source paper: https://arxiv.org/abs/1706.03741
Conference record: https://papers.nips.cc/paper/2017/hash/d5e2c0adad503c91f91df240d0cd4e49-Abstract.html

## Citation

Christiano, P. F., Leike, J., Brown, T., Martic, M., Legg, S., & Amodei, D. (2017). Deep reinforcement learning from human preferences. In *Advances in Neural Information Processing Systems 30* (NIPS 2017). arXiv:1706.03741. First posted to arXiv on June 12, 2017.

## Author lineup — significance

The author list reads like a who's-who of subsequent alignment leadership:
- **Paul F. Christiano** — first author, later ARC founder and AISI Head of Safety.
- **Jan Leike** — co-led Superalignment at OpenAI, later moved to Anthropic.
- **Tom Brown** — first author on the GPT-3 paper; Anthropic co-founder.
- **Miljan Martic** — DeepMind safety research.
- **Shane Legg** — DeepMind co-founder, Chief AGI Scientist.
- **Dario Amodei** — later Anthropic CEO and co-founder.

The paper is therefore the documentary intersection point of the OpenAI ↔ DeepMind ↔ Anthropic alignment lineage. It is the foundational text everyone in modern RLHF descends from, with Christiano as the named lead.

## Core contribution

The paper "explores goals defined in terms of (non-expert) human preferences between pairs of trajectory segments, and separates learning the goal from learning the behavior to achieve it." Key claims:

1. A learned reward model can be trained from pairwise human preference comparisons rather than from a hand-coded reward function.
2. The approach can solve complex RL tasks — Atari, simulated robotic locomotion — without access to the true reward.
3. Feedback is needed on only about **0.1% of the agent's interactions** with the environment, which "reduces the cost of human oversight far enough that it can be practically applied to state-of-the-art RL systems."

## Why this is the RLHF origin

Modern RLHF as used in ChatGPT, Claude, Gemini, and every frontier post-training pipeline traces its specific algorithmic shape — preference pairs, a learned reward model, a policy optimizer (PPO) trained against the reward model — directly to this 2017 paper. When Christiano is described publicly as "the inventor of RLHF," the artifact in question is this paper.

## Why this anchors the persona

This is the empirical credential behind every Christiano stance about RLHF's limitations. When he says on the Dwarkesh Podcast (Oct 2023) that RLHF is a "basic solution" useful as a stepping stone but not a solution to alignment of powerful AI, he is critiquing his own method — which is a different kind of statement than a critic from outside making the same observation.
