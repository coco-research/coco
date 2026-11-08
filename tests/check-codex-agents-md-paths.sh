#!/usr/bin/env bash
# Issues #261 and #262. The codex adapter (generic execs it) must not tell the
# agent to read a file this install does not create and the checkout does not have.
# It also checks that agents/PROMPT-DEFENSE.md is not listed as an agent.
# Run from anywhere: bash tests/check-codex-agents-md-paths.sh
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/proj" "$tmp/home"
if ! (cd "$tmp/proj" && env -u CLAUDE_HOME -u CURSOR_HOME -u COCO_HOME -u XDG_CONFIG_HOME \
    HOME="$tmp/home" bash "$ROOT/adapters/codex/install.sh" >"$tmp/log" 2>&1); then
  echo "FAIL: codex install exited non-zero" >&2
  cat "$tmp/log" >&2
  exit 1
fi

python3 - "$tmp/proj/AGENTS.md" "$tmp/home" "$tmp/proj" <<'PY'
import os, re, sys
agents, home, project = sys.argv[1:]
text = open(agents).read()
missing = []

def skip(p):
    # Patterns, not files: <command>, globs, {placeholders}.
    return any(c in p for c in "<>{}*")

def is_file_path(p):
    if not p or skip(p) or p.startswith("path/to/"):
        return False
    base = os.path.basename(p.rstrip("/"))
    ext = "." in base
    if p.startswith(("~/", "./", "../")):
        return ext or p.endswith("/")
    if p.startswith("/") and (ext or p.endswith("/")):
        return True
    if re.match(r"(skills|commands|rules|templates|systems|adapters)/", p):
        return ext or p.endswith("/")
    return False

found = []

def add(p):
    p = p.strip().strip('"').strip("'").rstrip(".,;:")
    if is_file_path(p):
        found.append(p)

for m in re.finditer(r"`([^`\n]*)`", text):
    inner = m.group(1).strip()
    if (
        " " in inner
        and re.match(r"^(?:~/|\./|\.\./|/)", inner)
        and (re.search(r"\.[A-Za-z0-9]+$", inner) or inner.endswith("/"))
    ):
        add(inner)
        continue
    if is_file_path(inner):
        add(inner)
        continue
    cm = re.match(r"(?:bash|python3|python|sh)\s+(?:\"([^\"]+)\"|(\S+))", inner)
    if cm:
        add(cm.group(1) or cm.group(2))
        continue
    for tok in re.findall(
        r"(?:~/|\./|\.\./)[^\s\"']+|(?<![\w./~-])(?:skills|commands|rules|templates|systems|adapters)/[^\s\"']+",
        inner,
    ):
        add(tok)

nobt = re.sub(r"`[^`\n]*`", "", text)
for tok in re.findall(r"~/[^\s\"']+", nobt):
    add(tok)
for tok in re.findall(r"\"(/[^\"]+)\"", nobt):
    add(tok)

source = ""
sm = re.search(r"^Source: (.+)$", text, re.M)
if sm:
    source = sm.group(1).strip()
    if not os.path.isdir(source):
        missing.append("Source: " + source)

def resolve(p):
    if p.startswith("~/"):
        return os.path.join(home, p[2:])
    if p.startswith("/"):
        return p
    for base in (project, source):
        cand = os.path.join(base, p)
        if base and os.path.exists(cand):
            return cand
    return os.path.join(source or project, p)

seen = set()
for p in found:
    if p in seen:
        continue
    seen.add(p)
    if not os.path.exists(resolve(p)):
        missing.append(p)

if "team.md" in text:
    missing.append("team.md (no such router; the file is commands/team/_index.md)")

# PROMPT-DEFENSE.md is a shared prompt header the agents include, not an agent.
if re.search(r"^- \*\*PROMPT-DEFENSE\*\*", text, re.M):
    missing.append("PROMPT-DEFENSE listed as an agent (it is a shared prompt header)")

team_lines = [ln for ln in text.splitlines() if re.match(r"^- `/team(?::|`)", ln)]
if not any(re.match(r"^- `/team`(?: —| \()", ln) for ln in team_lines):
    missing.append("/team router entry")
for ln in team_lines:
    files = [p for p in re.findall(r"`([^`]+)`", ln) if p.endswith(".md") and p.startswith("/")]
    if not any(os.path.isfile(p) for p in files):
        missing.append("team entry with no shipped file: " + ln)

if missing:
    print("FAIL %d path(s) referenced from AGENTS.md do not exist:" % len(missing), file=sys.stderr)
    for p in missing:
        print("  " + p, file=sys.stderr)
    sys.exit(1)
print("ok %d paths exist" % len(seen))
PY
