# Aya Program — Multilingual AI for the Global Majority

Source documents:

- https://cohere.com/research/aya
- https://arxiv.org/abs/2412.04261 — Aya Expanse (December 2024)
- https://arxiv.org/pdf/2402.07827 — original Aya Model paper (February 2024)
- https://huggingface.co/CohereLabs/aya-expanse-8b
- https://huggingface.co/CohereLabs/aya-expanse-32b
- https://venturebeat.com/ai/cohere-for-ai-launches-open-source-llm-for-101-languages
- https://fortune.com/2025/03/17/cohere-ai-sara-hooker-gen-ai-languages/
- https://www.axios.com/2024/02/13/open-source-ai-languages

## Program scope

The Aya program is the largest open multilingual AI initiative produced under Hooker's leadership at Cohere For AI / Cohere Labs.

- Original Aya model and Aya Dataset (announced February 2024): instruction-tuned open multilingual LLM covering 101 languages, assembled in collaboration with **over 3,000 researchers from 119 countries**.
- Aya 23 (mid-2024): mid-size multilingual model release.
- Aya Expanse 8B and 32B (October–December 2024): "state-of-the-art multilingual family of models to bridge the language gap in AI" per the arXiv paper (2412.04261, December 6, 2024). 41+ co-authors including Hooker as senior author.
- Aya Vision (early 2025): adds vision-language capabilities across 23 languages.

## What is novel about it

Aya is not just "we trained a bigger multilingual model." The novelty is institutional:

1. **Crowd-sourced multilingual data.** The Aya Dataset was assembled by a globally distributed volunteer research network rather than purchased from data vendors or scraped from the web. This is the operational embodiment of the global-majority thesis.
2. **Open weights, open dataset, open evaluation.** Models are on Hugging Face under permissive licenses. The dataset is public. Evaluation methodology is documented.
3. **Disaggregated evaluation.** Aya papers report performance per language rather than averaging, which is the disparate-impact discipline from the compression work applied at multilingual scale.

## How Hooker frames it publicly

From the Fortune profile (March 17, 2025) and the Axios coverage (February 13, 2024): Hooker frames Aya as both a moral and a commercial argument. Morally, AI that works in 100 languages serves the global majority rather than the English-speaking elite. Commercially, an enterprise AI vendor whose products work across all of a multinational customer's geographies has a structural advantage over English-only competitors.

She repeatedly emphasizes that 3,000 volunteer researchers from 119 countries is itself the proof: there is no scarcity of talent or interest in non-English AI work; the scarcity is institutional access to compute and to research infrastructure.

## Why this is the operationalization of the Hardware Lottery thesis

If the Hardware Lottery essay was the diagnosis (research wins by hardware fit, not merit, and that gap is widening), the Aya program is the prescription: build the institution that explicitly funds the unfavored direction. Multilingual non-English AI was unfavored because data, evaluation, and compute infrastructure had all been built around English. Aya is a deliberate counter-investment.

## Continuity into Adaption Labs

When Hooker frames Adaption Labs as "the next breakthrough" coming from "extremely efficient adaptation," the Aya history is the proof point she leans on: Aya demonstrated that sophisticated data curation and training technique can compensate for raw model size across dozens of languages. Adaption Labs generalizes the move from "multilingual coverage with smaller models" to "task-specific coverage with smaller adaptive models."

## Recent signal

"The Bitter Lesson Learned from 2,000+ Multilingual Benchmarks" (arXiv 2504.15521, April 2025) is a Cohere Labs paper from her late period at the lab. It collects and annotates 2,024 multilingual-benchmark studies from 148 countries. The title is a deliberate reframe of Sutton's "Bitter Lesson": the bitter lesson of multilingual evaluation is that the benchmarks themselves do not serve the global majority, and so models that look strong on the benchmarks may still be failing the populations they claim to serve.
