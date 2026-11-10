"""Grader for writing-skills. Deterministic: no model calls, no network.

Each item tests one behaviour the SKILL.md asks for. The item names it in "check" and
quotes the SKILL.md line it comes from in "rule".

    score = 0.75 * signals * 0.5 ** avoided + 0.25 * terms

signals  Fraction of the check's signals found in the reply. A signal is a regex, or
         ("words", lo, hi): the reply has from lo to hi words (split on whitespace).
avoided  Number of the check's avoid patterns (a workflow summary in the description, an
         @ link) found in the reply; each halves the signals.
terms    Fraction of the item's case terms the reply repeats, so the reply has to be about
         this skill and not a generic lecture.

Only the first 200,000 characters of a reply are read.
"""
import re

W_SIGNALS, W_TERMS = 0.75, 0.25
MAX_CHARS = 200_000  # bounds the work a runaway reply can cause


def _rx(pattern):
    return re.compile(pattern, re.I | re.M)


CHECKS = {
    "description-use-when": {
        "need": [
            ("frontmatter name uses letters, numbers and hyphens", _rx(r"^name:[ \t]*[a-z0-9-]+[ \t]*$")),
            ("description starts with 'Use when'", _rx(r"^description:[ \t]*[\"']?Use when\b")),
        ],
        "avoid": [("description is in the first person", _rx(r"^description:[^\n]*\b(?:I|my|we|our)\b"))],
    },
    "description-not-workflow": {
        "need": [
            ("rewrites it to start with 'Use when'", _rx(r"\bUse when\b")),
            ("says a description states when to use, not what it does", _rx(
                r"\bwhen to use\b|\bnot what\b|\btrigger\w*")),
        ],
        "avoid": [("the new description still lists steps", _rx(r"^description:[^\n]*\b(?:then|steps?)\b"))],
    },
    "baseline-test-first": {"need": [
        ("runs a baseline without the skill", _rx(r"\bbaseline\b|\bwithout the skill\b")),
        ("uses a pressure scenario", _rx(r"\bpressure\b|\bscenarios?\b")),
        ("watches the agent fail first", _rx(r"\bfail\w*")),
    ]},
    "verb-first-name": {"need": [
        ("suggests a hyphenated name with an -ing verb", _rx(
            r"\b[a-z]+ing(?:-[a-z0-9]+){1,6}\b|\b(?:[a-z0-9]+-){1,6}[a-z]+ing\b")),
        ("explains names say what you do", _rx(r"\bverb\w*|\bactive voice\b|\bwhat you do\b|\bgerund\w*")),
    ]},
    "word-budget": {"need": [
        ("stays between 40 and 199 words", ("words", 40, 199)),
        ("has an Overview or When to Use heading", _rx(r"^#{1,3}[ \t]+(?:overview|when to use)\b")),
    ]},
    "required-cross-reference": {
        "need": [("marks the other skill as REQUIRED", _rx(r"\bREQUIRED (?:SUB-SKILL|BACKGROUND)\b"))],
        "avoid": [
            ("uses an @ link that force-loads the file", _rx(r"@[\w./-]*(?:skills/|SKILL\.md)")),
            ("points at a file path instead of the skill name", _rx(r"\bskills/[\w-]+/")),
        ],
    },
}


def _met(spec, text):
    if isinstance(spec, tuple):
        _, lo, hi = spec
        return lo <= len(text.split()) <= hi
    return bool(spec.search(text))


def grade(item, output):
    text = (output if isinstance(output, str) else "")[:MAX_CHARS]
    check = CHECKS[item["check"]]
    missed = [label for label, spec in check["need"] if not _met(spec, text)]
    avoided = [label for label, rx in check.get("avoid", ()) if rx.search(text)]
    signals = 1 - len(missed) / len(check["need"])
    lowered = " ".join(text.lower().split())  # a term may wrap across lines
    absent = [t for t in item["terms"] if t.lower() not in lowered]
    terms = 1 - len(absent) / len(item["terms"])
    raw = W_SIGNALS * signals * 0.5 ** len(avoided) + W_TERMS * terms
    notes = ["missing: " + m for m in missed] + ["avoid: " + a for a in avoided]
    if absent:
        notes.append("case terms not mentioned: " + ", ".join(absent))
    return {"score": round(min(1.0, raw), 4), "notes": notes}
