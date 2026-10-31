#!/usr/bin/env bash
# Journey: after a plain Claude Code install, every generated SI command is
# usable as written. A leftover {{template}} is a failure. $ARGUMENTS is
# Claude Code's own expansion and is allowed. Every concrete path the command
# cites (absolute, ~/ expanded against this install's HOME, or a path under
# this clone) must exist. URLs are ignored, as are run-time slots such as
# <file> or [name].
#
# Run from anywhere: bash tests/check-si-commands-resolve.sh
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
home=$(mktemp -d)
work=$(mktemp -d)
trap 'rm -rf "$home" "$work"' EXIT

cd "$root"
install_log="$work/install.log"
if ! HOME="$home" bash install.sh --adapter claude-code </dev/null >"$install_log" 2>&1; then
  echo "checked 0 command files, 0 distinct paths"
  echo "FAIL"
  echo "install.sh: exited non-zero"
  tail -n 40 "$install_log" >&2
  exit 1
fi

report=$(python3 - "$home" "$root" <<'PY'
import os, re, sys

home = sys.argv[1]
clone = os.path.realpath(sys.argv[2])
cmd_dir = os.path.join(home, ".claude", "commands")

placeholder_re = re.compile(r"\{\{[^{}]*\}\}")
# ~/.coco/disabled is a kill-switch the commands only test for existence; a normal install must not create it.
sentinels = {"~/.coco/disabled"}
url_re = re.compile(r"https?://[^\s`\"')>]+")
tilde_re = re.compile(r"~/(?:[A-Za-z0-9._+-]+/)*[A-Za-z0-9._+-]+")
abs_re = re.compile(r"(?<![A-Za-z0-9._+~-])(/(?:[A-Za-z0-9._+-]+/)+[A-Za-z0-9._+-]+)")
rel_re = re.compile(
    r"(?<![A-Za-z0-9._+/-])((?:[A-Za-z0-9._+-]+/)+[A-Za-z0-9._+-]+\.[A-Za-z0-9]+)"
)
path_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._+-/")
runtime_chars = set("<>[]")


def covered(start, end, spans):
    for a, b in spans:
        if start < b and end > a:
            return True
    return False


def trim(text):
    return text.rstrip(".,;:)\"'`")


def is_sentinel(cited):
    if cited in sentinels:
        return True
    # The absolute-path rule cites the slash after the tilde as its own path.
    return cited.startswith("/") and ("~" + cited) in sentinels


def runtime(text):
    return any(ch in text for ch in runtime_chars)


def resolve(cited):
    if cited.startswith("~/"):
        return os.path.normpath(os.path.join(home, cited[2:]))
    if cited.startswith("/"):
        return os.path.normpath(cited)
    return os.path.normpath(os.path.join(clone, cited))


def scan(text):
    """Return (events, consumed spans). events are (index, 'ph'|'path', cited)."""
    urls = [(m.start(), m.end()) for m in url_re.finditer(text)]
    events = []
    consumed = []

    for m in placeholder_re.finditer(text):
        events.append((m.start(), "ph", m.group(0)))

    start = 0
    while True:
        i = text.find(clone, start)
        if i < 0:
            break
        j = i + len(clone)
        if covered(i, j, urls) or (j < len(text) and text[j] != "/"):
            start = i + 1
            continue
        k = j
        while k < len(text) and text[k] in path_chars:
            k += 1
        cited = trim(text[i:k])
        nxt = text[k] if k < len(text) else ""
        consumed.append((i, k))
        if not runtime(cited) and nxt not in "<[":
            events.append((i, "path", cited))
        start = k if k > i else i + 1

    def skip(m):
        cited = trim(m.group(1))
        span = (m.start(1), m.end(1))
        if not cited or runtime(cited) or runtime(m.group(1)):
            return None
        if covered(span[0], span[1], urls) or covered(span[0], span[1], consumed):
            return None
        if clone.startswith(cited) or cited.startswith(clone + "/") or cited == clone:
            return None
        return (m.start(1), cited)

    for m in abs_re.finditer(text):
        hit = skip(m)
        if hit:
            events.append((hit[0], "path", hit[1]))

    for m in tilde_re.finditer(text):
        cited = trim(m.group(0))
        if not cited or runtime(cited) or runtime(m.group(0)):
            continue
        if covered(m.start(), m.end(), urls):
            continue
        events.append((m.start(), "path", cited))

    for m in rel_re.finditer(text):
        hit = skip(m)
        if not hit:
            continue
        cited = hit[1]
        first = cited.split("/", 1)[0]
        if not os.path.exists(os.path.join(clone, first)):
            continue
        events.append((hit[0], "path", cited))

    events.sort(key=lambda item: (item[0], 0 if item[1] == "ph" else 1))
    return events


names = []
if os.path.isdir(cmd_dir):
    names = sorted(
        name for name in os.listdir(cmd_dir)
        if name.startswith("SI") and name.endswith(".md")
        and os.path.isfile(os.path.join(cmd_dir, name))
    )

paths = set()
bads = []
for name in names:
    with open(os.path.join(cmd_dir, name), encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    first = None
    for _index, kind, cited in scan(text):
        if kind == "path":
            if is_sentinel(cited):
                continue
            paths.add(resolve(cited))
            if first is None and not os.path.exists(resolve(cited)):
                first = cited
        elif first is None:
            first = cited
    if first is not None:
        bads.append("%s: %s" % (name, first))

if not names:
    bads.append("install: no SI*.md commands in ~/.claude/commands")

print("FILES %d" % len(names))
print("PATHS %d" % len(paths))
for line in bads:
    print("BAD " + line)
PY
)

nfiles=$(printf '%s\n' "$report" | sed -n 's/^FILES //p')
npaths=$(printf '%s\n' "$report" | sed -n 's/^PATHS //p')
if [[ -z "$nfiles" || -z "$npaths" ]]; then
  echo "checked 0 command files, 0 distinct paths"
  echo "FAIL"
  echo "checker: produced no summary"
  printf '%s\n' "$report" >&2
  exit 1
fi

file_word="files"
[[ "$nfiles" -eq 1 ]] && file_word="file"
path_word="paths"
[[ "$npaths" -eq 1 ]] && path_word="path"
echo "checked $nfiles command $file_word, $npaths distinct $path_word"

bads=$(printf '%s\n' "$report" | sed -n 's/^BAD //p')
if [[ -n "$bads" ]]; then
  echo "FAIL"
  printf '%s\n' "$bads"
  exit 1
fi
echo "PASS"
