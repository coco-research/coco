"""Deterministic humanizer grader. Tell patterns live here, not in the skill."""
import re

# Case-insensitive phrases, plus the em dash character. Fixed list, not loaded
# from SKILL.md.
_TELLS = (
    ("delve", re.compile(r"\bdelve\b", re.I)),
    ("tapestry", re.compile(r"\btapestry\b", re.I)),
    ("testament to", re.compile(r"\btestament to\b", re.I)),
    ("in today's fast-paced world", re.compile(r"\bin today['\u2019]s fast-paced world\b", re.I)),
    ("it's important to note", re.compile(r"\bit['\u2019]s important to note\b", re.I)),
    ("navigate the complexities", re.compile(r"\bnavigate the complexities\b", re.I)),
    ("seamless", re.compile(r"\bseamless\b", re.I)),
    ("leverage", re.compile(r"\bleverage\b", re.I)),
    ("robust", re.compile(r"\brobust\b", re.I)),
    ("game-changer", re.compile(r"\bgame-changer\b", re.I)),
    ("moreover", re.compile(r"\bmoreover\b", re.I)),
    ("furthermore", re.compile(r"\bfurthermore\b", re.I)),
    ("in conclusion", re.compile(r"\bin conclusion\b", re.I)),
    ("not just ... but", re.compile(r"\bnot just\b.*?\bbut\b", re.I | re.S)),
    ("em dash", re.compile("\u2014")),
    ("cutting-edge", re.compile(r"\bcutting-edge\b", re.I)),
    ("thrilled to", re.compile(r"\bthrilled to\b", re.I)),
    ("empower", re.compile(r"\bempower\b", re.I)),
    ("elevate", re.compile(r"\belevates?\b", re.I)),
    ("pivotal", re.compile(r"\bpivotal\b", re.I)),
)


def _counts(text):
    text = text if isinstance(text, str) else ""
    total = 0
    hits = []
    for name, pattern in _TELLS:
        n = len(pattern.findall(text))
        total += n
        if n:
            hits.append(f"tell: {name}" if n == 1 else f"tell: {name} x{n}")
    return total, hits


_HEADING = re.compile(r"^\s*(#{1,6}\s+.*|\*\*[^*]+\*\*:?\s*|[A-Z][\w '\"-]{0,40}:\s*)$")


def final_rewrite(output):
    """The skill delivers a draft, audit bullets and a final rewrite: grade only the last.

    Takes the text after the last heading or label line that mentions "final"
    (e.g. "## Final rewrite", "**Final rewrite**", "Final rewrite:") up to the next
    heading. Falls back to the whole output when there is no such heading.
    """
    lines = output.splitlines()
    starts = [i for i, line in enumerate(lines) if _HEADING.match(line) and "final" in line.lower()]
    if not starts:
        return output
    body = []
    for line in lines[starts[-1] + 1:]:
        if _HEADING.match(line) and line.strip():
            break
        body.append(line)
    text = "\n".join(body).strip()
    return text or output


def grade(item, output):
    output = final_rewrite(output if isinstance(output, str) else "")
    source = item["text"] if isinstance(item.get("text"), str) else ""
    tells_before, _ = _counts(source)
    tells_after, tell_notes = _counts(output)
    removal = 1 - min(tells_after / max(tells_before, 1), 1)
    facts = item.get("facts") or []
    missing = [fact for fact in facts if fact.lower() not in output.lower()]
    facts_kept = (len(facts) - len(missing)) / len(facts) if facts else 1.0
    notes = list(tell_notes)
    notes.extend(f"missing fact: {fact}" for fact in missing)
    score = 0.5 * removal + 0.5 * facts_kept
    in_words = len(source.split())
    out_words = len(output.split())
    if in_words and (out_words < 0.4 * in_words or out_words > 1.6 * in_words):
        score *= 0.5
        notes.append("length guard: word count outside 40-160% of the input")
    return {"score": float(score), "notes": notes}
