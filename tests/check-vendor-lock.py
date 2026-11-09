#!/usr/bin/env python3
"""Gate: vendored third-party code is locked to a licence, a ref and a digest.

data/vendor-lock.json is the machine-readable half of CREDITS.md's first table.
CREDITS says what CoCo took and why shipping it is lawful; the lock says which
files carry it, under which licence, and at which upstream ref. This gate keeps
the two in step, so a vendored licence cannot change, and a vendored item cannot
quietly lose its row, without a row changing with it.

Rules, one line per problem:
  (a) every row's `paths` globs match at least one file;
  (b) every `licence_files[].sha256` equals the sha256 of that file on disk;
  (c) every vendored row in CREDITS.md has a lock row with the same name, and
      no lock row names something CREDITS.md does not vendor;
  (d) `licence_spdx` is one of ALLOWED_SPDX, and LicenseRef-GSAP belongs to the
      GSAP row alone.

Which CREDITS rows count as vendored. The first table credits every project,
but three kinds of row ship no code here: a link-only stub, an item that is not
bundled, and an item whose licence has no id in ALLOWED_SPDX (CC0, CC BY 4.0).
The last kind cannot be locked at all, so it is not required to have a row.

Digests are pinned, never guessed. `--update` rewrites every `sha256` from the
files on disk and you commit the result. Until a file is pinned its digest is
the empty string, and rule (b) then compares the file with its own committed
blob instead, so an unpinned entry still catches a local edit; only a committed
one can slip past. Run `--update` once and the lock stands on its own.

Run from the repo root:
  python3 tests/check-vendor-lock.py
  python3 tests/check-vendor-lock.py --update
"""
import glob
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = ROOT / "data" / "vendor-lock.json"
CREDITS_PATH = ROOT / "CREDITS.md"

ALLOWED_SPDX = ("MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC",
                "OFL-1.1", "LicenseRef-GSAP")
FIELDS = ("name", "paths", "repo", "pinned_ref", "licence_spdx",
          "licence_files", "mode", "patch")
MODES = ("verbatim", "adapted")
LICENCE_NAMES = ("LICENSE", "LICENSE.txt", "NOTICE", "NOTICE.md")

HEADING = "## Bundled / adapted systems"
# Rows that ship no code here.
STUB = re.compile(r"link-only stub|not bundled|not redistributed", re.I)
# Rows whose licence we can name with an id from ALLOWED_SPDX.
NAMED_LICENCE = re.compile(
    r"\bMIT\b|\bApache[- ]2\.0\b|\bBSD-[23]-Clause\b|\bISC\b|\bOFL\b|\bGSAP\b", re.I)
PARENTHETICAL = re.compile(r"\s*\([^()]*\)\s*$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def credits_rows():
    """(name, what we took, licence cell) for every row of the first table."""
    text = CREDITS_PATH.read_text(encoding="utf-8")
    if HEADING not in text:
        raise SystemExit(f"CREDITS.md has no '{HEADING}' section")
    section = text.split(HEADING, 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|") or not line.strip("| -"):
            continue                      # prose, or the |---| separator
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        bold = re.match(r"\*\*(.+?)\*\*", cells[0])
        if not bold:
            continue
        name = PARENTHETICAL.sub("", bold.group(1)).strip()
        rows.append((name, cells[1], cells[3]))
    return rows


def vendored_rows():
    """CREDITS rows that ship code here: {name: licence cell}."""
    out = {}
    for name, took, licence in credits_rows():
        if STUB.search(took) or not NAMED_LICENCE.search(licence):
            continue
        out[name] = licence
    return out


def committed_bytes(rel):
    """The bytes of `rel` in HEAD, or None when git cannot answer."""
    try:
        done = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"],
                              capture_output=True)
    except OSError:
        return None
    return done.stdout if done.returncode == 0 else None


def check_shape(label, row):
    problems = []
    missing = [field for field in FIELDS if field not in row]
    if missing:
        problems.append(f"{label}: missing field(s) {', '.join(missing)}")
    if row.get("mode") not in MODES:
        problems.append(f"{label}: mode must be one of {', '.join(MODES)}, got {row.get('mode')!r}")
    spdx = row.get("licence_spdx")
    if spdx not in ALLOWED_SPDX:
        problems.append(f"{label}: licence_spdx {spdx!r} is not one of {', '.join(ALLOWED_SPDX)}")
    if spdx == "LicenseRef-GSAP" and row.get("name") != "GSAP":
        problems.append(f"{label}: LicenseRef-GSAP is reserved for the GSAP row")
    return problems


def check_paths(label, row):
    """(a) every pattern matches something, and every one is repo-relative."""
    problems = []
    patterns = row.get("paths") or []
    if not patterns:
        problems.append(f"{label}: has no paths")
    for pattern in patterns:
        if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            problems.append(f"{label}: path {pattern!r} is not repo-relative")
            continue
        if not glob.glob(str(ROOT / pattern), recursive=True):
            problems.append(f"{label}: path {pattern!r} matches nothing")
    return problems


def check_licences(label, row):
    """(b) every listed licence file is where the lock says, unchanged."""
    problems = []
    notices = []
    for entry in row.get("licence_files") or []:
        rel = entry.get("path") if isinstance(entry, dict) else None
        if not rel:
            problems.append(f"{label}: licence_files entry without a path")
            continue
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            problems.append(f"{label}: licence file {rel!r} is not repo-relative")
            continue
        path = ROOT / rel
        if not path.is_file():
            problems.append(f"{label}: licence file {rel} does not exist")
            continue
        if path.name not in LICENCE_NAMES:
            problems.append(f"{label}: {rel} is not one of {', '.join(LICENCE_NAMES)}")
            continue
        digest = entry.get("sha256")
        actual = sha256_bytes(path.read_bytes())
        if digest:
            if not isinstance(digest, str) or not HEX64.match(digest):
                problems.append(f"{label}: {rel} has a malformed sha256 {digest!r}")
            elif digest != actual:
                problems.append(f"{label}: {rel} changed since it was pinned "
                                f"(sha256 {actual})")
            continue
        # Unpinned: the file must at least still match the copy in HEAD.
        base = committed_bytes(rel)
        if base is None:
            notices.append(f"{label}: {rel} is unpinned and has no committed copy to compare with")
        elif sha256_bytes(base) != actual:
            problems.append(f"{label}: {rel} changed and its sha256 is not pinned "
                            f"(run: python3 tests/check-vendor-lock.py --update)")
    return problems, notices


def check_credits(rows):
    """(c) the lock covers every vendored CREDITS row, and names no other."""
    problems = []
    required = vendored_rows()
    locked = [row.get("name") for row in rows]
    for name in required:
        if name not in locked:
            problems.append(f"CREDITS.md row {name!r} is vendored but "
                            f"data/vendor-lock.json has no row for it")
    for name in locked:
        if name not in required:
            problems.append(f"data/vendor-lock.json row {name!r} does not match "
                            f"a vendored row in CREDITS.md")
    if len(set(locked)) != len(locked):
        problems.append("data/vendor-lock.json: duplicate row names")
    return problems


def unpinned_count(rows):
    return sum(1 for row in rows for entry in row.get("licence_files") or []
               if isinstance(entry, dict) and not entry.get("sha256"))


def pin(rows):
    """Rewrite every digest from the files on disk."""
    for row in rows:
        for entry in row.get("licence_files") or []:
            if not isinstance(entry, dict) or not entry.get("path"):
                continue
            path = ROOT / entry["path"]
            if path.is_file():
                entry["sha256"] = sha256_bytes(path.read_bytes())
    LOCK_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")


def main(argv):
    update = "--update" in argv
    try:
        rows = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"data/vendor-lock.json: cannot read the lock ({exc})")
        return 1
    if not isinstance(rows, list):
        print("data/vendor-lock.json: the lock must be a JSON array of rows")
        return 1

    problems, notices = [], []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            problems.append(f"row {index}: must be an object")
            continue
        label = row.get("name") or f"row {index}"
        problems += check_shape(label, row)
        problems += check_paths(label, row)
        if not update:
            found, notes = check_licences(label, row)
            problems += found
            notices += notes
    problems += check_credits(rows)

    if problems:
        for problem in problems:
            print(problem)
        return 1
    for notice in notices:
        print(notice)
    if update:
        pin(rows)
        print(f"Pinned {sum(len(row.get('licence_files') or []) for row in rows)} "
              f"licence digests in data/vendor-lock.json.")
        return 0
    print(f"Vendored items locked: {len(rows)} rows checked against CREDITS.md.")
    unpinned = unpinned_count(rows)
    if unpinned:
        print(f"{unpinned} licence digest(s) still unpinned; pin them with: "
              f"python3 tests/check-vendor-lock.py --update")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
