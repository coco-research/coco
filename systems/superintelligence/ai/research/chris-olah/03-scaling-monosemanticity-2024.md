# "Scaling Monosemanticity" — Anthropic, May 2024

Sources:
- https://transformer-circuits.pub/2024/scaling-monosemanticity/
- https://www.anthropic.com/research/engineering-challenges-interpretability
- https://www.anthropic.com/research/toy-models-of-superposition
- https://transformer-circuits.pub/2022/toy_model/index.html

## Publication details

- **Title:** Scaling Monosemanticity: Extracting Interpretable Features from Claude 3 Sonnet
- **Date:** May 2024
- **Lead author:** Adly Templeton (et al., with Olah as senior author on the broader team)
- **Venue:** transformer-circuits.pub

## What they did

- Trained **sparse autoencoders (SAEs)** on the **middle-layer residual stream** of Claude 3 Sonnet — a then-production-scale model.
- Extracted approximately **34 million latent features** at the largest SAE size.
- Demonstrated that features were:
  - **Monosemantic** (each one corresponded to a single recognizable concept, where polysemantic neurons had previously bundled many)
  - **Steerable** — activating or suppressing the "Golden Gate Bridge feature" caused Claude to start describing itself as the Golden Gate Bridge in unrelated contexts (the famous "Golden Gate Claude" demo)
  - **Safety-relevant** — features included those representing deception, sycophancy, bias, dangerous code patterns

## Why this paper matters in the Olah arc

- **Direct continuation** of "Toy Models of Superposition" (Elhage, Hume, Olsson, Olah et al., 2022 — arXiv 2209.10652).
- Closes the loop that the Toy Models paper opened: superposition is the central reason features are hard to find; dictionary learning via SAEs is the technique that unblocks it; here is proof the technique works at production scale.
- Establishes the empirical basis for Olah's October 2023 tweet (ch402/status/1709998674087227859): "If you'd asked me a year ago, superposition would have been by far the reason I was most worried that mechanistic interpretability would hit a dead end. I'm now very optimistic. I'd go as far as saying it's now primarily an engineering problem — hard, but less fundamental risk."

## "Toy Models of Superposition" — precursor paper

- **Date:** September 14, 2022
- **Authors:** Nelson Elhage, Tristan Hume, Catherine Olsson, Neel Nanda… Christopher Olah, et al.
- **Core finding:** Networks under representation pressure store more features than they have neurons by overlapping them in **near-orthogonal directions** in activation space. This is "superposition," and it is the structural reason that individual neurons appear polysemantic.
- **Phase change:** They showed there is a phase boundary in sparsity-vs-dimensionality space where networks shift from clean monosemantic representations to dense superposed ones.
- **Safety implication:** "Superposition is deeply connected to the challenge of using interpretability to make claims about AI safety, and is a challenge to using interpretability to ensure neural networks won't perform certain harmful behaviors."

## "Engineering Challenges of Scaling Interpretability" — companion essay

- **Date:** June 13, 2024
- **Venue:** anthropic.com/research/engineering-challenges-interpretability
- Anthropic's interpretability team essay reframing the field as engineering-bound: "engineering will be one of the major bottlenecks to progress in AI interpretability — and ultimately, AI safety — research."
- Reinforces Olah's recurring 2025 framing: progress in interp is now infrastructure, distributed training over petabyte-scale activation datasets, and tooling — not waiting for a new conceptual breakthrough.

## Why "Scaling Monosemanticity" is canonical for Olah

This is the paper where the **interpretability-for-safety thesis** stops being a research bet and becomes an empirically defensible engineering program. It is the inflection point between "we hope to do this" and "we are doing this on the production model." Subsequent Olah profiles (TIME100, Forbes billionaire profile, Vatican coverage) all reference it implicitly when they say "interpretability is now scaling with capability."
