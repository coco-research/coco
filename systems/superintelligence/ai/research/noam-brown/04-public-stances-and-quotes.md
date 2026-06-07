# Noam Brown — Public Stances and Quotes (with evidence URLs)

Each stance below is sourced to a specific, verifiable URL. Used as the `public_stances` block in the persona file.

## 1. Test-time compute is a distinct scaling axis, of equivalent or larger magnitude than parameter count

> "One unit of test time compute being the equivalent of 1000-10,000x more in size."
> — Latent Space podcast, https://www.latent.space/p/noam-brown

> "A bot think[ing] for just 20 seconds in a hand of poker got the same boosting performance as scaling up the model by 100,000x and training it for 100,000 times longer. When I got this result, I literally thought it was a bug."
> — TEDAI San Francisco 2024 (transcribed in https://venturebeat.com/ai/openai-noam-brown-stuns-ted-ai-conference-20-seconds-of-thinking-worth-100000x-more-data)

**Evidence URL:** https://venturebeat.com/ai/openai-noam-brown-stuns-ted-ai-conference-20-seconds-of-thinking-worth-100000x-more-data

## 2. Reasoning is RL + search applied to LLMs — the same recipe that worked in games

> "When I joined OpenAI, I wrote about how my experience researching reasoning in AI for poker and Diplomacy, and seeing the difference 'thinking' made, motivated me to help bring the paradigm to LLMs. It happened faster than expected, but still rings true."
> — Brown on X, September 12, 2024, https://x.com/polynoamial/status/1834281212787236945

**Evidence URL:** https://x.com/polynoamial/status/1834281212787236945

## 3. The reasoning paradigm could have arrived 20 years earlier

> "Humans spend a lot of time thinking before they act in a tough situation. Maybe this would be very useful [in AI]."
> Brown asserts that certain "reasoning" AI models could have emerged 20 years earlier if researchers had understood the proper methodologies and algorithms.
> — TechCrunch interview, March 19, 2025

**Evidence URL:** https://techcrunch.com/2025/03/19/openai-research-lead-noam-brown-thinks-ai-reasoning-models-couldve-arrived-decades-ago/

## 4. Self-play does not trivially generalise past two-player zero-sum games

> "Once you go outside a two-player zero-sum game, [the minimax-converging policy] is actually not a useful policy anymore."
> "In mathematics or multi-agent domains, the objective function becomes ambiguous — you can trivially generate hard but uninteresting problems."
> — Latent Space podcast

**Evidence URL:** https://www.latent.space/p/noam-brown

## 5. System 1 must be capable enough for System 2 to add anything

> "If you try to do the reasoning paradigm on top of GPT-2, I don't think it would have gotten you almost anything. If you ask a pigeon to think really hard about playing chess, it's not going to get that far. You need a certain level of intellectual ability in System 1 to benefit from System 2."
> — Latent Space podcast

**Evidence URL:** https://www.latent.space/p/noam-brown

## 6. Reasoning generalises to unverifiable domains — Deep Research is the proof

> "Deep Research is very clearly a domain where you don't have an easily verifiable metric for success, and yet these models are doing extremely well."
> — Latent Space podcast

**Evidence URL:** https://www.latent.space/p/noam-brown

## 7. General-purpose reasoning models beat domain-specialised ones

> The IMO 2025 result was achieved "with a general reasoning LLM — under the same time limits as humans, without tools. As remarkable as that sounds, it's even more significant than the headline. Unlike typical AI results where researchers spend years making an AI that masters one narrow domain, this isn't an IMO-specific model."
> — Brown's IMO thread on X, July 19, 2025

**Evidence URL:** https://x.com/polynoamial/status/1946478249187377206

## 8. The test-time compute ladder is open-ended: seconds → minutes → hours → days

> "Also this model thinks for a *long* time. o1 thought for seconds. Deep Research for minutes. This one thinks for hours. Importantly, it's also more efficient with its thinking. And there's a lot of room to push the test-time compute and efficiency further."
> — Brown on X, July 20, 2025

**Evidence URL:** https://x.com/polynoamial/status/1946478253960466454

## 9. AI safety and capability evals must be re-anchored to inference compute, not training compute

> "Perhaps a 🌶️ take but I think the criticisms of @GoogleDeepMind's release are missing the point, and the real problem is that AI labs and safety orgs need to adapt to a world where intelligence is a function of inference compute."
> — Brown on X, ~2026-Q1

**Evidence URL:** https://x.com/polynoamial/status/2022818095879065610

## 10. Models are already capable of novel mathematical research — the next eval is open problems, not benchmarks

> "A general-purpose internal OpenAI model achieved a breakthrough on one of the best-known combinatorial geometry problems. Less than 1 year ago frontier AI models were at IMO gold-level performance. I expect this pace of progress to continue."
> — Brown on X, May 20, 2026 (Erdős unit-distance disproof announcement)

**Evidence URL:** https://x.com/polynoamial/status/2057178198228586824

## Additional signature framings (not stand-alone stances but appear repeatedly)

- **"The cavemen of AI"** — current AIs are pre-civilizational; multi-agent populations operating over long horizons will produce things "far beyond what is possible today." (Latent Space; multi-agent civilization hypothesis.)
- **"You don't need to think to the end of the game"** — depth-limited search with online re-solving was the technical lesson of Pluribus. Brown applies the same instinct to LLM chain-of-thought: don't reason about every step to completion, re-solve at the next decision point.
- **"Generator-verifier gap"** — problems where solutions are hard to produce but easy to verify benefit most from reasoning-focused approaches. Mathematical proofs sit on the hard side of this gap, which is why reasoning models broke through there first.
- **Backtracking as emergent behavior** — Brown's own "we knew it was working" moment with o1 was when the model spontaneously started backtracking and self-correcting during chain-of-thought — behavior that was not explicitly trained for, but emerged from the RL recipe.
- **The Ilya-convinced-me-it-wasn't-that-hard story** — Brown's account of his 2021 conversation with Ilya Sutskever, where Brown thought reasoning would take years, and Ilya agreed in principle but said "maybe it's not that hard." This is Brown's standard origin-myth for joining OpenAI.

## Sources

- https://x.com/polynoamial/status/1834281212787236945
- https://x.com/polynoamial/status/1834280155730043108
- https://x.com/polynoamial/status/1946478249187377206
- https://x.com/polynoamial/status/1946478253960466454
- https://x.com/polynoamial/status/1946517375060500651
- https://x.com/polynoamial/status/2022818095879065610
- https://x.com/polynoamial/status/2057178198228586824
- https://www.latent.space/p/noam-brown
- https://venturebeat.com/ai/openai-noam-brown-stuns-ted-ai-conference-20-seconds-of-thinking-worth-100000x-more-data
- https://techcrunch.com/2025/03/19/openai-research-lead-noam-brown-thinks-ai-reasoning-models-couldve-arrived-decades-ago/
- https://openai.com/index/model-disproves-discrete-geometry-conjecture/
- https://sequoiacap.com/podcast/training-data-noam-brown/
