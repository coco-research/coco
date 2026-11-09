#!/usr/bin/env python3
"""Offline checker for Super Intelligence persona files (stdlib only, no network).

Usage:
  python3 scripts/check-personas.py <persona.md> [<persona.md> ...]

Prints one line per problem, "<file>: (<rule>) <name>: <detail>", and exits 1
if there is any problem, 0 if every file passes.

Rules (taken from the existing validate_persona.py / validate_offline.py copies,
templates/attribution.md and the real persona files):
  (a) frontmatter   parses, and has every field all shipped personas carry, non-empty
  (b) sources       at least 3 sources, each an https:// URL
  (c) label         a file that speaks in the person's voice (a `> "..."` block)
                    carries the approved label line from templates/attribution.md
  (d) roster        the slug is listed in its department's registry.json / roster.json
  (e) quote         every `> "..."` line has an https:// URL or [paraphrase] on the
                    same or the next line
  (f) stances       every public_stances entry has an evidence_url
  (g) signals       active: >= 2 recent_signal_12mo; archetype: >= 2 persistent_signals
  (h) pairs         pairs_well_with / productive_conflict_with name slugs listed in
                    some department's roster

The live URL check in validate_persona.py needs the network, so it is not here.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTRIBUTION = ROOT / "systems" / "superintelligence" / "templates" / "attribution.md"

# The fields every one of the 495 shipped personas has, non-empty.
REQUIRED = ["slug", "real_name", "archetype", "teams", "cell", "cell_role", "status",
            "domains", "signature_moves", "canonical_works", "public_stances",
            "voice_style", "confidence", "sources"]

KEY = re.compile(r"^([A-Za-z0-9_]+):(?:\s+(.*))?$")
SUBKEY = re.compile(r"^\s*([A-Za-z0-9_]+):(?:\s+(.*))?$")
QUOTE = re.compile(r'^\s*>\s*["“]')
SOURCED = re.compile(r"https://|\[paraphrase\]")


def scalar(s: str):
    s = s.strip()
    if s[:1] in "'\"" and s[-1:] == s[:1] and len(s) > 1:
        return s[1:-1]
    s = re.sub(r"\s+#.*$", "", s)
    return None if s in ("", "~", "null") else s


def flow_list(s: str) -> list:
    items = re.findall(r"'[^']*'|\"[^\"]*\"|[^,\[\]]+", s.strip()[1:-1])
    return [v for v in (scalar(i) for i in items) if v]


def parse_frontmatter(text: str):
    """Top-level keys of a persona frontmatter: scalars, lists of scalars, lists of maps.

    ponytail: covers the YAML shapes the persona files use, not full YAML.
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    lines = text[4:end].split("\n")
    fm: dict = {}
    i = 0
    while i < len(lines):
        m = KEY.match(lines[i])
        i += 1
        if not m:
            continue
        key, rest = m.group(1), (m.group(2) or "").strip()
        block = []
        while i < len(lines) and (lines[i][:1] in (" ", "-") or not lines[i].strip()):
            block.append(lines[i])
            i += 1
        if rest.startswith("["):
            fm[key] = flow_list(rest[:rest.rfind("]") + 1])  # drop a trailing comment
        elif rest.startswith("{"):
            fm[key] = {} if rest.replace(" ", "") == "{}" else {"_": rest}
        elif rest and rest[0] not in "|>#":
            fm[key] = scalar(rest)
        elif rest[:1] in ("|", ">"):
            fm[key] = "\n".join(block).strip() or None
        else:
            fm[key] = block_value(block)
    return fm


def block_value(block: list):
    rows = [b for b in block if b.strip() and not b.strip().startswith("#")]
    if not rows:
        return None
    if not rows[0].lstrip().startswith("- "):
        return {"_": rows[0].strip()}  # a nested mapping: non-empty is all we need
    dash = len(rows[0]) - len(rows[0].lstrip())
    items: list = []
    for r in rows:
        ind = len(r) - len(r.lstrip())
        if ind == dash and r.lstrip().startswith("- "):
            body = r.lstrip()[2:]
            m = SUBKEY.match(body)
            items.append({m.group(1): scalar(m.group(2) or "")} if m and not body.startswith(("'", '"', "http")) else scalar(body))
        elif ind == dash + 2 and isinstance(items[-1], dict):
            m = SUBKEY.match(r)
            if m:
                items[-1][m.group(1)] = scalar(m.group(2) or "")
    return items


def roster_slugs(dept: Path, cache: dict):
    if dept not in cache:
        slugs, found = set(), False
        for name in ("registry.json", "roster.json"):
            p = dept / name
            if p.is_file():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue  # unreadable: counts as no roster, reported as (d)
                found = True
                people = data.get("personas") if isinstance(data, dict) else None
                if isinstance(people, (dict, list)):  # {slug: {...}} or [slug | {slug}]
                    slugs |= {s for s in people if isinstance(s, str)}
                stack = [data]
                while stack:
                    o = stack.pop()
                    if isinstance(o, dict):
                        if isinstance(o.get("slug"), str):
                            slugs.add(o["slug"])
                        stack.extend(o.values())
                    elif isinstance(o, list):
                        stack.extend(o)
        cache[dept] = slugs if found else None
    return cache[dept]


def label_template() -> str:
    try:
        m = re.search(r"\*\*<Name> persona\*\*: [^\n]*", ATTRIBUTION.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as e:
        m, why = None, f"cannot read: {e}"
    else:
        why = "approved label line not found"
    if not m:
        print(f"{ATTRIBUTION}: {why}", file=sys.stderr)
        sys.exit(2)  # setup error, distinct from exit 1 (files failed)
    return m.group(0).strip()


def check(path: Path, label: str, cache: dict) -> list:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [f"(a) frontmatter: cannot read file: {e}"]
    fm = parse_frontmatter(text)
    if fm is None:
        return ["(a) frontmatter: no '---' frontmatter block at the top"]
    out = []
    missing = [k for k in REQUIRED if not fm.get(k)]
    if missing:
        out.append(f"(a) frontmatter: missing or empty fields: {', '.join(missing)}")

    src = fm.get("sources") if isinstance(fm.get("sources"), list) else []
    if len(src) < 3:
        out.append(f"(b) sources: {len(src)} source URLs, need at least 3")
    bad = [s for s in src if not (isinstance(s, str) and s.startswith("https://"))]
    if bad:
        out.append(f"(b) sources: not https://: {', '.join(map(str, bad[:3]))}")

    body = text.split("\n")
    quotes = [n for n, line in enumerate(body) if QUOTE.match(line)]
    name = fm.get("real_name") or "<Name>"
    named = label.replace("<Name>", str(name))
    if quotes and named not in text:
        out.append(f"(c) label: speaks as {name} (line {quotes[0] + 1}) but lacks the label line: {named}")

    slugs = roster_slugs(path.resolve().parent.parent, cache) if path.resolve().parent.name == "personas" else None
    slug = fm.get("slug")
    if slugs is None:
        out.append("(d) roster: no readable registry.json or roster.json beside this personas/ folder")
    elif slug not in slugs:
        out.append(f"(d) roster: slug '{slug}' is not listed in its department's registry/roster")

    for n in quotes:
        if not SOURCED.search(" ".join(body[n:n + 2])):
            out.append(f"(e) quote: line {n + 1} has no https:// source or [paraphrase] on it or the next line")

    stances = fm.get("public_stances") if isinstance(fm.get("public_stances"), list) else []
    uncited = [str(i) for i, s in enumerate(stances) if isinstance(s, dict) and not s.get("evidence_url")]
    if uncited:
        out.append(f"(f) stances: public_stances without evidence_url at index {', '.join(uncited)}")

    field = "persistent_signals" if fm.get("status") == "archetype" else "recent_signal_12mo"
    sig = fm.get(field) if isinstance(fm.get(field), list) else []
    if len(sig) < 2:
        out.append(f"(g) signals: {field} has {len(sig)}, need at least 2")

    if slugs is not None:
        # Pairs may cross departments (the meta-orchestrator convenes across teams).
        pool = set().union(*(roster_slugs(d, cache) or set() for d in path.resolve().parent.parent.parent.iterdir() if d.is_dir()))
        for fld in ("pairs_well_with", "productive_conflict_with"):
            vals = fm.get(fld) if isinstance(fm.get(fld), list) else []
            off = [v for v in vals if isinstance(v, str) and v not in pool]
            if off:
                out.append(f"(h) pairs: {fld} names slugs not in any department roster: {', '.join(off)}")
    return out


def main(argv: list) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    label, cache, fails = label_template(), {}, 0
    for f in argv:
        problems = check(Path(f), label, cache)
        fails += bool(problems)
        for p in problems:
            print(f"{f}: {p}")
    print(f"check-personas: {len(argv) - fails}/{len(argv)} pass", file=sys.stderr)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
