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
import sys


def _finite(v):
    try:
        return math.isfinite(v)
    except OverflowError:  # a JSON int of ~309+ digits cannot become a float
        return False


def _require_scores(vals, where):
    """Scores must be real and finite. bool is a subclass of int, so check it first."""
    for i, v in enumerate(vals):
        if isinstance(v, bool):
            raise ValueError(f"boolean score at item {i} in {where}")
        if not _finite(v):
            raise ValueError(f"non-finite score at item {i} in {where}")


def paired_bootstrap(base, cand, n_boot=10000, seed=0):
    """95% bootstrap CI for mean(cand - base) over paired items."""
    if len(base) != len(cand):
        raise ValueError(
            f"base and cand must have the same length ({len(base)} != {len(cand)})")
    if len(base) < 1:
        raise ValueError("inputs must be non-empty")
    _require_scores(base, "base")
    _require_scores(cand, "cand")
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
    """Indices significant under Benjamini-Hochberg at level q.
    Raises ValueError unless every p-value is finite and in [0, 1] and 0 < q <= 1."""
    if isinstance(q, bool) or not isinstance(q, (int, float)) or not _finite(q) or not 0.0 < q <= 1.0:
        raise ValueError("q must be a finite number in (0, 1]")
    for i, p in enumerate(pvalues):
        # bool is a subclass of int and would sort as 0 or 1.
        if (isinstance(p, bool) or not isinstance(p, (int, float))
                or not math.isfinite(p) or not 0.0 <= p <= 1.0):
            raise ValueError(f"p-value at index {i} must be finite and in [0, 1]")
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


def decide(base, cand, null_arms, min_n=30, q=0.1, max_team_drop=None):
    """Accept iff: n >= min_n, the 95% CI excludes 0, and the candidate beats
    every null arm (cosmetic edits) by more than the null arm beats the
    baseline. max_team_drop, when set, additionally rejects if any single item
    regresses by more than that amount.
    Raises ValueError if min_n < 1, inputs are empty, arm lengths differ,
    or any score is a boolean or not finite (NaN, Infinity, -Infinity)."""
    if min_n < 1:
        raise ValueError("min_n must be >= 1")
    n = len(base)
    if len(cand) != n or any(len(a) != n for a in null_arms):
        raise ValueError("all arms must have the same length (same item order)")
    if n < 1:
        raise ValueError("inputs must be non-empty")
    for arm_name, vals in (("base", base), ("cand", cand)):
        _require_scores(vals, arm_name)
    for j, arm in enumerate(null_arms):
        _require_scores(arm, f"null[{j}]")
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
    if not isinstance(vals, list):
        raise ValueError(f"{path}: expected a JSON list of numbers")
    for i, v in enumerate(vals):
        # bool is a subclass of int; float(True) is 1.0 and would look like a score.
        if isinstance(v, bool):
            raise ValueError(f"{path}: item {i} is a boolean, not a number")
        if not isinstance(v, (int, float)):
            raise ValueError(f"{path}: expected a JSON list of numbers")
        if not _finite(v):
            raise ValueError(f"{path}: item {i} is not a finite number")
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

    # 9. Booleans are not scores. [false]*40 vs [true]*40 used to accept (bool subclasses int).
    def _raises(fn, match):
        try:
            got = fn()
        except ValueError as e:
            assert match in str(e), e
            return
        raise AssertionError(f"expected ValueError containing {match!r}, got {got!r}")

    _raises(lambda: decide([False] * 40, [True] * 40, []), "boolean score at item 0 in base")

    # 10. min_n < 1 is invalid. Empty inputs crash the mean; reject them instead.
    _raises(lambda: decide([0.5] * 40, [0.6] * 40, [], min_n=0), "min_n must be >= 1")
    _raises(lambda: paired_bootstrap([], []), "inputs must be non-empty")
    _raises(lambda: decide([], [], []), "inputs must be non-empty")

    # 11. Extra items must not be dropped by zip.
    _raises(lambda: paired_bootstrap([0.1, 0.2, 0.3], [0.2, 0.3]), "same length")

    # 12. p-values: NaN used to be marked significant; 1.5 and -0.2 were accepted.
    assert bh_fdr([0.0, 1.0], q=0.1) == {0}
    for bad_q in (True, float("nan"), 0, -0.1, 1.5, "0.1", 10 ** 400):
        _raises(lambda bad_q=bad_q: bh_fdr([0.01], q=bad_q), "q must be a finite number in (0, 1]")
    for bad in (float("nan"), float("inf"), 1.5, -0.2, True):
        _raises(lambda bad=bad: bh_fdr([0.04, bad]), "must be finite and in [0, 1]")

    # 13. NaN in a null arm.
    nan_null = list(base)
    nan_null[4] = float("nan")
    _nonfinite_rejected(lambda: decide(base, cand, [nan_null]), 4, "null[0]")

    # 14. One item regressing past max_team_drop rejects even when the CI is positive.
    drop_cand = [1.0] * 40
    drop_cand[7] = 0.50 - 0.30
    d = decide([0.50] * 40, drop_cand, [], max_team_drop=0.10)
    assert not d["accept"] and "item 7" in d["reason"] and "max_team_drop" in d["reason"], d

    # 15. Loader rejects booleans, non-numbers, and NaN/Infinity tokens.
    import os
    import shutil
    import tempfile

    def _loader_rejects(text, match):
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(text)
            _raises(lambda: _load(path), match)
        finally:
            os.remove(path)

    _loader_rejects("[true, false]", "boolean, not a number")
    _loader_rejects("[" + "9" * 400 + "]", "not a finite number")
    _raises(lambda: decide([10 ** 400] * 40, [0.5] * 40, []), "non-finite score at item 0 in base")
    _loader_rejects("[1, \"x\"]", "expected a JSON list of numbers")
    _loader_rejects("[1, null]", "expected a JSON list of numbers")
    _loader_rejects("{\"a\": 1}", "expected a JSON list of numbers")
    _loader_rejects("[1, NaN]", "not a finite number")
    _loader_rejects("[1, Infinity]", "not a finite number")

    # 16. CLI: every ValueError is one stderr line and a non-zero exit. No traceback.
    import subprocess

    def _cli_error(base_text, cand_text):
        td = tempfile.mkdtemp()
        try:
            bp = os.path.join(td, "base.json")
            cp = os.path.join(td, "cand.json")
            with open(bp, "w") as f:
                f.write(base_text)
            with open(cp, "w") as f:
                f.write(cand_text)
            r = subprocess.run(
                [sys.executable, os.path.abspath(__file__), "--base", bp, "--cand", cp],
                capture_output=True, text=True)
            assert r.returncode != 0, (r.returncode, r.stdout, r.stderr)
            assert "Traceback" not in r.stderr and "Traceback" not in r.stdout, r.stderr
            line = r.stderr.strip()
            assert line and "\n" not in line, r.stderr
            return line
        finally:
            shutil.rmtree(td)

    err = _cli_error(json.dumps([False] * 40), json.dumps([True] * 40))
    assert "boolean" in err, err
    err = _cli_error("[0.1, 0.2]", "[0.3]")
    assert "same length" in err, err
    err = _cli_error("[1, NaN]", "[1, 2]")
    assert "finite" in err, err
    err = _cli_error("[]", "[]")
    assert "non-empty" in err, err

    print("self-test: 16/16 passed")


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
    try:
        result = decide(_load(a.base), _load(a.cand), [_load(p) for p in a.null])
    except ValueError as e:
        print(e, file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
