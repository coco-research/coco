#!/usr/bin/env python3
"""Run one automatic improvement round on one agent skill. Stdlib only.

Pure core; the CLI lands in slice 3. This module checks a proposed SKILL.md edit,
composing several edits, and the dev and held-out decisions. The proposer, the
round driver, the peek ledger and the CLI come in follow-up changes. Constants
named here for those parts are limits the follow-up enforces, not yet checked.

Held-out decision: one-sided paired bootstrap, kept only when the delta is
positive and p is below ALPHA / MAX_TOTAL_PEEKS. A held-out set may be peeked
at most MAX_TOTAL_PEEKS times over its life, so the per-peek threshold is
Bonferroni-split across them and the life-time false-keep rate stays near ALPHA.
"""
import difflib
import hashlib
import pathlib
import re
import sys

import run, score

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evals"))
import paired

DEV_MARGIN, MIN_WINS, WIN_EPS = 0.05, 2, 0.01
MAX_CHANGED_LINES, MAX_GROWTH_BYTES = 30, 4000
ALPHA, N_BOOT, BOOT_SEED = 0.05, 10000, 0
MAX_TOTAL_PEEKS = 5  # life-time peeks per held-out set (enforced by the round driver)
PEEK_ALPHA = ALPHA / MAX_TOTAL_PEEKS  # Bonferroni split across those peeks


class Reject(Exception):
    """A proposal that must not be scored. str(e) is the reason."""


def die(msg, code=2):
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def frontmatter(text):
    m = re.match(r"---\n.*?\n---\n", text, re.S)
    return m.group(0) if m else ""


def strip_outer_fence(text):
    lines = text.strip("\n").split("\n")
    m = re.match(r"(`{3,}|~{3,})[\w+.-]*\s*$", lines[0])
    if m and len(lines) > 2:
        ends = [i for i, l in enumerate(lines) if i > 0 and l.strip() == m.group(1)]
        if ends:
            return "\n".join(lines[1:ends[-1]]) + "\n"
    return text.strip("\n") + "\n"


_DIFF_START = re.compile(
    r"(?:diff --git [^\n]*\n)?(?:index [^\n]*\n)?--- [^\n]+\n\+\+\+ [^\n]+\n@@ ")
_HUNK = re.compile(r"@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")


def apply_diff(base_lines, diff_text, skill):
    allowed = {"SKILL.md", "skills/%s/SKILL.md" % skill}
    lines = diff_text.rstrip("\n").split("\n")
    hunks, cur, k = [], None, 0          # hunk = [declared_start, old_lines, new_lines]
    while k < len(lines):
        line = lines[k]
        if line.startswith("--- ") and k + 1 < len(lines) and lines[k + 1].startswith("+++ "):
            for hdr in (line[4:], lines[k + 1][4:]):
                name = hdr.split("\t")[0].strip()
                if name == "/dev/null":
                    raise Reject("diff creates, deletes or renames a file")
                if name[:2] in ("a/", "b/"):
                    name = name[2:]
                if name not in allowed:
                    raise Reject("diff touches another file: " + name)
            cur = None
            k += 2
            continue
        m = _HUNK.match(line)
        if m:
            cur = [int(m.group(1)), [], []]
            hunks.append(cur)
        elif cur is not None and (line == "" or line[:1] in (" ", "-", "+")):
            tag, text = (line[:1], line[1:]) if line else (" ", "")
            if tag != "+":
                cur[1].append(text)
            if tag != "-":
                cur[2].append(text)
        elif line.startswith(("new file", "deleted file", "rename ", "Binary")):
            raise Reject("diff creates, deletes or renames a file")
        elif line.startswith("\\") or line.startswith(("diff --git", "index ", "similarity")):
            pass
        elif cur is None:
            pass                          # prose before the first hunk
        else:
            raise Reject("unexpected line in diff")
        k += 1
    if not hunks:
        raise Reject("diff has no hunks")
    out, pos = [], 0
    for n, (start, old, new) in enumerate(hunks, 1):
        if not old or old == new:
            raise Reject("hunk %d has no context or no change" % n)
        hits = [p for p in range(len(base_lines) - len(old) + 1)
                if base_lines[p:p + len(old)] == old]
        if not hits:
            raise Reject("hunk %d does not match SKILL.md" % n)
        hits.sort(key=lambda p: abs(p - (start - 1)))
        if len(hits) > 1 and abs(hits[0] - (start - 1)) == abs(hits[1] - (start - 1)):
            raise Reject("hunk %d is ambiguous" % n)
        if hits[0] < pos:
            raise Reject("hunks overlap or are out of order")
        out.extend(base_lines[pos:hits[0]])
        out.extend(new)
        pos = hits[0] + len(old)
    out.extend(base_lines[pos:])
    return out


def edit_script(base_lines, new_lines):
    sm = difflib.SequenceMatcher(None, base_lines, new_lines, autojunk=False)
    return [(i1, i2, tuple(new_lines[j1:j2]))
            for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]


def n_changed(edits):
    return sum((i2 - i1) + len(new) for i1, i2, new in edits)


def conflict(e, f):
    return e != f and e[0] <= f[1] and f[0] <= e[1]


def apply_edits(base_lines, edits):
    out, pos = [], 0
    for i1, i2, new in sorted(set(edits)):
        out.extend(base_lines[pos:i1])
        out.extend(new)
        pos = i2
    out.extend(base_lines[pos:])
    return out


def compose(base_lines, ranked, cap):
    """ranked: [(proposal_id, edits)] best first. Returns (lines, used_ids, dropped)."""
    kept, dropped, union = [], [], set()
    for pid, edits in ranked:
        clash = next((q for q, qe in kept
                      if any(conflict(e, f) for e in edits for f in qe)), None)
        if clash:
            dropped.append({"id": pid, "why": "conflicts with " + clash})
        elif n_changed(union | set(edits)) > cap:
            dropped.append({"id": pid, "why": "over the composed cap"})
        else:
            kept.append((pid, edits))
            union |= set(edits)
    return apply_edits(base_lines, union), [q for q, _ in kept], dropped


def dev_verdict(base, cand, margin, min_wins):
    ids = sorted(base)
    d = [cand[i] - base[i] for i in ids]
    wins = sum(1 for x in d if x >= WIN_EPS)
    losses = sum(1 for x in d if x <= -WIN_EPS)
    gain = sum(d) / len(d)
    return {"mean": sum(cand[i] for i in ids) / len(ids), "gain": gain,
            "wins": wins, "losses": losses,
            "pass": gain >= margin and wins >= min_wins and wins > losses}


def peek_stats(base, cand, alpha=PEEK_ALPHA):
    delta, lo, hi = paired.paired_bootstrap(base, cand, N_BOOT, BOOT_SEED)
    p = paired.boot_p_greater([c - b for b, c in zip(base, cand)], N_BOOT, BOOT_SEED)
    return {"n": len(base), "base_mean": sum(base) / len(base), "cand_mean": sum(cand) / len(cand),
            "delta": delta, "ci95": [lo, hi], "p_one_sided": p, "alpha": alpha,
            "pass": delta > 0 and p < alpha}


def parse_proposal(raw, base, skill, max_changed=MAX_CHANGED_LINES):
    text = raw.replace("\r\n", "\n").strip("\n")
    if not text.strip():
        raise Reject("empty reply")
    body = strip_outer_fence(text)
    if _DIFF_START.match(body):
        new = "\n".join(apply_diff(base.split("\n"), body, skill))
    else:
        new = body
    new = new.rstrip("\n") + "\n"
    if "\x00" in new:
        raise Reject("NUL byte")
    edits = edit_script(base.split("\n"), new.split("\n"))
    if not edits:
        return base, []
    if frontmatter(new) != frontmatter(base):
        raise Reject("front matter changed")
    if n_changed(edits) > max_changed:
        raise Reject("too many changed lines: %d > %d" % (n_changed(edits), max_changed))
    if len(new.encode()) - len(base.encode()) > MAX_GROWTH_BYTES:
        raise Reject("too large: grows by more than %d bytes" % MAX_GROWTH_BYTES)
    return new, edits


def others_check(changed, skill):
    own = "skills/%s/SKILL.md" % skill
    shared = sorted(p for p in changed if p != own)
    if not shared:
        return {"status": "skipped", "reason": "only " + own + " changed"}
    return {"status": "failed", "reason": "shared files changed: " + ", ".join(shared)}
