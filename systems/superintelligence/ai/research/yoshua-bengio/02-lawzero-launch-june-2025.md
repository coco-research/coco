# LawZero — Launch and Mission

Sources:
- https://lawzero.org/ (verified 2026-05-27)
- https://lawzero.org/en/news/yoshua-bengio-launches-lawzero-new-nonprofit-advancing-safe-design-ai
- https://yoshuabengio.org/2025/06/03/introducing-lawzero/
- https://www.prnewswire.com/news-releases/yoshua-bengio-launches-lawzero-a-new-nonprofit-advancing-safe-by-design-ai-302471271.html
- https://time.com/7290554/yoshua-bengio-launches-lawzero-for-safer-ai/
- https://thenextweb.com/news/bengio-ai-extinction-warning-lawzero-safety

## Launch

- **Date:** June 3, 2025
- **Founder & Scientific Director:** Yoshua Bengio
- **Location:** Montreal, Quebec; incubated through Mila — Quebec AI Institute
- **Initial team:** more than 15 researchers
- **Initial funding:** approximately $30 million in philanthropic contributions
- **Funders:** Future of Life Institute, Open Philanthropy, Schmidt Sciences, Silicon Valley Community Foundation, Jaan Tallinn (individual donor, Skype founding engineer), and (per Time / TNW) the Gates Foundation and Founders Pledge in subsequent reporting
- **Operations:** Cassidy MacNeil — Senior Assistant and Operations Lead
- **Board / Advisory:** In January 2026, LawZero appointed 7 global leaders including former New Zealand Prime Minister Jacinda Ardern

## Mission statement

LawZero's stated mission is "protecting human joy and endeavour" by rethinking the building blocks of frontier AI so they are "highly capable and safe-by-design." The organization positions itself explicitly as a counter-weight to the agentic, commercially-driven AI race.

## Why Bengio founded it (direct quotes)

> "LawZero is my team's constructive response to these challenges. It's an approach to AI that is not only powerful but also fundamentally safe."

> "What really moves me is not fear for myself but love, the love of my children, of all the children."

> Mountain-driving metaphor for current AI development: "a thrilling yet deeply uncertain ascent into uncharted territory, where the risk of losing control is all too real."

> "When I realized how dangerous the current agency-driven AI trajectory could be for future generations, I knew I had to do all I could to make AI safer." (TED2025, April 8, 2025)

## Technical approach — "Scientist AI"

LawZero's core research program builds what Bengio calls "Scientist AI" — explicitly non-agentic, designed to *understand* rather than *act*. The proposal is laid out in the February 2025 arXiv paper "Superintelligent Agents Pose Catastrophic Risks: Can Scientist AI Offer a Safer Path?" (arXiv:2502.15657).

Key properties:

- **Non-agentic.** No optimization-over-trajectories objective. The system answers questions and predicts outcomes; it does not pursue goals.
- **Two-part architecture.** A world model that generates explanatory theories from data, and a question-answering mechanism over those theories.
- **Bayesian posteriors as outputs.** Predictions come with explicit uncertainty quantification rather than confident answers from a single point estimate.
- **Memoryless and stateless** at the inference boundary so it cannot accumulate goals across sessions.
- **Structured reasoning chains as latent variables**, intended to be honest and inspectable.
- **Designed as a guardrail.** A Scientist AI sitting in front of an agentic system can predict whether a proposed action could cause harm and block it.

## Why "safe by design" rather than RLHF / Constitutional AI / patches

Bengio's framing in the launch post and arXiv paper is that current frontier systems are agents trained to imitate humans — and humans include bad actors, deception, self-preservation. Patching that with RLHF is fundamentally limited because the substrate already has the wrong shape. He argues the alternative is to start from a different substrate (non-agentic, science-of-the-world) and build agency on top only where strictly needed and gated.

## Funding-context quote (Time, June 2025)

Time describes Bengio as "the most-cited computer scientist" and notes the $30M figure is small relative to frontier labs — Bengio is explicit that LawZero is not racing to produce a competing frontier model, it is producing a safer alternative substrate and a guardrail others can adopt.

## December 2025 stance

Bengio publicly argued that granting rights to AI systems would be a "huge mistake," emphasizing that "being able to shut them down is essential for safety." This is the corrigibility position made unambiguous.
