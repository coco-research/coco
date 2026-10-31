#!/usr/bin/env bash
# Issue #258: the aider adapter wrote an AGENTS.md of agent names only (0 skills,
# 0 commands, 0 rules, 0 SI front doors) and ignored every bundle but gsd. It now
# reuses the codex AGENTS.md compiler, so its sections must hold the same entries as
# the generic adapter's AGENTS.md for the same bundles, and its receipt must report
# what the file holds. Runs against a temp HOME and temp project dirs; no network.
set -euo pipefail
unset CDPATH COCO_HOME COCO_SI_REPO COCO_SI_COMMANDS_DIR COCO_ADAPTER_LABEL COCO_AUTODETECTED
cd "$(dirname "$0")/.."
ROOT=$(pwd)

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
export HOME="$tmp/home"
mkdir -p "$HOME" "$tmp/proj" "$tmp/gen" "$tmp/core" "$tmp/dry" "$tmp/dryhome"

fail() { echo "FAIL: $*"; exit 1; }

bundles=$(bash "$ROOT/scripts/installable-bundles.sh")

(cd "$tmp/proj" && bash "$ROOT/install.sh" --adapter aider > "$tmp/receipt.txt")
(cd "$tmp/gen" && bash "$ROOT/adapters/generic/install.sh" -o "$tmp/gen/AGENTS.md" --systems "$bundles" > /dev/null)

A="$tmp/proj/AGENTS.md"
[[ -f "$A" ]] || fail "install.sh --adapter aider wrote no AGENTS.md"

# Sections, entries, receipt counts and the generic comparison.
python3 - "$A" "$tmp/gen/AGENTS.md" "$tmp/receipt.txt" <<'PY'
import re, sys

LISTS = ["Skills", "Commands", "Super Intelligence Commands", "Agents"]

def sections(path):
    # First occurrence of each top-level heading only: rule bodies reuse "## Commands".
    out, cur = {}, None
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.startswith("## "):
            h = line[3:]
            if h in LISTS + ["Rules"] and h not in out:
                cur, out[h] = h, []
            elif cur != "Rules":
                cur = None
            continue
        if cur == "Rules":
            if re.fullmatch(r"### [a-z0-9-]+", line):
                out[cur].append(line)
        elif cur and line.startswith("- "):
            out[cur].append(line)
    return out

aider, generic = sections(sys.argv[1]), sections(sys.argv[2])
bad = []
for k in LISTS + ["Rules"]:
    if not aider.get(k):
        bad.append(f"aider AGENTS.md has an empty or missing '{k}' section")
    elif aider[k] != generic.get(k):
        bad.append(f"'{k}': aider has {len(aider[k])} entries, generic has {len(generic.get(k, []))} (or they differ)")

def has(section, cmd):
    return any(e == f"- `{cmd}`" or e.startswith(f"- `{cmd}` ") for e in aider.get(section, []))

for sec, cmd in (("Commands", "/team"), ("Commands", "/team:ship"), ("Super Intelligence Commands", "/SI")):
    if not has(sec, cmd):
        bad.append(f"aider AGENTS.md does not list {cmd} under '{sec}'")

text = open(sys.argv[1], encoding="utf-8").read()
if "## Aider Invocation Guide" not in text or "Codex" in text.split("## Skills")[0]:
    bad.append("aider AGENTS.md does not address Aider in its invocation guide")

receipt = open(sys.argv[3], encoding="utf-8").read()
for label, key in (("Skills", "Skills"), ("Commands", "Commands"),
                   ("SI commands", "Super Intelligence Commands"), ("Agents", "Agents"), ("Rules", "Rules")):
    m = re.search(rf"^  {re.escape(label)} +: (\d+)$", receipt, re.M)
    if not m:
        bad.append(f"receipt has no '{label}' count")
    elif int(m.group(1)) != len(aider.get(key, [])):
        bad.append(f"receipt says {label} {m.group(1)}, AGENTS.md holds {len(aider.get(key, []))}")
m = re.search(r"^  AGENTS.md +: (.+) \(\d+ lines\)$", receipt, re.M)
if not m or m.group(1) != sys.argv[1]:
    bad.append(f"receipt does not name the real target {sys.argv[1]}: {m.group(1) if m else 'no AGENTS.md line'}")

for b in bad:
    print("FAIL:", b)
sys.exit(1 if bad else 0)
PY

# Codex and generic still address Codex.
grep -qx '## Codex Invocation Guide' "$tmp/gen/AGENTS.md" || fail "generic AGENTS.md lost its Codex invocation guide"

# .aider.conf.yml loads AGENTS.md and makes no slash-command claim aider can't keep.
C="$tmp/proj/.aider.conf.yml"
grep -qx '  - AGENTS.md' "$C" || fail ".aider.conf.yml does not read AGENTS.md"
if grep -q '/skill-name' "$C"; then fail ".aider.conf.yml still claims /skill-name invocation"; fi

# Re-run over untouched output: no backup. A user edit is backed up first.
(cd "$tmp/proj" && bash "$ROOT/install.sh" --adapter aider > /dev/null)
backups=$(find "$tmp/proj" -name 'AGENTS.md.coco-backup*' | wc -l | tr -d ' ')
[[ "$backups" == 0 ]] || fail "re-install over untouched AGENTS.md made $backups backup(s)"
echo 'MY EDIT' >> "$A"
(cd "$tmp/proj" && bash "$ROOT/install.sh" --adapter aider > /dev/null)
grep -q 'MY EDIT' "$A.coco-backup" || fail "edited AGENTS.md was not backed up before the re-install"

# --core-only gives a smaller file.
(cd "$tmp/core" && bash "$ROOT/install.sh" --adapter aider --core-only > /dev/null)
core_size=$(wc -c < "$tmp/core/AGENTS.md")
full_size=$(wc -c < "$A")
[[ "$core_size" -lt "$full_size" ]] || fail "--core-only AGENTS.md ($core_size bytes) is not smaller than the default ($full_size)"

# --dry-run writes nothing, in the project or under HOME.
(cd "$tmp/dry" && HOME="$tmp/dryhome" bash "$ROOT/adapters/aider/install.sh" --dry-run > /dev/null)
written=$(find "$tmp/dry" "$tmp/dryhome" -mindepth 1)
[[ -z "$written" ]] || fail "--dry-run wrote files: $written"

# Run from inside a Coco checkout (issue #238): refuse before writing anything.
mkdir -p "$tmp/fake/adapters/aider" "$tmp/fake/sub"
cp "$ROOT/adapters/aider/install.sh" "$tmp/fake/adapters/aider/install.sh"
for d in "$tmp/fake" "$tmp/fake/sub"; do
  rc=0
  (cd "$d" && bash "$tmp/fake/adapters/aider/install.sh" > /dev/null 2>&1) || rc=$?
  [[ "$rc" == 2 ]] || fail "run inside the checkout ($d) exited $rc, want 2"
  [[ ! -e "$d/AGENTS.md" && ! -e "$d/.aider.conf.yml" ]] || fail "run inside the checkout ($d) wrote files"
done

echo "PASS: aider AGENTS.md carries skills, commands, SI commands, agents and rules; receipt, backups, --core-only, --dry-run and the checkout guard hold"
