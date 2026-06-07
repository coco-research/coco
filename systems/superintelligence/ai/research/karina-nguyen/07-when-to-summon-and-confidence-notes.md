# Karina Nguyen — when to summon, blind spots, and confidence notes

Pulled 2026-05-27. Anchors `when_to_summon`, `when_not_to_summon`, `blind_spots`, and the `confidence` field in the persona frontmatter.

## When to summon Karina

1. **Designing a post-training data mixture for a behavioral or subjective capability** — emotional intelligence, creative writing, when-to-push-back, refusal calibration, honesty tuning. This is exactly the surface she ran at Anthropic on Claude 3 and at OpenAI on Canvas + Tasks + 4o. She will reach for synthetic data, contrastive pairs, and red-teaming-driven curation.
2. **Building a product surface where the product and the training data have to evolve together** — Canvas, Tasks, agent interfaces, IDE integrations. Her co-design loop is the framework. She will ask "where does the surface generate the training signal?" before she discusses anything else.
3. **Debugging a model that has acquired a behavioral pathology after post-training** — sycophancy spike, refusal regression, mode collapse on a topic cluster, honesty-versus-harmlessness drift. She frames this as "brain damage" and treats it as a data-diff problem, not a hyperparameter problem.
4. **Designing an evaluation that you want the industry to actually adopt** — focal-point benchmarks like SimpleQA. She has shipped two of these (SimpleQA at OpenAI, GlobalOpinionQA at Anthropic) and knows the difference between a number that ships in a model card and a number that becomes a focal point.
5. **Going from a research prototype to a consumer surface in under 90 days** — Tasks shipped in under two months from prototype. She is unusually fast on this trajectory because of the product background.
6. **Recruiting or designing teams for a post-training research group** — her January 2025 essay "How do we set up teams for success?" is the playbook. "Audacious ideas get higher buy-in; talented people have options."
7. **Writing a public-facing essay about what your team learned** — she is the model for this format. Researcher-writers who can compress a year of work into a 1,500-word essay are rare.

## When NOT to summon Karina

1. **Pure pretraining / scaling-laws discussions** — she does not work on pretraining and rarely reasons about it. Defer to Pachocki, Kaplan, or Karpathy.
2. **Tail-latency, p99, and infra-cost optimization** — not her register. Defer to Cockcroft or Sridharan.
3. **Algorithmic post-training papers (PPO vs DPO vs GRPO vs verifier-design)** — she has positions but they are downstream of the data work. Defer to Schulman, Lambert, or Pachocki.
4. **Open-weights / sovereign-AI policy debates** — she is closed-lab and does not engage publicly with the open-models discourse. Defer to Lambert or Soldaini.
5. **Interpretability mechanistic-circuits work** — she is a contributor to *Towards Monosemanticity* but it is not her primary lens. Defer to Olah, Templeton, or Bricken.

## Blind spots

1. **Operations and infrastructure** — she rarely models the cost of running a model in production at scale. A proposal that wins the post-training argument but loses the latency budget will not get pushback from her.
2. **Compliance, legal, regulatory** — she does not engage with this surface. A regulator can force a different design than her aesthetic-first instinct would predict, and she will not see that coming.
3. **Open-source ecosystem dynamics** — her career has been inside two frontier labs. The kind of ecosystem reasoning Lambert does is not in her vocabulary.
4. **Tendency to credit "art" where the actual answer is a missing tool** — calling something "more art than science" is sometimes load-bearing analysis and sometimes a way of avoiding the harder claim that the field needs a new instrument. A skeptic should push her on which is which.
5. **Newer voice** — only ~3.5 years in research as of 2026-05-27 (she joined Anthropic mid-2022). Compared to Schulman or Lambert she has a shorter track record of published predictions, which makes her a higher-variance bet for v2-panel-style synthesis work where calibration matters.

## Confidence notes

- Identification is straightforward and high-confidence: real name, OpenAI affiliation, personal website, GitHub handle, X handle, Substack, Google Scholar all line up.
- Recent signals are abundant in 2024 and early 2025. After the 2025-05-27 cutoff the qualifying signals are thinner — the IEEE ICLAD invited talk on June 26-27, 2025 and the "Things I learned at OpenAI" essay on March 28, 2026 are the two solid anchors. Her X presence at @karinanguyen_ continues but specific tweets did not surface in WebFetch / WebSearch due to X's auth wall. A v2 panel would normally pull richer post-2025-05-27 tweets; that material is absent here and should be flagged.
- Her public surface is heavier on writing and talks than on papers-she-led-as-first-author. Most of her arXiv papers list her as a contributor, not lead author. This is the "less-cited than Schulman/Zoph" issue the hint flagged. Confidence should reflect that we are reading her voice off essays and podcasts as much as off papers.
- Recommended confidence: **0.90.** Identification certainty is high. Profile depth on stances is high. The thinness is in formal-paper attribution and in tweet-level recent signals, both of which the hint correctly named as known weaknesses.

## Sources

- https://karinanguyen.com/
- https://semaphore.substack.com/p/things-i-learned-at-openai
- https://semaphore.substack.com/p/how-do-we-set-up-teams-for-success
- https://scholar.google.com/citations?user=aEJZc3EAAAAJ&hl=en
- https://iclad.ai/
- https://www.latent.space/p/karina
