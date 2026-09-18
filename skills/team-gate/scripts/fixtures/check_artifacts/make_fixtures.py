#!/usr/bin/env python3
"""Generate deterministic fixtures for check_artifacts.py's self-test.

Anchors on this file's own location. Accepts --out DIR to write elsewhere.
Every fixture repo is a real git repository so check_artifacts.py can resolve
git rev-parse HEAD; commit dates, author, and committer are pinned so two
generations are byte-identical. Override the pinned timestamp with the
TEAM_FIXED_TS environment variable (an ISO-8601 string); otherwise a fixed
default is used.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FIXED_TS = "2026-01-01T00:00:00Z"
FIXED_NAME = "Team Gate Fixtures"
FIXED_EMAIL = "team-gate-fixtures@example.invalid"

FORBIDDEN_LINE = "TODO: fill this in later\n"


def fixed_ts() -> str:
    return os.environ.get("TEAM_FIXED_TS", DEFAULT_FIXED_TS)


def init_git_repo(repo_dir: Path) -> None:
    """git init + commit everything currently in repo_dir, with pinned identity and dates."""
    env = dict(os.environ)
    env.update({
        "GIT_AUTHOR_NAME": FIXED_NAME,
        "GIT_AUTHOR_EMAIL": FIXED_EMAIL,
        "GIT_AUTHOR_DATE": fixed_ts(),
        "GIT_COMMITTER_NAME": FIXED_NAME,
        "GIT_COMMITTER_EMAIL": FIXED_EMAIL,
        "GIT_COMMITTER_DATE": fixed_ts(),
    })
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, env=env, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, env=env, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "fixture commit", "--no-gpg-sign"],
        cwd=repo_dir, env=env, check=True
    )


def research_brief(valid: bool = True, extra: str = "") -> str:
    lines = ["# Research Brief", "", "## Key Findings", ""]
    if valid:
        for i in range(20):
            lines.append(f"Finding {i + 1}: a non-trivial research finding.")
    else:
        lines.append("Only one short finding.")
    if extra:
        lines.append("")
        lines.append(extra)
    return "\n".join(lines) + "\n"


def architecture_options(with_chosen_heading: bool, filler_lines: int = 11, in_fence: bool = False) -> str:
    lines = ["# Architecture Options", ""]
    for i in range(filler_lines):
        lines.append(f"Filler line {i + 1}: architecture discussion.")
    if with_chosen_heading:
        if in_fence:
            lines += ["", "```", "# Chosen", "Option A, inside a fence.", "```"]
        else:
            lines += ["", "## Chosen", "Option A is chosen for its simplicity."]
    return "\n".join(lines) + "\n"


def plan_md() -> str:
    lines = ["# Plan", ""]
    for i in range(12):
        lines.append(f"Task {i + 1}: implementation step.")
    return "\n".join(lines) + "\n"


def arch_plan_json() -> str:
    return '{\n  "schemaVersion": 1,\n  "components": []\n}\n'


def review_findings() -> str:
    lines = ["# Review Findings", ""]
    for i in range(3):
        lines.append(f"- Finding {i + 1}: minor issue, already addressed.")
    return "\n".join(lines) + "\n"


def brownfield_map_md() -> str:
    """Hand-rendered stand-in for brownfield_map.py's real output: the same five
    headings (Summary, Entry points, Impact, Tests, Limits), no wall-clock, no
    forbidden tokens, and enough non-heading lines to clear the manifest's minLines.
    """
    lines = [
        "# Brownfield map",
        "",
        "## Summary",
        "",
        "- Task: none given; showing the default ranked map.",
        "- Repository: not greenfield.",
        "- Languages: Python (3).",
        "- Files: 3.",
        "- Symbols: 5.",
        "",
        "## Entry points",
        "",
        "- **add** - src/util.py",
        "- **helper** - src/main.py",
        "",
        "## Impact",
        "",
        "- src/util.py: ranked first by call-graph importance.",
        "- src/main.py: ranked second by call-graph importance.",
        "",
        "## Tests",
        "",
        "- tests/test_util.py",
        "",
        "## Limits",
        "",
        "- Multi-file localization is the weakest measured result.",
        "- The call graph is name-based and unsound by construction.",
        "- Churn, ownership and co-change need real git history.",
    ]
    return "\n".join(lines) + "\n"


def build_repo(repo_dir: Path, files: dict, run_id: str = "run-001") -> None:
    """Create .team-ship/ contents plus the RUN pointer, then commit a git repo."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    team_ship = repo_dir / ".team-ship"
    team_ship.mkdir(parents=True, exist_ok=True)

    for rel_path, content in files.items():
        target = repo_dir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, tuple) and content[0] == "symlink":
            if target.exists() or target.is_symlink():
                target.unlink()
            target.symlink_to(content[1])
        else:
            target.write_text(content, encoding="utf-8")

    if run_id is not None:
        (team_ship / "RUN").write_text(run_id, encoding="utf-8")

    # Ensure the repo always has something to commit, even when files is empty.
    (repo_dir / ".fixture-marker").write_text("fixture repo\n", encoding="utf-8")

    init_git_repo(repo_dir)


def make_run_dir(fixture_dir: Path, run_id: str = "run-001") -> None:
    (fixture_dir / "runs" / run_id).mkdir(parents=True, exist_ok=True)


VALID_ARCHITECTURE_OPTIONS = architecture_options(with_chosen_heading=True)
VALID_RESEARCH_BRIEF = research_brief(valid=True)
VALID_PLAN = plan_md()
VALID_ARCH_PLAN_JSON = arch_plan_json()
VALID_REVIEW_FINDINGS = review_findings()
VALID_BROWNFIELD_MAP = brownfield_map_md()


def create_complete_stage(out: Path) -> None:
    fixture_dir = out / "complete-stage"
    build_repo(fixture_dir / "repo", {
        ".team-ship/RESEARCH-BRIEF.md": VALID_RESEARCH_BRIEF,
        ".team-ship/BROWNFIELD-MAP.md": VALID_BROWNFIELD_MAP,
    })
    make_run_dir(fixture_dir)


def create_missing_input(out: Path) -> None:
    fixture_dir = out / "missing-input"
    build_repo(fixture_dir / "repo", {})
    make_run_dir(fixture_dir)


def create_trivial_artifact_too_short(out: Path) -> None:
    fixture_dir = out / "trivial-artifact-too-short"
    build_repo(fixture_dir / "repo", {
        ".team-ship/RESEARCH-BRIEF.md": research_brief(valid=False),
    })
    make_run_dir(fixture_dir)


def create_forbidden_token(out: Path) -> None:
    fixture_dir = out / "forbidden-token"
    build_repo(fixture_dir / "repo", {
        ".team-ship/RESEARCH-BRIEF.md": research_brief(valid=True, extra=FORBIDDEN_LINE),
    })
    make_run_dir(fixture_dir)


def create_missing_heading(out: Path) -> None:
    fixture_dir = out / "missing-heading"
    # filler_lines=12 meets minLines on its own, so the missing heading is the only violation.
    build_repo(fixture_dir / "repo", {
        ".team-ship/ARCHITECTURE-OPTIONS.md": architecture_options(with_chosen_heading=False, filler_lines=12),
    })
    make_run_dir(fixture_dir)


def create_no_run(out: Path) -> None:
    fixture_dir = out / "no-run"
    build_repo(fixture_dir / "repo", {}, run_id=None)
    # Deliberately no runs/ directory and no .team-ship/RUN pointer.


def create_forbidden_token_in_fence(out: Path) -> None:
    fixture_dir = out / "forbidden-token-in-fence"
    content = research_brief(valid=True) + "\n```\n" + FORBIDDEN_LINE + "```\n"
    build_repo(fixture_dir / "repo", {
        ".team-ship/RESEARCH-BRIEF.md": content,
    })
    make_run_dir(fixture_dir)


def create_forbidden_token_substring_ok(out: Path) -> None:
    fixture_dir = out / "forbidden-token-substring-ok"
    # "TODOs" and "mastodon" both contain the substring "todo" but neither is the
    # whole word "TODO", so word-boundary matching must let this pass.
    build_repo(fixture_dir / "repo", {
        ".team-ship/RESEARCH-BRIEF.md": research_brief(
            valid=True, extra="We closed all TODOs on mastodon."
        ),
        ".team-ship/BROWNFIELD-MAP.md": VALID_BROWNFIELD_MAP,
    })
    make_run_dir(fixture_dir)


def create_map_missing(out: Path) -> None:
    fixture_dir = out / "map-missing"
    # A complete stage 2 input set except the map: RESEARCH-BRIEF.md present and
    # valid, .team-ship/BROWNFIELD-MAP.md deliberately absent.
    build_repo(fixture_dir / "repo", {
        ".team-ship/RESEARCH-BRIEF.md": VALID_RESEARCH_BRIEF,
    })
    make_run_dir(fixture_dir)


def create_heading_only_in_fence(out: Path) -> None:
    fixture_dir = out / "heading-only-in-fence"
    build_repo(fixture_dir / "repo", {
        ".team-ship/ARCHITECTURE-OPTIONS.md": architecture_options(with_chosen_heading=True, in_fence=True),
    })
    make_run_dir(fixture_dir)


def create_symlink_escape(out: Path) -> None:
    fixture_dir = out / "symlink-escape"
    repo_dir = fixture_dir / "repo"
    build_repo(repo_dir, {
        "outside-secret.txt": "content that lives outside .team-ship\n",
        ".team-ship/RESEARCH-BRIEF.md": ("symlink", "../outside-secret.txt"),
    })
    make_run_dir(fixture_dir)


def create_unknown_stage(out: Path) -> None:
    fixture_dir = out / "unknown-stage"
    build_repo(fixture_dir / "repo", {
        ".team-ship/RESEARCH-BRIEF.md": VALID_RESEARCH_BRIEF,
    })
    make_run_dir(fixture_dir)


def create_adversarial_filler_no_heading(out: Path) -> None:
    fixture_dir = out / "adversarial-filler-no-heading"
    # Exactly minLines (12) worth of filler, no "chosen" heading anywhere.
    build_repo(fixture_dir / "repo", {
        ".team-ship/ARCHITECTURE-OPTIONS.md": architecture_options(with_chosen_heading=False, filler_lines=12),
    })
    make_run_dir(fixture_dir)


def create_stage_output_ok(out: Path) -> None:
    fixture_dir = out / "stage-output-ok"
    build_repo(fixture_dir / "repo", {
        ".team-ship/PLAN.md": VALID_PLAN,
    })
    make_run_dir(fixture_dir)


def create_stage_output_undeclared(out: Path) -> None:
    fixture_dir = out / "stage-output-undeclared"
    build_repo(fixture_dir / "repo", {
        ".team-ship/PLAN.md": VALID_PLAN,
    })
    make_run_dir(fixture_dir)


def create_stage_output_symlink_escape(out: Path) -> None:
    fixture_dir = out / "stage-output-symlink-escape"
    repo_dir = fixture_dir / "repo"
    build_repo(repo_dir, {
        "outside-secret.txt": "content that lives outside .team-ship\n",
        ".team-ship/PLAN.md": ("symlink", "../outside-secret.txt"),
    })
    make_run_dir(fixture_dir)


def create_approval_ready_ok(out: Path) -> None:
    fixture_dir = out / "approval-ready-ok"
    build_repo(fixture_dir / "repo", {
        ".team-ship/RESEARCH-BRIEF.md": VALID_RESEARCH_BRIEF,
        ".team-ship/ARCHITECTURE-OPTIONS.md": VALID_ARCHITECTURE_OPTIONS,
        ".team-ship/PLAN.md": VALID_PLAN,
        ".team-ship/ARCH-PLAN.json": VALID_ARCH_PLAN_JSON,
        ".team-ship/REVIEW-FINDINGS.md": VALID_REVIEW_FINDINGS,
    })
    make_run_dir(fixture_dir)


def create_approval_missing(out: Path) -> None:
    fixture_dir = out / "approval-missing"
    build_repo(fixture_dir / "repo", {
        ".team-ship/RESEARCH-BRIEF.md": VALID_RESEARCH_BRIEF,
        ".team-ship/ARCHITECTURE-OPTIONS.md": VALID_ARCHITECTURE_OPTIONS,
        ".team-ship/PLAN.md": VALID_PLAN,
        ".team-ship/REVIEW-FINDINGS.md": VALID_REVIEW_FINDINGS,
        # ARCH-PLAN.json deliberately absent.
    })
    make_run_dir(fixture_dir)


FIXTURE_BUILDERS = [
    create_complete_stage,
    create_missing_input,
    create_trivial_artifact_too_short,
    create_forbidden_token,
    create_missing_heading,
    create_no_run,
    create_forbidden_token_in_fence,
    create_forbidden_token_substring_ok,
    create_heading_only_in_fence,
    create_symlink_escape,
    create_unknown_stage,
    create_adversarial_filler_no_heading,
    create_stage_output_ok,
    create_stage_output_undeclared,
    create_stage_output_symlink_escape,
    create_approval_ready_ok,
    create_approval_missing,
    create_map_missing,
]


def main() -> int:
    out_dir = HERE / "_build"
    if "--out" in sys.argv:
        out_dir = Path(sys.argv[sys.argv.index("--out") + 1]).resolve()

    if out_dir.exists():
        for entry in sorted(out_dir.iterdir(), reverse=True):
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                entry.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)

    for builder in FIXTURE_BUILDERS:
        builder(out_dir)

    print(f"Fixtures created in {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
