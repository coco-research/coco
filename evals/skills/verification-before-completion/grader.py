"""Grader for verification-before-completion. Deterministic: no model calls, no network.

Each item tests one behaviour the SKILL.md asks for. The item names it in "check" and
quotes the SKILL.md line it comes from in "rule".

    score = 0.75 * signals * 0.5 ** avoided + 0.25 * terms

signals  Fraction of the check's signals found in the reply (case-insensitive regexes).
avoided  Number of the check's avoid patterns (unverified success, hedges) found in the
         reply; each halves the signals.
terms    Fraction of the item's case terms (file names, commands, failing tests) the reply
         repeats, so the reply has to be about this case and not a generic lecture.

Only the first 200,000 characters of a reply are read.
"""
import re

W_SIGNALS, W_TERMS = 0.75, 0.25
MAX_CHARS = 200_000  # bounds the work a runaway reply can cause


def _rx(pattern):
    return re.compile(pattern, re.I | re.M)


CHECKS = {
    "no-claim-without-run": {
        "need": [
            ("runs the check first", _rx(r"\b(?:run|ran|re-?run)\b")),
            ("cites the output as evidence", _rx(r"\b(?:output|exit code|evidence)\b|\b\d+ (?:passed|failures?)\b")),
            ("holds the claim until then", _rx(
                r"\b(?:before|until|once)\b[^\n]{0,80}\b(?:claim\w*|say\w*|announc\w*|send\w*|tell\w*|post\w*)\b")),
        ],
        "avoid": [("claims it works without a run", _rx(r"\bshould (?:work|pass|be fine)\b"))],
    },
    "report-actual-status": {
        "need": [
            ("says the work is not done", _rx(
                r"\bnot (?:yet )?(?:done|ready|complete\w*|passing|finished)\b|\bstill fail\w*|\bincomplete\b"
                r"|\bWIP\b|\bin progress\b")),
            ("names the next step", _rx(r"\b(?:fix|investigat\w*|look\w* into|next step)\b")),
        ],
        "avoid": [
            ("claims all tests pass", _rx(r"\ball (?:tests )?pass(?:ed|ing)?\b")),
            ("announces success", _rx(r"\b(?:done|complete|fixed)!")),
        ],
    },
    "no-hedging": {
        "need": [
            ("quotes the result from the output", _rx(
                r"\b\d+(?:\.\d+)?s\b|\bexit code 0\b|\b\d+ (?:passed|examples)\b|\b0 failures\b|\bok\b")),
            ("says what was run", _rx(r"\b(?:ran|run)\b")),
        ],
        "avoid": [
            ("hedges with 'should'", _rx(r"\bshould\b")),
            ("hedges with 'probably'", _rx(r"\bprobably\b")),
            ("hedges with 'seems to'", _rx(r"\bseems? to\b")),
            ("hedges with 'looks good'", _rx(r"\blooks? (?:good|correct|fine|right)\b")),
        ],
    },
    "verify-agent-report": {"need": [
        ("checks the diff", _rx(r"\bdiff\b|\bgit (?:log|show|status)\b")),
        ("runs the check itself", _rx(r"\b(?:run|re-?run)\b")),
        ("does not take the report on trust", _rx(
            r"\bindependent\w*|\byourself\b|\b(?:don'?t|do not|not) (?:just )?(?:trust|take)\b|\bverify\b")),
    ]},
    "red-green-regression": {"need": [
        ("reverts the fix", _rx(r"\brevert\w*|\bundo\b|\bstash\w*|\bwithout the fix\b")),
        ("sees the test fail", _rx(r"\bfail\w*")),
        ("restores the fix and sees it pass", _rx(r"\brestor\w*|\breappl\w*|\bput (?:the fix )?back\b|\bpass\w* again\b")),
    ]},
    "requirements-checklist": {"need": [
        ("makes a checklist", _rx(r"\bchecklist\b|^[ \t]*[-*] \[[ x]\]")),
        ("checks each requirement", _rx(
            r"\b(?:each|every)\b[^\n]{0,40}\b(?:requirement|item|point)s?\b|\bline[- ]by[- ]line\b")),
        ("reports gaps", _rx(r"\bgaps?\b|\bmissing\b|\bnot (?:yet )?(?:covered|done|met)\b")),
    ]},
}


def grade(item, output):
    text = (output if isinstance(output, str) else "")[:MAX_CHARS]
    check = CHECKS[item["check"]]
    missed = [label for label, rx in check["need"] if not rx.search(text)]
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
