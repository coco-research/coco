"""Grader for test-driven-development. Deterministic: no model calls, no network.

Each item tests one behaviour the SKILL.md asks for. The item names it in "check" and
quotes the SKILL.md line it comes from in "rule".

    score = 0.75 * signals * 0.5 ** avoided + 0.25 * terms

signals  Fraction of the check's signals found in the reply. A signal is a regex, or
         ("before", A, B): A is found and B is absent or comes later, or
         ("count", A, n): at least n different matches of A.
avoided  Number of the check's avoid patterns found in the reply; each halves the signals.
terms    Fraction of the item's case terms (function names, values) the reply repeats, so
         the reply has to be about this case and not a generic lecture.

Only the first 200,000 characters of a reply are read.
"""
import re

W_SIGNALS, W_TERMS = 0.75, 0.25
MAX_CHARS = 200_000  # bounds the work a runaway reply can cause


def _rx(pattern):
    return re.compile(pattern, re.I | re.M)


TEST = _rx(r"\bdef test_\w+|\b(?:test|it)\(\s*['\"]")
IMPL = _rx(r"\bdef (?!test_)\w+\s*\(|\bfunction (?!test)\w+\s*\(|\bclass (?!Test)\w+")
TEST_NAME = _rx(r"\bdef test_\w+|\b(?:test|it)\(\s*['\"][^'\"\n]{1,80}['\"]")

CHECKS = {
    "test-first": {"need": [
        ("writes a test", TEST),
        ("puts the test before the implementation", ("before", TEST, IMPL)),
        ("runs it and sees it fail", _rx(r"\bfail\w*")),
    ]},
    "fails-first": {"need": [
        ("says the test checks existing behaviour", _rx(
            r"\bexisting behaviou?r\b|\balready (?:exists|works|implemented|passes|there)\b")),
        ("says a new test must fail first", _rx(
            r"\b(?:should|must|needs? to|has to) fail\b|\b(?:see|watch) it fail\b|\bfail first\b")),
        ("fixes the test", _rx(r"\b(?:fix|rewrite|change|correct) (?:the |your |that )?test\b")),
    ]},
    "minimal-green": {"need": [
        ("keeps the code minimal", _rx(r"\b(?:minimal|simplest|just enough|smallest)\b")),
        ("leaves out what the test does not need", _rx(
            r"\bYAGNI\b|\b(?:no|without|skip|leave out|not add\w*|drop) (?:the )?(?:extra|options|logging|config)")),
        ("runs the test to see it pass", _rx(r"\b(?:run|re-?run)\b[^\n]{0,60}\btests?\b")),
    ]},
    "delete-and-restart": {"need": [
        ("deletes the code written first", _rx(r"\bdelete\b|\bthrow (?:it )?away\b|\bdiscard\b")),
        ("starts over test-first", _rx(r"\bstart (?:over|again)\b|\bfrom scratch\b|\brewrite\b")),
        ("says tests written after prove little", _rx(
            r"\bsunk cost\b|\bimmediately\b|\bprove\w* nothing\b|\bad-?hoc\b|\bno record\b")),
    ]},
    "bug-test-first": {"need": [
        ("writes a failing test for the bug", _rx(r"\bfailing test\b|\btest (?:that|which) (?:fails|reproduces)\b")),
        ("reproduces the bug", _rx(r"\breproduc\w*")),
        ("keeps it as a regression test", _rx(r"\bregression\b|\bcom(?:es|ing) back\b")),
    ]},
    "one-behaviour-per-test": {
        "need": [
            ("at least two separate tests", ("count", TEST_NAME, 2)),
            ("one behaviour per test", _rx(r"\bone (?:behaviou?r|thing|case)\b|\beach test\b")),
        ],
        "avoid": [
            ("one catch-all test_everything", _rx(r"\btest_everything\b")),
            ("a test name joined with 'and'", _rx(r"\bdef test_\w*_and_\w*")),
        ],
    },
}


def _met(spec, text):
    if isinstance(spec, tuple):
        kind, rx, arg = spec
        if kind == "before":
            first, later = rx.search(text), arg.search(text)
            return bool(first) and (later is None or first.start() < later.start())
        return len({m.group(0) for m in rx.finditer(text)}) >= arg
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
