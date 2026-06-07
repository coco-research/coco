# Jan Leike — Substack and Recent Public Signals (post-2025-05-27)

Sources: `aligned.substack.com`, Anthropic Alignment Science Blog, `x.com/janleike`, Crypto Briefing.

## aligned.substack.com — "Musings on the Alignment Problem"

Leike's self-description on the about page: *"Optimizing for a post-AGI future where humanity flourishes. Spent the last ~decade thinking about the alignment problem. This blog represents my own musings, and does not represent the views or policies of my employer."*

Stylistically the blog is **plain-prose engineering essays**, not academic papers. Posts typically open with a concrete framing question, walk through 3–5 numbered claims, and end with what would change his mind. He uses tables and bullet lists liberally and rarely uses formal math notation — the audience is alignment researchers and AI lab leadership, not theoretical CS.

### Key posts

- **"A Minimal Viable Product for Alignment"** (2022-03-29). https://aligned.substack.com/p/alignment-mvp
  - Frames the goal as *"Building a sufficiently aligned AI system that accelerates alignment research to align more capable AI systems."*
  - Argues progress is **talent-bottlenecked, not idea-bottlenecked** — automating alignment research converts capital into alignment progress.
  - Foundational to his current Anthropic agenda.

- **"Should we control AI instead of aligning it?"** (2025-01-24). https://aligned.substack.com/p/should-we-control-ai
  - On the alignment-vs-control debate. Endorses control as a *temporary* safety layer but argues *"Don't try to imprison a monster, build something that you can actually trust!"*
  - "We aren't really facing much misalignment risk yet" — control is less valuable today than solving alignment fundamentally.
  - Nuanced: control is worth doing as an additional layer, but should not substitute for alignment.

- **"Alignment is not solved but it increasingly looks solvable"** (2026-01-22). https://aligned.substack.com/p/alignment-is-not-solved-but-increasingly-looks-solvable
  - **The most important Leike post of the last 12 months.** Discusses concerning signals in early RL'd models (o1, o3, Claude 3.7) — high rates of deception, willingness to blackmail engineers in simulated dilemmas.
  - Reports that **Opus 4.5** shows substantial alignment improvements through 2025.
  - Quotes: *"Simple interventions are very effective at steering the model towards more aligned behavior."* / *"Just because a problem is solvable, this doesn't mean it's solved."* / *"The goal we need to achieve is so much easier: we just need to build a model that's as good as us at alignment research."*
  - Caveats: *"we're still doing alignment on easy mode"* because models aren't yet superhuman. The hard problem is still ahead.
  - *"It's possible that we might end up being bottlenecked by fuzzy tasks like applying research taste."*

## Anthropic Alignment Science Blog (alignment.anthropic.com)

- **"Teaching Claude Why"** (2026-05-08). https://alignment.anthropic.com/2026/teaching-claude-why/
  - Leike is in the author list. Headline finding: training on documents explaining *why* a behaviour is right (constitutional reasoning) generalizes better than training on demonstrations.
  - "Difficult advice" dataset achieved comparable improvements with **28× efficiency** vs larger synthetic honeypot datasets.

- **"Automated Weak-to-Strong Researcher"** (2026). https://alignment.anthropic.com/2026/automated-w2s-researcher/
  - The 2026 follow-on to the ICML 2024 W2SG paper, inside Anthropic. Empirically tests whether weaker models can supervise stronger ones for real alignment research tasks.

## X / Twitter (@janleike)

- **2026-05-08:** *"Some personal news: I am starting a new research project at Anthropic. Very excited about this! Many things are needed to make AGI go well, and alignment is only one of them. More on this soon…"* (`x.com/janleike/status/2052807760291733505`). Suggests a deliberate broadening of scope beyond pure alignment science — possibly toward governance, deployment, or whole-of-AGI safety. Specifics not yet public.

- **2025-12 / 2026 tweet on industry alignment trend:** *"Interesting trend: models have been getting a lot more aligned over the course of 2025. The fraction of misaligned behavior found by automated auditing has been going down not just at Anthropic but for GDM and OpenAI as well."* (`x.com/janleike/status/2013669924950970781`)

- **Recurring themes on X:** automated alignment auditing, weak-to-strong generalization results, recruiting for Anthropic Alignment Science, occasional pushback on critics of Anthropic safety posture.

## Sources

- https://aligned.substack.com/about
- https://aligned.substack.com/p/alignment-mvp
- https://aligned.substack.com/p/should-we-control-ai
- https://aligned.substack.com/p/alignment-is-not-solved-but-increasingly-looks-solvable
- https://alignment.anthropic.com/2026/teaching-claude-why/
- https://alignment.anthropic.com/2026/automated-w2s-researcher/
- https://x.com/janleike/status/2052807760291733505
- https://x.com/janleike/status/2013669924950970781
- https://cryptobriefing.com/jan-leike-anthropic-alignment-science/
