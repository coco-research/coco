# Lilian Weng — Blog as Canonical Research Artifact

`lilianweng.github.io` ("Lil'Log") is one of the most-cited individual research blogs in the LLM / RL / safety field. Posts there function the way arXiv papers do — researchers reference them in literature reviews, cite them via BibTeX, and treat them as load-bearing source material for graduate-level coursework.

## The pedagogical contract

Weng's posts are survey-length (most are 20–40 minute reads), heavily diagrammed, and dense with paper citations. They are not opinion pieces. The implicit contract is: *if you read this post, you will leave with a unified, paper-grounded mental model of the topic*. This is a different artifact-type from Karpathy's "build it from scratch in 200 lines" pedagogical contract, but it is the same philosophical move — the writer compresses the public literature into a teachable artifact that they themselves had to construct to understand the field.

Karpathy's unit of pedagogy is **lines of code**. Weng's unit of pedagogy is **the comprehensive survey post**. Both are signature pedagogical contracts of the field's modern era.

## Canonical posts

### 2023

- **"Prompt Engineering"** (March 15, 2023). Survey of prompt-engineering techniques. URL: `https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/`. Cited heavily during the 2023 prompt-engineering boom.
- **"LLM Powered Autonomous Agents"** (June 23, 2023). The agent-stack canonicalization. URL: `https://lilianweng.github.io/posts/2023-06-23-agent/`. Defined the three-component decomposition: **planning + memory + tool use** orchestrated by an LLM "brain." Companion tweet: "Agent = LLM + memory + planning skills + tool use. This is probably just a start of a new era :)" (June 26, 2023, X). The post became the canonical reference for the entire agent-framework boom of 2023–2024.
- **"Adversarial Attacks on LLMs"** (October 25, 2023). URL: `https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/`. Survey of jailbreak prompts, gradient-based attacks, transfer attacks, and the structural difficulty of adversarial robustness in discrete-token models.

### 2024

- **"Thinking about High-Quality Human Data"** (February 5, 2024). On annotation quality, RLHF labeling cost, and the under-investment of the field in data-quality work.
- **"Diffusion Models for Video Generation"** (April 12, 2024). Temporal-consistency survey extending the older diffusion-models post into video.
- **"Extrinsic Hallucinations in LLMs"** (July 7, 2024). Taxonomy distinguishing in-context (the model can't access information present in its context) and extrinsic (the model fabricates external facts) hallucinations. Argues models should "be factual and acknowledge not knowing the answer."
- **"Reward Hacking in Reinforcement Learning"** (November 28, 2024). URL: `https://lilianweng.github.io/posts/2024-11-28-reward-hacking/`. Published shortly after her OpenAI departure. Defined two-category taxonomy: **environment/goal misspecification** vs **reward tampering**. Anchored to Goodhart's Law. Argued: "research into practical mitigations, especially in the context of RLHF and LLMs, remains limited."

### 2025

- **"Why We Think"** (May 1, 2025). URL: `https://lilianweng.github.io/posts/2025-05-01-thinking/`. A 40-minute survey of test-time compute, chain-of-thought, latent-variable framings of reasoning, RL on reasoning traces, and the safety implications of optimizing CoT. Key passage: "We would suggest being very cautious when trying to apply optimization directly on CoT during RL training, or trying to avoid it altogether" — a direct safety argument against rewarding the *content* of chain-of-thought, because doing so destroys its monitorability. Acknowledges John Schulman for feedback. This post is the single most important recent-signal artifact for the persona.

## What the canonical-works list tells us about her method

1. **Surveys, not opinions.** Almost every post is a literature survey with paper citations, not an op-ed. When she takes a strong position (the reward-hacking-is-endemic position; the CoT-monitoring position) she earns it across thousands of words of grounded synthesis.
2. **Topic sequencing tracks the field's frontier.** Agents (2023), adversarial attacks (2023), hallucinations (2024), reward hacking (2024), reasoning models (2025). She writes the field's next chapter roughly six months before it becomes the dominant frame in academic conferences.
3. **Conservative cadence.** ~3–5 posts per year. Each is a major artifact. This contrasts with Nathan Lambert's high-frequency Interconnects substack model — Weng's brand is the comprehensive low-frequency canonical post, not the running commentary.
4. **Co-authorship signals.** Acknowledgements typically credit OpenAI colleagues during her tenure (John Schulman appears multiple times) and academic collaborators. The "Why We Think" acknowledgement of John Schulman in May 2025, after both had left OpenAI, is a soft signal that the TML cohort remained intellectually tied.

## Citation pattern

Academic papers cite Weng's posts using the standard form:

```
@article{weng2023agent,
  title = "LLM-powered Autonomous Agents",
  author = "Weng, Lilian",
  journal = "lilianweng.github.io",
  year = "2023",
  month = "Jun",
  url = "https://lilianweng.github.io/posts/2023-06-23-agent/"
}
```

This is materially unusual — most personal blogs are not cited in BibTeX with `@article` even when academics read them. Weng's posts have crossed the threshold where they are treated as bona fide research artifacts.

## Sources

- https://lilianweng.github.io/
- https://lilianweng.github.io/posts/
- https://lilianweng.github.io/posts/2023-06-23-agent/
- https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/
- https://lilianweng.github.io/posts/2024-11-28-reward-hacking/
- https://lilianweng.github.io/posts/2025-05-01-thinking/
- https://x.com/lilianweng/status/1673535600690102273
- https://x.com/lilianweng/status/1863436864411341112
