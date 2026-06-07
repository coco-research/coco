# Hyung Won Chung — Public Stances & Mental Models

Every stance below is anchored to a citable URL. None inferred.

## Public stance 1: Don't teach, incentivize

- **Claim:** Hand-engineered teaching of skills is dominated by setting the right objective at scale. "Incentivize the model with the right objective; abilities emerge as a by-product of the prediction loss."
- **Evidence:** MIT EI Seminar talk "Don't teach. Incentivize." May 2, 2024. [YouTube](https://www.youtube.com/watch?v=kYWUEV_e2ss).
- **Strong form:** This is Chung's signature framing. He delivered it at MIT, then at Stanford CS25, then at Cornell — restated and extended each time.

## Public stance 2: The bitter lesson is the strongest predictor in ML — general methods that scale with compute win

- **Claim:** Sutton's bitter lesson is not just a historical observation; it's a working heuristic. Domain-specific structures should be treated as scaffolding to be removed once the model has enough compute and data to do the same work itself.
- **Evidence:** Chung's framing in MIT EI talk and Stanford CS25, summarized in [obviouslywrong.org — Bitter Lesson is Misunderstood](https://www.obviouslywrong.org/p/the-bitter-lesson-is-misunderstood) and [rlancemartin.github.io — Learning the Bitter Lesson](https://rlancemartin.github.io/2025/07/30/bitter_lesson/), both of which directly cite Chung's "add structure, then remove it" reframing.
- **Concrete quote (paraphrased from talks):** "Add structures needed for the given level of compute and data available — and then remove them later, because these shortcuts will bottleneck further improvement."

## Public stance 3: Reasoning is unlocked by inference-time compute, not by teaching steps

- **Claim:** o1 / o3 lineage validates that letting the model spend more compute at inference is a more general lever than teaching chain-of-thought via supervised fine-tuning.
- **Evidence:** Chung's [hwchung2.github.io](https://hwchung2.github.io/) bio lists o1-preview, o1, and Deep Research as foundational contributions framed under reasoning/agents. The September 2024 timing of his MIT EI talk upload, in his own words, was "timely as OpenAI had just released o1" — the framing was retrospectively validated by the o-series.

## Public stance 4: Instruction tuning is what bridges raw generative models to useful systems

- **Claim:** Instruction fine-tuning is the scaling axis people most under-invest in. Scaling tasks, model size, and CoT data simultaneously produces transferable improvements across benchmarks.
- **Evidence:** First-author paper [arXiv 2210.11416 — Scaling Instruction-Finetuned Language Models](https://arxiv.org/abs/2210.11416), 2022. Released Flan-T5 and Flan-PaLM checkpoints; Flan-T5-XL (3B params) outscored GPT-3 175B on MMLU. This is the canonical evidence base.

## Public stance 5: AI agents are a fourth class of leverage — permissionless and compound

- **Claim:** Naval's labor / capital / code/media taxonomy is incomplete; AI agents are a new category that blends labor and code, with zero marginal cost replication and no permission requirement.
- **Evidence:** Cornell lecture "AI as an Ultimate Form of Leverage" (May 2025). [globalvlabs.com](https://globalvlabs.com/ai-as-an-ultimate-form-of-leverage-hyung-won-chung/), [36kr](https://eu.36kr.com/en/p/3383893455698952).
- **Direct quote:** "Agents that exist in pure software form have the characteristics of code — if you want 10 agents to work together, you just need to make a copy. You don't need to get anyone's permission."

## Public stance 6: Compute and long-term focus matter more than headline model launches

- **Claim:** The decision criteria for an AI research lab worth joining are compute access and a long-horizon mandate. Headline launches are a downstream output.
- **Evidence:** His own X post on joining Meta Superintelligence Labs: "Very excited about the compute and long term focus of the new lab." [x.com/hwchung27/status/1956092401854111934](https://x.com/hwchung27/status/1956092401854111934), 2025-08.

## Mental models

1. **Next-token prediction as implicit multitask learning.** Skills are downstream of the prediction objective, not upstream.
2. **Add structure for current compute, remove it as compute grows.** Every architectural shortcut has a half-life.
3. **The hidden trap: we fail to remove old structure as methods update.** Most "novel" architecture work is reinventing scaffolding that scale would dissolve.
4. **Levers compound when they don't need permission.** AI agents are valuable precisely because they inherit code's permissionless-copy property.
5. **Inference compute is the new scaling axis** — once pretraining plateaus, you scale at test time (o1 line).
6. **Cost is a research input, not an afterthought.** Per-tenant budget caps and batch-mode discounts (50% off) are first-class design constraints, not finance-team concerns. (This is the framing that made him "Cell E cost owner" in the Marvin v2 panel.)

## Voice signature

- Speaks in **paradigm-shift terms** ("we should study the change itself") rather than benchmark deltas.
- Repeats short, declarative slogans: "Don't teach. Incentivize." "Add structure, remove structure." "Compute and long-term focus."
- Comfortable saying the field "fails to" do something. Diagnostic, not boosterish.
- Speaks from his own pivot story (mechanical engineering → ML) — pedagogical without being preachy.
- Less first-person essayist than Karpathy or Wei; thinking surfaces in lectures and tweets, not blog posts.
