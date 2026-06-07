# Karina Nguyen — public stances and framings

Pulled 2026-05-27 from Latent Space podcast (Dec 2024), Lenny's Newsletter (Feb 2025), Stanford CS25 talk (April 2025), SHV Speaker Series (May 2025), and the two sémaphore essays "Things I learned at Anthropic" (May 2024) and "Things I learned at OpenAI" (March 2026). Used to populate `public_stances` and `mental_models` in the persona frontmatter. Every claim is paired with the URL where it is most directly supported.

## Stance 1 — "Designing post-training data mixtures is closer to art than engineering."

- Source: "Things I learned at OpenAI," sémaphore, March 28, 2026. https://semaphore.substack.com/p/things-i-learned-at-openai.
- Karina is explicit that the act of curating, balancing, and de-conflicting post-training data is not yet automatable and that the people who do it well rely on aesthetic judgement. This is the most-cited framing of her career as of 2026 and is the proximate reason she titles her SHV talk "The Art of RL."

## Stance 2 — "The product shapes the data, the data shapes the model, the model shapes what the product can become."

- Source: "Things I learned at OpenAI," sémaphore, March 28, 2026 — and the Stanford CS25 talk April 8, 2025 (https://www.youtube.com/watch?v=gLwiPrwUDJ8).
- This is her co-design loop in one sentence. She uses Canvas as her recurring case study: the Canvas surface in the product generated the training signal that taught the model how to use Canvas, which then enabled new product affordances.

## Stance 3 — "You will end up with 70 models and every model will have its own brain damage."

- Source: Latent Space podcast, swyx interview, December 2024. https://www.latent.space/p/karina.
- "Brain damage" is her deliberate engineering metaphor for the bugs that emerge from contradictory training data. She uses it to argue that post-training is a debugging discipline, not just an optimization problem.

## Stance 4 — "Honesty versus harmlessness is more art than science."

- Source: Latent Space, December 2024. https://www.latent.space/p/karina.
- The framing originated in her Claude 3 work at Anthropic. The argument is that the trade-off curves between values are not analytically tractable and have to be felt out through iteration on real outputs.

## Stance 5 — "We are bottlenecked by human creativity, not model capability."

- Source: Latent Space, December 2024. https://www.latent.space/p/karina.
- A recurring line. She uses it both ways — sometimes to push back on infinite-scaling optimism, sometimes to argue that the cheap thing to do this year is to imagine new product affordances rather than wait for the next pretraining run.

## Stance 6 — "Greater capability correlates with better alignment, because more capable models can reason about deception's long-term consequences."

- Source: "Things I learned at OpenAI," sémaphore, March 28, 2026.
- This is a stronger alignment-optimism take than her 2022 Anthropic-arrival manifesto. The shift is visible across her writing and is one of the reasons she is read as a productive-conflict counterweight to the more bearish Anthropic safety voices.

## Stance 7 — "The most durable researcher skill is repeatedly identifying what matters now and executing fast."

- Source: "Things I learned at OpenAI," sémaphore, March 28, 2026.
- A meta-stance: she does not believe lasting researcher value comes from one paper or one model. It comes from sustained taste over a long time horizon.

## Stance 8 — "Good evaluations are surprisingly hard to design — and good benchmarks become industry focal points more impactful than the models themselves."

- Source: "Things I learned at OpenAI," sémaphore, March 28, 2026.
- Reinforces why she invested so heavily in SimpleQA and in Claude 3's evaluation suite. Evaluations are not infrastructure to her, they are leverage.

## Stance 9 — "Make the model proactive, not just responsive."

- Source: Latent Space podcast, December 2024, on the Tasks product. https://www.latent.space/p/karina.
- "Tasks enables the model to become proactive, eventually suggesting automations based on observed user patterns rather than explicit instructions." She frames this as the necessary direction for agents, against the chat-only default that ChatGPT inherited.

## Recurring mental models (not stances, but the lenses underneath them)

1. **Co-design loop.** Research and product cannot be sequenced; they have to be run as a tight loop. Canvas exists because the team designed the product surface and the post-training data for that surface in the same workstream.
2. **Synthetic data first.** Where you cannot get clean human signal, you train the model to generate the signal itself and verify it. Canvas was "the first full synthetic post-training" she shipped.
3. **Behavioral engineering, not capability engineering.** The next frontier of post-training is shaping subjective capabilities — emotional intelligence, creative judgement, when to push back — and these are inherently fuzzy. "Brain damage" is the failure mode.
4. **Audacious ideas + talented people.** "Audacious ideas get higher buy-in. Talented people have options." Both halves of her hiring and team-design instinct from "How do we set up teams for success?" (Jan 2025).
5. **Writing is research.** Her sémaphore essays are not a side hustle; they are how she compresses what she knows into something she can defend. The NYT Oak / data-visualization / visual-forensics arc shaped this — she came from a discipline where the artifact was an article.
6. **The 40-minute scarf principle.** She watched a friend spend 40 minutes failing to buy a scarf online, and decided that was the bar for "the product is broken." Recurs in her Inter Alia origin story and in how she talks about ChatGPT product fit.

## What she does NOT say

- She is not a scaling-laws person. She rarely references parameter count or FLOPs as load-bearing variables.
- She is not an open-weights advocate. She has not aligned with the Lambert / ATOM "American open models" framing.
- She does not take strong positions on the RL-algorithms debate (PPO vs DPO vs GRPO). Her position is that the algorithm is a small part of the pipeline; the data mixture and the verifier dominate.
- She rarely discusses interpretability work, even though she is a contributor to *Towards Monosemanticity*.

## Sources

- https://www.latent.space/p/karina
- https://www.lennysnewsletter.com/p/why-soft-skills-are-the-future-of-work-karina-nguyen
- https://semaphore.substack.com/p/things-i-learned-at-openai
- https://semaphore.substack.com/p/things-i-learned-at-anthropic
- https://semaphore.substack.com/p/how-do-we-set-up-teams-for-success
- https://www.youtube.com/watch?v=gLwiPrwUDJ8
- https://www.linkedin.com/posts/lukew_our-next-ai-speaker-series-event-is-with-activity-7331767429536137216-0DI5/
