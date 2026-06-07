# Adaption Labs — Launch, Funding, and Thesis

Source documents:

- https://techcrunch.com/2025/10/22/why-coheres-ex-ai-research-lead-is-betting-against-the-scaling-race/
- https://fortune.com/2026/02/04/adaption-labs-50-million-seed-funding-emergence-captial-sara-hooker-sudip-roy-ai-models-that-learn-on-the-fly/
- https://finance.yahoo.com/news/former-cohere-exec-sara-hooker-130000524.html
- https://betakit.com/ex-cohere-execs-sara-hooker-and-sudip-roy-unveil-new-ai-startup/
- https://adaptionlabs.ai/blog
- https://www.sarahooker.me/
- https://x.com/sarahookr/status/1968684311764177265 (September 18, 2025 — Observer AI Power Index acknowledgement)
- https://x.com/sarahookr/status/1981127919025213691 (October 22, 2025 — bet against scaling)
- https://x.com/sarahookr/status/2026286134104613157 ("3 months in" — January/February 2026 — adaptive data as starting point)

## Timeline

- **August 2025** — Hooker exits Cohere as VP of Research.
- **September 2025** — She remains involved enough to close out the Cohere For AI Scholars cohort. She tweets on September 18, 2025: "Honored to be recognized in @observer 2025 AI Power Index. It is very meaningful to receive as I close one chapter and begin another. Important problems await, time for the fun to begin." This is the first public confirmation that the next chapter is real.
- **October 7–9, 2025** — Adaption Labs is quietly announced. BetaKit and TechCrunch cover the launch in the following two weeks.
- **October 22, 2025** — TechCrunch publishes the "betting against the scaling race" framing. Hooker tweets the same day quoting the article and calling adaptation efficiency "the most important problem."
- **February 4, 2026** — $50M seed close announced via Fortune. Lead investor Emergence Capital Partners. Mozilla Ventures, Fifty Years, Threshold Ventures, Alpha Intelligence Capital, E14 Fund, and Neo participate.
- **~January–February 2026** — She tweets "3 months in, today is fun because we start to collaborate with builders. Our goal by the end of year is to make the entire AI stack adaptable. Data is the foundation all AI progress has been built on. So, it is our natural starting point."

## Founding team

- Sara Hooker — CEO. Former VP of Research at Cohere, founder of Cohere For AI, Google Brain alumna.
- Sudip Roy — CTO. Former director of inference computing at Cohere, Google veteran.

## Investor list (Feb 2026 seed)

Emergence Capital Partners (lead), Mozilla Ventures, Fifty Years, Threshold Ventures, Alpha Intelligence Capital, E14 Fund, Neo. The Mozilla Ventures presence is a signal that the open-source / public-interest framing remains a positioning anchor.

## Stated mission

From sarahooker.me: "All intelligence adapts, so should AI." Adaption Labs builds AI systems that continuously learn and evolve.

From the TechCrunch article (October 22, 2025), direct Hooker quote:

> "There is a turning point now where it's very clear that the scaling formula — scaling-pilled approaches, which are attractive but extremely boring — hasn't produced intelligence able to navigate the world."

And:

> "We have frontier labs serving the same models to everyone at high cost, but that doesn't need to be true anymore. AI systems can very efficiently learn from environments."

From Fortune (February 4, 2026):

> "Most labs won't quadruple the size of their model each year, mainly because we're seeing saturation in the architecture."

> "This is probably the most important problem that I've worked on."

## Technical approach (three pillars)

1. **Adaptive data** — systems that generate and curate needed data in real time rather than relying on a static pretraining corpus. This is the explicit starting point per her January/February 2026 tweet.
2. **Adaptive intelligence** — dynamically adjust computational expenditure based on problem complexity. Easy queries do not need frontier-model compute.
3. **Adaptive interfaces** — go beyond the chat bar. The seed funding is explicitly earmarked partly for designers and design engineers.

## Technical methods (as publicly disclosed)

- **Gradient-free learning at inference.** Modify model behavior without altering the core weights.
- **On-the-fly adapter merging.** Pick small adapter models at request time to shape primary-model output. (This is a direct successor to the Aya Expanse model-merging research lineage.)
- **Dynamic decoding.** Adjust output probabilities by task without changing underlying weights.
- **Evolutionary algorithms** as a potential alternative to gradient descent (per Sudip Roy's BetaKit quote).

## Competitive context

TechCrunch and Fortune both place Adaption Labs alongside Core Automation (Jerry Tworek, ex-OpenAI) and Ineffable Intelligence (David Silver, ex-DeepMind) as the "continuous learning" cohort of frontier-skeptical startups. The shared thesis: scaling has hit saturation; the next decade is about learning-from-experience rather than pretraining-from-corpus.

## Productive conflict targets

The Adaption Labs thesis is explicitly a bet *against*:

- Closed-frontier-lab maximalism (OpenAI, Anthropic, xAI). She is not against frontier models; she is against the idea that they should be served identically to everyone at high cost.
- Compute-threshold AI governance (her 2024 paper, "On the Limitations of Compute Thresholds as a Governance Strategy"). Regulating by FLOPs locks in the lottery winners.
- "Scaling is all you need" framings from labs and from policy circles.

## Public narrative beats since launch

The X account @sarahookr has been her primary public-comms channel since the launch. Recurring themes:

- Adaptation efficiency is THE next-decade variable, not parameter count.
- The optimization space is expanding far beyond the model space.
- Talent flows toward labs where the problem is genuinely the most interesting; she pitches Adaption Labs on problem-quality rather than compensation arms race.
- "Make the entire AI stack adaptable."
