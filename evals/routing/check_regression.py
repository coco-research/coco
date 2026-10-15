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


def _run_date(p):
    """Sort key: the run's own date (run.date), else the YYYY-MM-DD filename prefix."""
    import datetime
    d = None
    try:
        d = (json.loads(p.read_text()).get("run") or {}).get("date")
    except Exception:
        pass
    for cand in (d, p.name[:10]):
        try:
            return (datetime.date.fromisoformat(cand), p.name)
        except (TypeError, ValueError):
            continue
    return (datetime.date.min, p.name)


def latest_run(runs_dir=RUNS):
    files = sorted(runs_dir.glob("*.json"), key=_run_date)
    return files[-1] if files else None


def model_digest(embed_url, model):
    """Ollama model digest (the tag is floating). None if not an Ollama endpoint."""
    import urllib.request
    u = urllib.parse.urlparse(embed_url)
    try:
        with urllib.request.urlopen(f"{u.scheme}://{u.netloc}/api/tags", timeout=5) as r:
            for m in json.load(r).get("models", []):
                if m.get("name") in (model, model + ":latest") or m.get("model") in (model, model + ":latest"):
                    return m.get("digest")
    except Exception:
        return None
    return None


def compare(prev, cur, tolerance=0.02, delegate_tolerance=0.05):
    """Return a list of failure strings; empty means no regression."""
    fails = []
    if cur["top1_accuracy"] < prev["top1_accuracy"] - tolerance:
        fails.append(f"top-1 {cur['top1_accuracy']:.3f} < previous {prev['top1_accuracy']:.3f} - {tolerance}")
    if cur["delegate_precision"] < prev["delegate_precision"] - delegate_tolerance:
        fails.append(f"delegate precision {cur['delegate_precision']:.3f} < previous "
                     f"{prev['delegate_precision']:.3f} - {delegate_tolerance}")
    pd, cd = (prev.get("run") or {}).get("embed_digest"), (cur.get("run") or {}).get("embed_digest")
    if pd and not cd:
        fails.append(f"baseline pins embedding digest {pd[:12]} but this run has none (tags lookup failed?)")
    elif pd and cd and pd != cd:
        fails.append(f"embedding model digest {cd[:12]} != pinned {pd[:12]}; re-baseline in a separate PR")
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
    metrics["run"] = {"mode": "auto", "split": "heldout", "embed_model": meta_select.EMBED_MODEL,
                      "embed_digest": model_digest(meta_select.EMBED_URL, meta_select.EMBED_MODEL)}
    return metrics


def probe_exit(ok, ref):
    """Exit code when the local Ollama probe result is `ok`: a miss fails on main, skips elsewhere."""
    if ok:
        return 0
    return 1 if ref == "refs/heads/main" else 0


def probe(url="http://127.0.0.1:11434", model="nomic-embed-text"):
    import shutil, subprocess, urllib.request
    try:
        urllib.request.urlopen(f"{url}/api/version", timeout=3)
    except Exception:
        return False
    if not shutil.which("ollama"):
        return False
    return subprocess.run(["ollama", "show", model], capture_output=True, timeout=30).returncode == 0


def self_test():
    base = {"top1_accuracy": 0.90, "delegate_precision": 1.0}
    assert compare(base, {"top1_accuracy": 0.89, "delegate_precision": 1.0}) == []
    assert compare(base, {"top1_accuracy": 0.95, "delegate_precision": 1.0}) == []
    assert len(compare(base, {"top1_accuracy": 0.85, "delegate_precision": 1.0})) == 1
    assert len(compare(base, {"top1_accuracy": 0.90, "delegate_precision": 0.80})) == 1
    assert len(compare(base, {"top1_accuracy": 0.10, "delegate_precision": 0.0})) == 2
    pin = dict(base, run={"embed_digest": "a" * 64})
    assert compare(pin, dict(base, run={"embed_digest": "a" * 64})) == []
    assert len(compare(pin, dict(base, run={"embed_digest": "b" * 64}))) == 1
    assert compare(base, dict(base, run={"embed_digest": "b" * 64})) == []
    assert len(compare(pin, dict(base, run={"embed_digest": None}))) == 1
    assert len(compare(pin, dict(base))) == 1
    assert compare(base, dict(base)) == []
    assert probe_exit(True, "refs/heads/main") == 0
    assert probe_exit(False, "refs/heads/main") == 1
    assert probe_exit(False, "refs/pull/345/merge") == 0
    assert probe_exit(False, "") == 0
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        assert latest_run(d) is None
        for n in ("2026-10-15-aaaaaaa.json", "2026-11-01-bbbbbbb.json", "2026-10-20-ccccccc.json"):
            (d / n).write_text("{}")
        assert latest_run(d).name == "2026-11-01-bbbbbbb.json"
        (d / "zz-misc.json").write_text(json.dumps({"run": {"date": "2026-10-01"}}))
        assert latest_run(d).name == "2026-11-01-bbbbbbb.json"
    print("check_regression self-test passed")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tolerance", type=float, default=0.02,
                    help="allowed top-1 drop (default 0.02, about 2 of 116 items, for cross-platform float noise)")
    ap.add_argument("--delegate-tolerance", type=float, default=0.05)
    ap.add_argument("--write", metavar="PATH", help="also write this run's metrics JSON")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--probe", action="store_true",
                    help="check local Ollama + model; write ok=0/1 to $GITHUB_OUTPUT; exit 1 on a miss only on main")
    a = ap.parse_args()
    if a.self_test:
        self_test(); return
    if a.probe:
        import os
        ok = probe()
        out = os.environ.get("GITHUB_OUTPUT")
        if out:
            with open(out, "a") as f:
                f.write(f"ok={int(ok)}\n")
        ref = os.environ.get("GITHUB_REF", "")
        code = probe_exit(ok, ref)
        if not ok:
            print(("FAIL" if code else "SKIP") + ": no local Ollama on 127.0.0.1:11434 or nomic-embed-text "
                  f"not present ({ref or 'no ref'}); router gate not run")
        sys.exit(code)
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
