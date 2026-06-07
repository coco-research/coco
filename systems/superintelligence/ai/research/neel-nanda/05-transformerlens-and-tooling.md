# TransformerLens and Neel Nanda's tooling stance

## TransformerLens

- Repo: https://github.com/TransformerLensOrg/TransformerLens
- v3.2.1 released 2026-05-09
- ~3.5k GitHub stars, ~574 forks
- Created by Neel Nanda after leaving Anthropic's interpretability team. Current maintainers: Bryce Meyer and Jonah Larson.

### What it does

A Python library for mechanistic interpretability of GPT-2-style transformer language models. Core capabilities:

- Loads 50+ open-source models with a unified `HookedTransformer` API
- Exposes activations at every layer (attention pre/post, MLP pre/post, residual stream)
- Caches activations at any layer for offline analysis
- Hook-based editing: replace, ablate, patch activations during the forward pass
- Activation patching, attribution patching, path patching for causal interventions
- Supports experimental Mamba / SSM architectures

### Why it matters

Before TransformerLens, mech interp work was bespoke per-paper. Each researcher rebuilt the hooks layer. TransformerLens collapsed that into shared infrastructure — the de facto interpretability stdlib. Has enabled:
- Grokking circuit discovery (Nanda et al. 2023)
- Induction-head studies
- Othello-GPT emergent-world-representation analysis
- Hundreds of MATS / ARENA student projects

### v2.0 split

HookedSAETransformer was moved out into a separate library, **SAELens**, around 2024. This reflects the modular evolution of the ecosystem — SAE work has its own tooling now.

## Stance: tooling is research

Neel's repeated implicit claim is that **building the shared instrument is itself research output**. TransformerLens is more cited (and arguably more impactful) than any single mech-interp paper of the same period. This anchors a community-building theory of change: the field grows faster when the tooling is shared.

## Related infrastructure he champions

- **SAELens** — sparse autoencoder companion library (community-maintained)
- **Gemma Scope / Gemma Scope 2** — open SAE checkpoints on Gemma 2 / 3 from DeepMind
- **Neuronpedia** — community SAE feature browser (he amplifies it on X)

## Open-source posture

Everything Neel touches publicly is released under permissive licenses. He has explicitly framed this as the moral default — interpretability that lives behind closed doors at one lab doesn't help the safety community.
