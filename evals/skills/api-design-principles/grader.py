"""Grader for api-design-principles. Deterministic: no model calls, no network.

Each item tests one behaviour the SKILL.md asks for. The item names it in "check" and
quotes the SKILL.md line it comes from in "rule".

    score = 0.75 * signals * 0.5 ** avoided + 0.25 * terms

signals  Fraction of the check's signals found in the reply (regexes).
avoided  Number of the check's avoid patterns found in the reply (a verb endpoint listed
         as a proposed route); each halves the signals.
terms    Fraction of the item's case terms (resource and field names) the reply repeats,
         so the reply has to be about this API and not a generic lecture.

Only the first 200,000 characters of a reply are read.
"""
import re

W_SIGNALS, W_TERMS = 0.75, 0.25
MAX_CHARS = 200_000  # bounds the work a runaway reply can cause


def _rx(pattern):
    return re.compile(pattern, re.I | re.M)


CHECKS = {
    "resource-nouns": {
        # Case-sensitive on purpose: noun paths are lowercase ("/orders/{id}"), verb paths
        # are camelCase or snake_case ("/createOrder", "/get_order").
        "need": [
            ("lists a collection with GET", re.compile(r"\bGET[ \t]+/(?:[a-z0-9_{}-]+/)*[a-z]+s\b")),
            ("creates with POST on the collection", re.compile(r"\bPOST[ \t]+/(?:[a-z0-9_{}-]+/)*[a-z]+s\b")),
            ("changes or removes with PATCH, PUT or DELETE", re.compile(
                r"\b(?:PATCH|PUT|DELETE)[ \t]+/(?:[a-z0-9_{}-]+/)*[a-z]+s/(?:\{\w+\}|:\w+)")),
        ],
        # Only a line that proposes the route counts, so "replace POST /createOrder" is fine.
        "avoid": [("proposes a verb endpoint", re.compile(
            r"^[ \t]*(?:[-*|][ \t]*)?`?(?:GET|POST|PUT|PATCH|DELETE)[ \t]+/(?:[\w{}-]+/)*"
            r"(?:create|get|delete|update|add|remove|fetch|list|cancel)(?:[A-Z_-]\w*)?\b", re.M))],
    },
    "status-codes": {"need": [
        ("404 for a missing resource", _rx(r"\b404\b")),
        ("400 or 422 for bad input", _rx(r"\b(?:400|422)\b")),
        ("201 on create or 5xx for server faults", _rx(r"\b(?:201|5\d\d)\b")),
    ]},
    "consistent-errors": {"need": [
        ("one error shape for every endpoint", _rx(
            r"\b(?:one|single|same|consistent|standard\w*) (?:error )?(?:shape|schema|format|envelope|body|response)")),
        ("an error code field", _rx(r"[\"']?\b(?:error|code)\b[\"']?[ \t]*:")),
        ("a message field", _rx(r"[\"']?\bmessage\b[\"']?[ \t]*:")),
        ("per-field details", _rx(r"[\"']?\b(?:details|field|errors)\b[\"']?[ \t]*:")),
    ]},
    "paginate": {"need": [
        ("a page or cursor parameter", _rx(r"\b(?:page|cursor|offset|limit|page_size|per_page)\b")),
        ("a maximum page size", _rx(r"\bmax\w*|\bat most\b|\bup to\b|\ble=|\bcap\w*")),
        ("a total or next link in the response", _rx(r"\b(?:total|next|has_next|next_cursor)\b")),
    ]},
    "version-breaking-change": {"need": [
        ("versions the API", _rx(r"/v\d\b|\bversion\w*")),
        ("deprecates the old field", _rx(r"\bdeprecat\w*")),
        ("gives clients time to move", _rx(r"\bsunset\w*|\bwindow\b|\bmigrat\w*|\bboth fields\b|\buntil\b")),
    ]},
    "decouple-from-db": {"need": [
        ("says the API should not mirror the table", _rx(r"\bmirror\w*|\bcoupl\w*|\bdecoupl\w*|\bleak\w*|\bexpos\w*")),
        ("defines a response model", _rx(r"\bresponse model\b|\bDTO\b|\bserializ\w*|\bschema\b|\brepresentation\b")),
        ("drops internal columns", _rx(r"\b(?:remove|drop|omit|hide|exclude|never return)\b")),
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
