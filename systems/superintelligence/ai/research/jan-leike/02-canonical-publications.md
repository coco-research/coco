# Jan Leike — Canonical Publications

Compiled from his publications page at `jan.leike.name/publications.html`, Semantic Scholar, and arXiv.

## Foundational alignment papers

### Deep Reinforcement Learning from Human Preferences (2017)
- Authors: Paul F. Christiano, **Jan Leike**, Tom B. Brown, Miljan Martic, Shane Legg, Dario Amodei.
- Venue: NeurIPS 2017.
- arXiv: https://arxiv.org/abs/1706.03741
- Significance: The **founding RLHF paper.** Showed that pairwise human preference comparisons over short trajectory segments are enough to train Atari agents and simulated robotics policies without an explicit reward function — using feedback on less than 1% of agent interactions. Direct technical lineage to InstructGPT, ChatGPT, and Claude post-training. Co-authored with both the eventual OpenAI head of alignment (Christiano, later founder of ARC) and the eventual CEO of Anthropic (Dario Amodei) — a tight alignment-genealogy artifact.

### Scalable agent alignment via reward modeling: a research direction (2018)
- Authors: **Jan Leike**, David Krueger, Tom Everitt, Miljan Martic, Vishal Maini, Shane Legg.
- arXiv: https://arxiv.org/abs/1811.07871
- DeepMind blog mirror: https://www.deepmind.com/publications/scalable-agent-alignment-via-reward-modeling-a-research-direction
- Significance: Proposed **recursive reward modeling (RRM)** as the high-level research agenda. The frame: solve alignment by training a reward model from human feedback, then use *aligned* assistant models to help humans evaluate harder tasks, recursively scaling oversight beyond what unaided humans can judge. This is the intellectual ancestor of "automated alignment researcher" framing he carried into Superalignment and now Anthropic.

### Reward learning from human preferences and demonstrations in Atari (2018)
- Authors: Borja Ibarz, **Jan Leike**, Tobias Pohlen, Geoffrey Irving, Shane Legg, Dario Amodei.
- Venue: NeurIPS 2018.

## OpenAI / RLHF-for-LLMs era

### Recursively summarizing books with human feedback (2021)
- Authors: Jeffrey Wu, Long Ouyang, Daniel M. Ziegler, et al., incl. **Jan Leike**.
- Significance: First serious **scalable oversight demonstration** on a real LLM task — humans evaluate summaries of summaries of summaries, never reading the whole book. Direct empirical instantiation of recursive reward modeling.

### Training language models to follow instructions with human feedback (InstructGPT, 2022)
- Authors: Long Ouyang, Jeffrey Wu, Xu Jiang, et al., incl. **Jan Leike**.
- Venue: NeurIPS 2022.
- The InstructGPT paper. Established RLHF as the de facto post-training paradigm for LLMs.

## Anthropic era (2024+)

### Weak-to-Strong Generalization: Eliciting Strong Capabilities With Weak Supervision (2024)
- Authors: Collin Burns, Pavel Izmailov, Jan Hendrik Kirchner, ..., **Jan Leike** (the work was done at OpenAI's Superalignment team but published at ICML 2024).
- Venue: ICML 2024.
- Significance: The single most-cited concrete output of OpenAI Superalignment. Studied whether weak supervisor models can elicit the capabilities of stronger student models — the experimental analogue of the "human supervising superhuman AI" problem.

### Sparse autoencoder scaling (2024)
- Authors: Leo Gao, Tom Dupré la Tour, et al., incl. **Jan Leike**.
- Mech-interp adjacent; another OpenAI-era output.

### LLM Critics Help Catch LLM Bugs (2024)
- Authors: Nat McAleese, Rai Michael Pokorny, et al., incl. **Jan Leike**.
- Significance: Empirical evidence for the *evaluation-easier-than-generation* claim he keeps centering — LLM critics catch bugs human reviewers miss.

### Prover-Verifier Games improve legibility of LLM outputs (2024)
- Authors: Jan Hendrik Kirchner, Yining Chen, Harri Edwards, **Jan Leike**, et al.

### Teaching Claude Why (May 8, 2026)
- Authors: Jonathan Kutasov, Adam Jermyn (leads); Julius Steen, Minh Le, Samuel R. Bowman, Samuel Marks, **Jan Leike**, Amanda Askell, Chris Olah, Evan Hubinger, Sara Price.
- Venue: Anthropic Alignment Science blog: https://alignment.anthropic.com/2026/teaching-claude-why/
- Headline finding: Training on documents that **explain why a behaviour is right** (constitution articles, principled reasoning) generalizes better than training on demonstrations of the behaviour alone. "Difficult advice" dataset achieved comparable improvements with **28× efficiency** vs larger synthetic honeypot datasets.

### Automated Weak-to-Strong Researcher (2026)
- Anthropic Alignment Science blog: https://alignment.anthropic.com/2026/automated-w2s-researcher/
- Significance: The 2026 instantiation of his "use AI to do alignment research" agenda inside Anthropic.
