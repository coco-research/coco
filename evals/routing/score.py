import sys
import json
import argparse
import datetime
import hashlib
import pathlib
import subprocess

def run_self_test():
    print("Running self-test with synthetic data...")
    synthetic_items = [
        {"id": "s1", "prompt": "AI stuff", "label": "ai", "kind": "positive", "split": "heldout"},
        {"id": "s2", "prompt": "Trading stuff", "label": "trading", "kind": "positive", "split": "heldout"},
        {"id": "s3", "prompt": "Finance stuff", "label": "finance", "kind": "near-miss", "split": "heldout"},
        {"id": "s4", "prompt": "Chit chat", "label": "none", "kind": "none", "split": "heldout"},
        {"id": "s5", "prompt": "More AI", "label": "ai", "kind": "positive", "split": "heldout"},
        {"id": "s6", "prompt": "Unknown", "label": "none", "kind": "none", "split": "heldout"}
    ]
    
    def stub_select(prompt):
        if "AI" in prompt:
            return {"delegate": True, "delegate_team": "ai", "teams": [{"team_key": "ai"}, {"team_key": "engineering"}]}
        elif "Trading" in prompt:
            return {"delegate": False, "delegate_team": None, "teams": [{"team_key": "finance"}, {"team_key": "trading"}]}
        elif "Finance" in prompt:
            return {"delegate": True, "delegate_team": "finance", "teams": [{"team_key": "finance"}]}
        else:
            # None returns empty or some random ones
            return {"delegate": False, "delegate_team": None, "teams": []}

    results = evaluate(synthetic_items, stub_select)
    print("Results from stub_select:")
    print(json.dumps(results, indent=2))
    
    try:
        assert results["top1_accuracy"] == 0.75, f"Expected 0.75, got {results['top1_accuracy']}"
        assert results["top4_recall"] == 1.0, f"Expected 1.0, got {results['top4_recall']}"
        assert results["delegate_precision"] == 1.0, f"Expected 1.0, got {results['delegate_precision']}"
        assert results["abstain_rate"] == 1.0, f"Expected 1.0, got {results['abstain_rate']}"
        assert results["per_team_top1"]["ai"] == 1.0, f"Expected 1.0, got {results['per_team_top1']['ai']}"
        assert results["per_team_top1"]["trading"] == 0.0, f"Expected 0.0, got {results['per_team_top1']['trading']}"
        assert results["per_team_top1"]["finance"] == 1.0, f"Expected 1.0, got {results['per_team_top1']['finance']}"
    except AssertionError as e:
        print("AssertionError:", e)
        sys.exit(1)

    def negative_stub_select(prompt):
        return {"delegate": False, "delegate_team": None, "teams": [{"team_key": "wrong_team"}]}

    negative_results = evaluate(synthetic_items, negative_stub_select)
    print("Results from negative_stub_select:")
    print(json.dumps(negative_results, indent=2))
    try:
        assert negative_results["top1_accuracy"] == 0.0, f"Expected 0.0, got {negative_results['top1_accuracy']}"
    except AssertionError as e:
        print("AssertionError:", e)
        sys.exit(1)

    print("Self-test passed!")
    sys.exit(0)

def evaluate(items, select_fn):
    total = 0
    top1_correct = 0
    top4_correct = 0
    
    delegate_total = 0
    delegate_correct = 0
    
    none_total = 0
    none_abstained = 0
    
    per_team = {}

    for item in items:
        label = item["label"]
        res = select_fn(item["prompt"])
        
        teams = [t.get("team_key") for t in res.get("teams", [])]
        delegate = res.get("delegate", False)
        # delegate_team in res is team_id, but we need team_key. 
        # If delegate is True, it delegates to the first team.
        delegate_team_key = teams[0] if delegate and teams else None

        if label != "none":
            total += 1
            if label not in per_team:
                per_team[label] = {"total": 0, "top1": 0}
            per_team[label]["total"] += 1
            
            if teams and teams[0] == label:
                top1_correct += 1
                per_team[label]["top1"] += 1
                
            if label in teams[:4]:
                top4_correct += 1
                
            if delegate and delegate_team_key:
                delegate_total += 1
                if delegate_team_key == label:
                    delegate_correct += 1
        else:
            none_total += 1
            # Abstain means router didn't pick any team or didn't auto-delegate?
            # Actually, "none" implies off-topic. A perfect router would return empty teams or at least not delegate.
            # But the requirement: "abstain rate (on 'none' items)"
            # Usually, abstain means delegate is false or teams list is empty.
            # Meta select returns delegate=False and some teams with low scores.
            # Maybe abstain = not delegate? Or empty teams?
            # We'll define abstain as `not delegate`.
            if not delegate:
                none_abstained += 1

    metrics = {
        "top1_accuracy": top1_correct / total if total else 0.0,
        "top4_recall": top4_correct / total if total else 0.0,
        "delegate_precision": delegate_correct / delegate_total if delegate_total else 0.0,
        "abstain_rate": none_abstained / none_total if none_total else 0.0,
        "per_team_top1": {
            t: (stats["top1"] / stats["total"]) if stats["total"] else 0.0
            for t, stats in per_team.items()
        }
    }
    return metrics

def _items_path(root, given):
    if not given:
        return root / "evals" / "routing" / "items.jsonl"
    path = pathlib.Path(given)
    if path.is_absolute():
        return path
    from_cwd = pathlib.Path.cwd() / path
    if from_cwd.exists():
        return from_cwd
    return root / path


def _rel_items(root, path):
    resolved = path.resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return resolved.as_posix()


def _commit(root):
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def _scored_method(methods):
    """embed or keyword only when every routed call used that method. Anything else is mixed."""
    kinds = set(methods)
    if kinds == {"embed"}:
        return "embed"
    if kinds == {"keyword"}:
        return "keyword"
    return "mixed"


def _run_meta(items, mode, split_name, embed_model, embed_url, commit):
    """Same run fields the held-out record carries: date, commit, task count, model."""
    labelled = sum(1 for item in items if item.get("label") != "none")
    return {
        "commit": commit,
        "date": datetime.date.today().isoformat(),
        "mode": mode,
        "split": split_name,
        "n_labelled": labelled,
        "n_none": sum(1 for item in items if item.get("label") == "none"),
        "embed_model": embed_model,
        "embed": {"model": embed_model, "url": embed_url},
    }


def main():
    parser = argparse.ArgumentParser(description="T1 routing evaluation")
    parser.add_argument("--split", choices=["train", "heldout"], default="heldout")
    parser.add_argument("--mode", choices=["auto", "keyword"], default="auto")
    parser.add_argument("--json", type=str, metavar="PATH", help="Path to write JSON report")
    parser.add_argument("--items", default=None,
                        help="JSONL items (default: evals/routing/items.jsonl)")
    parser.add_argument("--split-name", default=None,
                        help="record this split name, the items path, and items_sha256")
    parser.add_argument("--vs-keyword", action="store_true",
                        help="add vs_keyword.baseline_top1 from keyword mode on the same items")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()

    root = pathlib.Path(__file__).resolve().parents[2]
    scripts_dir = root / "systems" / "superintelligence" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    
    import meta_select
    
    items_path = _items_path(root, args.items)
    items = []
    with open(items_path, "r") as f:
        for line in f:
            item = json.loads(line)
            if item["split"] == args.split:
                items.append(item)

    # A named auto record is a measurement of the embedding router. Keyword
    # fallback must not be written as that number. COCO_EMBED_URL overrides
    # the default http://127.0.0.1:1234/v1/embeddings (see meta_select).
    record = bool(args.split_name or args.vs_keyword)
    strict_auto = args.mode == "auto" and record
    if strict_auto:
        try:
            meta_select.embed(["."])
        except Exception as e:
            print(f"embedding server not reachable at {meta_select.EMBED_URL}: "
                  f"{type(e).__name__}: {e}", file=sys.stderr)
            print("refusing to write a keyword score as the router top-1", file=sys.stderr)
            sys.exit(1)

    if args.mode == "keyword":
        # Force keyword mode by wrapping select to catch and fallback, or monkeypatching
        # `meta_select.EMBED_URL` to something invalid, or directly calling `select_keyword`.
        def select_fn(prompt):
            profs = meta_select.team_profiles()
            return meta_select.select_keyword(prompt, profs)
    elif strict_auto:
        profs = meta_select.team_profiles()

        def select_fn(prompt):
            return meta_select.select_embed(prompt, profs)
    else:
        select_fn = meta_select.select

    # Count the scored calls only. The vs_keyword baseline is a separate pass.
    routed_methods = []

    def select_routed(prompt):
        res = select_fn(prompt)
        routed_methods.append(res.get("method") if isinstance(res, dict) else None)
        return res

    try:
        metrics = evaluate(items, select_routed)
    except Exception as e:
        if strict_auto:
            print(f"embedding server failed during scoring at {meta_select.EMBED_URL}: "
                  f"{type(e).__name__}: {e}", file=sys.stderr)
            print("refusing to write a keyword score as the router top-1", file=sys.stderr)
            sys.exit(1)
        raise
    scored_method = _scored_method(routed_methods)
    if strict_auto and scored_method != "embed":
        print(f"routed method was {scored_method}, not embed", file=sys.stderr)
        print("refusing to write a keyword score as the router top-1", file=sys.stderr)
        sys.exit(1)

    if args.vs_keyword:
        def keyword_fn(prompt):
            profs = meta_select.team_profiles()
            return meta_select.select_keyword(prompt, profs)
        metrics["vs_keyword"] = {"baseline_top1": evaluate(items, keyword_fn)["top1_accuracy"]}

    if args.split_name:
        metrics["split"] = args.split_name
        metrics["items"] = _rel_items(root, items_path)
        metrics["items_sha256"] = hashlib.sha256(items_path.read_bytes()).hexdigest()

    if record:
        metrics["run"] = _run_meta(
            items, args.mode, args.split_name or args.split,
            meta_select.EMBED_MODEL, meta_select.EMBED_URL, _commit(root))

    metrics["method"] = scored_method
    # Keyword mode is the method itself. A fallback is a keyword call while mode is auto.
    metrics["keyword_fallbacks"] = (
        sum(1 for method in routed_methods if method == "keyword")
        if args.mode == "auto" else 0)

    if args.json:
        report_json = json.dumps(metrics, indent=2)
        print(report_json)
        with open(args.json, "w") as f:
            f.write(report_json)
    else:
        print(f"Top-1 Accuracy: {metrics['top1_accuracy']:.2%}")
        print(f"Top-4 Recall:   {metrics['top4_recall']:.2%}")
        print(f"Delegate Prec:  {metrics['delegate_precision']:.2%}")
        print(f"Abstain Rate:   {metrics['abstain_rate']:.2%}")
        print("Per-team Top-1:")
        for t, acc in metrics["per_team_top1"].items():
            print(f"  {t}: {acc:.2%}")

if __name__ == "__main__":
    main()
