#!/usr/bin/env bash
# PI-Desktop adapter — wires Coco artifacts into the folders PI-Desktop reads
# natively, so no plugin is required and nothing has to be drag-and-dropped.
#
# Where things land:
#   commands/<ns>/<name>.md   -> ~/.pi/agent/prompts/<ns>-<name>.md    (composer slash command)
#   commands/<ns>/_index.md   -> ~/.pi/agent/prompts/<ns>.md           (the bare /<ns> command)
#   skills/<name>/            -> ~/.agents/skills/<name>/              (copy, assets included)
#   systems/<b>/skills/<n>/   -> ~/.agents/skills/<n>/                 (only with --systems)
#   workflows/*.md            -> ~/.agents/skills/coco-workflow-<n>/   (procedural instructions)
#   agents/*.md               -> ~/.agents/subagents/coco-<name>.md    (Task subagent)
#   systems/<b>/agents/*.md   -> ~/.agents/subagents/coco-<name>.md    (only with --systems)
#
# Why a plugin is not used: a PI-Desktop plugin may only touch the workspace or a
# directory the user picks at runtime (manifest.fs.root is "workspace" or
# "userSelected"), so it cannot write into ~/.agents or ~/.pi/agent. Files are the
# interface, and this script writes them.
#
# Usage:
#   bash adapters/pi-desktop/install.sh                        # install everything
#   bash adapters/pi-desktop/install.sh --systems gsd,brain    # add system bundles
#   bash adapters/pi-desktop/install.sh --dry-run              # preview only
#   bash adapters/pi-desktop/install.sh --uninstall            # remove what it wrote
#   bash adapters/pi-desktop/install.sh --source /path/to/coco # install a different checkout
#   bash adapters/pi-desktop/install.sh --force                # replace files this adapter did not write
#
# Environment overrides (mainly for tests):
#   PI_AGENT_HOME   default ~/.pi/agent    (commands land in $PI_AGENT_HOME/prompts)
#   AGENTS_HOME     default ~/.agents      (skills and subagents land under it)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_ROOT="$REPO_ROOT"
DRY_RUN=0
UNINSTALL=0
FORCE=0
SYSTEMS_CSV=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --force) FORCE=1 ;;
    --systems) shift; SYSTEMS_CSV="${1:-}" ;;
    --source) shift; SOURCE_ROOT="$(cd "${1:-.}" && pwd)" ;;
    --help|-h) grep '^#' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required by the PI-Desktop adapter (front matter rewriting)." >&2
  echo "Install python3 and re-run." >&2
  exit 1
fi

export COCO_SOURCE_ROOT="$SOURCE_ROOT"
export COCO_PI_AGENT_HOME="${PI_AGENT_HOME:-$HOME/.pi/agent}"
export COCO_FORCE="$FORCE"
export COCO_AGENTS_HOME="${AGENTS_HOME:-$HOME/.agents}"
export COCO_DRY_RUN="$DRY_RUN"
export COCO_UNINSTALL="$UNINSTALL"
export COCO_SYSTEMS="$SYSTEMS_CSV"

python3 - <<'PY'
"""Install the Coco framework into PI-Desktop's native discovery folders.

Three surfaces, all file-based:

  commands/<ns>/<file>.md -> <pi-agent>/prompts/<ns>-<file>.md   slash command
  <skill dir>/            -> ~/.agents/skills/<id>/             agent skill
  agents/<name>.md        -> ~/.agents/subagents/coco-<name>.md Task subagent

Every generated file carries a marker line, which is what makes `--uninstall`
safe and re-running idempotent: the script only ever replaces or deletes files it
wrote itself.
"""
import os
import re
import shutil
import sys
from collections import Counter

SOURCE = os.environ["COCO_SOURCE_ROOT"]
PI_AGENT = os.environ["COCO_PI_AGENT_HOME"]
AGENTS = os.environ["COCO_AGENTS_HOME"]
DRY = os.environ["COCO_DRY_RUN"] == "1"
UNINSTALL = os.environ["COCO_UNINSTALL"] == "1"
FORCE = os.environ["COCO_FORCE"] == "1"
SYSTEMS = [s.strip() for s in os.environ["COCO_SYSTEMS"].split(",") if s.strip()]

PROMPT_DIR = os.path.join(PI_AGENT, "prompts")
SKILL_DIR = os.path.join(AGENTS, "skills")
SUBAGENT_DIR = os.path.join(AGENTS, "subagents")

MARKER = "Coco PI-Desktop adapter"
DESC_CAP = 240          # PI-Desktop caps skill descriptions at 240 characters
MAX_TURNS = 80          # the host's own ceiling for a subagent
SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", ".DS_Store", ".pytest_cache"}
READ_TOOLS = ["Read", "Glob", "Grep", "Bash"]
WRITE_TOOLS = ["Read", "Glob", "Grep", "Bash", "Edit", "Write"]
WRITER_NAMES = {
    "ai-engineer", "data-specialist", "database-architect", "mcp-specialist",
    "refactoring-specialist", "typescript-pro", "ui-ux-designer",
    "gsd-executor", "gsd-code-fixer", "gsd-doc-writer",
}

written, skipped, removed = [], [], []


def say(msg):
    print(msg)




def parse_frontmatter(text):
    """Return (mapping, body). Tolerant of the simple front matter these files use."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block, body = text[4:end], text[end + 4:].lstrip("\n")
    fm = {}
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm, body


def one_line(value):
    return " ".join(str(value).split())


def clip(text, limit=DESC_CAP):
    text = one_line(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def front_matter(fields):
    """Emit front matter the host's own parser reads back unambiguously."""
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(value)}]")
        else:
            safe = str(value).replace('"', "'").replace("\n", " ")
            lines.append(f'{key}: "{safe}"')
    lines.append("---")
    return "\n".join(lines)


    for para in body.split("\n\n"):
        para = para.strip()
        if para and not para.startswith(("#", ">", "|", "---", "<!--")):
            return one_line(re.sub(r"[*`\[\]]", "", para))
    return ""


def prose_fallback(body):
    """First real prose paragraph, used when a file documents no description."""
    for para in body.split("\n\n"):
        para = para.strip()
        if para and not para.startswith(("#", ">", "|", "---", "<!--")):
            return one_line(re.sub(r"[*`\[\]]", "", para))
    return ""


def marker_note(origin):
    return (f"\n\n<!-- {MARKER}. Source: {os.path.relpath(origin, SOURCE)}. "
            f"Remove with: bash adapters/pi-desktop/install.sh --uninstall -->\n")

def owns(path):
    """True when `path` is absent, was written by this adapter, or --force is set.

    ~/.agents/skills also holds skills the user wrote by hand, so replacing an
    unmarked file is opt-in rather than the default.
    """
    if FORCE:
        return True
    if not os.path.exists(path):
        return True
    target = path if os.path.isfile(path) else os.path.join(path, "SKILL.md")
    try:
        with open(target, encoding="utf-8", errors="replace") as fh:
            return MARKER in fh.read()
    except OSError:
        return False


# --------------------------------------------------------------- collection
def skill_sources():
    """(skill id, directory, origin SKILL.md) for everything this run installs."""
    found = []
    for entry in sorted(os.listdir(SOURCE)):
        base = os.path.join(SOURCE, entry)
        if entry == "skills" and os.path.isdir(base):
            for name in sorted(os.listdir(base)):
                p = os.path.join(base, name, "SKILL.md")
                if os.path.isfile(p):
                    found.append((name, os.path.join(base, name), p))
        elif entry == "systems" and os.path.isdir(base):
            for bundle in sorted(os.listdir(base)):
                # Bundles are opt-in: without --systems the core install only.
                if bundle not in SYSTEMS:
                    continue
                skills = os.path.join(base, bundle, "skills")
                if not os.path.isdir(skills):
                    continue
                for name in sorted(os.listdir(skills)):
                    p = os.path.join(skills, name, "SKILL.md")
                    if os.path.isfile(p):
                        found.append((name, os.path.join(skills, name), p))

    # workflows are procedural instructions, so they ship as skills
    wf = os.path.join(SOURCE, "workflows")
    if os.path.isdir(wf):
        for name in sorted(os.listdir(wf)):
            if name.endswith(".md"):
                stem = name[:-3]
                found.append((f"coco-workflow-{stem}", None, os.path.join(wf, name)))

    # a bundle skill may share a name with a top-level skill; keep both, prefixed
    seen = Counter(i for i, _, _ in found)
    out = []
    for sid, directory, origin in found:
        if seen[sid] > 1:
            rel = os.path.relpath(origin, SOURCE).split(os.sep)
            sid = f"{rel[1] if rel[0] == 'systems' else 'coco'}-{sid}"
        out.append((sid, directory, origin))
    return out


def agent_sources():
    out = []
    for parent in ("agents", os.path.join("systems")):
        base = os.path.join(SOURCE, parent)
        if not os.path.isdir(base):
            continue
        if parent == "agents":
            cands = [os.path.join(base, f) for f in sorted(os.listdir(base))]
        else:
            cands = []
            for bundle in sorted(os.listdir(base)):
                if bundle not in SYSTEMS:
                    continue
                adir = os.path.join(base, bundle, "agents")
                if os.path.isdir(adir):
                    cands += [os.path.join(adir, f) for f in sorted(os.listdir(adir))]
        for path in cands:
            if not path.endswith(".md") or not os.path.isfile(path):
                continue
            stem = os.path.basename(path)[:-3]
            if stem in ("README", "INDEX", "PROMPT-DEFENSE", "_index"):
                continue
            out.append((stem, path))
    return out


def command_sources():
    base = os.path.join(SOURCE, "commands")
    out = []
    if not os.path.isdir(base):
        return out
    for ns in sorted(os.listdir(base)):
        nsdir = os.path.join(base, ns)
        if not os.path.isdir(nsdir):
            continue
        for fn in sorted(os.listdir(nsdir)):
            if not fn.endswith(".md") or fn == "INDEX.md":
                continue
            stem = fn[:-3]
            slash = ns if stem == "_index" else f"{ns}-{stem}"
            out.append((slash, os.path.join(nsdir, fn)))
    return out


# ------------------------------------------------------------------ install
def install_skills():
    for sid, directory, origin in skill_sources():
        dest = os.path.join(SKILL_DIR, sid)
        if not owns(dest):
            skipped.append(dest)
            continue
        fm, body = parse_frontmatter(open(origin, encoding="utf-8", errors="replace").read())
        fields = {"name": one_line(fm.get("name") or sid)}
        desc = one_line(fm.get("description") or "") or prose_fallback(body)
        if desc:
            fields["description"] = clip(desc)
        for key in ("domain", "license", "version"):
            if fm.get(key):
                fields[key] = fm[key]
        if DRY:
            say(f"DRY: skill  {sid:<44} {len(body.splitlines()):>5} lines")
            continue
        os.makedirs(SKILL_DIR, exist_ok=True)
        if directory and os.path.isdir(directory):
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            shutil.copytree(directory, dest, ignore=shutil.ignore_patterns(*SKIP_DIRS))
        else:
            os.makedirs(dest, exist_ok=True)
        with open(os.path.join(dest, "SKILL.md"), "w", encoding="utf-8") as fh:
            fh.write(front_matter(fields) + "\n" + body.lstrip("\n") + marker_note(origin))
        written.append(dest)


def install_agents():
    for stem, origin in agent_sources():
        name = stem if stem.startswith("coco-") else f"coco-{stem}"
        name = name[:40]
        dest = os.path.join(SUBAGENT_DIR, f"{name}.md")
        if not owns(dest):
            skipped.append(dest)
            continue
        fm, body = parse_frontmatter(open(origin, encoding="utf-8", errors="replace").read())
        desc = one_line(fm.get("description") or "") or prose_fallback(body)
        if not desc:
            skipped.append(origin)
            continue
        base = name[5:] if name.startswith("coco-") else name
        fields = {
            "name": name,
            "description": clip(desc),
            "tools": WRITE_TOOLS if base in WRITER_NAMES else READ_TOOLS,
            "maxTurns": MAX_TURNS,
        }
        if DRY:
            say(f"DRY: agent  {name:<44} tools={len(fields['tools'])}")
            continue
        os.makedirs(SUBAGENT_DIR, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(front_matter(fields) + "\n" + body.lstrip("\n") + marker_note(origin))
        written.append(dest)


def install_commands():
    for slash, origin in command_sources():
        dest = os.path.join(PROMPT_DIR, f"{slash}.md")
        if not owns(dest):
            skipped.append(dest)
            continue
        text = open(origin, encoding="utf-8", errors="replace").read()
        fm, body = parse_frontmatter(text)
        desc = one_line(fm.get("description") or "") or prose_fallback(body)
        fields = {}
        if desc:
            fields["description"] = clip(desc)
        if fm.get("argument-hint"):
            fields["argument-hint"] = fm["argument-hint"]
        if DRY:
            say(f"DRY: slash  /{slash:<43} {len(body.splitlines()):>5} lines")
            continue
        os.makedirs(PROMPT_DIR, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(front_matter(fields) + "\n" + body.lstrip("\n") + marker_note(origin))
        written.append(dest)


def uninstall():
    roots = [(SKILL_DIR, True), (SUBAGENT_DIR, False), (PROMPT_DIR, False)]
    for root, is_dir in roots:
        if not os.path.isdir(root):
            continue
        for entry in sorted(os.listdir(root)):
            path = os.path.join(root, entry)
            if is_dir and os.path.isdir(path):
                head = os.path.join(path, "SKILL.md")
            elif not is_dir and entry.endswith(".md"):
                head = path
            else:
                continue
            if not owns(head) or not os.path.exists(head):
                continue
            if DRY:
                say(f"DRY: remove {path}")
                continue
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
            removed.append(path)


if UNINSTALL:
    uninstall()
    say("")
    say(f"{'Would remove' if DRY else 'Removed'}: {len(removed)} entries")
    for p in removed[:5]:
        say("  " + p)
    if len(removed) > 5:
        say(f"  … and {len(removed) - 5} more")
    sys.exit(0)

say("Coco · PI-Desktop adapter")
say(f"Source: {SOURCE}")
say(f"Slash commands -> {PROMPT_DIR}")
say(f"Skills         -> {SKILL_DIR}")
say(f"Subagents      -> {SUBAGENT_DIR}")
if SYSTEMS:
    say(f"Bundles        -> {', '.join(SYSTEMS)}")
say("")

install_commands()
install_skills()
install_agents()

say("")
if DRY:
    say(f"Would write {len(written)} files.")
else:
    say(f"Installed {len(written)} files.")
if skipped:
    verb = "Would leave" if DRY else "Left"
    say(f"{verb} {len(skipped)} existing path(s) untouched — not written by this adapter:")
    for p in skipped[:5]:
        say("  " + p)
    if len(skipped) > 5:
        say(f"  … and {len(skipped) - 5} more")
    if not FORCE:
        say("Re-run with --force to replace them.")
if DRY:
    say("Dry run — nothing written.")
say("Restart PI-Desktop (or open a new session) to pick the new commands and skills up.")
PY
