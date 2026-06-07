# Lilian Weng — OpenAI Departure (November 2024)

## The note

On November 8, 2024, Lilian Weng posted to X (`@lilianweng/status/1855031273690984623`):

> "After working at OpenAI for almost 7 years, I decide to leave. I learned so much and now I'm ready for a reset and something new."

The attached image of her note to the team included these characterized passages (reconstructed from TechCrunch's and Gigazine's reporting; the original X post is paywalled to public unauthenticated fetches but multiple news outlets reproduce the text):

- "After 7 years at OpenAI, I feel ready to reset and explore something new."
- "Looking at what we have achieved, I'm so proud of everyone on the Safety Systems team and I have extremely high confidence that the team will continue thriving."
- (On the team build-out:) The Safety Systems team grew from a handful of people to ~80 by her departure, covering deployment safety, model evals, jailbreak resistance, the Preparedness Framework reds, and policy interfaces.

Her last day was November 15, 2024.

## The cluster of departures

Weng's exit was the latest in a 6-month run of senior safety and research departures from OpenAI in 2024:

| Date            | Departure                                   |
|-----------------|---------------------------------------------|
| May 14, 2024    | Ilya Sutskever (Chief Scientist, co-founder)|
| May 17, 2024    | Jan Leike (Head of Alignment; Superalignment co-lead) — *defining safety-culture resignation* |
| August 2024     | John Schulman (co-founder, RLHF) — to Anthropic; later left for TML |
| August 2024     | Andrej Karpathy (founding member, returned 2023–2024) — to Eureka Labs |
| September 2024  | Mira Murati (CTO)                           |
| September 2024  | Bob McGrew (Chief Research Officer)         |
| September 2024  | Barret Zoph (VP Research)                   |
| November 8, 2024| Lilian Weng (VP Research, Safety)           |

This pattern is the public-narrative spine for the "OpenAI safety culture is unraveling" frame that defined late-2024 AI coverage.

## Public framing of why she left

Weng's note is more measured than Jan Leike's "safety culture and processes have taken a backseat to shiny products" thread. She did not publicly accuse OpenAI of de-prioritizing safety. But two facts make her departure read in the same cluster:

1. **Timing.** She left within weeks of Murati, Zoph, and McGrew, after being elevated to VP only three months earlier. Promotion-then-departure is a strong organizational signal — typically read as "the elevation didn't change the operating environment."
2. **Destination.** She rejoined the same cohort at Thinking Machines Lab in February 2025 — co-founding a company with the explicit pitch of "AI that works for everyone," collaborative open publishing, and reliable foundations. Murati, Schulman, Zoph all reassembled there. The choice of destination is the implicit comment.

By contrast to Leike, who said it explicitly and went to Anthropic, Weng said it implicitly and went to TML. The persona file therefore credits her with a safety-culture critique on departure, but flagged as "implied through cluster and destination" rather than "stated directly." Confidence on the implicit reading: 0.88.

## OpenAI's response

OpenAI spokesperson statement (TechCrunch, November 8, 2024):

> "We deeply appreciate Lilian's contributions to breakthrough safety research and building rigorous technical safeguards. We are confident the Safety Systems team will continue playing a key role in ensuring our systems are safe and reliable, serving hundreds of millions of people globally."

No internal-conflict acknowledgement. Standard corporate exit language.

## What Weng built at OpenAI that still ships

- **The Safety Systems team itself** (deployment safety, real-time moderation, model-card production, jailbreak resistance) — still the standing org under a new lead post-November 2024.
- **Contributions to the Preparedness Framework.** OpenAI's catastrophic-risk evaluation policy covering cybersecurity, CBRN, persuasion, and model autonomy with the "medium / high" deployment thresholds.
- **GPT-4o system card** (August 8, 2024). Weng is credited among core contributors to the preparedness and safety evaluation sections.
- **o1 system card** (September 12, 2024). Final major system card under her watch before her departure; introduced the chain-of-thought safety analysis that her May 2025 blog post would later generalize.

## Sources

- https://techcrunch.com/2024/11/08/openai-loses-another-lead-safety-researcher-lilian-weng/
- https://x.com/lilianweng/status/1855031273690984623
- https://gigazine.net/gsc_news/en/20241110-openai-loses-another-lead-safety-researcher-lilian-weng/
- https://cdn.openai.com/gpt-4o-system-card.pdf
- https://openai.com/index/openai-o1-system-card/
