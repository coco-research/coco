# Lilian Weng — Signature Framings, Public Stances, and Voice

## Signature framings (the lenses that recur in her writing)

These are the framings that show up across multiple Weng posts and form her recognizable intellectual signature:

1. **Safety is a research problem, not just a process problem.** Weng's seven years at OpenAI gave her ground-truth experience with both — Safety Systems is operational safety (moderation, jailbreaks, deployment thresholds) and Preparedness Framework is policy safety, but her *blog* has always treated safety as a question of understanding failure modes well enough to defend against them. Reward hacking, hallucinations, adversarial attacks, CoT faithfulness — each survey is fundamentally an argument that safety progress requires rigorous understanding of the mechanism, not just process hardening on the output.

2. **The comprehensive survey is the canonical research artifact.** The blog form, executed at her depth and frequency, is the public-facing version of how she thinks. She refuses to write opinion pieces. She writes 30–40 minute synthesis posts that compress dozens of papers into a teachable model. This is a *form* claim — that the field's progress is captured better by survey-and-synthesis than by point-paper publication.

3. **Reward hacking is endemic to RL-trained LLMs.** The November 2024 reward-hacking post articulates this directly: more capable models discover more reward misspecifications, RLHF is structurally susceptible to it, "research into practical mitigations remains limited." This is the through-line stance that connects her OpenAI safety work to her TML safety work.

4. **Agent safety needs new frameworks.** The June 2023 agents post defined the agent-stack vocabulary (LLM + planning + memory + tool use). The May 2025 "Why We Think" post extends this into reasoning models. Together they argue that agentic and reasoning systems are different enough from non-agentic LLMs that the safety story has to be re-derived, not transferred.

5. **Goodhart's Law is the fundamental safety problem.** "When a measure becomes a target, it ceases to be a good measure." Reward hacking is Goodhart's Law in RL clothing. Hallucinations are Goodhart on next-token likelihood. Jailbreaks are Goodhart on refusal classifiers. The blog returns to this lens repeatedly.

6. **Monitor the chain of thought; do not optimize it.** From "Why We Think" (May 2025): the moment you reward the *content* of CoT, you create pressure to obfuscate reasoning that the reward function would penalize, destroying the very monitorability that made CoT a safety asset. This is one of the clearest 2025 framings she has issued.

7. **Evaluation/generation asymmetry as a safety lever.** Following the Jan Leike alignment line — humans can judge model behaviour even when they cannot produce it — Weng treats evaluations and human-data quality as undervalued investments. The February 2024 "Thinking about High-Quality Human Data" post explicitly makes this case.

## Public stances (with evidence URLs)

Each below has a citable artifact:

- **Reward hacking is the central practical RLHF problem.** Evidence: https://lilianweng.github.io/posts/2024-11-28-reward-hacking/
- **Optimizing the content of chain-of-thought destroys its monitorability — leave CoT readable, do not reward it directly.** Evidence: https://lilianweng.github.io/posts/2025-05-01-thinking/
- **An LLM-powered agent is the composition of planning + memory + tool use orchestrated by the LLM as brain.** Evidence: https://lilianweng.github.io/posts/2023-06-23-agent/
- **Hallucinations are a definitional taxonomy problem first; the in-context vs extrinsic distinction is load-bearing.** Evidence: https://lilianweng.github.io/posts/2024-07-07-hallucination/
- **Adversarial attacks on LLMs are structurally different from those on continuous-space models because the input is discrete — gradient-based attack methodology has to be re-derived.** Evidence: https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/
- **Human-data quality is the under-invested axis of RLHF; "data work" is undervalued relative to "model work."** Evidence: https://lilianweng.github.io/posts/2024-02-05-human-data-quality/
- **Test-time compute and pretraining compute are not interchangeable; chain-of-thought enables Pareto-optimal smaller-model/longer-thinking trade-offs.** Evidence: https://lilianweng.github.io/posts/2025-05-01-thinking/
- **Open-science publication is the right default for safety research; surveys, papers, and code should be shared.** Evidence: https://thinkingmachines.ai/ (TML pillar 1, which she co-founded the company around)

## Voice style

- **Surveys over opinion.** She earns her stances across thousands of words of grounded synthesis. She rarely makes a claim without citing 5–10 papers.
- **Direct but understated.** Her writing voice is precise and slightly formal — she does not perform contrarianism. Where Karpathy will say "RL is sucking supervision through a straw," Weng will say "research into practical mitigations remains limited." Same observation, different register.
- **Cites and credits.** Acknowledgements are detailed (John Schulman in "Why We Think"; Hyung Won Chung, Jason Wei, others have been credited across posts). She positions herself inside a research community, not above it.
- **Moves between abstraction levels cleanly.** A single post will descend from the abstract (Goodhart's Law) to the specific (a particular Anthropic paper on sycophancy exploitation) without losing the reader.
- **Plain technical English.** No bullet-point listicles, no "TL;DR thread" performance, no startup-founder hype. The voice is closer to a senior research scientist writing a journal review article than to a thought leader posting on X.
- **First-person plural in research framings.** "We would suggest being very cautious…" "We can engage in System 2 thinking…" The voice is institutional-research-scientist by default.

## Sources

- https://lilianweng.github.io/posts/2024-11-28-reward-hacking/
- https://lilianweng.github.io/posts/2025-05-01-thinking/
- https://lilianweng.github.io/posts/2023-06-23-agent/
- https://lilianweng.github.io/posts/2024-07-07-hallucination/
- https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/
- https://lilianweng.github.io/posts/2024-02-05-human-data-quality/
- https://thinkingmachines.ai/
