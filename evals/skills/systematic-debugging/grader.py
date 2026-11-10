"""Grader for systematic-debugging. Deterministic: no model calls, no network.

Each item tests one behaviour the SKILL.md asks for. The item names it in "check" and
quotes the SKILL.md line it comes from in "rule".

    score = 0.75 * signals + 0.25 * terms

signals  Fraction of the check's signals found in the reply (case-insensitive regexes).
terms    Fraction of the item's case terms (file names, error text) the reply repeats, so
         the reply has to be about this case and not a generic lecture.

Only the first 200,000 characters of a reply are read.
"""
import re

W_SIGNALS, W_TERMS = 0.75, 0.25
MAX_CHARS = 200_000  # bounds the work a runaway reply can cause


def _rx(pattern):
    return re.compile(pattern, re.I | re.M)


CHECKS = {
    "investigate-before-fix": {"need": [
        ("names finding the root cause", _rx(r"\broot[- ]cause\b")),
        ("reproduces the failure first", _rx(r"\breproduc\w*")),
        ("reads the error, trace or logs", _rx(r"\b(?:stack trace|traceback|error message|logs?)\b")),
    ]},
    "reproduce-first": {"need": [
        ("tries to reproduce it", _rx(r"\breproduc\w*")),
        ("adds logging or instrumentation", _rx(r"\b(?:log|logs|logging|instrument\w*|diagnostic\w*)\b")),
        ("gathers data or evidence before changing code", _rx(r"\b(?:data|evidence)\b")),
    ]},
    "check-recent-changes": {"need": [
        ("uses git history", _rx(r"\bgit (?:diff|log|bisect|blame)\b")),
        ("asks what changed recently", _rx(r"\brecent (?:commits?|changes?|deploys?)\b|\bwhat changed\b")),
        ("checks dependencies, config or environment", _rx(r"\b(?:dependenc\w*|config\w*|environment\w*)\b")),
    ]},
    "single-hypothesis": {"need": [
        ("states 'I think X ... because Y'", _rx(r"\bI think\b[^\n]{0,200}\bbecause\b")),
        ("calls it a hypothesis", _rx(r"\bhypothes[ie]s\b")),
        ("tests it with one small change", _rx(r"\b(?:one|single) (?:variable|change|thing)\b|\bsmallest\b|\bminimal\b")),
    ]},
    "failing-test-first": {"need": [
        ("writes a failing test before the fix", _rx(r"\bfailing test\b|\btest (?:that|which) fails\b")),
        ("makes one change at the source", _rx(r"\b(?:one|single) (?:fix|change)\b|\bat the (?:source|root)\b")),
        ("runs the tests to verify", _rx(r"\b(?:run|re-?run)\b[^\n]{0,60}\btests?\b")),
    ]},
    "question-architecture": {"need": [
        ("questions the architecture or design", _rx(r"\barchitectur\w*|\bdesign\b")),
        ("stops trying more fixes", _rx(r"\bstop\b|\bstep back\b")),
        ("discusses it with a person first", _rx(r"\b(?:discuss\w*|talk (?:to|with)|partner|team)\b")),
    ]},
}


def grade(item, output):
    text = (output if isinstance(output, str) else "")[:MAX_CHARS]
    check = CHECKS[item["check"]]
    missed = [label for label, rx in check["need"] if not rx.search(text)]
    signals = 1 - len(missed) / len(check["need"])
    lowered = " ".join(text.lower().split())  # a term may wrap across lines
    absent = [t for t in item["terms"] if t.lower() not in lowered]
    terms = 1 - len(absent) / len(item["terms"])
    raw = W_SIGNALS * signals + W_TERMS * terms
    notes = ["missing: " + m for m in missed]
    if absent:
        notes.append("case terms not mentioned: " + ", ".join(absent))
    return {"score": round(min(1.0, raw), 4), "notes": notes}
