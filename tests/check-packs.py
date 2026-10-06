#!/usr/bin/env python3
"""Gate: every installable bundle under systems/ is a valid pack.

A pack is a systems/<name>/ bundle with installable content: the shapes that
adapters/claude-code/install.sh (link_system) wires in, which are skills/*/,
<team>/SKILL.md, agents/*.md, commands/*.md and the command generator
ai/scripts/build_commands.py. Each one ships a pack.json.
Bundles with nothing to install (learning, team) need none.

Rules (optional-packs architecture, C5):
  * pack.json is JSON with only the known fields; `name` equals the folder; `summary`
    is at most 60 characters; `kind` is ours or third-party; `licence` is an SPDX
    expression (LicenseRef-<name> for a custom licence).
  * ours: no `upstream`.
  * third-party: an `attribution`, a LICENSE file, `upstream` as <https url>@<commit>
    (7-40 hex characters), and a SECURITY-REVIEW.md whose header lines read
        Reviewer: Grok 4.7
        Commit: <the same commit as upstream>
        Verdict: SHIP
  * explicit_only and pointer_only packs are never in the default set
    (scripts/installable-bundles.sh), and the default set names only real packs.

GRANDFATHERED below lists the third-party bundles that shipped before the review rule.
Each may skip only the evidence named for it, and only while its pack.json says
"review": "pending". Delete the entry, and the field, when the evidence lands.

Run from repo root:
  python3 tests/check-packs.py              # check the real tree
  python3 tests/check-packs.py --self-test  # prove every rule fires, on a throwaway tree
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GRANDFATHERED = {
    "gsd": {"license-file", "commit", "review"},  # no LICENSE in the bundle, commit not recorded
    "hyperframes": {"commit", "review"},  # commit not recorded
    "reverse-skill": {"review"},  # commit is recorded in its README
}

FIELDS = {"name", "title", "summary", "kind", "licence", "upstream", "attribution",
          "explicit_only", "pointer_only", "content_exceptions", "review"}
REQUIRED = ("name", "title", "summary", "kind", "licence")
SPDX_ID = r"(?:LicenseRef-[A-Za-z0-9.-]+|[A-Za-z0-9][A-Za-z0-9.+-]*)"
SPDX = re.compile(rf"{SPDX_ID}(?: (?:AND|OR|WITH) {SPDX_ID})*")
UPSTREAM = re.compile(r"https://[^\s@]+@([0-9a-f]{7,40}|unknown)")
LICENSE_FILES = ("LICENSE", "LICENSE.md", "LICENSE.txt")


def installable(d):
    """True when an installer would link something out of this bundle (see link_system)."""
    return (any(p.is_dir() for p in (d / "skills").glob("*"))
            or any((t / "SKILL.md").is_file() for t in d.iterdir() if t.is_dir())
            or any(d.glob("agents/*.md")) or any(d.glob("commands/*.md"))
            or (d / "ai" / "scripts" / "build_commands.py").is_file())


def review_header(path):
    """`Key: value` lines near the top of SECURITY-REVIEW.md, keys lower-cased, emphasis dropped."""
    out = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:40]:
        m = re.match(r"^[\s>*_`-]*([A-Za-z][A-Za-z ]*?)[\s*_`]*:[\s*_`]*(.*?)[\s*_`]*$", line)
        if m:
            out.setdefault(m.group(1).lower(), m.group(2))
    return out


def check_review(d, commit, bad):
    f = d / "SECURITY-REVIEW.md"
    if not f.is_file():
        return bad("third-party pack has no SECURITY-REVIEW.md")
    h = review_header(f)
    if "Grok 4.7" not in h.get("reviewer", ""):
        bad("SECURITY-REVIEW.md header must say 'Reviewer: Grok 4.7'")
    rc = h.get("commit", "")
    # With no upstream commit to compare against, the upstream error already fails the gate.
    if commit and not (re.fullmatch(r"[0-9a-f]{7,40}", rc)
                       and (rc.startswith(commit) or commit.startswith(rc))):
        bad(f"SECURITY-REVIEW.md commit {rc!r} must match the upstream commit {commit!r}")
    if h.get("verdict", "").upper() != "SHIP":
        bad("SECURITY-REVIEW.md header must say 'Verdict: SHIP'")


def check_pack(d, pack, grandfathered, bad):
    """Report every problem with one pack folder `d` whose pack.json parsed to the dict `pack`."""
    for k in sorted(set(pack) - FIELDS):
        bad(f"unknown field {k!r}")
    for k in REQUIRED:
        if not isinstance(pack.get(k), str) or not pack[k].strip():
            bad(f"{k} must be a non-empty string")
    if isinstance(pack.get("name"), str) and pack["name"] != d.name:
        bad(f"name {pack['name']!r} must equal the folder name {d.name!r}")
    if isinstance(pack.get("summary"), str) and len(pack["summary"]) > 60:
        bad(f"summary is {len(pack['summary'])} characters, the limit is 60")
    kind = pack.get("kind")
    if isinstance(kind, str) and kind not in ("ours", "third-party"):
        bad("kind must be 'ours' or 'third-party'")
    lic = pack.get("licence")
    if isinstance(lic, str) and not SPDX.fullmatch(lic):
        bad(f"licence {lic!r} is not an SPDX expression (use LicenseRef-<name> for a custom one)")
    for k in ("explicit_only", "pointer_only"):
        if k in pack and not isinstance(pack[k], bool):
            bad(f"{k} must be true or false")
    exc = pack.get("content_exceptions", [])
    if not (isinstance(exc, list) and all(
            isinstance(e, dict) and all(isinstance(e.get(k), str) and e[k].strip()
                                        for k in ("path", "reason")) for e in exc)):
        bad("content_exceptions must be a list of objects that each have a path and a reason")

    owed = set()  # evidence this pack may skip because it is grandfathered and still pending
    if "review" in pack:
        if pack["review"] != "pending":
            bad("review must be 'pending', or absent once SECURITY-REVIEW.md is committed")
        elif d.name not in grandfathered or kind != "third-party":
            bad("review: pending is only for the grandfathered third-party bundles "
                f"({', '.join(sorted(grandfathered))})")
        else:
            owed = grandfathered[d.name]
    upstream = pack.get("upstream")
    if kind == "ours" and upstream:
        bad("upstream is for third-party packs only")
    if kind == "third-party":
        if not str(pack.get("attribution", "")).strip():
            bad("third-party packs need an attribution")
        if "license-file" not in owed and not any((d / f).is_file() for f in LICENSE_FILES):
            bad("third-party pack has no LICENSE file")
        m = UPSTREAM.fullmatch(upstream) if isinstance(upstream, str) else None
        if not m:
            bad("upstream must be <https url>@<commit>, the commit being 7-40 hex characters")
        elif m.group(1) == "unknown" and "commit" not in owed:
            bad("upstream commit 'unknown' is only allowed for grandfathered packs")
        if "review" not in owed:
            check_review(d, m.group(1) if m else None, bad)
    return owed


def check(root, defaults, grandfathered):
    """Return (errors, notes) for the tree under `root`."""
    errors, notes, packs = [], [], {}
    for d in sorted(p for p in (root / "systems").iterdir() if p.is_dir()):
        f = d / "pack.json"
        if not f.is_file():
            if installable(d):
                errors.append(f"systems/{d.name}/ has installable content but no pack.json")
            continue

        def bad(msg):
            errors.append(f"systems/{d.name}/pack.json: {msg}")

        try:
            pack = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as e:
            bad(f"not valid JSON ({e})")
            continue
        if not isinstance(pack, dict):
            bad("must be a JSON object")
            continue
        packs[d.name] = pack
        owed = check_pack(d, pack, grandfathered, bad)
        if owed:
            notes.append(f"{d.name} is grandfathered (review pending), exempt from: "
                         + ", ".join(sorted(owed)))
    for name in defaults:
        if name not in packs:
            errors.append(f"scripts/installable-bundles.sh: default bundle {name!r} "
                          f"has no valid systems/{name}/pack.json")
        elif packs[name].get("explicit_only") or packs[name].get("pointer_only"):
            errors.append(f"scripts/installable-bundles.sh: default bundle {name!r} "
                          "is explicit_only or pointer_only")
    for name in grandfathered:
        if packs.get(name, {}).get("review") != "pending":
            errors.append(f"GRANDFATHERED lists {name!r} but systems/{name}/pack.json is not "
                          "'review': 'pending': delete the entry")
    return errors, notes


def read_defaults(root):
    script = root / "scripts" / "installable-bundles.sh"
    r = subprocess.run(["bash", str(script), "--one-per-line"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FAIL: {script.name} exited {r.returncode}:\n{r.stderr}")
    return r.stdout.split()


# ---- self-test: plant a defect in a throwaway tree and require the gate to say so ----

GOOD_REVIEW = "# Security review\n\nReviewer: Grok 4.7\nCommit: abcdef1234\nVerdict: SHIP\n"


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _pack(**extra):
    return {"name": "x", "title": "X", "summary": "A pack", "kind": "ours", "licence": "MIT", **extra}


def _base(root):
    for name, pack, files in (
        ("ours-pack", _pack(), []),
        ("third-pack", _pack(kind="third-party", attribution="By someone",
                             upstream="https://github.com/o/r@abcdef1234"),
         [("LICENSE", "MIT"), ("SECURITY-REVIEW.md", GOOD_REVIEW)]),
        ("legacy", _pack(kind="third-party", attribution="By someone", review="pending",
                         upstream="https://github.com/o/r@unknown"), []),
    ):
        pack["name"] = name
        _write(root, f"systems/{name}/pack.json", json.dumps(pack))
        _write(root, f"systems/{name}/skills/s/SKILL.md", "---\nname: s\n---\n")
        for rel, text in files:
            _write(root, f"systems/{name}/{rel}", text)
    _write(root, "systems/docs-only/README.md", "No installable content, so no pack.json needed.\n")


def _edit(folder, /, **changes):
    def apply(root):
        f = root / "systems" / folder / "pack.json"
        data = json.loads(f.read_text())
        for k, v in changes.items():
            if v is None:
                data.pop(k, None)
            else:
                data[k] = v
        f.write_text(json.dumps(data))
    return apply


def _rm(rel):
    return lambda root: (root / "systems" / rel).unlink()


def _put(rel, text):
    return lambda root: _write(root, f"systems/{rel}", text)


CASES = [  # (what is planted, how, the error it must produce)
    ("an installable bundle with no pack.json", _rm("ours-pack/pack.json"), "no pack.json"),
    ("a bundle that installs only through the command generator",
     _put("gen-only/ai/scripts/build_commands.py", "# generator\n"), "no pack.json"),
    ("pack.json that is not JSON", _put("ours-pack/pack.json", "{"), "not valid JSON"),
    ("a typo'd or retired field", _edit("ours-pack", default=True), "unknown field 'default'"),
    ("a missing required field", _edit("ours-pack", summary=None), "summary must be"),
    ("a summary over 60 characters", _edit("ours-pack", summary="x" * 61), "limit is 60"),
    ("a name that is not the folder", _edit("ours-pack", name="other"), "must equal the folder"),
    ("an unknown kind", _edit("ours-pack", kind="mine"), "kind must be"),
    ("a licence that is not SPDX", _edit("ours-pack", licence="mit license"), "not an SPDX"),
    ("an ours pack with an upstream", _edit("ours-pack", upstream="https://x.io/y@abcdef1"),
     "third-party packs only"),
    ("malformed content_exceptions", _edit("ours-pack", content_exceptions=[{"path": "a"}]),
     "content_exceptions"),
    ("third-party without a LICENSE", _rm("third-pack/LICENSE"), "no LICENSE file"),
    ("third-party without attribution", _edit("third-pack", attribution=None), "attribution"),
    ("an upstream with no commit", _edit("third-pack", upstream="https://github.com/o/r"),
     "upstream must be"),
    ("an unknown commit outside the grandfather list",
     _edit("third-pack", upstream="https://github.com/o/r@unknown"), "only allowed for grandfathered"),
    ("third-party without SECURITY-REVIEW.md", _rm("third-pack/SECURITY-REVIEW.md"),
     "no SECURITY-REVIEW.md"),
    ("a review by someone else",
     _put("third-pack/SECURITY-REVIEW.md", GOOD_REVIEW.replace("Grok 4.7", "A Person")), "Grok 4.7"),
    ("a review of another commit",
     _put("third-pack/SECURITY-REVIEW.md", GOOD_REVIEW.replace("abcdef1234", "1234567")),
     "must match the upstream commit"),
    ("a verdict that is not SHIP",
     _put("third-pack/SECURITY-REVIEW.md", GOOD_REVIEW.replace("SHIP", "SHIP WITH FIXES")),
     "Verdict: SHIP"),
    ("a review file that is not UTF-8",
     lambda root: (root / "systems/third-pack/SECURITY-REVIEW.md").write_bytes(b"\xff\xfe"),
     "Grok 4.7"),
    ("pending review on a pack not grandfathered", _edit("third-pack", review="pending"),
     "only for the grandfathered"),
    ("a grandfather entry whose pack is no longer pending", _edit("legacy", review=None),
     "delete the entry"),
    ("a default bundle that is explicit_only", _edit("ours-pack", explicit_only=True),
     "explicit_only or pointer_only"),
]


def self_test():
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "base"
        _base(base)
        grandfathered = {"legacy": {"license-file", "commit", "review"}}

        def run(root, defaults=("ours-pack",)):
            return check(root, list(defaults), grandfathered)[0]

        errs = run(base)
        print(f"  {'PASS' if not errs else 'FAIL'}: the unmodified fixture is accepted")
        failures += bool(errs)
        for e in errs:
            print(f"    {e}")
        # The review header also parses with markdown emphasis.
        case = Path(tmp) / "md"
        shutil.copytree(base, case)
        _write(case, "systems/third-pack/SECURITY-REVIEW.md",
               "# Review\n\n**Reviewer:** Grok 4.7\n- **Commit:** `abcdef1234`\n**Verdict**: **SHIP**\n")
        errs = run(case)
        print(f"  {'PASS' if not errs else 'FAIL'}: a markdown-styled review header is accepted")
        failures += bool(errs)
        # A default bundle with no pack at all.
        errs = run(base, ("ours-pack", "ghost"))
        ok = any("'ghost'" in e for e in errs)
        print(f"  {'PASS' if ok else 'FAIL'}: a default bundle with no pack is rejected")
        failures += not ok
        # A defaults script that fails is reported with its own stderr, not as a traceback.
        broken = Path(tmp) / "broken"
        _write(broken, "scripts/installable-bundles.sh", "echo boom >&2; exit 3\n")
        try:
            read_defaults(broken)
            ok = False
        except SystemExit as e:
            ok = "boom" in str(e)
        print(f"  {'PASS' if ok else 'FAIL'}: a failing defaults script is reported with its stderr")
        failures += not ok
        # A missing upstream commit is one error, not a second misleading review-commit error.
        case = Path(tmp) / "nocommit"
        shutil.copytree(base, case)
        _edit("third-pack", upstream="https://github.com/o/r")(case)
        errs = run(case)
        ok = (any("upstream must be" in e for e in errs)
              and not any("must match the upstream commit" in e for e in errs))
        print(f"  {'PASS' if ok else 'FAIL'}: a missing upstream commit is reported once")
        failures += not ok
        for i, (what, plant, expect) in enumerate(CASES):
            case = Path(tmp) / f"case{i}"
            shutil.copytree(base, case)
            plant(case)
            errs = run(case)
            ok = any(expect in e for e in errs)
            print(f"  {'PASS' if ok else 'FAIL'}: rejects {what}")
            if not ok:
                failures += 1
                print(f"    expected an error containing {expect!r}, got: {errs or 'no errors'}")
    print("self-test:", "all rules fire" if not failures else f"{failures} rule(s) did not fire")
    return 1 if failures else 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    errors, notes = check(ROOT, read_defaults(ROOT), GRANDFATHERED)
    for n in notes:
        print(f"  NOTE: {n}")
    for e in errors:
        print(f"  FAIL: {e}")
    if errors:
        return 1
    n = sum(1 for p in (ROOT / "systems").glob("*/pack.json"))
    print(f"PASS: {n} packs are valid, and every installable bundle has one")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
