#!/usr/bin/env python3
"""Score one agent skill on a fixed dev or held-out item split. Stdlib only.

Held-out records carry ids and scores only: no model outputs and no grader notes.
The executor is local. COCO_SKILL_EXEC_URL must be a loopback host, the same
rule as the router regression gate.

Directory names starting with "_" are fixtures for this harness, not pilots.

    python3 evals/skills/score.py --skill NAME --split dev|heldout [--executor ollama|stub]
                                   [--skill-md PATH] [--out FILE]
    python3 evals/skills/score.py --self-test
"""
import argparse
import datetime
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys

import run

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "evals" / "skills"
SEED = 0
# Directory names starting with "_" are fixtures for this harness, not pilots.
_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_-]*")
_META = {
    "commit", "date", "skill", "split", "executor", "model", "seed",
    "items_sha256", "grader_sha256", "skill_sha256", "n", "mean", "per_item",
}


def die(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(2)


def _shown(path):
    path = pathlib.Path(path)
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def git_short():
    r = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        err = r.stderr.strip().splitlines()
        die(err[-1] if err else "git rev-parse failed")
    return r.stdout.strip()


def _finite(v):
    try:
        return math.isfinite(v)
    except OverflowError:
        return False


def load_items(path):
    path = pathlib.Path(path)
    items, seen = [], set()
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            die(f"{_shown(path)}:{lineno}: invalid JSON")
        if not isinstance(item, dict):
            die(f"{_shown(path)}:{lineno}: item must be an object")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            die(f"{_shown(path)}:{lineno}: id must be a non-empty string")
        if item_id in seen:
            die(f"duplicate id {item_id}")
        seen.add(item_id)
        split = item.get("split")
        if split not in ("dev", "heldout"):
            die(f"unknown split {split!r} for {item_id}")
        if not isinstance(item.get("input"), str):
            die(f"{item_id}: input must be a string")
        items.append(item)
    return items


def load_grader(path):
    path = pathlib.Path(path)
    ns = {}
    try:
        exec(compile(path.read_text(), _shown(path), "exec"), ns)
    except SyntaxError as e:
        die(f"{_shown(path)}: {e.msg}")
    grade = ns.get("grade")
    if not callable(grade):
        die(f"{_shown(path)} must expose grade(item, output)")
    return grade


def _check_result(item_id, result):
    if not isinstance(result, dict) or "score" not in result or "notes" not in result:
        die(f"grader result for {item_id} must include score and notes")
    score, notes = result["score"], result["notes"]
    bad = (
        isinstance(score, bool) or not isinstance(score, (int, float))
        or not _finite(score) or not 0.0 <= score <= 1.0
    )
    if bad:
        die(f"invalid score for {item_id}: {score!r}")
    if not isinstance(notes, list) or any(not isinstance(n, str) for n in notes):
        die(f"notes for {item_id} must be a list of strings")
    return float(score), notes


def score_run(name, split, executor, items_path, grader_path, skill_md_path, *, model, seed, url):
    """Score one split. Held-out records omit outputs and notes."""
    if split not in ("dev", "heldout"):
        die(f"unknown split {split!r}")
    if executor not in ("ollama", "stub"):
        die(f"unknown executor {executor!r}")
    items_path, grader_path, skill_md_path = map(pathlib.Path, (items_path, grader_path, skill_md_path))
    for path in (items_path, grader_path, skill_md_path):
        if not path.is_file():
            die(f"missing {_shown(path)}")
    chosen = [it for it in load_items(items_path) if it["split"] == split]
    if not chosen:
        die(f"no items in split {split}")
    grade = load_grader(grader_path)
    skill_md = skill_md_path.read_text()
    per_item, outputs, notes = {}, {}, {}
    for item in chosen:
        item_id, user_input = item["id"], item["input"]
        if executor == "stub":
            output = run.stub(skill_md, user_input, model=model or "", url=url, seed=seed)
        else:
            output = run.generate(skill_md, user_input, model=model, url=url, seed=seed)
        score, note_list = _check_result(item_id, grade(item, output))
        per_item[item_id] = score
        outputs[item_id] = output
        notes[item_id] = note_list
    record = {
        "commit": git_short(),
        "date": datetime.date.today().isoformat(),
        "skill": name,
        "split": split,
        "executor": executor,
        "model": model,
        "seed": seed,
        "items_sha256": sha256_file(items_path),
        "grader_sha256": sha256_file(grader_path),
        "skill_sha256": sha256_file(skill_md_path),
        "n": len(per_item),
        "mean": sum(per_item.values()) / len(per_item),
        "per_item": per_item,
    }
    # Held-out records stay numeric: a proposer must not see outputs or notes.
    if split == "dev":
        record["outputs"] = outputs
        record["notes"] = notes
    return record


def record_json(record):
    return json.dumps(record, indent=2) + "\n"


def _py(script, env=None):
    return subprocess.run(
        [sys.executable, "-c", script], cwd=HERE, env=env, capture_output=True, text=True,
    )


def _cli(*args):
    return subprocess.run(
        [sys.executable, str(HERE / "score.py"), *args],
        cwd=ROOT, capture_output=True, text=True,
    )


def _expect_exit_2(items_text, grader_src, needle):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        (p / "items.jsonl").write_text(items_text)
        (p / "grader.py").write_text(grader_src)
        (p / "SKILL.md").write_text("# Toy\nRepeat.\n")
        script = (
            "import score\n"
            "score.score_run('_t', 'dev', 'stub', {items!r}, {grader!r}, {skill!r}, "
            "model=None, seed=0, url={url!r})\n"
        ).format(
            items=str(p / "items.jsonl"), grader=str(p / "grader.py"),
            skill=str(p / "SKILL.md"), url=run.DEFAULT_URL,
        )
        r = _py(script)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    err = r.stderr.strip()
    assert err and "\n" not in err, r.stderr
    assert "Traceback" not in r.stderr and "Traceback" not in r.stdout
    assert needle in err, err


def _assert_hashes_track_files():
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        dest = pathlib.Path(td) / "_selftest"
        shutil.copytree(HERE / "_selftest", dest)

        def rec():
            return score_run(
                "_selftest", "dev", "stub",
                dest / "items.jsonl", dest / "grader.py", dest / "SKILL.md",
                model=None, seed=SEED, url=run.DEFAULT_URL,
            )

        first = rec()
        for key, filename in (
            ("items_sha256", "items.jsonl"),
            ("grader_sha256", "grader.py"),
            ("skill_sha256", "SKILL.md"),
        ):
            assert re.fullmatch(r"[0-9a-f]{64}", first[key])
            assert first[key] == sha256_file(dest / filename)
        (dest / "SKILL.md").write_bytes((dest / "SKILL.md").read_bytes() + b"\n")
        second = rec()
        assert second["skill_sha256"] != first["skill_sha256"]
        assert second["items_sha256"] == first["items_sha256"]
        assert second["grader_sha256"] == first["grader_sha256"]
        (dest / "items.jsonl").write_bytes((dest / "items.jsonl").read_bytes() + b"\n")
        third = rec()
        assert third["items_sha256"] != second["items_sha256"]
        assert third["grader_sha256"] == second["grader_sha256"]
        assert third["skill_sha256"] == second["skill_sha256"]
        (dest / "grader.py").write_bytes((dest / "grader.py").read_bytes() + b"\n")
        fourth = rec()
        assert fourth["grader_sha256"] != third["grader_sha256"]
        assert fourth["items_sha256"] == third["items_sha256"]
        assert fourth["skill_sha256"] == third["skill_sha256"]


def _assert_loopback():
    import os
    env = os.environ.copy()
    env.pop("COCO_SKILL_EXEC_URL", None)
    ok = _py("import run; run.executor_url()", env)
    assert ok.returncode == 0, ok.stderr
    for url in ("http://127.0.0.1:11434", "http://localhost:11434", "http://[::1]:11434"):
        env["COCO_SKILL_EXEC_URL"] = url
        ok = _py("import run; run.executor_url()", env)
        assert ok.returncode == 0, (url, ok.stderr)
    env["COCO_SKILL_EXEC_URL"] = "http://example.com:11434"
    bad = _py("import run; run.executor_url()", env)
    assert bad.returncode != 0, "non-loopback COCO_SKILL_EXEC_URL was accepted"
    assert "example.com" in bad.stderr and "Traceback" not in bad.stderr, bad.stderr
    import importlib.util
    path = ROOT / "evals" / "routing" / "check_regression.py"
    spec = importlib.util.spec_from_file_location("router_check_regression", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert run.LOOPBACK == mod.LOOPBACK


def _assert_cache_key():
    opts = run.chat_options(0)
    base = run.cache_digest("m", 0, opts, "skill", "input")
    assert len(base) == 64 and re.fullmatch(r"[0-9a-f]{64}", base)
    assert base == run.cache_digest("m", 0, opts, "skill", "input")
    assert base != run.cache_digest("m", 0, opts, "skill", "other")
    assert base != run.cache_digest("m", 1, run.chat_options(1), "skill", "input")
    assert base != run.cache_digest("other", 0, opts, "skill", "input")
    assert base != run.cache_digest("m", 0, opts, "other", "input")


def self_test():
    fix = HERE / "_selftest"
    kw = dict(model=None, seed=SEED, url=run.DEFAULT_URL)
    dev = score_run("_selftest", "dev", "stub", fix / "items.jsonl", fix / "grader.py", fix / "SKILL.md", **kw)
    held = score_run("_selftest", "heldout", "stub", fix / "items.jsonl", fix / "grader.py", fix / "SKILL.md", **kw)

    # Toy fixture: stub echoes the input, the grader scores token presence. dev is 2/4, heldout is 3/4.
    assert dev["n"] == 4 and held["n"] == 4
    assert dev["mean"] == 0.5, dev["mean"]
    assert held["mean"] == 0.75, held["mean"]
    assert dev["per_item"] == {"d1": 1.0, "d2": 0.0, "d3": 1.0, "d4": 0.0}
    assert held["per_item"] == {"h1": 1.0, "h2": 1.0, "h3": 1.0, "h4": 0.0}
    assert dev["outputs"] == {
        "d1": "stub:red cube", "d2": "stub:red cube",
        "d3": "stub:green sphere", "d4": "stub:green sphere",
    }
    assert dev["notes"] == {"d1": ["hit"], "d2": ["miss"], "d3": ["hit"], "d4": ["miss"]}
    assert set(dev) == _META | {"outputs", "notes"}
    assert set(held) == _META
    held_text = record_json(held)
    assert "outputs" not in held_text and "notes" not in held_text, held_text
    assert dev["split"] == "dev" and held["split"] == "heldout"
    assert dev["skill"] == "_selftest" and held["skill"] == "_selftest"
    assert dev["executor"] == "stub" and held["executor"] == "stub"
    assert dev["model"] is None and held["model"] is None
    assert dev["seed"] == 0 and held["seed"] == 0
    assert dev["date"] == datetime.date.today().isoformat()
    commit = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert dev["commit"] == commit and held["commit"] == commit
    for key in ("items_sha256", "grader_sha256", "skill_sha256"):
        assert dev[key] == held[key]

    skill_md = str(fix / "SKILL.md")
    held_cli = _cli("--skill", "_selftest", "--split", "heldout", "--executor", "stub", "--skill-md", skill_md)
    assert held_cli.returncode == 0, held_cli.stderr
    assert "outputs" not in held_cli.stdout and "notes" not in held_cli.stdout
    assert json.loads(held_cli.stdout)["mean"] == 0.75

    _assert_hashes_track_files()
    _assert_loopback()
    _assert_cache_key()

    good = 'def grade(item, output):\n    return {"score": 1.0, "notes": []}\n'
    one = '{"id": "x", "split": "dev", "input": "hello"}\n'
    _expect_exit_2(one, 'def grade(item, output):\n    return {"score": 1.5, "notes": []}\n', "1.5")
    _expect_exit_2(one, 'def grade(item, output):\n    return {"score": float("nan"), "notes": []}\n', "nan")
    _expect_exit_2('{"id": "x", "split": "train", "input": "hello"}\n', good, "unknown split")
    _expect_exit_2(one + '{"id": "x", "split": "heldout", "input": "hello"}\n', good, "duplicate id")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = str(pathlib.Path(td) / "run.json")
        r = _cli("--skill", "_selftest", "--split", "dev", "--executor", "stub", "--skill-md", skill_md, "--out", out)
        assert r.returncode == 0, r.stderr
        assert r.stdout == ""
        got = json.loads(pathlib.Path(out).read_text())
        assert got["mean"] == 0.5 and "outputs" in got and "notes" in got

    print("PASS")


def main():
    ap = argparse.ArgumentParser(description="Score an agent skill on one item split.")
    ap.add_argument("--skill", help="skill name; items live in evals/skills/<NAME>/")
    ap.add_argument("--split", choices=["dev", "heldout"])
    ap.add_argument("--executor", choices=["ollama", "stub"], default="ollama")
    ap.add_argument("--skill-md", help="candidate SKILL.md (default: skills/<NAME>/SKILL.md)")
    ap.add_argument("--out", metavar="FILE", help="write the run record here instead of stdout")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    if not a.skill or not a.split:
        ap.error("--skill and --split are required (or use --self-test)")
    if not _NAME.fullmatch(a.skill):
        die(f"invalid skill name {a.skill!r}")
    items_path = HERE / a.skill / "items.jsonl"
    grader_path = HERE / a.skill / "grader.py"
    skill_md_path = pathlib.Path(a.skill_md) if a.skill_md else ROOT / "skills" / a.skill / "SKILL.md"
    if a.executor == "ollama":
        url, model = run.executor_url(), run.executor_model()
    else:
        url, model = run.DEFAULT_URL, None
    record = score_run(
        a.skill, a.split, a.executor, items_path, grader_path, skill_md_path,
        model=model, seed=SEED, url=url,
    )
    text = record_json(record)
    if a.out:
        pathlib.Path(a.out).write_text(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
