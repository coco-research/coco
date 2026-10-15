#!/usr/bin/env python3
"""Router regression gate (audit step 3).

Reruns the routing scorer (auto mode, heldout split) and fails if the router
regressed against the newest run file in evals/routing/runs/.

Local embeddings only: meta_select reads COCO_EMBED_URL / COCO_EMBED_MODEL and
this script refuses any non-loopback URL. Any keyword fallback fails the gate,
because a degraded run is not a measurement of the embedding router.

Embeddings are memoised per text for the run, so each team profile and cell
description is embedded once instead of once per item.

    python3 evals/routing/check_regression.py [--tolerance 0.02] [--write PATH]
    python3 evals/routing/check_regression.py --self-test
"""
import argparse, json, pathlib, sys, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNS = ROOT / "evals" / "routing" / "runs"
sys.path.insert(0, str(ROOT / "systems" / "superintelligence" / "scripts"))
sys.path.insert(0, str(ROOT / "evals" / "routing"))

LOOPBACK = {"127.0.0.1", "localhost", "::1"}


def latest_run(runs_dir=RUNS):
    files = sorted(p for p in runs_dir.glob("*.json"))
    return files[-1] if files else None


def compare(prev, cur, tolerance=0.02, delegate_tolerance=0.05):
    """Return a list of failure strings; empty means no regression."""
    fails = []
    if cur["top1_accuracy"] < prev["top1_accuracy"] - tolerance:
        fails.append(f"top-1 {cur['top1_accuracy']:.3f} < previous {prev['top1_accuracy']:.3f} - {tolerance}")
    if cur["delegate_precision"] < prev["delegate_precision"] - delegate_tolerance:
        fails.append(f"delegate precision {cur['delegate_precision']:.3f} < previous "
                     f"{prev['delegate_precision']:.3f} - {delegate_tolerance}")
    return fails


def run_scorer():
    import meta_select, score
    host = urllib.parse.urlparse(meta_select.EMBED_URL).hostname
    if host not in LOOPBACK:
        sys.exit(f"refusing non-local embedding endpoint host {host!r}")
    cache, raw = {}, meta_select.embed

    def embed(texts):
        missing = [t for t in dict.fromkeys(texts) if t not in cache]
        if missing:
            for t, e in zip(missing, raw(missing)):
                cache[t] = e
        return [cache[t] for t in texts]
    meta_select.embed = embed

    fallbacks = []

    def select(prompt):
        r = meta_select.select(prompt)
        if r.get("method") != "embed":
            fallbacks.append(r.get("fallback_reason", "unknown"))
        return r

    items = [json.loads(l) for l in open(ROOT / "evals" / "routing" / "items.jsonl")]
    items = [i for i in items if i["split"] == "heldout"]
    metrics = score.evaluate(items, select)
    if fallbacks:
        sys.exit(f"FAIL: {len(fallbacks)} keyword fallbacks (first: {fallbacks[0]}); embeddings not reachable")
    metrics["run"] = {"mode": "auto", "split": "heldout", "embed_model": meta_select.EMBED_MODEL}
    return metrics


def self_test():
    base = {"top1_accuracy": 0.90, "delegate_precision": 1.0}
    assert compare(base, {"top1_accuracy": 0.89, "delegate_precision": 1.0}) == []
    assert compare(base, {"top1_accuracy": 0.95, "delegate_precision": 1.0}) == []
    assert len(compare(base, {"top1_accuracy": 0.85, "delegate_precision": 1.0})) == 1
    assert len(compare(base, {"top1_accuracy": 0.90, "delegate_precision": 0.80})) == 1
    assert len(compare(base, {"top1_accuracy": 0.10, "delegate_precision": 0.0})) == 2
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        assert latest_run(d) is None
        for n in ("2026-10-15-aaaaaaa.json", "2026-11-01-bbbbbbb.json", "2026-10-20-ccccccc.json"):
            (d / n).write_text("{}")
        assert latest_run(d).name == "2026-11-01-bbbbbbb.json"
    print("check_regression self-test passed")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tolerance", type=float, default=0.02,
                    help="allowed top-1 drop (default 0.02, about 2 of 116 items, for cross-platform float noise)")
    ap.add_argument("--delegate-tolerance", type=float, default=0.05)
    ap.add_argument("--write", metavar="PATH", help="also write this run's metrics JSON")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test(); return
    prev_path = latest_run()
    if prev_path is None:
        sys.exit("FAIL: no run file in evals/routing/runs/")
    prev = json.loads(prev_path.read_text())
    cur = run_scorer()
    print(f"previous {prev_path.name}: top-1 {prev['top1_accuracy']:.3f}, delegate precision {prev['delegate_precision']:.3f}")
    print(f"this run: top-1 {cur['top1_accuracy']:.3f}, delegate precision {cur['delegate_precision']:.3f}, "
          f"top-4 {cur['top4_recall']:.3f}")
    if a.write:
        pathlib.Path(a.write).write_text(json.dumps(cur, indent=2) + "\n")
    fails = compare(prev, cur, a.tolerance, a.delegate_tolerance)
    for f in fails:
        print("REGRESSION:", f)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
