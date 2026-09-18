#!/usr/bin/env python3
"""Generate the run-aware fixtures for arch_gate.py's baseline, plan-declare,
plan-verify and conformance subcommands.

Anchored on this file's own location; accepts --out for an alternative root.
Every fixture is a small git repository under _build/<name>/, with commit
timestamps and identity pinned via TEAM_FIXED_TS so two generations are
byte-identical except for .git/index and .git/logs.

This generator covers only the fixtures new to the run-aware subcommands.
The pre-existing standalone-mode fixtures (clean, stale-pin, remove-verdict,
prune-verdict, and the tools-dir-* variants derived from them) are still
built by make_fixtures.sh from templates/, unchanged, and are reused by the
run-aware self-test cases that need an .arch/index.json baseline.

Fixtures:
  no-index       a one-commit repository with no .arch directory at all.
                 Used for baseline-no-index and declare-no-plan (it also has
                 no .team-ship/ARCH-PLAN.json), and for no-run (never given
                 an active run at all).
  repo-root-mismatch
                 an outer, one-commit repository containing
                 "nested-unrelated", its own one-commit repository with no
                 .team-ship of its own. Mirrors brownfield_map's fixture of
                 the same name: proves that pointing --repo-root at the
                 nested repository is caught and refused before anything is
                 written, even though gate_state.find_run() walks up from it
                 and finds the outer run.
  arch-plan-declare-pass
                 a one-commit repository with a shape-valid
                 .team-ship/ARCH-PLAN.json (one new component, symmetric
                 connections, non-conflicting outOfScope).
  arch-plan-declare-fail
                 the same plan with one component id "Bad_ID", which is not
                 kebab-case, so --declare reports a SHAPE 3 violation.
  arch-plan-verify-pass
                 a two-commit repository. Commit 1 is the base; its sha is
                 declaredAtCommit. Commit 2 physically builds the single
                 declared component's directory and file. --verify finds
                 both paths and no out-of-scope violation.
  arch-plan-verify-missing-path
                 the same declaredAtCommit as arch-plan-verify-pass, but the
                 declared component's directory and file are never created,
                 so --verify reports a BUILT 1 violation naming the
                 component id.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

FIXED_NAME = "Team Gate Fixtures"
FIXED_EMAIL = "team-gate-fixtures@example.invalid"


def _git_env(ts: str) -> dict:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = FIXED_NAME
    env["GIT_AUTHOR_EMAIL"] = FIXED_EMAIL
    env["GIT_COMMITTER_NAME"] = FIXED_NAME
    env["GIT_COMMITTER_EMAIL"] = FIXED_EMAIL
    env["GIT_AUTHOR_DATE"] = ts
    env["GIT_COMMITTER_DATE"] = ts
    return env


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _commit(path: Path, message: str, ts: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=str(path), check=True,
                    capture_output=True, env=_git_env(ts))


def _init_git_repo(path: Path, ts: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", FIXED_NAME], cwd=str(path), check=True,
                    capture_output=True)
    subprocess.run(["git", "config", "user.email", FIXED_EMAIL], cwd=str(path), check=True,
                    capture_output=True)
    _commit(path, "fixture", ts)


def _head_sha(path: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(path), check=True,
                             capture_output=True, text=True)
    return result.stdout.strip()


def _make_no_index(out_dir: Path, ts: str) -> None:
    repo = out_dir / "no-index"
    _reset_dir(repo)
    (repo / "app.py").write_text("def main():\n    print('no index')\n")
    _init_git_repo(repo, ts)


def _make_repo_root_mismatch(out_dir: Path, ts: str) -> None:
    outer = out_dir / "repo-root-mismatch"
    _reset_dir(outer)
    (outer / "app.py").write_text("def main():\n    print('outer')\n")
    _init_git_repo(outer, ts)

    nested = outer / "nested-unrelated"
    nested.mkdir()
    (nested / "lib.py").write_text("def helper():\n    return 1\n")
    _init_git_repo(nested, ts)


def _base_plan(component_id: str, declared_at_commit: str) -> dict:
    return {
        "schemaVersion": "1.0",
        "declaredAt": "2026-01-01T00:00:00Z",
        "declaredAtCommit": declared_at_commit,
        "basis": "new",
        "components": [
            {
                "id": component_id,
                "title": "Webhook Ingestion Service",
                "purpose": "Accepts inbound provider callbacks.",
                "status": "new",
                "connections": [],
                "intendedPaths": {
                    "directories": ["services/webhooks"],
                    "files": ["services/webhooks/handler.py"],
                    "rationale": "New service tree; the entry point is named explicitly.",
                },
            }
        ],
        "outOfScope": ["vendor"],
        "notes": "",
    }


def _make_arch_plan_declare_pass(out_dir: Path, ts: str) -> None:
    repo = out_dir / "arch-plan-declare-pass"
    _reset_dir(repo)
    (repo / "README.md").write_text("Base repository for a declare fixture.\n")
    _init_git_repo(repo, ts)

    plan = _base_plan("webhook-ingest", "0" * 40)
    ship_dir = repo / ".team-ship"
    ship_dir.mkdir()
    (ship_dir / "ARCH-PLAN.json").write_text(json.dumps(plan, indent=2))


def _make_arch_plan_declare_fail(out_dir: Path, ts: str) -> None:
    repo = out_dir / "arch-plan-declare-fail"
    _reset_dir(repo)
    (repo / "README.md").write_text("Base repository for a declare-fail fixture.\n")
    _init_git_repo(repo, ts)

    plan = _base_plan("Bad_ID", "0" * 40)
    ship_dir = repo / ".team-ship"
    ship_dir.mkdir()
    (ship_dir / "ARCH-PLAN.json").write_text(json.dumps(plan, indent=2))


def _make_arch_plan_verify_pass(out_dir: Path, ts: str) -> None:
    repo = out_dir / "arch-plan-verify-pass"
    _reset_dir(repo)
    (repo / "README.md").write_text("Base repository for a verify-pass fixture.\n")
    _init_git_repo(repo, ts)
    declared_at_commit = _head_sha(repo)

    webhooks_dir = repo / "services" / "webhooks"
    webhooks_dir.mkdir(parents=True)
    (webhooks_dir / "handler.py").write_text("def handle(event):\n    return event\n")
    _commit(repo, "build the declared component", ts)

    plan = _base_plan("webhook-ingest", declared_at_commit)
    ship_dir = repo / ".team-ship"
    ship_dir.mkdir()
    (ship_dir / "ARCH-PLAN.json").write_text(json.dumps(plan, indent=2))


def _make_arch_plan_verify_missing_path(out_dir: Path, ts: str) -> None:
    repo = out_dir / "arch-plan-verify-missing-path"
    _reset_dir(repo)
    (repo / "README.md").write_text("Base repository for a verify-missing-path fixture.\n")
    _init_git_repo(repo, ts)
    declared_at_commit = _head_sha(repo)

    # The declared component's directory and file are never built.
    plan = _base_plan("webhook-ingest", declared_at_commit)
    ship_dir = repo / ".team-ship"
    ship_dir.mkdir()
    (ship_dir / "ARCH-PLAN.json").write_text(json.dumps(plan, indent=2))


def generate_fixtures(out_dir: Path) -> None:
    ts = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")
    out_dir.mkdir(parents=True, exist_ok=True)
    _make_no_index(out_dir, ts)
    _make_repo_root_mismatch(out_dir, ts)
    _make_arch_plan_declare_pass(out_dir, ts)
    _make_arch_plan_declare_fail(out_dir, ts)
    _make_arch_plan_verify_pass(out_dir, ts)
    _make_arch_plan_verify_missing_path(out_dir, ts)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Generate run-aware fixtures for arch_gate.py.")
    parser.add_argument("--out", default=None, help="output directory (default: _build next to this file)")
    args = parser.parse_args()
    out_dir = Path(args.out).resolve() if args.out else Path(__file__).resolve().parent / "_build"
    generate_fixtures(out_dir)
    print(f"wrote fixtures to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
