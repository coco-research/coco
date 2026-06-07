# Hyung Won Chung — Canonical Works

## Anchor talk: "Don't teach. Incentivize."

- **Venue:** MIT EI Seminar, CSAIL.
- **Date:** May 2, 2024 (talk given); YouTube upload September 2024 (delayed because OpenAI had just released o1, making the framing newly resonant).
- **YouTube:** [kYWUEV_e2ss](https://www.youtube.com/watch?v=kYWUEV_e2ss)
- **CSAIL event page:** [csail.mit.edu/event/...](https://www.csail.mit.edu/event/ei-seminar-hyung-won-chung-openai-dont-teach-incentivize-scale-first-view-large-language)
- **Stated goal in talk:** "share how I think with AI as a running example, rather than share specific technical knowledge."

### Core thesis

- Next-token prediction over a large corpus is **implicit multitask learning**.
- Models don't directly learn linguistic concepts or skills through explicit teaching; abilities emerge as a by-product of the prediction objective.
- The bitter lesson is real: **general methods that scale with compute beat domain-engineered methods**.
- Practical heuristic: "Add structures needed for the given level of compute and data available. Remove them later, because these shortcuts will bottleneck further improvement."
- Recurring failure mode: *we often fail to remove all the structure we add as we update our methods*.

This is the **incentivize-vs-teach** framing: set the right objective at scale, the model finds its own path. Don't hand-engineer the path.

## Stanford CS25 lecture: "Shaping the Future of AI from the History of Transformer Architectures"

- Stanford CS25 V4, with Jason Wei.
- YouTube: [c_9bxtyOd1o](https://www.youtube.com/watch?v=c_9bxtyOd1o) (Chung solo) and [3gb-ZkVRemQ](https://www.youtube.com/watch?v=3gb-ZkVRemQ) (with Wei).
- X announcement: [status 1800676312916656592](https://x.com/hwchung27/status/1800676312916656592), 2024-06-12.
- Quote: "AI is moving so fast that it's hard to keep up. Instead of spending all our energy catching up with the latest development, we should study the change itself."

## Cornell lecture: "AI as an Ultimate Form of Leverage"

- Cornell University, ~May 2025 (Chung's X post referred to it as "2 months ago" from July 2025).
- X post: [status 1945355238187393257](https://x.com/hwchung27/status/1945355238187393257).
- Coverage: [Global Venturing Labs](https://globalvlabs.com/ai-as-an-ultimate-form-of-leverage-hyung-won-chung/), [36kr EU](https://eu.36kr.com/en/p/3383893455698952) (2025-07-18).
- **Core argument:** Extends Naval Ravikant's leverage taxonomy (labor → capital → code/media) to a fourth category: **AI agents = permissionless compound leverage**, blending labor (does work for you) with code (copy-paste, zero marginal cost).
- Quote: "Agents that exist in pure software form have the characteristics of code — if you want 10 agents to work together, you just need to make a copy ... you don't need to get anyone's permission."

## Key papers (first or senior author)

1. **"Scaling Instruction-Finetuned Language Models"** (Chung, Hou, Longpre, Zoph, Tay et al., 2022). arXiv [2210.11416](https://arxiv.org/abs/2210.11416). **First author.** The FLAN-T5 / Flan-PaLM paper.
   - Released Flan-T5 checkpoints; Flan-T5-XL (3B) beat GPT-3 175B on MMLU (52.4% vs 43.9%).
   - Flan-PaLM 540B hit 75.2% five-shot MMLU.
   - Three scaling axes: number of tasks, model size, chain-of-thought data.

2. **PaLM** — co-author on the Pathways scaling paper at Google Brain.

3. **o1-preview / o1 / Deep Research** — foundational contributor on the OpenAI reasoning model line. His personal site lists these as career-defining contributions.

4. **"Measuring short-form factuality in LLMs"** (Wei, Karina, Jiao, Papay, Glaese, Schulman, Fedus, Chung, 2024) — SimpleQA paper. Co-author.

## Sources

- https://www.youtube.com/watch?v=kYWUEV_e2ss
- https://www.csail.mit.edu/event/ei-seminar-hyung-won-chung-openai-dont-teach-incentivize-scale-first-view-large-language
- https://www.youtube.com/watch?v=c_9bxtyOd1o
- https://www.youtube.com/watch?v=3gb-ZkVRemQ
- https://x.com/hwchung27/status/1800676312916656592
- https://x.com/hwchung27/status/1945355238187393257
- https://globalvlabs.com/ai-as-an-ultimate-form-of-leverage-hyung-won-chung/
- https://eu.36kr.com/en/p/3383893455698952
- https://arxiv.org/abs/2210.11416
