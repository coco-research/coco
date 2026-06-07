# Noam Brown — Canonical Works

## Game-AI era (2017 – 2023)

### Libratus (Brown & Sandholm, Science 2018)
- Title: "Superhuman AI for heads-up no-limit poker: Libratus beats top professionals"
- Venue: Science 359, 418–424 (January 2018)
- URL: https://www.science.org/doi/10.1126/science.aao1733 (paywall) / preprint at https://noambrown.github.io/papers/17-IJCAI-Libratus.pdf and arXiv equivalents
- One-liner: First poker AI to beat top human professionals in heads-up no-limit Texas hold'em. The "20-day Brains vs AI" match at Rivers Casino, Pittsburgh, January 2017. Won the Marvin Minsky Medal.
- Significance for persona: Established Brown's signature methodology — solve a hard imperfect-information problem by combining a precomputed blueprint strategy with online search ("nested safe search"), rather than by adding more parameters. This is the structural ancestor of test-time compute as a paradigm.

### Pluribus (Brown & Sandholm, Science 2019)
- Title: "Superhuman AI for multiplayer poker"
- Venue: Science Vol. 365 Issue 6456 (cover, 30 August 2019; First Release 11 July 2019)
- URL: https://www.science.org/doi/10.1126/science.aay2400
- One-liner: First AI to beat elite humans at six-player no-limit Texas hold'em — the first time AI had surpassed humans in a benchmark game with more than two players. Ran live play on just 28 cores after an 8-day, 12,400-core-hour blueprint computation. Underlying algorithm: depth-limited search via continual re-solving.
- Significance: Demonstrated that the search-plus-learning paradigm scaled past two-player zero-sum (the canonical "self-play converges to Nash" setting) into multi-agent regimes. Direct precursor to CICERO.

### ReBeL (Brown, Bakhtin, Lerer, Gong — NeurIPS 2020)
- Title: "Combining Deep Reinforcement Learning and Search for Imperfect-Information Games"
- Venue: NeurIPS 2020
- URL: https://papers.nips.cc/paper_files/paper/2020/hash/c61f571dbd2fb949d3fe5ae1608dd48b-Abstract.html (arXiv preprint: https://arxiv.org/abs/2007.13544)
- One-liner: A general framework that generalises self-play RL + search (the AlphaZero recipe) to imperfect-information games. Provably converges to a Nash equilibrium in any two-player zero-sum game; in perfect-info games it reduces to something AlphaZero-like. Achieved superhuman performance in heads-up no-limit Texas hold'em using "far less domain knowledge than any prior poker AI."
- Significance: This is the paper that, in retrospect, was the bridge between his CMU game-AI work and the o1 paradigm — the abstract framework for combining learned policies with online search that he later argued generalises to language reasoning. Brown frequently cites this as the conceptual ancestor of test-time compute scaling.

### CICERO (Meta FAIR Diplomacy team — Brown is a senior author, Science 2022)
- Title: "Human-level play in the game of Diplomacy by combining language models with strategic reasoning"
- Venue: Science Vol. 378 Issue 6624 (November 2022)
- URL: https://www.science.org/doi/10.1126/science.ade9097 (preprint: https://noambrown.github.io/papers/22-Science-Diplomacy-TR.pdf)
- One-liner: First AI to achieve human-level performance in Diplomacy, a seven-player natural-language strategy game. Combined a planning-and-strategic-reasoning module with a language model trained on Diplomacy conversations. Played in the online Diplomacy league webDiplomacy.net under a pseudonym and scored more than 2x the average human opponent over 40 games.
- Significance: Brown's first published artifact that explicitly fused LLMs with structured strategic reasoning. Sets up his later thesis that "deliberative reasoning" can be bolted on top of language models the way it was bolted on top of poker blueprints.

## o-series era (2023 – present)

### OpenAI o1 / o1-preview / o1-mini launch (September 2024)
- Title: "Introducing OpenAI o1-preview" (and the o1 launch in December 2024)
- Venue: OpenAI blog and system card
- URL: https://openai.com/index/introducing-openai-o1-preview/
- One-liner: First publicly released model trained via reinforcement learning to generate a long internal chain-of-thought before answering, with performance that improves with both training compute and inference compute. Brown received joint credit on the o1 launch video and the o1 System Card; he is publicly identified as one of the project's research leads alongside Pachocki.
- Brown's own framing tweet (September 12, 2024): "Today, I'm excited to share with you all the fruit of our effort at OpenAI to create AI models capable of truly general reasoning: OpenAI's new o1 model series!" — https://x.com/polynoamial/status/1834280155730043108

### "Inventing the Reasoning Paradigm" — Noam Brown, OpenAI (talk)
- Format: Lecture / YouTube Shorts excerpt
- URL: https://www.youtube.com/shorts/C2--1RWBpqY
- One-liner: Brown's preferred framing of the o-series story — "we invented a paradigm," not "we improved a benchmark." Used in multiple 2025 talks and interviews.

### CMU SCS Katayanagi Distinguished Lecture — "Learning to Reason with LLMs"
- Date: November 21, 2024
- Venue: Rashid Auditorium, Gates Hillman 4401, Carnegie Mellon
- URL: https://csd.cmu.edu/calendar/scs-katayanagi-distinguished-lecture-noam-brown
- One-liner: Returned to his PhD institution to deliver the canonical o1 lecture. Frames o1 as an LLM "trained via reinforcement learning to generate a hidden chain of thought before its response," with performance improving "consistently with additional computational resources." This lecture, plus the September 2024 Simons Institute talk ("Learning to Reason with LLMs," https://simons.berkeley.edu/talks/noam-brown-openai-2024-09-26) and the Kempner Institute talk at Harvard, together cover most of Brown's 2024 academic-circuit material.

### TEDAI San Francisco 2024 keynote — "AI won't plateau — if we give it time to think"
- URL: https://tedai-sanfrancisco.ted.com/speakers/noam-brown/ ; podcast at https://pod.wave.co/podcast/ted-talks-daily/ai-wont-plateau-if-we-give-it-time-to-think-noam-brown-c9e6fd2a
- One-liner: The mainstream-press version of his thesis. Source of the widely-quoted "20 seconds of thinking is worth 100,000x more training data" claim — which originally came from his poker work, not from o1, but transferred cleanly.

### "Scaling Test Time Compute to Multi-Agent Civilizations" — Latent Space interview (Swyx & Alessio)
- URL: https://www.latent.space/p/noam-brown
- One-liner: The longest-form Brown interview in the public record on the o1 paradigm. Covers System 1 vs System 2 framing, why self-play doesn't trivially generalise past two-player zero-sum, the "AI civilization" hypothesis, deep research as existence proof for unverifiable domains, and the Ilya-convinced-me-it-wasn't-that-hard story.

### Sequoia Training Data podcast — "Teaching LLMs to Reason"
- URL: https://sequoiacap.com/podcast/training-data-noam-brown/
- One-liner: Brown, Ilge Akkaya, and Hunter Lightman together; explains "inference-time scaling laws" as the most significant discovery of o1, and introduces the generator-verifier-gap framing for which problems benefit from extra thinking.

### IMO 2025 gold-medal tweet thread (July 2025)
- URL: https://x.com/polynoamial/status/1946478249187377206
- One-liner: Announced OpenAI's general reasoning LLM achieving gold-medal performance on the 2025 IMO under human time limits, without tools — solving 5/6 problems for 35/42 points. Brown explicitly framed the result as evidence that reasoning generalises ("this isn't an IMO-specific model").

### Erdős unit-distance disproof announcement (May 20, 2026)
- URL: https://x.com/polynoamial/status/2057178198228586824 ; OpenAI post at https://openai.com/index/model-disproves-discrete-geometry-conjecture/
- One-liner: "A general-purpose internal OpenAI model achieved a breakthrough on one of the best-known combinatorial geometry problems. Less than 1 year ago frontier AI models were at IMO gold-level performance. I expect this pace of progress to continue." This is Brown's mostly-recent canonical signal as of 2026-05-28.

## Background paper (PhD-era)

### "Depth-Limited Solving for Imperfect-Information Games" (Brown, Sandholm, Amos — NeurIPS 2018)
- URL: https://papers.nips.cc/paper/2018/hash/7e93a96fb6f6bd5d6c1f1c8c2c1d4f4f-Abstract.html (semantic scholar mirror)
- One-liner: The technical innovation that let Pluribus search to a shallow depth while still playing strongly — by re-solving the subgame online and accounting for opponents' best responses to a fixed continuation strategy. Foreshadows the "you don't need to think to the end of the game, just deeper than the opponent" instinct that Brown later mapped onto LLM chain-of-thought.

## Sources

- https://www.science.org/doi/10.1126/science.aao1733
- https://www.science.org/doi/10.1126/science.aay2400
- https://www.science.org/doi/10.1126/science.ade9097
- https://papers.nips.cc/paper_files/paper/2020/hash/c61f571dbd2fb949d3fe5ae1608dd48b-Abstract.html
- https://arxiv.org/abs/2007.13544
- https://openai.com/index/introducing-openai-o1-preview/
- https://csd.cmu.edu/calendar/scs-katayanagi-distinguished-lecture-noam-brown
- https://www.latent.space/p/noam-brown
- https://sequoiacap.com/podcast/training-data-noam-brown/
- https://tedai-sanfrancisco.ted.com/speakers/noam-brown/
- https://x.com/polynoamial/status/1834280155730043108
- https://x.com/polynoamial/status/1946478249187377206
- https://x.com/polynoamial/status/2057178198228586824
- https://openai.com/index/model-disproves-discrete-geometry-conjecture/
- https://simons.berkeley.edu/talks/noam-brown-openai-2024-09-26
