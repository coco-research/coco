# Substack — "Language Models in Plato's Cave"

Source: https://sergeylevine.substack.com/p/language-models-in-platos-cave
Date: June 8, 2025
Author: Sergey Levine, on "Learning and Control"

Companion piece to "Sporks of AGI." Where Sporks argues against surrogate data for robotics, Plato's Cave argues that **the LLM success story does not actually generalize** to physical intelligence the way many people assume. It is one of his most-cited 2025 essays.

## Central puzzle

Why do language models learn so much from next-token prediction, while video models learn so little from next-frame prediction, even though video contains strictly more information about the physical world?

The obvious answer ("we need more compute, more data, more parameters for video") is, in Levine's reading, wrong.

## The brain-scanner hypothesis

Levine's proposal: LLMs work because they are not learning the world. They are learning the **shape of the human mind that produced the text**.

> "LLMs might acquire their capabilities by observing the human mind and copying its function."
>
> "By acquiring compressed representations of [text], the LLM is essentially trying to reverse engineer the mental process that gave rise to it."

Text on the internet is the byproduct of a vast distributed compression — billions of humans collapsing their reasoning into language. An LLM that fits this distribution is reverse-engineering the cognition that produced it, not the physics that the cognition is about.

Video, by contrast, is a recording of the world itself, not of a mind compressing the world. A video model has to learn physics, causality, object permanence, and dynamics on its own. That is a strictly harder problem than copying the artifact of already-compressed reasoning.

## Plato's cave

The metaphor: LLMs inhabit Plato's cave, watching shadows of human cognition projected onto text. They have not seen the sun. Their capabilities are bounded by what humans have already thought hard enough about to write down.

## Implication for AGI

> "AI systems will not acquire the flexibility and adaptability of human intelligence until they can actually learn like humans do."

For Levine, this implies that scaling text-only LLMs has a ceiling: the ceiling of human cognition encoded in writing. To go past it, models need to learn from the world directly, with their own actions, in feedback loops.

## Implication for robotics

This is where the essay turns load-bearing for his broader research program. A Mars rover does not have internet text in its operating environment. Neither does a robot in a new home, a new factory, or a new disaster zone. None of these settings can be solved by reading more of the internet.

The only path to robot intelligence that generalizes outside the human-text manifold is:

1. Real-world data, collected by real robots, in real environments.
2. RL or autonomous self-improvement on top of that base.
3. Treating internet text as the **scaffolding** (priors on language, semantics, object names), not the substrate.

## Why this essay matters for the persona

- It is his crispest articulation of why the LLM playbook does not transfer to robotics by analogy.
- It implicitly criticizes labs that bet on text-only scaling as a path to embodied intelligence.
- It complements "Sporks of AGI" — together they say: you cannot fake real-world data with simulation, and you cannot substitute for real-world data with internet text.
- The "brain scanner" framing is now widely cited in 2025–2026 ML discourse and is a recognizable Levine signature.

## Quotable lines

- "LLMs might acquire their capabilities by observing the human mind and copying its function."
- "By acquiring compressed representations of this text, the LLM is essentially trying to reverse engineer the mental process that gave rise to it."
- "AI systems will not acquire the flexibility and adaptability of human intelligence until they can actually learn like humans do."
