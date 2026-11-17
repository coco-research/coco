#!/usr/bin/env python3
"""Run one unattended RSI turn across all baseline-ready skill evals. Stdlib only.

Reuses evals/skills/improve.py for every proposal, dev check, and held-out peek
(zero duplicate scoring logic). Honours RSI.OFF before any proposer or model call,
writes evals/skills/_rounds/<skill>/rNNN.json via improve.py, and creates one
local git branch per kept change without opening pull requests in tests.
"""
# ponytail: ceiling = sequential single-host loop over pilot skills; upgrade path = lockfile + sharded worker queue past 25 skills.

import argparse
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import improve  # noqa: E402
import run  # noqa: E402
import score  # noqa: E402


def discover_skills(root):
    """Skills under evals/skills/<name>/ that have items.jsonl, grader.py, SKILL.md, and baseline runs."""
    ev_root = root / "evals" / "skills"
    if not ev_root.is_dir():
        return []
    found = []
    for entry in sorted(ev_root.iterdir(), key=lambda p: p.name):
        name = entry.name
        if not entry.is_dir() or name.startswith("_") or name.startswith("."):
            continue
        if not (entry / "items.jsonl").is_file() or not (entry / "grader.py").is_file():
            continue
        if not (root / "skills" / name / "SKILL.md").is_file():
            continue
        runs_dir = entry / improve.RUNS_DIR
        if not runs_dir.is_dir() or not any(runs_dir.glob("*.json")):
            continue
        found.append(name)
    return found


def load_stub_override(script_path):
    spec = importlib.util.spec_from_file_location("_rsi_turn_stub", str(script_path))
    if spec is None or spec.loader is None:
        improve.die("cannot load stub executor script: %s" % script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "stub", None)
    if not callable(fn):
        improve.die("stub executor script must define stub(skill_md, user_input, **kw)")
    return fn


def git_env():
    drop = {
        "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    }
    return {k: v for k, v in os.environ.items() if k not in drop}


def create_kept_branch(root, branch_dir, branch_name):
    """Commit <out>/branch/* onto refs/heads/<branch_name> off HEAD without touching the working tree."""
    env_base = git_env()
    head_proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
        capture_output=True, text=True, env=env_base, check=True,
    )
    parent_sha = head_proc.stdout.strip()

    with tempfile.TemporaryDirectory(prefix="rsi-idx-") as idx_dir:
        idx_file = os.path.join(idx_dir, "index")
        env = dict(env_base, GIT_INDEX_FILE=idx_file)
        subprocess.run(["git", "-C", str(root), "read-tree", parent_sha], env=env, check=True, capture_output=True)

        for file_path in sorted(p for p in pathlib.Path(branch_dir).rglob("*") if p.is_file()):
            rel = file_path.relative_to(branch_dir).as_posix()
            blob_proc = subprocess.run(
                ["git", "-C", str(root), "hash-object", "-w", str(file_path)],
                capture_output=True, text=True, env=env, check=True,
            )
            blob_sha = blob_proc.stdout.strip()
            subprocess.run(
                ["git", "-C", str(root), "update-index", "--add", "--cacheinfo", f"100644,{blob_sha},{rel}"],
                env=env, check=True, capture_output=True,
            )

        tree_proc = subprocess.run(
            ["git", "-C", str(root), "write-tree"],
            capture_output=True, text=True, env=env, check=True,
        )
        tree_sha = tree_proc.stdout.strip()

        skill_part = branch_name.split("/")[-1]
        msg = f"feat(skills): unattended RSI improvement ({skill_part})\n"
        commit_env = dict(
            env,
            GIT_AUTHOR_NAME=env.get("GIT_AUTHOR_NAME", "Coco Research"),
            GIT_AUTHOR_EMAIL=env.get("GIT_AUTHOR_EMAIL", "68911604+coco-research@users.noreply.github.com"),
            GIT_COMMITTER_NAME=env.get("GIT_COMMITTER_NAME", "Coco Research"),
            GIT_COMMITTER_EMAIL=env.get("GIT_COMMITTER_EMAIL", "68911604+coco-research@users.noreply.github.com"),
        )
        commit_proc = subprocess.run(
            ["git", "-C", str(root), "commit-tree", tree_sha, "-p", parent_sha, "-m", msg],
            capture_output=True, text=True, env=commit_env, check=True,
        )
        commit_sha = commit_proc.stdout.strip()
        subprocess.run(
            ["git", "-C", str(root), "update-ref", f"refs/heads/{branch_name}", commit_sha],
            env=env_base, check=True, capture_output=True,
        )
        return commit_sha


def run_one_skill(root, skill, args):
    with tempfile.TemporaryDirectory(prefix=f"rsi-{skill}-") as out_dir:
        argv = [
            "--skill", skill,
            "--root", str(root),
            "--out", out_dir,
            "--executor", args.executor,
            "--max-proposals", str(args.max_proposals),
            "--dev-margin", str(args.dev_margin),
            "--max-changed-lines", str(args.max_changed_lines),
            "--base-ref", args.base_ref,
        ]
        buf_out = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf_out):
                improve.main(argv)
        except SystemExit as exc:
            if exc.code not in (0, None):
                raise

        lines = [ln for ln in buf_out.getvalue().splitlines() if ln.strip().startswith("{")]
        if not lines:
            improve.die(f"improve.py produced no JSON summary for {skill}", code=1)
        summary = json.loads(lines[-1])
        rid = summary["round"]
        ledger_file = root / "evals" / "skills" / improve.ROUNDS_DIR / skill / f"{rid}.json"
        rec = json.loads(ledger_file.read_text(encoding="utf-8"))

        outcome = rec.get("outcome")
        peek = (rec.get("gate") or {}).get("peek") or {}
        if outcome == "kept":
            cand_held = peek.get("cand_mean")
            base_held = peek.get("base_mean")
            if cand_held is None or base_held is None or cand_held < base_held:
                return "rejected", rid, None
            branch_name = f"{args.branch_prefix}{skill}-{rid}"
            sha = create_kept_branch(root, pathlib.Path(out_dir) / "branch", branch_name)
            if args.open_pr:
                subprocess.run(["git", "-C", str(root), "push", "-u", "origin", branch_name], check=True, env=git_env())
                subprocess.run(
                    ["gh", "pr", "create", "--head", branch_name, "--title", f"feat({skill}): RSI {rid}", "--body", rec.get("reason") or ""],
                    cwd=str(root), check=True, env=git_env(),
                )
            return "kept", rid, branch_name
        if int(rec.get("peek_count") or 0) > 0:
            return "rejected", rid, None
        return "no_change", rid, None


def format_bucket(label, items):
    if items:
        return f"{label} {len(items)} ({', '.join(items)})"
    return f"{label} 0"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run one unattended RSI turn across pilot skills.")
    ap.add_argument("--root", default=None)
    ap.add_argument("--executor", choices=("ollama", "stub"), default="ollama")
    ap.add_argument("--skills", default=None, help="Optional comma-separated skill names.")
    ap.add_argument("--max-proposals", type=int, default=improve.K_DEFAULT)
    ap.add_argument("--dev-margin", type=float, default=improve.DEV_MARGIN)
    ap.add_argument("--max-changed-lines", type=int, default=improve.MAX_CHANGED_LINES)
    ap.add_argument("--base-ref", default="origin/main")
    ap.add_argument("--branch-prefix", default="rsi/")
    ap.add_argument("--stub-script", default=None)
    ap.add_argument("--open-pr", action="store_true")
    args = ap.parse_args(argv)

    root = pathlib.Path(args.root).resolve() if args.root else improve.ROOT
    if (root / "RSI.OFF").exists():
        print("turn: off (RSI.OFF honoured)")
        return 0

    if root != improve.ROOT:
        score.ROOT = root

    orig_stub = run.stub
    stub_script = args.stub_script or os.environ.get("COCO_RSI_STUB_SCRIPT")
    if stub_script:
        if args.executor != "stub":
            improve.die("--stub-script is valid only with --executor stub")
        run.stub = load_stub_override(stub_script)

    try:
        skills = (
            [s.strip() for s in args.skills.split(",") if s.strip()]
            if args.skills
            else discover_skills(root)
        )
        if not skills:
            improve.die("no baseline-ready skills found under evals/skills/")

        kept, rejected, no_change = [], [], []
        for skill in skills:
            if (root / "RSI.OFF").exists():
                print("turn: off (RSI.OFF honoured)")
                return 0
            status, _rid, _branch = run_one_skill(root, skill, args)
            if status == "kept":
                kept.append(skill)
            elif status == "rejected":
                rejected.append(skill)
            else:
                no_change.append(skill)

        print(
            f"turn: {len(skills)} skills · {format_bucket('kept', kept)} · "
            f"{format_bucket('rejected', rejected)} · no change {len(no_change)}"
        )
        return 0
    finally:
        run.stub = orig_stub


if __name__ == "__main__":
    raise SystemExit(main())
