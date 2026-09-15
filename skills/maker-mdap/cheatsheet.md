# Cheatsheet — MAKER / MDAP Decision Guide

## Decision rule: should you use an MDAP/MAKER-style approach at all?
- If your task needs **many dependent LLM steps completed with near-zero error tolerance** →
  yes, consider MDAP. A single-agent chain's success probability decays exponentially in step
  count; no amount of "smarter model" reliably fixes this past a few hundred steps.
- If your task is **independent-example accuracy averaged over a benchmark** (few dependent
  steps per example) → MDAP machinery is unnecessary overhead; standard prompting/evals suffice.
- If your task requires **generating a novel plan/strategy** (insight), not just following one
  → MAKER as described here doesn't cover this; treat it as a separate, harder problem (Ch 5's
  "insights vs. execution" distinction). A decomposition-agent variant exists as early-stage
  work (Appendix F) but is not the validated core result.

## Decomposition granularity: pick m, not s
| Symptom | Action |
|---|---|
| Cost blowing up as task grows | Check subtask size `m` first — cost is **exponential in m**, only log-linear in step count `s`. Shrink subtasks toward `m=1` (MAD). |
| Tempted to bundle steps "for efficiency" | Don't. Bundling looks efficient (fewer calls) but is the single biggest cost driver in this framework (Figure 5). |
| Each agent's context keeps growing across steps | Re-architect so every agent receives only `(current state, fixed strategy)` — never the run's action history. |

## Model / k selection at scale
1. Estimate `p` (per-step success rate) and mean output tokens on a small, cheap, ground-truth-
   known sample — never guess this on a big-budget run.
2. Compute `k_min` per candidate model from the target success probability `t`:
   `k_min ≈ ⌈ ln(t^(−m/s) − 1) / ln((1−p)/p) ⌉`.
3. Rank models by **`c/p`** (cost per token ÷ success rate), not by raw `$/token` and not by
   "most capable" reputation alone — the cheapest-per-token or most-reasoning model is often
   *not* the cost-optimal choice once `k_min` is factored in.
4. Also weigh **API/infra reliability** at your target call volume — an unreliable API can
   dominate practical cost/risk at millions of calls even if it's cheaper per token.
5. Default assumption to challenge: reasoning models are *not required* — small, non-reasoning
   models were sufficient and often cheaper overall in this paper's results.

## Red-flagging thresholds
| Signal | Rule of thumb | Why |
|---|---|---|
| Response length | Flag responses past the point where error rate visibly spikes (~700–750 tokens in this paper's setup — **re-derive empirically for your own domain/prompt**, don't hardcode this number) | Long responses correlate with the model "talking in circles" after an early mistake |
| Output format | Flag any response that fails a **strict** parser (exact shape/count/value-set checks) | Malformed output correlates with confused generation, not just a cosmetic slip |
| On flag | **Discard and resample** — never attempt to repair/salvage | Repair-and-keep was shown to *increase* correlated-error collisions vs. discard-and-resample |

## Trade-off matrix: repairing parser vs. red-flagging parser
| Dimension | Repairing parser | Red-flagging parser |
|---|---|---|
| Use case | Cheap p-estimation / calibration only | The actual production/scale-up run |
| Malformed output | Tries to salvage an answer | Discards immediately, resamples |
| Correlated-error collisions | Higher | Lower |
| Extra sampling cost | Lower (fewer discards) | Slightly higher (more discards → resamples) |
| Recommended for a zero-error target | No | Yes |

## Sanity checks before trusting a voting-based error-correction result
- [ ] Did you check for **collisions** (steps whose first 1–2 votes are all wrong), not just
      average per-step error rate? A low average error rate can still hide correlated failures.
- [ ] Is per-step error rate roughly **flat** as task length grows, or does it creep up? Rising
      error rate with length signals a decomposition or context-leakage problem.
- [ ] Are you feeding **only** current state + strategy into each agent, or has run history
      crept back into the prompt?
- [ ] Have you priced the model choice by **`c/p`**, or only by sticker price per token?

## Fast facts / thresholds from the paper (context-specific, not universal constants)
- 1% per-step error rate → expected failure by ~100 steps.
- 20-disk Towers of Hanoi = 2^20 − 1 = 1,048,575 steps.
- `k_min` grows `Θ(ln s)` — logarithmic in step count.
- Total expected cost grows `Θ(s·ln s)` under MAD (m=1); **exponentially in m** if subtasks are
  bundled larger.
- gpt-4.1-mini at k_min=3, 750-token cap, solved the full 1M+-step task with **zero errors**.
