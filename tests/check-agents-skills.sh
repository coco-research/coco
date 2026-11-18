#!/usr/bin/env bash
# Hermetic verification for `bash install.sh --agents-skills` (`scripts/link-agents-skills.sh`).
# Compatible with bash 3.2 and bash 5. Never touches the caller's real HOME.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)
ROOT_REAL=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$ROOT")

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

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
                rows.append("d " + rel + " %o" % (os.lstat(p).st_mode & 0o7777))
        for name in sorted(filenames):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            if os.path.islink(p):
                rows.append("l " + rel + " -> " + os.readlink(p))
            elif os.path.isfile(p):
                digest = hashlib.sha256(open(p, "rb").read()).hexdigest()
                rows.append("f " + rel + " " + digest + " %o" % (os.lstat(p).st_mode & 0o7777))
rows.sort()
sys.stdout.write("\n".join(rows) + ("\n" if rows else ""))
PY
}

# 1. Fresh HOME: links all default skills (core + installable-bundles + 13 SI front doors),
#    excludes opt-in `reverse-skill`, writes `.coco-agents-skills`, and is byte-identical on re-run.
FRESH_HOME="$WORK/fresh-home"
mkdir -p "$FRESH_HOME"

env -u CLAUDECODE -u AGENTS_HOME -u AGENTS_SKILLS_DIR HOME="$FRESH_HOME" \
  bash "$ROOT/install.sh" --agents-skills >"$WORK/fresh-1.log" 2>&1

SKILLS_DIR="$FRESH_HOME/.agents/skills"
MARKER="$SKILLS_DIR/.coco-agents-skills"
[[ -d "$SKILLS_DIR" ]] || fail "missing $SKILLS_DIR"
[[ -f "$MARKER" && ! -L "$MARKER" ]] || fail "missing marker $MARKER"
grep -qx '# managed-by: coco' "$MARKER" || fail "marker missing managed-by header"

# Check counts, SI front door resolution, and absence of reverse-skill by default.
LINK_COUNT=$(python3 - "$SKILLS_DIR" "$ROOT_REAL" <<'PY'
import os, sys
skills_dir, root_real = sys.argv[1], sys.argv[2]
links = []
for name in sorted(os.listdir(skills_dir)):
    if name == ".coco-agents-skills":
        continue
    p = os.path.join(skills_dir, name)
    assert os.path.islink(p), f"expected symlink at {p}"
    real = os.path.realpath(p)
    assert real.startswith(root_real + os.sep), f"link {name} points outside repo: {real}"
    assert os.path.isfile(os.path.join(real, "SKILL.md")), f"link {name} missing SKILL.md"
    assert "/systems/reverse-skill/" not in real, f"opt-in reverse-skill leaked into default install: {name}"
    links.append(name)
assert "humanizer" in links, "missing core skill humanizer"
assert "ai-super-intelligence" in links, "missing SI front door ai-super-intelligence"
assert "gtm-super-intelligence" in links, "missing SI front door gtm-super-intelligence"
print(len(links))
PY
)
[[ "$LINK_COUNT" -ge 180 ]] || fail "expected >= 180 default links, got $LINK_COUNT"

tree_id "$FRESH_HOME/.agents" >"$WORK/fresh-before.txt"
env -u CLAUDECODE -u AGENTS_HOME -u AGENTS_SKILLS_DIR HOME="$FRESH_HOME" \
  bash "$ROOT/install.sh" --agents-skills >"$WORK/fresh-2.log" 2>&1
tree_id "$FRESH_HOME/.agents" >"$WORK/fresh-after.txt"
cmp -s "$WORK/fresh-before.txt" "$WORK/fresh-after.txt" \
  || fail "re-running --agents-skills changed ~/.agents bytes or links"

# 2. User folders and foreign symlinks are NEVER replaced or deleted (including on --uninstall).
USER_HOME="$WORK/user-home"
EXT_DIR="$WORK/external-skill"
mkdir -p "$USER_HOME/.agents/skills/my-custom-skill" \
         "$USER_HOME/.agents/skills/humanizer" \
         "$EXT_DIR"
printf 'custom\n' >"$USER_HOME/.agents/skills/my-custom-skill/SKILL.md"
printf 'user-owned-humanizer\n' >"$USER_HOME/.agents/skills/humanizer/SKILL.md"
printf 'external\n' >"$EXT_DIR/SKILL.md"
ln -s "$EXT_DIR" "$USER_HOME/.agents/skills/prd-generator"

env -u CLAUDECODE -u AGENTS_HOME -u AGENTS_SKILLS_DIR HOME="$USER_HOME" \
  bash "$ROOT/install.sh" --agents-skills >"$WORK/user-1.log" 2>&1

grep -q "skip humanizer: user folder kept" "$WORK/user-1.log" \
  || fail "did not report keeping user folder 'humanizer'"
grep -q "skip prd-generator: user link kept" "$WORK/user-1.log" \
  || fail "did not report keeping user symlink 'prd-generator'"
[[ ! -L "$USER_HOME/.agents/skills/humanizer" ]] || fail "user folder humanizer was turned into a symlink"
[[ "$(cat "$USER_HOME/.agents/skills/humanizer/SKILL.md")" == "user-owned-humanizer" ]] \
  || fail "user folder humanizer content changed"
[[ "$(cat "$USER_HOME/.agents/skills/my-custom-skill/SKILL.md")" == "custom" ]] \
  || fail "unrelated user folder my-custom-skill was altered"
[[ -L "$USER_HOME/.agents/skills/prd-generator" && "$(readlink "$USER_HOME/.agents/skills/prd-generator")" == "$EXT_DIR" ]] \
  || fail "foreign user symlink prd-generator was replaced"

#Narrowing to --core-only removes Coco bundle links while keeping all user folders/links intact.
env -u CLAUDECODE -u AGENTS_HOME -u AGENTS_SKILLS_DIR HOME="$USER_HOME" \
  bash "$ROOT/install.sh" --agents-skills --core-only >"$WORK/user-core.log" 2>&1
[[ ! -e "$USER_HOME/.agents/skills/ai-super-intelligence" && ! -L "$USER_HOME/.agents/skills/ai-super-intelligence" ]] \
  || fail "--core-only did not prune Coco-managed bundle link ai-super-intelligence"
[[ "$(cat "$USER_HOME/.agents/skills/humanizer/SKILL.md")" == "user-owned-humanizer" ]] \
  || fail "--core-only touched user folder humanizer"
[[ "$(cat "$USER_HOME/.agents/skills/my-custom-skill/SKILL.md")" == "custom" ]] \
  || fail "--core-only touched user folder my-custom-skill"

# Uninstall removes Coco links + marker and leaves user folders and foreign symlink untouched.
env -u CLAUDECODE -u AGENTS_HOME -u AGENTS_SKILLS_DIR HOME="$USER_HOME" \
  bash "$ROOT/scripts/link-agents-skills.sh" --uninstall >"$WORK/user-uninst.log" 2>&1
[[ ! -e "$USER_HOME/.agents/skills/.coco-agents-skills" ]] || fail "uninstall left marker file"
[[ -f "$USER_HOME/.agents/skills/humanizer/SKILL.md" ]] || fail "uninstall removed user folder humanizer"
[[ -f "$USER_HOME/.agents/skills/my-custom-skill/SKILL.md" ]] || fail "uninstall removed my-custom-skill"
[[ -L "$USER_HOME/.agents/skills/prd-generator" ]] || fail "uninstall removed foreign symlink prd-generator"

# 3. --dry-run creates nothing in a clean HOME.
DRY_HOME="$WORK/dry-home"
mkdir -p "$DRY_HOME"
env -u CLAUDECODE -u AGENTS_HOME -u AGENTS_SKILLS_DIR HOME="$DRY_HOME" \
  bash "$ROOT/install.sh" --agents-skills --dry-run >"$WORK/dry.log" 2>&1
[[ ! -e "$DRY_HOME/.agents" ]] || fail "--dry-run created ~/.agents"

# 4. --packs integration narrows links to core + gsd.
PACK_HOME="$WORK/pack-home"
mkdir -p "$PACK_HOME"
env -u CLAUDECODE -u AGENTS_HOME -u AGENTS_SKILLS_DIR HOME="$PACK_HOME" \
  bash "$ROOT/install.sh" --agents-skills --packs gsd >"$WORK/pack.log" 2>&1
[[ ! -L "$PACK_HOME/.agents/skills/ai-super-intelligence" ]] || fail "--packs gsd included si front door"
[[ -L "$PACK_HOME/.agents/skills/humanizer" ]] || fail "--packs gsd missing core skill"

# 5. Replacing a previously-managed symlink with a foreign symlink preserves the foreign target, and combined --uninstall --adapter --agents-skills cleans both.
EXT_SKILL="$WORK/ext-foreign-skill"
mkdir -p "$EXT_SKILL"
rm "$PACK_HOME/.agents/skills/humanizer"
ln -s "$EXT_SKILL" "$PACK_HOME/.agents/skills/humanizer"
env -u CLAUDECODE -u AGENTS_HOME -u AGENTS_SKILLS_DIR HOME="$PACK_HOME" \
  bash "$ROOT/install.sh" --agents-skills --core-only >"$WORK/relink.log" 2>&1
[[ "$(readlink "$PACK_HOME/.agents/skills/humanizer")" == "$EXT_SKILL" ]] \
  || fail "previously-managed name replaced user's foreign symlink"

COMB_HOME="$WORK/comb-home"
mkdir -p "$COMB_HOME"
env -u CLAUDECODE -u AGENTS_HOME -u AGENTS_SKILLS_DIR HOME="$COMB_HOME" \
  bash "$ROOT/install.sh" --adapter cursor --agents-skills --core-only -y >"$WORK/comb-inst.log" 2>&1
[[ -f "$COMB_HOME/.agents/skills/.coco-agents-skills" ]] || fail "combined install missed ~/.agents/skills"
env -u CLAUDECODE -u AGENTS_HOME -u AGENTS_SKILLS_DIR HOME="$COMB_HOME" \
  bash "$ROOT/install.sh" --uninstall --adapter cursor --agents-skills >"$WORK/comb-uninst.log" 2>&1
[[ ! -e "$COMB_HOME/.agents/skills/.coco-agents-skills" ]] || fail "combined --uninstall --adapter --agents-skills did not remove ~/.agents/skills"

echo "~/.agents/skills: ${LINK_COUNT} links · idempotent · user folders kept · packs + dry-run clean"
