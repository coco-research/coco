"""Grader for brainstorming. Deterministic: no model calls, no network.

Each item tests one behaviour the SKILL.md asks for. The item names it in "check" and
quotes the SKILL.md line it comes from in "rule".

    score = 0.75 * signals * 0.5 ** avoided + 0.25 * terms

signals  Fraction of the check's signals found in the reply. A signal is a regex, or
         ("count", A, n): at least n different matches of A, ignoring case.
avoided  Number of the check's avoid patterns (code before a design, extra questions)
         found in the reply; each halves the signals.
terms    Fraction of the item's case terms the reply repeats, so the reply has to be
         about this idea and not a generic lecture.

Only the first 200,000 characters of a reply are read.
"""
import re

W_SIGNALS, W_TERMS = 0.75, 0.25
MAX_CHARS = 200_000  # bounds the work a runaway reply can cause


def _rx(pattern):
    return re.compile(pattern, re.I | re.M)


CODE_FENCE = ("writes code before a design is approved", _rx(r"^[ \t]*```"))

CHECKS = {
    "design-before-code": {
        "need": [
            ("talks about a design first", _rx(r"\bdesign\b")),
            ("asks for approval before building", _rx(r"\b(?:approv\w*|sign[- ]off|agree\w*|confirm\w*)\b")),
            ("asks a question", _rx(r"\?")),
        ],
        "avoid": [CODE_FENCE],
    },
    "one-question": {
        "need": [("asks a question", _rx(r"\?"))],
        "avoid": [
            ("asks two or more questions", _rx(r"\?[^?]*\?")),
            ("asks three or more questions", _rx(r"\?[^?]*\?[^?]*\?")),
        ],
    },
    "propose-approaches": {"need": [
        ("names at least two approaches", ("count", _rx(r"\b(?:approach|option) (?:[1-3abc]|one|two|three)\b"), 2)),
        ("gives trade-offs", _rx(r"\btrade-?offs?\b|\bpros?\b|\bcons?\b|\bdownsides?\b")),
        ("recommends one", _rx(r"\brecommend\w*")),
    ]},
    "decompose-scope": {"need": [
        ("splits it into sub-projects", _rx(r"\bsub-?projects?\b|\bdecompos\w*|\bbreak (?:it|this) (?:down|up|into)\b|\bsplit\b")),
        ("calls the pieces independent", _rx(r"\bindependent\b|\bseparate\b")),
        ("picks the first piece to design", _rx(r"\bfirst\b|\bstart with\b|\bbegin with\b")),
    ]},
    "sectioned-design": {"need": [
        ("covers at least three design areas", ("count", _rx(
            r"\b(?:architecture|components?|data flow|error handling|testing)\b"), 3)),
        ("asks whether it looks right so far", _rx(
            r"\b(?:look|sound)s? right\b|\bdoes (?:this|that) (?:look|work)\b|\bany changes\b"
            r"|\bbefore I (?:continue|go on|move on)\b")),
    ]},
    "spec-then-writing-plans": {
        "need": [
            ("writes the design down as a spec", _rx(r"docs/superpowers/specs/|\bspec\b|\bdesign doc\w*")),
            ("asks the user to review the spec", _rx(r"\breview\w*")),
            ("hands off to writing-plans", _rx(r"\bwriting-plans\b")),
        ],
        "avoid": [CODE_FENCE, ("invokes another implementation skill", _rx(r"\bfrontend-design\b|\bmcp-builder\b"))],
    },
}


def _met(spec, text):
    if isinstance(spec, tuple):
        _, rx, n = spec
        return len({m.group(0).lower() for m in rx.finditer(text)}) >= n
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
