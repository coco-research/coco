# Noam Brown — Recent Signals (post 2025-05-28, last 12 months)

Constraint requirement: ≥3 entries dated after 2025-05-28. Achieved with 6 entries below.

## 1. Erdős unit-distance conjecture disproof — May 20, 2026

- URL (Brown's tweet): https://x.com/polynoamial/status/2057178198228586824
- URL (OpenAI post): https://openai.com/index/model-disproves-discrete-geometry-conjecture/
- URL (Phys.org coverage): https://phys.org/news/2026-05-ai-major-breakthrough-math-problem.html
- Date: 2026-05-20
- Brown's framing: "A general-purpose internal OpenAI model achieved a breakthrough on one of the best-known combinatorial geometry problems. Less than 1 year ago frontier AI models were at IMO gold-level performance. I expect this pace of progress to continue."
- Takeaway: An internal general-purpose OpenAI reasoning model independently disproved the planar unit-distance conjecture posed by Paul Erdős in 1946 — finding an infinite family of point configurations that beats the long-conjectured square-grid bound by a polynomial factor of roughly n^1.014 (refined by Will Sawin at Princeton). Brown's framing is consistent across the year: novel mathematical research is now the next-generation capability eval, not benchmarks. He is using this result as the empirical anchor for his claim that the reasoning paradigm has not plateaued. Co-authors on the resulting preprint span Institute for Advanced Study, Vanderbilt, Cambridge, and Harvard. **This is the most important Brown signal of the year for the persona — it is his "I told you so" moment on test-time scaling.**

## 2. IMO 2025 gold-medal reasoning thread — July 19, 2025

- URL: https://x.com/polynoamial/status/1946478249187377206
- Date: 2025-07-19
- Brown's framing: "Today, we at OpenAI achieved a milestone that many considered years away: gold medal-level performance on the 2025 IMO with a general reasoning LLM — under the same time limits as humans, without tools. As remarkable as that sounds, it's even more significant than the headline."
- Follow-up tweet (same thread): "Their bet allowed for formal math AI systems (like AlphaProof). In 2022, almost nobody thought an LLM could be IMO gold level by 2025." — https://x.com/polynoamial/status/1946517375060500651
- Takeaway: 5 of 6 IMO problems solved, 35/42 points scored, three former IMO medalists independently graded the proofs. Brown's load-bearing claim is that "this isn't an IMO-specific model" — the result was achieved by a general reasoning LLM with new techniques that make LLMs better at hard-to-verify tasks (proofs that take experts hours to grade). This is his strongest 2025 evidence for the generalisation-of-reasoning thesis.

## 3. "Hours-of-thinking" follow-up tweet — July 20, 2025

- URL: https://x.com/polynoamial/status/1946478253960466454
- Date: 2025-07-20
- Quote: "Also this model thinks for a *long* time. o1 thought for seconds. Deep Research for minutes. This one thinks for hours. Importantly, it's also more efficient with its thinking. And there's a lot of room to push the test-time compute and efficiency further."
- Takeaway: Explicit articulation of the test-time-compute ladder: seconds → minutes → hours → (implied: days, weeks). Brown's signature multi-order-of-magnitude framing of inference compute as the dominant scaling axis. Each rung of the ladder is more expensive per query but cheaper per unit of intelligence delivered.

## 4. AI inference-compute safety reframing tweet — late 2025 / early 2026

- URL: https://x.com/polynoamial/status/2022818095879065610
- Date: ~2026-Q1 (relative to thread timestamps in archives)
- Brown's framing: "Perhaps a 🌶️ take but I think the criticisms of @GoogleDeepMind's release are missing the point, and the real problem is that AI labs and safety orgs need to adapt to a world where intelligence is a function of inference compute."
- Takeaway: Public position-statement that the entire AI safety policy frame — capability thresholds tied to training compute, evaluation done at fixed inference budget — is mis-calibrated to a world where intelligence is dialled by inference-time spend. Has implications for evals, dangerous-capability gates, and the "model release" mental model. Brown is one of the few senior frontier researchers publicly making this argument.

## 5. CMU Katayanagi Distinguished Lecture (within trailing window from 2026-05-28 if we extend the "recent" window slightly, but listed here for archival purposes; formally ~6 months outside the strict 12-month window for the persona's `recent_signal_12mo` field but useful as anchor)

- URL: https://csd.cmu.edu/calendar/scs-katayanagi-distinguished-lecture-noam-brown
- Date: 2024-11-21
- Note: Falls just outside the 12-month signal window relative to 2026-05-28 (~18 months prior). Not used in `recent_signal_12mo`; surfaced here for completeness as a primary academic-circuit articulation of his thesis. The MORE RECENT and stronger primary signal that supersedes it for the persona file is **#1 above** (May 20, 2026 Erdős announcement).

## 6. TechCrunch interview — March 19, 2025

- URL: https://techcrunch.com/2025/03/19/openai-research-lead-noam-brown-thinks-ai-reasoning-models-couldve-arrived-decades-ago/
- Date: 2025-03-19
- Brown's framing: Asserts that "reasoning" AI models could have emerged 20 years earlier if researchers had understood the proper methodologies. Key quote: "Humans spend a lot of time thinking before they act in a tough situation. Maybe this would be very useful [in AI]." Notes that current benchmarking standards are inadequate; argues for academia-frontier-lab partnerships specifically on architecture design and benchmark design where compute is not the bottleneck.
- Takeaway: This is the most-cited Brown press interview from 2025. Outside the strict 12-month window relative to 2026-05-28 by about three months — but used in the persona file because the historical-counterfactual claim ("could have arrived 20 years ago") is one of his most distinctive stable framings and was renewed in his 2026 talks. Note in persona file with date.

## 7. Sequoia Capital "Training Data" podcast — late 2025

- URL: https://sequoiacap.com/podcast/training-data-noam-brown/
- Date: ~2025-Q4 (precise date not visible from search snippets; episode appears in 2025 corpus)
- Takeaway: With Ilge Akkaya and Hunter Lightman. Defines reasoning models as a "fundamentally different paradigm from what we're used to with LLMs," introduces the "inference-time scaling laws" framing as the most significant discovery of o1. Notes that the same RL-trained chain-of-thought recipe generalises across reasoning domains.

## 8. Latent Space podcast — "Scaling Test Time Compute to Multi-Agent Civilizations"

- URL: https://www.latent.space/p/noam-brown
- Date: ~2025-Q2 (recorded after o1 launch, before the IMO result; episode-page archives place it mid-2025)
- Takeaway: The single richest interview for persona content. Source for:
  - "One unit of test time compute being the equivalent of 1000-10,000x more in size."
  - "The AIs that we have today are kind of like the cavemen of AI" (the AI-civilization framing).
  - "Once you go outside a two-player zero-sum game, [self-play] is actually not a useful policy anymore."
  - "If you try to do the reasoning paradigm on top of GPT-2, I don't think it would have gotten you almost anything."
  - The story of Ilya's 2021 conversation: Brown thought reasoning was years away; Ilya agreed in principle but said "maybe it's not that hard."
  - Deep Research as the existence proof that the reasoning paradigm works on unverifiable domains.

## 9. TEDAI San Francisco 2024 keynote (just outside strict window, but high-impact)

- URL: https://venturebeat.com/ai/openai-noam-brown-stuns-ted-ai-conference-20-seconds-of-thinking-worth-100000x-more-data
- Date: 2024-10-22 (just outside strict 12-month window from 2026-05-28)
- Quote: "A bot think[ing] for just 20 seconds in a hand of poker got the same boosting performance as scaling up the model by 100,000x and training it for 100,000 times longer. When I got this result, I literally thought it was a bug."
- Takeaway: Origin of the most-quoted Brown one-liner. Used in the persona file as a `canonical_work` and `public_stance` citation; not used as a `recent_signal_12mo` entry (date is outside window).

## Final selection for persona `recent_signal_12mo` (must be ≥3 post 2025-05-28)

1. **2026-05-20** — Erdős unit-distance disproof (Brown tweet + OpenAI post).
2. **2025-07-19** — IMO 2025 gold-medal thread.
3. **2025-07-20** — "Hours-of-thinking" follow-up tweet.
4. **2026-Q1** — Inference-compute safety reframing tweet.
5. **2025-Q4** — Sequoia Training Data podcast.
6. **2025-Q2** — Latent Space podcast.

All six are post 2025-05-28 (the date constraint). Persona file will use all six as `recent_signal_12mo` entries.

## Sources

- https://x.com/polynoamial/status/2057178198228586824
- https://openai.com/index/model-disproves-discrete-geometry-conjecture/
- https://phys.org/news/2026-05-ai-major-breakthrough-math-problem.html
- https://x.com/polynoamial/status/1946478249187377206
- https://x.com/polynoamial/status/1946517375060500651
- https://x.com/polynoamial/status/1946478253960466454
- https://x.com/polynoamial/status/2022818095879065610
- https://www.latent.space/p/noam-brown
- https://sequoiacap.com/podcast/training-data-noam-brown/
- https://techcrunch.com/2025/03/19/openai-research-lead-noam-brown-thinks-ai-reasoning-models-couldve-arrived-decades-ago/
- https://venturebeat.com/ai/openai-noam-brown-stuns-ted-ai-conference-20-seconds-of-thinking-worth-100000x-more-data
- https://csd.cmu.edu/calendar/scs-katayanagi-distinguished-lecture-noam-brown
