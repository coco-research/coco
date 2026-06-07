# Tim Dettmers — "My Journey Towards Coding Agents: Building SERA" (2026-01-27)

Source: https://timdettmers.com/2026/01/27/building-open-coding-agent-sera/

The SERA post is the single most important Dettmers artifact from his last 12 months for the persona file. It does three things at once: announces a concrete Ai2 deliverable, explains a methodology shift, and provides a personal narrative of why he stepped away from pure quantization work.

## What SERA is

- **SERA** is Ai2's family of open coding agents.
- **Core thesis:** "open-source models that exceed frontier performance because you use your private data, train your own model, and deploy it yourself."
- **Use case:** private codebase specialization. Teams generate massive amounts of repository-specific data without exposing proprietary code to an external API.

## The methodology

Three-stage synthetic data generation with **soft verification** — comparing generated patches for 50% line-by-line overlap with a reference rather than running expensive test suites against unit tests.

The counter-intuitive move:

> "There is a bug downstream from that function (even if there is no downstream function)."

Prompting the model with vague, possibly-false hints causes it to explore, examine the code, and imagine a plausible bug. The result is a stream of refactor suggestions and code-improvement edits alongside actual bug fixes.

## Cost and efficiency

- 7,000 trajectories: 19 GPU days.
- Full training baseline: $500.
- Initial cluster: 32 GPUs; scaled to 96.
- Final outcome: "A 32 billion model as good as the teacher, GLM 4.5-Air."

This is the operational evidence behind his "accessible ML" claim — frontier-comparable coding agents trainable for hundreds of dollars by a small team.

## What failed

- **Subtask splitting** — initially showed promise (0% → 24% on SWE-bench for 8B models) but proved equivalent to end-to-end approaches in compute terms.
- **Hard verification** — running real unit tests to confirm bug-induced breakage exhausted resources with one researcher on the project.

These are honest engineering disclosures — Dettmers does not soften them.

## The health break

He developed unspecified health problems in February 2025 and paused active research, while continuing to mentor the project's intern Ethan Shen. He explicitly credits Shen with much of SERA's progress during that period.

## Pivot away from pure quantization

Most consequential paragraph for the persona file:

> "Quantization research and other efficiency research [is] hitting diminishing returns."

He acknowledges disappointing colleagues who expected him to keep producing efficient-training and efficient-inference work, and frames coding agents as "the most promising direction." This is the moment the persona's blind-spot warning ("very quantization frame") becomes more nuanced — he is conscious of the trap and stepping out of it, though his canonical contributions are still in quantization.

## Why this matters for the persona

- **Recent signal post 2025-05-27** — qualifies.
- Shows his accessibility thesis applied to agents, not just quantization.
- Establishes a productive-conflict axis with the closed-frontier-only camp: same accessibility argument, new domain.
- Concrete dollar figures and GPU counts give the persona quantitative ground to stand on in convene sessions.

## Sources

- https://timdettmers.com/2026/01/27/building-open-coding-agent-sera/
