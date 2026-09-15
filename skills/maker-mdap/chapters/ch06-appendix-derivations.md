# Chapter 6: Appendix A/B — Log-Scale Figure and k_min Derivation

## Core Idea
Appendix B derives, in full, why the minimum vote margin needed for a target success
probability grows only logarithmically in the number of steps: `k_min = Θ(ln s)`. This is the
mathematical backbone behind Chapter 3's central scaling claim.

## Key Concepts
- **Starting point**: target overall success probability `t`; want the smallest integer k such
  that `t ≥ p_full = (1 + ((1−p)/p)^k)^(−s/m)`.
- **Substitution**: let `a = t^(−m/s)` and `b = (1−p)/p`. The inequality reduces to
  `a ≥ 1 + b^k`, solved for `k ≥ ln(a−1) / ln(b)` (note `ln b < 0` when `p > 0.5`, which flips
  the inequality direction correctly when solving).
- **Asymptotics**: writing `x = −(m/s)·ln(t)` and using the bounds `x ≤ e^x − 1 ≤ e^x·x` for
  `x ∈ (0,1)`, the derivation sandwiches `ln(t^(−m/s) − 1)` between two terms that both scale as
  `Θ(1) − ln(s)`. Dividing by `ln((1−p)/p) = −Θ(1)` (a constant, independent of s) yields
  `k_min = Θ(ln s)`.

## Reference Tables
| Symbol | Meaning |
|---|---|
| `t` | target overall (whole-task) success probability |
| `m` | steps per subtask (decomposition granularity) |
| `s` | total number of steps in the task |
| `p` | per-step success probability |
| `k_min` | minimum vote margin achieving success probability ≥ t |

## Key Takeaways
1. `k_min` depends on `s` only through a `ln(s)` term — doubling the task length does not
   double the required voting effort, it adds a constant amount.
2. The derivation explicitly assumes `p > 0.5` (so `ln((1−p)/p) < 0`) and `t > e^{-1}` (true in
   practice, since target success probabilities are chosen close to 1).
3. This result, combined with per-vote cost, is exactly what produces the `Θ(s ln s)` total-cost
   scaling law used throughout Chapter 3/4.

## Connects To
- **Ch 3**: uses `k_min = Θ(ln s)` (Eq. 14) directly to derive the `Θ(s ln s)` total cost result
  (Eq. 17–18).
