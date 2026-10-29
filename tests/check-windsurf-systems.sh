#!/usr/bin/env bash
# Issue #215: adapters/windsurf/manifest.json supports_systems must name every
# bundle a plain `install.sh --adapter windsurf` actually installs.
#
# The root installer does not filter that list. When supports_systems is
# non-empty it forwards the whole default set. The manifest has to match the
# set that was forwarded, and a dry-run must link every forwarded bundle that
# has skills/ or agents/ (superintelligence has neither, so it links nothing).
set -euo pipefail
cd "$(dirname "$0")/.."

home=$(mktemp -d)
trap 'rm -rf "$home"' EXIT
out="$home/out"
trace="$home/trace"

# xtrace is the observation: install.sh does not print the bundle list itself.
HOME="$home" bash -x install.sh --adapter windsurf --dry-run >"$out" 2>"$trace"

python3 - "$out" "$trace" <<'PY'
import json, re, sys
from pathlib import Path

out_path, trace_path = sys.argv[1], sys.argv[2]
manifest = json.loads(Path("adapters/windsurf/manifest.json").read_text())
claimed = manifest.get("supports_systems") or []
if not isinstance(claimed, list) or not all(isinstance(x, str) and x for x in claimed):
    sys.exit("FAIL: supports_systems must be a list of bundle names")

trace = Path(trace_path).read_text(errors="replace")
# Quoted when the repo path contains a space, bare otherwise.
matches = re.findall(
    r"adapters/windsurf/install\.sh['\"]?\s+--dry-run\s+--systems\s+(\S+)",
    trace,
)
if len(matches) != 1:
    tail = "\n".join(trace.splitlines()[-8:])
    sys.exit(f"FAIL: expected one forwarded --systems list, found {len(matches)}\n{tail}")
forwarded = [p.strip("'\"") for p in matches[0].split(",") if p.strip("'\"")]

linked = sorted(set(re.findall(r"systems/([^/\s]+)/", Path(out_path).read_text(errors="replace"))))

def show(label, items):
    print(f"  {label}: {','.join(items)}")

claimed_set, forwarded_set = set(claimed), set(forwarded)
if claimed_set != forwarded_set:
    print("FAIL: windsurf supports_systems does not match the bundles a plain install forwards")
    show("manifest", sorted(claimed_set))
    show("forwarded", sorted(forwarded_set))
    show("only in manifest", sorted(claimed_set - forwarded_set))
    show("only forwarded", sorted(forwarded_set - claimed_set))
    sys.exit(1)

missing, extra = [], sorted(set(linked) - claimed_set)
for name in sorted(claimed_set):
    root = Path("systems") / name
    if ((root / "skills").is_dir() or (root / "agents").is_dir()) and name not in linked:
        missing.append(name)
if missing or extra:
    print("FAIL: windsurf dry-run links do not match supports_systems")
    show("linked", linked)
    if missing:
        show("has skills/ or agents/ but no link", missing)
    if extra:
        show("linked but not in the manifest", extra)
    sys.exit(1)

print("PASS: windsurf supports_systems matches the bundles a plain install forwards ("
      + ",".join(forwarded) + ")")
PY
