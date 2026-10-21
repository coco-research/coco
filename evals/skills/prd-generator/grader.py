"""Grader for the prd-generator pilot. Deterministic: no model calls, no network.

grade(item, output) scores a generated PRD against the brief it was written from.

    score = 0.4 * sections + 0.2 * acceptance + 0.4 * facts - 0.1 * placeholders

The result is floored at 0 and capped at 1. novelty is the share of the reply's word
5-grams that do not appear in the brief (item["input"]). Words are lowercased,
punctuation is stripped, and what remains is split on whitespace. Fewer than five
reply words counts as novelty 0. Below 0.5, the score is multiplied by novelty / 0.5
and the note "mostly restates the brief (novelty X.XX)" is added. At 0.5 or above the
score is left unchanged. The score is then rounded to four places.

ponytail: 5-gram overlap is a cheap proxy. Upgrade path: a semantic similarity check.

sections      Fraction of five required parts that have a heading with content under
              it: problem or overview, goals or success metrics, requirements or user
              stories, acceptance criteria, out of scope or non-goals. A heading is a
              markdown "#" line, a bold line, a "Label:" line, or a short numbered
              line. Synonyms match case-insensitively and a heading earns every part
              it names ("Goals and Non-Goals" earns two). Content is a list item or a
              sentence before the next heading, so a bare heading earns nothing. The
              document's own title ("Product Requirements Document") earns nothing.
acceptance    1 when the acceptance-criteria part is earned, when a line starting with
              "Given" is followed by "when" and then "then", or when a user story
              ("As a ...") is followed by a checklist. Otherwise 0.
facts         Fraction of the item's facts found verbatim in the output. Case,
              whitespace, typographic dashes and quotes, and markdown emphasis marks
              are ignored.
placeholders  Each TBD, TBC, TODO, FIXME, "to be determined", lorem ipsum, {{slot}} or
              unfilled [bracketed template slot] costs 0.1. Checkboxes, links, ids
              such as [P0], tags such as [Must Have] and quoted lists are not slots.

Only the first 200,000 characters of a reply, and the first 300 of each line, are read.
"""
import re

W_SECTIONS, W_ACCEPTANCE, W_FACTS, PLACEHOLDER_COST = 0.4, 0.2, 0.4, 0.1
MAX_CHARS, MAX_LINE = 200_000, 300  # bounds the work a runaway reply can cause

# ponytail: a heading with one short line under it earns its part. Upgrade path: judge the
# section's text. The skill's other sections (personas, timeline, risks, ...) are not
# scored: a brief cannot supply them, and asking for them invites invented content.
PARTS = (
    ("acceptance criteria", r"acceptance|definition of done"),
    ("out of scope", r"out[- ]of[- ]scope|non[- ]?goals?|not (?:in scope|included|building|doing)"
                     r"|exclusions?|deferred|future (?:work|considerations|phases?)"),
    ("requirements or user stories", r"requirements?|stor(?:y|ies)|use cases?|functional"),
    ("goals or success metrics", r"(?<!non)(?<!non-)(?<!non )goals?|objectives?|success|metrics?|kpis?|okrs?"),
    ("problem or overview", r"problem|overview|summary|background|context|motivation|introduction"
                            r"|purpose|vision|rationale"),
)
_PARTS = [(name, re.compile(r"\b(?:%s)" % pats)) for name, pats in PARTS]

_ATX = re.compile(r" {0,3}(#{1,6})[ \t]+(.*)$")
_MARKER = re.compile(r"^\s*(?:[-*+]\s+(?:\[[ xX]\]\s+)?|\d+(?:\.\d+)*[.)]\s+)")
_BOLD = re.compile(r"(?:\*\*|__)([^*_\n]{1,80}?)(?:\*\*|__)[ \t]*:?[ \t]*(.*)$")
_LABEL = re.compile(r"([A-Za-z][^:\n]{1,60}?)[ \t]*:[ \t]*(.*)$")
_NUMBERED = re.compile(r"[ \t]*\d+(?:\.\d+)*[.)]?[ \t]+([^\n]{3,70})$")
_LIST_ITEM = re.compile(r"\s*(?:[-*+]|\d+[.)])\s+\S")
_CHECKBOX = re.compile(r"\s*[-*+]\s+\[[ xX]\]\s+\S")
_STORY = re.compile(r"[*_\s]*as an?\b", re.I)
_GIVEN = re.compile(r"[*_\s]*given\b", re.I)
_PLACEHOLDER = re.compile(
    r"(?-i:\b(?:TBD|TBC|TODO|FIXME)\b)"
    r"|(?i:lorem ipsum|\bto be (?:determined|decided|defined)\b)"
    r"|\{\{[^}\n]{1,80}\}\}"
    # [Feature Name]: not a checkbox, an id like [P0], a tag like [Must Have], a quoted list
    # item, a subscript like items[i], or a link.
    r"|(?<![\w)\]])\[(?![xX ]\])(?![A-Z]{1,4}-?\d+\])"
    r"(?!(?i:(?:must|should|could|won'?t|nice to) have|mvp|high|medium|low|critical|optional|done|open"
    r"|blocked|new|wip|approved|in (?:review|progress))\])"
    r"(?=[^\]\n\"']{0,80}[A-Za-z]{2})[^\[\]\n\"']{1,80}\](?![(\[])")
_TYPOGRAPHY = str.maketrans({
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
})


def _heading(line):
    """Return (level, title, rest-of-line) when the line reads as a heading, else None."""
    if "](" in line:  # a link, as in a table of contents
        return None
    m = _ATX.match(line)
    if m:
        title = m.group(2).rstrip(" \t#")
        return (len(m.group(1)), title, "") if title else None
    body = _MARKER.sub("", line, count=1)
    for pattern in (_BOLD, _LABEL):
        m = pattern.match(body)
        if m and len(m.group(1).split()) <= 6:
            return 9, m.group(1), m.group(2)
    m = _NUMBERED.match(line)
    if m and not m.group(1).rstrip().endswith((".", ",", ";", "!", "?")) and len(m.group(1).split()) <= 8:
        return 9, m.group(1), ""
    return None


def _parts(title):
    """The required parts a heading names."""
    title = re.sub(r"\bproduct requirements?(?: document)?\b", " ", title.lower())  # the document's title
    return {name for name, pattern in _PARTS if pattern.search(title)}


def _has_body(lines, index, level, rest):
    """True when the heading at lines[index] has content: text after "Label:", or a list item
    or a sentence within the next few lines, before the next heading of its own rank."""
    if len(rest.split()) >= 2:
        return True
    for line in lines[index + 1:index + 9]:
        m = _ATX.match(line)
        if m:
            if len(m.group(1)) <= min(level, 6):
                return False
            continue
        if level == 9 and not _LIST_ITEM.match(line) and _heading(line):
            return False
        if _LIST_ITEM.match(line) or len(line.split()) >= 3:
            return True
    return False


def _given_when_then(lines):
    """True when a line starting with "Given" is followed, within a few lines, by "when" then "then"."""
    for i, line in enumerate(lines):
        if _GIVEN.match(_MARKER.sub("", line, count=1)):
            text = " ".join(lines[i:i + 4]).lower()
            when = re.search(r"\bwhen\b", text)
            if when and re.search(r"\bthen\b", text[when.end():]):
                return True
    return False


def _story_checklist(lines):
    """True when a user story ("As a ...") is followed by a checkbox list."""
    for i, line in enumerate(lines):
        if _STORY.match(_MARKER.sub("", line, count=1)) and any(_CHECKBOX.match(l) for l in lines[i + 1:i + 9]):
            return True
    return False


def _norm(s):
    return " ".join(re.sub(r"[*_`~]", "", s.lower().translate(_TYPOGRAPHY)).split())


def _words(text):
    """Lowercased words with punctuation removed, then split on whitespace."""
    return "".join(ch if ch.isalnum() or ch.isspace() else "" for ch in text.lower()).split()


def novelty(output, brief):
    """Share of the output's word 5-grams that the brief does not contain.

    Fewer than five output words is 0: there is nothing new to measure.
    """
    out = _words(output)
    if len(out) < 5:
        return 0.0
    src = _words(brief)
    known = {tuple(src[i:i + 5]) for i in range(len(src) - 4)}
    total = len(out) - 4
    fresh = sum(tuple(out[i:i + 5]) not in known for i in range(total))
    return fresh / total


def grade(item, output):
    output = (output if isinstance(output, str) else "")[:MAX_CHARS]
    lines = [line[:MAX_LINE] for line in output.splitlines()]

    found = set()
    for index, line in enumerate(lines):
        head = _heading(line)
        if head:
            level, title, rest = head
            names = _parts(title)
            if names and _has_body(lines, index, level, rest):
                found |= names
    missing = [name for name, _ in PARTS if name not in found]
    sections = (len(PARTS) - len(missing)) / len(PARTS)

    criteria = 1.0 if "acceptance criteria" in found or _given_when_then(lines) or _story_checklist(lines) else 0.0

    facts = item["facts"]
    text = _norm(output)
    lost = [fact for fact in facts if _norm(fact) not in text]
    kept = (len(facts) - len(lost)) / len(facts) if facts else 1.0

    slots = [m.group(0) for m in _PLACEHOLDER.finditer(output)]

    raw = W_SECTIONS * sections + W_ACCEPTANCE * criteria + W_FACTS * kept - PLACEHOLDER_COST * len(slots)
    score = min(1.0, max(0.0, raw))
    nov = novelty(output, item["input"])
    notes = []
    if missing:
        notes.append("missing sections: " + ", ".join(missing))
    if not criteria:
        notes.append("no acceptance criteria (a labelled list, Given/When/Then, or a story checklist)")
    if lost:
        notes.append("facts kept %d/%d, missing: %s" % (len(facts) - len(lost), len(facts), "; ".join(lost)))
    if slots:
        notes.append("%d placeholder(s): %s" % (len(slots), ", ".join(sorted(set(slots))[:5])))
    if nov < 0.5:
        score *= nov / 0.5
        notes.append("mostly restates the brief (novelty %.2f)" % nov)
    return {"score": round(score, 4), "notes": notes}
