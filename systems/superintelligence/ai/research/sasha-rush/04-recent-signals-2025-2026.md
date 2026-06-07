# Sasha Rush — Recent Signals (post 2025-05-27)

Five concrete signals from the last twelve months that anchor Rush's current views.

## 1. Composer 2 technical report (2026-03-27)

- **URL:** https://cursor.com/blog/composer-2-technical-report
- **arXiv:** 2603.24477
- Rush listed as author. Public artifact establishing Cursor's RL-heavy post-training methodology as the new bar for application-layer LM work.
- Key takeaway: Two-phase training (continued pretraining on Kimi K2.5 base + large-scale RL on realistic Cursor sessions), MXFP8 MoE kernels on Blackwell GPUs, async multi-region RL pipeline, Anyrun sandbox platform for hundreds of thousands of coding environments. CursorBench 61.3, SWE-bench Multilingual 73.7. Rush's framing: RL training improves both average and best-of-K — meaning the model is genuinely better, not just better at sampling.

## 2. "The Future of Coding Agents with Sasha Rush" — Information Bottleneck podcast (2026-04-15)

- **URL:** https://www.the-information-bottleneck.com/the-future-of-coding-agents-with-sasha-rush-cursorcornell/
- Key claims:
  - "Coding is a kind of clear sense of like you've done something correctly or you've done something incorrectly" — why coding is the cleanest RL substrate.
  - "Roughly like 35% of the like PRs at the company have come from our kind of cloud agent system."
  - Pushes back on the academic fixation on binary rewards: "arbitrary rewards" provide richer mathematical signal for the coding domain.
  - On architecture: maintains his IsAttentionAllYouNeed.com bet but concedes "it does really seem like you need some attention in the process" — hybrids are the realistic destination.
  - Future framing: shift from "user uses CLI or IDE for interactive coding" to "user specifies a long-running challenging problem" for agents to solve autonomously.

## 3. Composer 1 launch and Simon Willison coverage (2025-10-29)

- **URL:** https://simonwillison.net/2025/Oct/29/cursor-composer/
- Direct Rush quote: "Our primary focus is on RL post-training. We think that is the best way to get the model to be a strong interactive agent."
- Composer-1 framed as 4× faster than similarly intelligent models. MoE, trained on live programming interactions.

## 4. Speculations on Test-Time Scaling tutorial (2025, distributed throughout the year)

- **URL:** https://srush.github.io/awesome-o1/o1-tutorial.pdf
- Co-authored with Daniel Ritter.
- Public lecture-style PDF covering o1-style reasoning, RL signals for inducing chain-of-thought, the tradeoff between inference-time compute and weights. Reflects Rush's transition into the RL-for-reasoning camp without abandoning his theory roots.

## 5. Simons Institute Special Year on LLMs, Part 2 (Spring 2025)

- **URL:** https://simons.berkeley.edu/people/sasha-rush
- Rush served as Visiting Scientist and Program Organizer.
- Brought theory and applied LM research together at Berkeley — concrete demonstration of his "theory still matters" stance even as the field skews applied.

## 6. COLM 2025 (October 2025)

- COLM second annual edition. Rush continues as President.
- The venue is now an established outlet for serious LM research that does not fit cleanly into NeurIPS / ICML / ACL.

## 7. Cursor publicly demoing Cheetah → Composer (October 2025)

- Cheetah was the codename for an earlier preview model; Rush publicly denied that it was based on xAI's Grok.
- The product-side velocity at Cursor in 2025–2026 (Composer 1, Composer 2, Agents, Automations, SDK) is the operating context for everything Rush now says about RL and coding agents.

## Why these signals matter

All five anchor Rush in the present tense as a **producer** of frontier post-training research at an application-layer company, while still being a **convener** (COLM, Simons) of academic LM theory. The persona must reflect both — he is not a pure academic, and he is not a pure industrial researcher.
