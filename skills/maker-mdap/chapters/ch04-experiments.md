# Chapter 4: Experiments — The 20-Disk, Million-Step, Zero-Error Run

## Core Idea
Before spending real money on a million-step run, the paper shows how to cheaply estimate a
model's per-step success rate p on a small sample, plug it into the Ch 3 cost formula to pick
the most cost-effective model, then run the full task once calibrated. With gpt-4.1-mini,
max-750-output-tokens, and k_min=3, the full 20-disk (1,048,575-step) Towers of Hanoi problem
was solved with **zero errors**.

## Frameworks Introduced
- **Calibrate-then-scale workflow**: (1) estimate p cheaply on a small random subset of steps
  where ground truth is known in advance, (2) use the cost formula (Eq. 18/20) to pick the
  model minimizing `c/p` (cost per token over success rate), (3) only then run the full-scale
  task.
  - When to use: any time a million-call-scale run is expensive enough that guessing wrong on
    model choice is costly — cheap small-scale calibration is worth doing first.
  - How: batch-sample many steps asynchronously (this paper used the OpenAI batch API) since
    correct answers/inputs for every step are known a priori in this domain; fit p, mean output
    tokens, and $/M-token cost per candidate model into Eq. 20 to project total cost.

## Key Concepts
- **Setup (4.1)**: each agent receives only the overall strategy (fixed prompt, valid for any
  even disk count) plus the current disk configuration — never the history of prior moves.
  Each agent must output *both* the next move and the resulting next state (the next state is
  what's fed forward to the next agent).
- **Single-step error-rate estimation (4.2)**: run on a random subset of steps with a
  "repairing" parser (attempts to fix common formatting errors) and a generous 2048-token
  output cap, purely to *measure* p across disk counts and models — not yet using
  red-flagging.
  - Two key empirical findings: (1) small non-reasoning models have per-step error rates
    *comparable to* larger reasoning models — reasoning capability is not what's limiting here;
    (2) per-step error rate stays roughly flat as disk count (and thus solution length) grows —
    strong evidence that MAKER's reliability doesn't erode as tasks get longer.
- **Cost projection table (Figure 6b)**: given $/M-token cost, mean output tokens, and measured
  (1−p), compute k_min and E[cost] per model. gpt-4.1-mini (τ=0.1) had the lowest projected
  proprietary cost (~$3.5K) despite gpt-4.1-nano being cheaper per token — because gpt-4.1-nano's
  much higher error rate (1−p ≈ 0.357) demands a far larger k_min (29) than gpt-4.1-mini's (3).
  gpt-oss-20B was the best open-source pick (~$1.7K projected).
- **The scale-up run (4.4)**: gpt-4.1-mini, max 750 output tokens (a red-flag threshold, not
  just a cap), a strict red-flagging parser, k_min=3 (so ≥3 samples drawn per step), first
  vote at temperature 0 then temperature 0.1 thereafter. Result: the full 2^20 − 1 =
  1,048,575-step task solved with **zero errors**.
- **Convergence pattern (Figure 8)**: the number of undecided steps decays exponentially with
  each additional voting/sampling round — almost all cost is spent in the first k_min rounds;
  finishing the long tail of harder steps is a rounding error on total cost. One pathological
  step (step 10241) needed 18 voting rounds before resolving.

## Mental Models
- **"Measure p before you pay for scale"**: treat per-step success rate the way you'd treat any
  expensive-to-discover parameter — get a cheap, small-sample estimate first, then project cost
  analytically (Eq. 18/20) instead of running the full task blind.
- **"Cheapest-per-token ≠ cheapest overall"**: minimize `c/p`, not `c` alone — a slightly
  pricier, much more reliable model can cost less overall because it needs a far smaller k_min.
- **"Most of the cost is paid up front"**: the exponential convergence in Figure 8 means you can
  budget expecting the bulk of spend in the first k rounds, with a thin, cheap tail.

## Anti-patterns
- **Picking a model by raw per-token price or by "most capable/reasoning" reputation alone**:
  the paper explicitly shows gpt-4.1-nano's cheap tokens and o3-mini's low error rate both lose
  to gpt-4.1-mini's balance of the two, once run through the actual cost formula.
- **Skipping small-scale calibration**: without first estimating p, there's no principled way to
  choose k or the model before committing to a million-call run.
- **Assuming API reliability doesn't matter**: the paper chose gpt-4.1-mini over the
  cost-optimal gpt-oss-20B partly because OpenAI's API was more operationally reliable than
  together.ai's at the scale of millions of calls — infra reliability is a real cost input at
  this scale, not just $/token and error rate.

## Key Takeaways
1. Estimate p on a cheap, small, ground-truth-known sample before committing to a
   million-call run.
2. Rank candidate models by `c/p` (cost divided by success rate) via Eq. 18/20, not by price or
   reputation alone — the "obviously cheap" or "obviously smart" model is often not the
   cost-optimal one.
3. Per-step error rate stayed flat as task length grew — evidence the approach doesn't
   silently degrade on longer tasks.
4. The task was solved end-to-end with **zero errors** across 1,048,575 steps using a
   *non-reasoning* model (gpt-4.1-mini), not a frontier reasoning model.
5. Voting cost is front-loaded: exponential convergence means the first k_min rounds dominate
   total spend.

## Connects To
- **Ch 3**: every equation used for calibration/cost-projection here (Eq. 12–20).
- **Ch 5**: Section 4.5's red-flagging results are unpacked further in the discussion chapter.
- **Ch 7 (Appendix C)**: exact system/user prompt templates and both parser implementations
  used in these experiments.
