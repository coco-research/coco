#!/usr/bin/env python3
"""Every example prompt in README.md routes to the team its command names (issue 240).

A README example looks like `/SI-AI-Decide "<prompt>"`: the department word after `SI-` names the team.
`/SI-Decide` names no team, so it only has to route to some team. Both router paths are scored:
keyword always, embed only when COCO_EMBED_URL points at a loopback embedder (else NOT RUN is printed).

    python3 tests/check-readme-prompts.py            # README.md
    README_PATH=other.md python3 tests/check-readme-prompts.py
"""
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "systems" / "superintelligence" / "scripts"))
import meta_select  # noqa: E402

# The department word in a command name, and the registry key it stands for.
DEPT = {"AI": "ai", "Eng": "engineering", "GRC": "risk-compliance", "Fin": "finance",
        "GTM": "gtm", "Strat": "strategy", "Data": "data-analytics", "Climate": "climate-energy",
        "Edu": "education-edtech", "Health": "healthcare-life-sciences", "Legal": "legal-ip",
        "Design": "product-design"}
LINE = re.compile(r'^/SI-([A-Za-z]+)(?:-[A-Za-z-]+)?\s+"([^"]+)"\s*$')


def examples(readme):
    found = []
    for line in readme.read_text(encoding="utf-8").splitlines():
        m = LINE.match(line.strip())
        if m:
            found.append((m.group(1), m.group(2)))
    return found


def top_team(select, prompt, profs):
    teams = select(prompt, profs).get("teams") or []
    return teams[0]["team_key"] if teams else None


BREW = "brew install " + "coco-research/coco/coco"  # the tap is a 404 (issue 252); split so this file does not match itself


def brew_hits():
    """Tracked files other than the changelog that still tell people to use the missing tap."""
    names = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True)
    hits = []
    for name in names.stdout.decode().split("\0"):
        path = ROOT / name
        if name and name != "CHANGELOG.md" and path.is_file() and not path.is_symlink():
            if BREW in path.read_bytes().decode("utf-8", "replace"):
                hits.append(name)
    return hits


def main():
    hits = brew_hits()
    if hits:
        print("FAIL: still tells people to run the missing tap:", ", ".join(hits))
        return 1
    print("docs: 0 files outside CHANGELOG.md name the missing brew tap")
    readme = pathlib.Path(os.environ.get("README_PATH", ROOT / "README.md"))
    items = examples(readme)
    if not items:
        print("FAIL: no /SI-... example prompts found in", readme)
        return 1
    unknown = sorted({w for w, _ in items if w != "Decide" and w not in DEPT})
    if unknown:
        print("FAIL: README names departments this test cannot map:", ", ".join(unknown))
        return 1
    profs = meta_select.team_profiles()
    modes = [("keyword", meta_select.select_keyword)]
    if os.environ.get("COCO_EMBED_URL"):
        modes.append(("embed", meta_select.select_embed))
    else:
        print("embed: NOT RUN (COCO_EMBED_URL not set)")
    bad = 0
    for name, select in modes:
        ok = 0
        for word, prompt in items:
            want = DEPT.get(word)
            got = top_team(select, prompt, profs)
            if got is not None and (want is None or got == want):
                ok += 1
            else:
                bad += 1
                print(f"FAIL [{name}] {prompt!r}: README names {want or 'any team'}, router said {got}")
        print(f"README prompts [{name}]: {ok} of {len(items)} routed as written")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
