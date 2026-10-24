# Shared throwaway-HOME helpers for the Claude Code install checks.
# Sourced by tests/check-install-manifest.sh, tests/check-install-safety.sh,
# and tests/check-uninstall.sh.
# Defines functions and the temp-HOME variables. Callers set -euo pipefail.
# shellcheck shell=bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "tests/lib/install-home.sh is sourced, not run" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
ADAPTER="$ROOT/adapters/claude-code/install.sh"

VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$ROOT/package.json")
COMMIT=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || true)

fail() { echo "FAIL $*" >&2; exit 1; }

snap() { (cd "$1" && find . -print | LC_ALL=C sort); }

# Bytes, symlink targets, and directories. Not mtimes.
tree_id() {
  python3 - "$1" <<'PY'
import hashlib, os, sys
root = os.path.abspath(sys.argv[1])
rows = []
if os.path.isdir(root):
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in sorted(dirnames):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            if os.path.islink(p):
                rows.append("l " + rel + " -> " + os.readlink(p))
            else:
                rows.append("d " + rel)
        for name in sorted(filenames):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            if os.path.islink(p):
                rows.append("l " + rel + " -> " + os.readlink(p))
            elif os.path.isfile(p):
                digest = hashlib.sha256(open(p, "rb").read()).hexdigest()
                rows.append("f " + rel + " " + digest)
            else:
                rows.append("o " + rel)
rows.sort()
sys.stdout.write("\n".join(rows) + ("\n" if rows else ""))
PY
}

# Manifest checks compare this JSON. Absolute path to link+target, dir,
# file+sha256, or other. Symlink directories are not walked. Not mtimes.
snap_tree() {
  python3 - "$1" "$2" <<'PY'
import hashlib, json, os, sys
root, dest = sys.argv[1:]

def snap(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in list(dirnames):
            p = os.path.join(dirpath, name)
            if os.path.islink(p):
                out[p] = ["link", os.readlink(p)]
                dirnames.remove(name)
            else:
                out[p] = ["dir"]
        for name in filenames:
            p = os.path.join(dirpath, name)
            if os.path.islink(p):
                out[p] = ["link", os.readlink(p)]
            elif os.path.isfile(p):
                out[p] = ["file", hashlib.sha256(open(p, "rb").read()).hexdigest()]
            else:
                out[p] = ["other"]
    return out

json.dump(snap(root), open(dest, "w"))
PY
}

# Parse JSONL. mode=plan checks a dry run; mode=install checks real files.
check_jsonl() {
  local file=$1 target=$2 mode=$3
  python3 - "$file" "$target" "$mode" "$VERSION" "$COMMIT" <<'PY'
import hashlib, json, os, sys
path, target, mode, version, commit = sys.argv[1:]
ops = {"link", "write", "block", "skip"}
kinds = {"generated", "manifest", "backup", "dir"}
lines = open(path, encoding="utf-8").read().splitlines()
if not lines:
    sys.exit("no JSON lines")
records = []
for i, line in enumerate(lines):
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as e:
        sys.exit(f"line {i+1} is not JSON: {e}")
    if i == len(lines) - 1:
        if set(obj) != {"summary"}:
            sys.exit(f"last line is not a summary: {obj}")
        summary = obj["summary"]
    else:
        if obj.get("op") not in ops:
            sys.exit(f"bad op on line {i+1}: {obj}")
        records.append(obj)
        p = obj.get("path")
        if not isinstance(p, str) or not os.path.isabs(p) or not (p == target or p.startswith(target + os.sep)):
            sys.exit(f"path outside target: {p}")
        base = os.path.basename(p)
        if base in ("settings.json", "settings.local.json", ".credentials.json"):
            sys.exit(f"protected path in plan: {p}")
        projects = os.path.join(target, "projects")
        if p == projects or p.startswith(projects + os.sep):
            sys.exit(f"protected path in plan: {p}")
need = ("adapter", "version", "commit", "target", "link", "write", "block", "skip", "paths", "managed_settings")
missing = [k for k in need if k not in summary]
if missing:
    sys.exit(f"summary missing {missing}")
if summary["adapter"] != "claude-code":
    sys.exit(f"adapter {summary['adapter']}")
if summary["version"] != version:
    sys.exit(f"version {summary['version']} != {version}")
if summary["commit"] != (commit or None):
    sys.exit(f"commit {summary['commit']!r} != {commit!r}")
if summary["target"] != target:
    sys.exit(f"target {summary['target']} != {target}")
ms = summary["managed_settings"]
if ms is not None and not isinstance(ms, str):
    sys.exit(f"managed_settings {ms!r}")
counts = {op: 0 for op in ops}
seen = {}
manifests = 0
for obj in records:
    counts[obj["op"]] += 1
    p = obj["path"]
    if p in seen:
        sys.exit(f"duplicate path: {p}")
    seen[p] = obj["op"]
    if obj["op"] == "write":
        kind = obj.get("kind")
        if kind not in kinds:
            sys.exit(f"bad kind: {obj}")
        if "sha256" not in obj or "sha256_after" not in obj or obj["sha256"] != obj["sha256_after"]:
            sys.exit(f"sha pair: {obj}")
        if kind == "manifest":
            manifests += 1
        if mode == "plan":
            if obj["sha256"] is not None:
                sys.exit(f"dry-run write has a sha256: {p}")
        elif kind == "dir":
            if obj["sha256"] is not None or os.path.islink(p) or not os.path.isdir(p):
                sys.exit(f"dir record: {p}")
        elif kind == "manifest":
            if obj["sha256"] is not None or not os.path.isfile(p):
                sys.exit(f"manifest record: {p}")
        else:
            if os.path.islink(p) or not os.path.isfile(p):
                sys.exit(f"missing write: {p}")
            digest = hashlib.sha256(open(p, "rb").read()).hexdigest()
            if digest != obj["sha256"]:
                sys.exit(f"sha256 mismatch: {p}")
        if mode == "install" and obj.get("backup") is not None:
            if not os.path.isfile(obj["backup"]):
                sys.exit(f"missing backup: {obj['backup']}")
    elif obj["op"] == "link" and mode == "install":
        if not os.path.islink(p):
            sys.exit(f"not a symlink: {p}")
        if os.path.realpath(p) != os.path.realpath(obj["source"]):
            sys.exit(f"symlink target mismatch: {p} -> {os.readlink(p)} != {obj['source']}")
        if not os.path.isabs(obj["source"]):
            sys.exit(f"source is not absolute: {obj['source']}")
        if "replaced_link" in obj and not isinstance(obj["replaced_link"], str):
            sys.exit(f"replaced_link: {obj}")
    elif obj["op"] == "block":
        if obj.get("marker") != "coco:rules":
            sys.exit(f"block marker: {obj}")
        if not isinstance(obj.get("created"), bool):
            sys.exit(f"created: {obj}")
        if mode == "plan":
            if obj.get("sha256_after") is not None:
                sys.exit(f"dry-run block has a sha256_after: {p}")
        else:
            if not os.path.isfile(p):
                sys.exit(f"missing rules file: {p}")
            digest = hashlib.sha256(open(p, "rb").read()).hexdigest()
            if digest != obj.get("sha256_after"):
                sys.exit(f"block sha256_after mismatch: {p}")
            bak = obj.get("backup")
            if bak is not None and not os.path.isfile(bak):
                sys.exit(f"missing block backup: {bak}")
    elif obj["op"] == "skip" and not isinstance(obj.get("reason"), str):
        sys.exit(f"skip reason: {obj}")
for op in ops:
    if summary[op] != counts[op]:
        sys.exit(f"summary {op}={summary[op]} but {counts[op]} records")
if summary["block"] != 1:
    sys.exit(f"expected one block, got {summary['block']}")
if summary["paths"] != summary["link"] + summary["write"] + summary["block"]:
    sys.exit(f"paths {summary['paths']} != link+write+block")
if manifests != 1:
    sys.exit(f"expected one manifest write, got {manifests}")
if mode == "plan" and (summary["link"] < 1 or summary["write"] < 1):
    sys.exit(f"plan missing links or writes: {summary}")
if mode == "install" and summary["write"] < 1:
    sys.exit("install recorded no writes")
print(f"ok   {mode} {summary['link']} link, {summary['write']} write, {summary['block']} block, {summary['skip']} skip, {summary['paths']} paths")
PY
}
