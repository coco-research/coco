# Chris Olah — "Looking Inside Neural Networks with Mechanistic Interpretability" (FAR.AI / SF Alignment Workshop, Feb 2023)

Source: https://www.far.ai/events/sessions/chris-olah-looking-inside-neural-networks-with-mechanistic-interpretability

## Talk metadata

- **Date:** February 26, 2023
- **Event:** San Francisco Alignment Workshop (FAR.AI)
- **Title:** Looking Inside Neural Networks with Mechanistic Interpretability
- **Speaker title:** Anthropic co-founder, leading interpretability research

## Why this talk is included

This is the most concentrated public statement of Olah's mechanistic-interpretability worldview prior to the "Scaling Monosemanticity" / "Biology of an LLM" era. It is still cited by his Anthropic team in 2025–2026 publications and by Lex Fridman's 2023 podcast appearance as the canonical short-form articulation. The 2025-2026 work is the technical execution of the program laid out here.

## Verbatim quotes

> "Take those neural network parameters and turn them into something like source code."

The aspirational definition of mechanistic interpretability. Treats trained weights as a compiled artifact that can be decompiled.

> "Interpretability is merely very hard but not impossible, with something existing between trivial and impossible."

The whole field-positioning move — push back on both "interpretability is solved by attention maps" optimism and "neural networks are inherently inscrutable" pessimism.

> "The impact of mechanistic interpretability for safety is going to rise or fall on this question [of superposition]."

Centers superposition as the gate. Toy Models (2022) and Scaling Monosemanticity (2024) are the technical responses to this exact framing.

> "Neural network weights, once you contextualize them, are full of structure."

The optimism case. Weights look like noise from the outside; they are organized when you look correctly. This is the rhetorical move that runs through every colah.github.io blog post.

> "We want to be able to say there don't exist features such that the model will deliberately do X."

The safety target. Note the form — it is a **universal-quantifier** safety claim about feature existence, not a behavioral evaluation. This is what distinguishes mechanistic interp from black-box red-teaming as a safety story.

> "Neural networks are full of beautiful structure if we're willing to put in the effort to find it."

The motivational frame. Olah consistently grounds his work in aesthetic-scientific terms — networks as objects of legitimate scientific inquiry, not just engineered artifacts.

## How these quotes show up in the persona

- Maps directly to the signature framings hinted at in the spec — "neural networks are objects we can understand if we look carefully enough" and "mechanistic interpretability is the path to AI safety."
- The "merely very hard but not impossible" line is the productive middle position Olah is famous for holding.
- The "rise or fall on superposition" line is what makes Toy Models, Towards Monosemanticity, and Scaling Monosemanticity the most-cited works in his canon.
