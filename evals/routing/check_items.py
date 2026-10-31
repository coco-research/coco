#!/usr/bin/env python3
"""Reject description-split prompts that leak their own team name.

A positive prompt fails when it contains its team's key or any word of its
name: case-insensitive, whole words, plus plurals and hyphenated forms.
Also fails when a router team has fewer than 8 positives, or an id repeats.

    python3 evals/routing/check_items.py [ITEMS]
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "systems" / "superintelligence" / "scripts"))

import meta_select  # noqa: E402

_IRREGULAR_PLURAL = {"life": "lives"}


def plural(word):
    if word in _IRREGULAR_PLURAL:
        return _IRREGULAR_PLURAL[word]
    if len(word) > 1 and word.endswith("y") and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    return word + "s"


def forms(word):
    word = word.lower()
    return {word, plural(word)}


def team_names():
    """team_key -> team_name, same teams team_profiles() will route."""
    names = {}
    for key, t in meta_select.META["teams"].items():
        tdir = meta_select.ROOT / pathlib.Path(t["dir"]).name
        reg = tdir / "registry.json"
        if not reg.exists():
            continue
        record = json.loads(reg.read_text())
        names[key] = record.get("team_name", key)
    return names


def banned_words(key, name):
    banned = set()
    for word in re.findall(r"[a-z0-9]+", f"{key} {name}".lower()):
        banned |= forms(word)
    banned.add(key.lower())
    banned.add(key.lower().replace("-", ""))
    return banned


def prompt_tokens(prompt):
    text = (prompt or "").lower()
    found = set(re.findall(r"[a-z0-9]+", text))
    for compound in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)+", text):
        found.add(compound)
        found.add(compound.replace("-", ""))
    return found


def check(items):
    """Return failure strings. Empty means the file is clean."""
    names = team_names()
    bans = {key: banned_words(key, name) for key, name in names.items()}
    counts = {key: 0 for key in names}
    seen = {}
    failures = []
    for item in items:
        item_id = item.get("id", "?")
        if item_id in seen:
            failures.append(f"{item_id}: duplicate id")
        seen[item_id] = True
        if item.get("kind") != "positive":
            continue
        label = item.get("label")
        if label in counts:
            counts[label] += 1
        if label not in bans:
            continue
        hit = prompt_tokens(item.get("prompt", "")) & bans[label]
        if hit:
            word = sorted(hit)[0]
            failures.append(f"{item_id}: positive prompt contains team word {word!r}")
    for key, n in counts.items():
        if n < 8:
            failures.append(f"{key}: fewer than 8 positive prompts ({n})")
    return failures


def main(argv):
    path = pathlib.Path(argv[1]) if len(argv) > 1 else (
        pathlib.Path(__file__).resolve().parent / "items-descriptions.jsonl")
    try:
        lines = path.read_text().splitlines()
    except OSError as e:
        print(f"{path}: {e}", file=sys.stderr)
        return 1
    items = []
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"{path}:{n}: {e}", file=sys.stderr)
            return 1
    failures = check(items)
    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
