#!/usr/bin/env python3
"""Generate test fixtures for claim_evidence.py, render_evidence.py,
render_approval.py, and render_pr_body.py.

Anchored on this file's own location; accepts --out for an alternative root.
Every fixture is a small git repository under <fixture-name>/_build/, with
.team-ship/ gitignored (so it stays untracked, matching a real checkout).
Commit timestamps are pinned via TEAM_FIXED_TS so two generations are
byte-identical except for .git/index and .git/logs.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import render_evidence


RESEARCH_BRIEF = "# Research Brief\n\nExisting tools surveyed. No blockers found.\n"
ARCHITECTURE_OPTIONS = "# Architecture Options\n\nChosen: Option B. Rationale: lowest risk.\n"
REVIEW_FINDINGS = "# Review Findings\n\nNo critical or major issues.\n"

PLAN_MD = """# Plan

---
requirements:
  - R1: All tests pass
must_haves:
  - M1: No regressions
---

Implementation proceeds in one phase.
"""

ARCH_PLAN_JSON = {
    "components": [
        {
            "id": "C1",
            "title": "Claim Checker + Evidence Rendering",
            "status": "new",
            "intendedPaths": ["skills/team-gate/scripts/claim_evidence.py"],
        }
    ],
    "declaredAtCommit": "0" * 40,
    "outOfScope": [],
}

BASE_EVIDENCE = {
    "schemaVersion": "1.0",
    "runId": "fixture-run",
    "head": "0" * 40,
    "entries": [
        {"id": "E1", "gate": 8, "label": "test-execution", "exit": 0, "passed": 759, "failed": 0, "skipped": 0},
        {"id": "E2", "gate": 10, "label": "coverage", "exit": 0, "coverage": 94.2},
        {"id": "E3", "gate": 7, "label": "env-parity", "exit": 0, "tool": "ruff"},
    ],
}

OVERRIDE_MARKUP_TEXT = "Ship with **bold** markup and <script>alert(1)</script> intact, per Rijul, 2026-09-17."
OVERRIDE_BACKTICKS_TEXT = "Override reason includes a fenced block:\n```\nsome code\n```\nper Rijul, 2026-09-17."


def _git_env() -> dict:
    env = os.environ.copy()
    fixed_ts = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")
    env.update({
        "GIT_AUTHOR_DATE": fixed_ts,
        "GIT_COMMITTER_DATE": fixed_ts,
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    })
    return env


def _write(build_dir: Path, relpath: str, content: str) -> None:
    path = build_dir / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _common_artifacts(build_dir: Path, include_evidence_md: bool = True,
                       omit: list = None) -> None:
    omit = omit or []
    if "RESEARCH-BRIEF.md" not in omit:
        _write(build_dir, ".team-ship/RESEARCH-BRIEF.md", RESEARCH_BRIEF)
    if "ARCHITECTURE-OPTIONS.md" not in omit:
        _write(build_dir, ".team-ship/ARCHITECTURE-OPTIONS.md", ARCHITECTURE_OPTIONS)
    if "PLAN.md" not in omit:
        _write(build_dir, ".team-ship/PLAN.md", PLAN_MD)
    if "ARCH-PLAN.json" not in omit:
        _write(build_dir, ".team-ship/ARCH-PLAN.json", json.dumps(ARCH_PLAN_JSON, indent=2))
    if "REVIEW-FINDINGS.md" not in omit:
        _write(build_dir, ".team-ship/REVIEW-FINDINGS.md", REVIEW_FINDINGS)
    if "EVIDENCE.json" not in omit:
        _write(build_dir, ".team-ship/EVIDENCE.json", json.dumps(BASE_EVIDENCE, indent=2))
        if include_evidence_md:
            _write(build_dir, ".team-ship/EVIDENCE.md", render_evidence.render(BASE_EVIDENCE))


def _init_git(build_dir: Path) -> None:
    env = _git_env()
    subprocess.run(["git", "init", "-q"], cwd=build_dir, check=True, env=env)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=build_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=build_dir, check=True)
    (build_dir / ".gitignore").write_text(".team-ship/\n")
    subprocess.run(["git", "add", "-A"], cwd=build_dir, check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=build_dir, check=True, env=env)


def _new_fixture(output_root: Path, name: str) -> Path:
    fixture_dir = output_root / name
    fixture_dir.mkdir(parents=True, exist_ok=True)
    build_dir = fixture_dir / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)
    return build_dir


def _finish_fixture(output_root: Path, name: str, build_dir: Path, description: str) -> None:
    _init_git(build_dir)
    fixture_dir = output_root / name
    metadata = {"name": name, "description": description}
    (fixture_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))


def _rename_branch_main(repo_dir: Path, env: dict) -> None:
    subprocess.run(["git", "branch", "-M", "main"], cwd=repo_dir, check=True, env=env)


def _make_bare_origin_from(source_dir: Path, dest_bare: Path, env: dict) -> None:
    """Bare-clone source_dir's already-committed history into dest_bare.

    A local clone hardlinks the existing (already timestamp-pinned) loose
    objects rather than repacking, so this is byte-identical across
    generations, matching every other fixture's determinism guarantee.
    """
    if dest_bare.exists():
        shutil.rmtree(dest_bare)
    subprocess.run(["git", "clone", "-q", "--bare", str(source_dir), str(dest_bare)], check=True, env=env)


def _make_unrelated_bare_origin(dest_bare: Path, env: dict) -> None:
    """Build a bare repository whose history shares no commit with the fixture build."""
    seed = dest_bare.parent / "_origin_seed"
    if seed.exists():
        shutil.rmtree(seed)
    seed.mkdir(parents=True)
    (seed / "README.md").write_text("Unrelated origin history, no shared commits with the fixture build.\n")
    subprocess.run(["git", "init", "-q"], cwd=seed, check=True, env=env)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=seed, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=seed, check=True)
    subprocess.run(["git", "add", "-A"], cwd=seed, check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", "unrelated origin history"], cwd=seed, check=True, env=env)
    _rename_branch_main(seed, env)
    _make_bare_origin_from(seed, dest_bare, env)
    shutil.rmtree(seed)


def _add_origin_remote(build_dir: Path, bare_path: Path, env: dict) -> None:
    subprocess.run(["git", "remote", "add", "origin", str(bare_path)], cwd=build_dir, check=True, env=env)
    subprocess.run(["git", "fetch", "-q", "origin"], cwd=build_dir, check=True, env=env)


def make_all_claims_backed(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "all-claims-backed")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\nNarrative goes here.\n\n## Results\n\n"
        "- 759 passed, 0 failed, 0 skipped. [E1]\n"
        "- Coverage is 94.2%. [E2]\n"
        "- ruff clean. [E3]\n"
    ))
    _finish_fixture(output_root, "all-claims-backed", build_dir,
                     "Every claim in the results section is correctly backed by EVIDENCE.json.")


def make_number_mismatch(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "number-mismatch")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\n## Results\n\n- 312 passed. [E1]\n"
    ))
    _finish_fixture(output_root, "number-mismatch", build_dir,
                     "E1 records 759 passed but the PR body claims 312, a contradiction.")


def make_unbacked_adjective(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "unbacked-adjective")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\n## Results\n\n- The fix is comprehensive.\n"
    ))
    _finish_fixture(output_root, "unbacked-adjective", build_dir,
                     "An unbacked-word list adjective with no citation.")


def make_uncited_claim(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "uncited-claim")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\n## Results\n\n- 759 passed.\n"
    ))
    _finish_fixture(output_root, "uncited-claim", build_dir,
                     "A quantitative claim with no [E<n>] citation at all.")


def make_number_words(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "number-words")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\n## Results\n\n- Twelve tests passed. [E1]\n"
    ))
    _finish_fixture(output_root, "number-words", build_dir,
                     "A spelled-out number word, unverifiable regardless of citation.")


def make_two_claims_one_tag(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "two-claims-one-tag")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\n## Results\n\n- 759 passed and coverage is 96% [E1]\n"
    ))
    _finish_fixture(output_root, "two-claims-one-tag", build_dir,
                     "One tag backs two claims; E1 has no coverage field so only that claim fails.")


def make_hand_edited_evidence_md(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "hand-edited-evidence-md")
    _common_artifacts(build_dir)
    md_path = build_dir / ".team-ship" / "EVIDENCE.md"
    text = md_path.read_text(encoding="utf-8")
    text = text.replace("759", "999")
    md_path.write_text(text, encoding="utf-8")
    _finish_fixture(output_root, "hand-edited-evidence-md", build_dir,
                     "EVIDENCE.md was hand-edited after generation; --check must detect it.")


def make_whitespace_edited_evidence_md(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "whitespace-edited-evidence-md")
    _common_artifacts(build_dir)
    md_path = build_dir / ".team-ship" / "EVIDENCE.md"
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("Head:"):
            lines[i] = line + " "
            break
    md_path.write_text("\n".join(lines), encoding="utf-8")
    _finish_fixture(output_root, "whitespace-edited-evidence-md", build_dir,
                     "EVIDENCE.md carries one trailing space; --check treats whitespace as a difference.")


def make_missing_approval_artifact(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "missing-approval-artifact")
    _common_artifacts(build_dir, omit=["ARCH-PLAN.json"])
    _finish_fixture(output_root, "missing-approval-artifact", build_dir,
                     "ARCH-PLAN.json, one of the five approval-gate artifacts, is missing.")


def make_requirement_not_met(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "requirement-not-met")
    _common_artifacts(build_dir)
    _finish_fixture(output_root, "requirement-not-met", build_dir,
                     "R1 maps to a gate that exits 1; self-test creates that gate at run time.")


def make_requirement_unverified(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "requirement-unverified")
    _common_artifacts(build_dir)
    _finish_fixture(output_root, "requirement-unverified", build_dir,
                     "R1 maps to no gate at all; self-test leaves it unmapped at run time.")


def make_override_with_markup(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "override-with-markup")
    _common_artifacts(build_dir)
    _finish_fixture(output_root, "override-with-markup", build_dir,
                     "Base repository for render_pr_body; self-test appends an override receipt "
                     "whose text contains markdown and HTML markup.")


def make_override_with_backticks(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "override-with-backticks")
    _common_artifacts(build_dir)
    _finish_fixture(output_root, "override-with-backticks", build_dir,
                     "Base repository for render_pr_body; self-test appends an override receipt "
                     "whose text contains a triple-backtick fenced block.")


def make_duplicate_evidence_id(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "duplicate-evidence-id")
    duplicate_evidence = {
        "schemaVersion": "1.0",
        "runId": "fixture-run",
        "head": "0" * 40,
        "entries": [
            {"id": "E1", "gate": 8, "label": "test-execution", "exit": 0, "passed": 100, "failed": 0, "skipped": 0},
            {"id": "E1", "gate": 8, "label": "test-execution", "exit": 0, "passed": 999, "failed": 0, "skipped": 0},
        ],
    }
    _common_artifacts(build_dir, include_evidence_md=False, omit=["EVIDENCE.json"])
    _write(build_dir, ".team-ship/EVIDENCE.json", json.dumps(duplicate_evidence, indent=2))
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\n## Results\n\n- 100 passed. [E1]\n"
    ))
    _finish_fixture(output_root, "duplicate-evidence-id", build_dir,
                     "Two entries share id E1 in EVIDENCE.json; every consumer must exit 2 "
                     "before doing any other work.")


def make_unresolved_tag(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "unresolved-tag")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\n## Results\n\n- 759 passed. [E99]\n"
    ))
    _finish_fixture(output_root, "unresolved-tag", build_dir,
                     "The body cites [E99], which names no entry in EVIDENCE.json; reported as "
                     "unresolved-tag, not as a missing field.")


def make_no_failures_phrase(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "no-failures-phrase")
    no_failures_evidence = {
        "schemaVersion": "1.0",
        "runId": "fixture-run",
        "head": "0" * 40,
        "entries": [
            {"id": "E1", "gate": 8, "label": "test-execution", "exit": 0, "passed": 100, "failed": 0, "skipped": 0},
            {"id": "E2", "gate": 8, "label": "test-execution", "exit": 0, "passed": 98, "failed": 2, "skipped": 0},
        ],
    }
    _common_artifacts(build_dir, include_evidence_md=False, omit=["EVIDENCE.json"])
    _write(build_dir, ".team-ship/EVIDENCE.json", json.dumps(no_failures_evidence, indent=2))
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\n## Results\n\n- No failures. [E1]\n"
    ))
    _write(build_dir, ".team-ship/PR-BODY-2.md", (
        "# PR\n\n## Results\n\n- No failures. [E2]\n"
    ))
    _finish_fixture(output_root, "no-failures-phrase", build_dir,
                     "PR-BODY.md cites E1 (failed 0), backed; PR-BODY-2.md cites E2 (failed 2), "
                     "a contradiction of the same 'no failures' phrase.")


def make_merged_not_ancestor(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "merged-not-ancestor")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\nThis change has already been merged.\n\n## Results\n"
    ))
    _finish_fixture(output_root, "merged-not-ancestor", build_dir,
                     "HEAD is on a branch not reachable from origin/main via a local bare "
                     "remote, so the 'merged' claim is a merge-claim finding.")
    env = _git_env()
    _rename_branch_main(build_dir, env)
    bare = build_dir / "_origin.git"
    _make_unrelated_bare_origin(bare, env)
    _add_origin_remote(build_dir, bare, env)


def make_merged_ancestor(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "merged-ancestor")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\nThis change has already been merged.\n\n## Results\n"
    ))
    _finish_fixture(output_root, "merged-ancestor", build_dir,
                     "HEAD is the tip of origin/main via a local bare remote, so the "
                     "'merged' claim holds and is not a finding.")
    env = _git_env()
    _rename_branch_main(build_dir, env)
    bare = build_dir / "_origin.git"
    _make_bare_origin_from(build_dir, bare, env)
    _add_origin_remote(build_dir, bare, env)


def make_ci_green_without_stage_13(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "ci-green-without-stage-13")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\nCI is green across the board.\n\n## Results\n"
    ))
    _finish_fixture(output_root, "ci-green-without-stage-13", build_dir,
                     "gates/14.json has no stage 13 row, so the 'ci is green' claim is a "
                     "merge-claim finding.")


def make_shipped_without_pr(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "shipped-without-pr")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\nThis feature has already been shipped.\n\n## Results\n"
    ))
    _finish_fixture(output_root, "shipped-without-pr", build_dir,
                     "receipts.jsonl carries no pr-opened receipt, so the 'shipped' claim is "
                     "a merge-claim finding.")


def make_shipped_with_pr_receipt(output_root: Path) -> None:
    build_dir = _new_fixture(output_root, "shipped-with-pr-receipt")
    _common_artifacts(build_dir)
    _write(build_dir, ".team-ship/PR-BODY.md", (
        "# PR\n\nThis feature has already been shipped.\n\n## Results\n"
    ))
    _finish_fixture(output_root, "shipped-with-pr-receipt", build_dir,
                     "Self-test appends a pr-opened receipt with the gate_state API before "
                     "running check, so the 'shipped' claim holds and is not a finding.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate claim_evidence fixtures")
    parser.add_argument("--out", type=Path, default=None, help="Output root directory")
    args = parser.parse_args()

    output_root = Path(args.out).resolve() if args.out else Path(__file__).resolve().parent

    make_all_claims_backed(output_root)
    make_number_mismatch(output_root)
    make_unbacked_adjective(output_root)
    make_uncited_claim(output_root)
    make_number_words(output_root)
    make_two_claims_one_tag(output_root)
    make_hand_edited_evidence_md(output_root)
    make_whitespace_edited_evidence_md(output_root)
    make_missing_approval_artifact(output_root)
    make_requirement_not_met(output_root)
    make_requirement_unverified(output_root)
    make_override_with_markup(output_root)
    make_override_with_backticks(output_root)
    make_duplicate_evidence_id(output_root)
    make_unresolved_tag(output_root)
    make_no_failures_phrase(output_root)
    make_merged_not_ancestor(output_root)
    make_merged_ancestor(output_root)
    make_ci_green_without_stage_13(output_root)
    make_shipped_without_pr(output_root)
    make_shipped_with_pr_receipt(output_root)
    print("Fixtures generated successfully")


if __name__ == "__main__":
    main()
