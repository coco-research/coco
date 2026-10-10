#!/usr/bin/env python3
"""Paired candidate-vs-baseline decision stats. Stdlib only.

paired_bootstrap(base, cand) -> (mean_delta, ci_low, ci_high)   95% bootstrap CI
bh_fdr(pvalues, q) -> set of significant indices                Benjamini-Hochberg
decide(base, cand, null_arms, ...) -> accept/reject dict

CLI:
    python3 evals/paired.py --base base.json --cand cand.json [--null n1.json ...]
    python3 evals/paired.py --self-test
"""
import argparse
import json
import math
import random


def paired_bootstrap(base, cand, n_boot=10000, seed=0):
    """95% bootstrap CI for mean(cand - base) over paired items."""
    diffs = [c - b for b, c in zip(base, cand)]
    n = len(diffs)
    mean_delta = sum(diffs) / n
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            s += diffs[rng.randrange(n)]
        means.append(s / n)
    means.sort()
    return mean_delta, means[int(0.025 * n_boot)], means[int(0.975 * n_boot)]


def bh_fdr(pvalues, q=0.1):
    """Indices significant under Benjamini-Hochberg at level q."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    k = 0
    for rank, i in enumerate(order, 1):
        if pvalues[i] <= q * rank / m:
            k = rank
    return set(order[:k])


def _boot_p_greater(vals, n_boot, seed):
    """One-sided bootstrap p-value for mean(vals) > 0."""
    n = len(vals)
    rng = random.Random(seed)
    below = 0
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            s += vals[rng.randrange(n)]
        if s / n <= 0:
            below += 1
    return (below + 1) / (n_boot + 1)


def _no(reason, n, delta=None, ci=None, null_win_rate=None):
    """Reject. Stats that were never computed are None, never a misleading 0."""
    return {"accept": False, "reason": reason, "delta": delta, "ci": ci,
            "n": n, "null_win_rate": null_win_rate}


def _first_nonfinite(vals):
    """Index of the first NaN or ±Infinity, or None when every value is finite."""
    for i, v in enumerate(vals):
        if not math.isfinite(v):
            return i
    return None


def decide(base, cand, null_arms, min_n=30, q=0.1, max_team_drop=None):
    """Accept iff: n >= min_n, the 95% CI excludes 0, and the candidate beats
    every null arm (cosmetic edits) by more than the null arm beats the
    baseline. max_team_drop, when set, additionally rejects if any single item
    regresses by more than that amount.
    Raises ValueError if any score is not finite (NaN, Infinity, -Infinity)."""
    n = len(base)
    if len(cand) != n or any(len(a) != n for a in null_arms):
        raise ValueError("all arms must have the same length (same item order)")
    for arm_name, vals in (("base", base), ("cand", cand)):
        i = _first_nonfinite(vals)
        if i is not None:
            raise ValueError(f"non-finite score at item {i} in {arm_name}")
    for j, arm in enumerate(null_arms):
        i = _first_nonfinite(arm)
        if i is not None:
            raise ValueError(f"non-finite score at item {i} in null[{j}]")
    if n < min_n:
        return _no(f"n={n} < min_n={min_n}", n)
    delta, lo, hi = paired_bootstrap(base, cand)
    if lo <= 0.0:
        return _no(f"95% CI [{lo:.4f}, {hi:.4f}] does not exclude 0 on the positive side", n, delta, [lo, hi])
    if max_team_drop is not None:
        for i, (b, c) in enumerate(zip(base, cand)):
            if c - b < -max_team_drop:
                return _no(f"item {i} regresses {b - c:.4f} > max_team_drop={max_team_drop}", n, delta, [lo, hi])
    null_win_rate = 0.0
    if null_arms:
        # Excess per item: (cand - null) - (null - base) = cand - 2*null + base.
        excess = [[c - 2.0 * a + b for b, a, c in zip(base, arm, cand)] for arm in null_arms]
        pvals = [_boot_p_greater(e, 10000, 0) for e in excess]
        wins = len(null_arms) - len(bh_fdr(pvals, q))
        null_win_rate = wins / len(null_arms)
        if wins:
            return _no(f"candidate fails to beat {wins}/{len(null_arms)} null arms "
                       f"beyond the null's own gain over baseline", n, delta, [lo, hi], null_win_rate)
    return {"accept": True,
            "reason": "candidate beats baseline (CI excludes 0) and every null arm beyond cosmetic gains",
            "delta": delta, "ci": [lo, hi], "n": n, "null_win_rate": null_win_rate}


def _load(path):
    def reject(token):
        raise ValueError(f"{path}: {token} is not a finite number")

    with open(path) as f:
        vals = json.load(f, parse_constant=reject)
    if not isinstance(vals, list) or not all(isinstance(v, (int, float)) for v in vals):
        raise SystemExit(f"{path}: expected a JSON list of numbers")
    i = _first_nonfinite(vals)
    if i is not None:
        raise SystemExit(f"{path}: item {i} is not a finite number")
    return [float(v) for v in vals]


def _self_test():
    rng = random.Random(7)

    def arm(n, mu, sd):
        return [rng.gauss(mu, sd) for _ in range(n)]

    # 1. Real effect -> must accept.
    base = arm(100, 0.50, 0.05)
    cand = [x + 0.10 + rng.gauss(0, 0.02) for x in base]
    d = decide(base, cand, [])
    assert d["accept"] and d["ci"][0] > 0, d

    # 2. No effect -> must reject (CI includes 0).
    d = decide(base, [x + rng.gauss(0, 0.05) for x in base], [])
    assert not d["accept"] and "CI" in d["reason"], d

    # 3. n=10 -> must reject on min_n.
    small = arm(10, 0.50, 0.05)
    d = decide(small, [x + 0.10 for x in small], [])
    assert not d["accept"] and "min_n" in d["reason"], d

    # 4. One null ties the candidate -> nulls win half the arms -> must reject.
    cand = [x + 0.10 for x in base]
    tie = list(cand)
    cosmetic = [x + rng.gauss(0, 0.005) for x in base]
    d = decide(base, cand, [tie, cosmetic])
    assert not d["accept"] and d["null_win_rate"] == 0.5, d

    # 5. Clearly worse candidate -> must reject (CI entirely below 0).
    d = decide(base, [x - 0.10 for x in base], [])
    assert not d["accept"] and "CI" in d["reason"], d
    assert d["delta"] < -0.05 and d["ci"][1] < 0, d  # measured stats are reported, not zeroed

    # 6–8. Non-finite scores are invalid. Never accept (NaN used to pass the CI gate).
    def _nonfinite_rejected(fn, item, arm):
        expected = f"non-finite score at item {item} in {arm}"
        try:
            got = fn()
        except ValueError as e:
            assert str(e) == expected, e
            return
        assert not got["accept"] and got["reason"] == expected, got

    nan_cand = list(cand)
    nan_cand[0] = float("nan")
    _nonfinite_rejected(lambda: decide(base, nan_cand, []), 0, "cand")

    nan_base = list(base)
    nan_base[0] = float("nan")
    _nonfinite_rejected(lambda: decide(nan_base, cand, []), 0, "base")

    inf_null = list(base)
    inf_null[0] = float("inf")
    _nonfinite_rejected(lambda: decide(base, cand, [inf_null]), 0, "null[0]")

    print("self-test: 8/8 passed")


def main():
    ap = argparse.ArgumentParser(description="Paired candidate-vs-baseline decision.")
    ap.add_argument("--base", help="JSON list of baseline scores, one per item")
    ap.add_argument("--cand", help="JSON list of candidate scores, same item order")
    ap.add_argument("--null", action="append", default=[], metavar="N.JSON",
                    help="JSON list of cosmetic-edit arm scores (repeatable)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        _self_test()
        return
    if not (a.base and a.cand):
        ap.error("--base and --cand are required (or use --self-test)")
    print(json.dumps(decide(_load(a.base), _load(a.cand), [_load(p) for p in a.null]), indent=2))


if __name__ == "__main__":
    main()
