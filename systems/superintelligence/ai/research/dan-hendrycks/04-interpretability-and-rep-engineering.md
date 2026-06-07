# Hendrycks on Interpretability and Representation Engineering

Primary sources:
- "Representation Engineering: A Top-Down Approach to AI Transparency," Zou, Phan, Chen, ... Hendrycks, arXiv:2310.01405. https://arxiv.org/abs/2310.01405 (initial Oct 2, 2023; revised March 3, 2025)
- "The Misguided Quest for Mechanistic AI Interpretability," Hendrycks, AI Frontiers, May 15, 2025. https://ai-frontiers.org/articles/the-misguided-quest-for-mechanistic-ai-interpretability
- Glitchwire coverage, https://glitchwire.com/news/rethinking-mechanistic-interpretability-in-ai/

## The core claim

Mechanistic interpretability — the program of reverse-engineering neural networks by labeling individual neurons and circuits — assumes that AI systems can be understood like simple physical mechanisms. Hendrycks calls this the "clockwork view" and argues it is fundamentally wrong for systems of LLM complexity.

Direct quote (AI Frontiers, May 2025):
> "More complex systems are more powerful. But they are also more opaque."
> "Despite substantial efforts over the past decade, the returns from interpretability have been roughly nonexistent."

## The track record he cites

He catalogs interpretability methods that promised but did not deliver:
- Feature visualizations (2015).
- Saliency maps (later shown to barely change when intermediate layers were randomized).
- BERT interpretability claims that did not transfer when the dataset changed.
- Sparse autoencoders, which he notes DeepMind has recently deprioritized.

## The compression problem

His key conceptual move: reducing a terabyte-scale model to a human-graspable explanation necessarily loses the edge cases — and the edge cases are where safety risks live. So "we understand this model" by mechanistic methods always means "we understand it on the average case," which is precisely the wrong distribution for catastrophic-risk reasoning.

## What he advocates instead — Representation Engineering (RepE)

- Operate on population-level representations across many neurons, not on individual neurons.
- Inspired by how scientists study other complex systems (meteorology, biology, psychology) without claiming to understand every constituent particle.
- Practical demonstrated results from the original 2023 paper and 2025 follow-ups:
  - Steering models to be more honest.
  - Steering models to refuse dual-use queries (bio, cyber).
  - "Unlearning" dual-use concepts at the representation level.
- Survey of 130+ follow-up papers: "Taxonomy, Opportunities, and Challenges of Representation Engineering for Large Language Models," arXiv:2502.19649 (2025).

Direct quote:
> "We do not need mechanistic understanding to make progress on safety."

## Tension with the interpretability community

This is genuinely contested. Anthropic's interpretability team (Chris Olah, Neel Nanda, and collaborators) continues to invest heavily in mechanistic interpretability with sparse autoencoders. Hendrycks' May 2025 essay is read in the field as a direct challenge to Anthropic's interpretability program. Note: Hendrycks pairs well with Olah and Nanda on the question of safety-via-internals, but they sharply disagree on which level of internal description is the right one.

## What this tells us about Hendrycks' research worldview

- He is more empirical than mechanistic — "does it actually steer behavior in the safety direction we want?" beats "does it produce a satisfying mechanical explanation?"
- He is willing to declare a research program a failure publicly and propose a successor, even when that program has prominent advocates in adjacent labs.
- He treats safety as a behavioral and operational property of deployed systems, not a property to be derived from white-box understanding.
