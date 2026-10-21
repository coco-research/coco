"""Grade a code-verification report. Stdlib only."""

import re

# Category names match the headings in skills/code-verification/SKILL.md.
# A hit is the full name or an obvious keyword from that heading.
_CATEGORIES = {
    "Variable Declaration Order (TDZ Prevention)": ("tdz", "temporal dead zone"),
    "Import/Export Integrity": ("import", "export"),
    "Reference Integrity": ("reference",),
    "Dead Code Detection": ("dead code",),
    "React State & Effects": ("react state", "useeffect"),
    "Mock Isolation (Test Files Only)": ("mock", "fake timer"),
    "CSS Class Integrity": ("css", "classname", "class name"),
}

_VERDICT = re.compile(r"\b(FAIL|PASS)\b", re.I)


def _verdict(output):
    found = {m.group(1).upper() for m in _VERDICT.finditer(output)}
    if "FAIL" in found:
        return "FAIL"
    if "PASS" in found:
        return "PASS"
    return None


def _keyword_hit(text, kw):
    if " " in kw:
        return kw in text
    return re.search(r"\b" + re.escape(kw) + r"\b", text) is not None


def _category_hit(output, name):
    text = output.lower()
    if name.lower() in text:
        return True
    return any(_keyword_hit(text, kw) for kw in _CATEGORIES.get(name, ()))


def _flagged(output):
    return [name for name in _CATEGORIES if _category_hit(output, name)]


def _locator_hit(output, item):
    token = item.get("token")
    if isinstance(token, str) and token and token in output:
        return True
    line = item.get("line")
    if type(line) is int and re.search(rf"\bline\s*:?\s*{line}\b", output, re.I):
        return True
    return False


def grade(item, output):
    output = output if isinstance(output, str) else ""
    got = _verdict(output)
    if item.get("verdict") == "PASS":
        if got == "FAIL":
            return {"score": 0.0, "notes": ["false alarm: verdict FAIL"]}
        if got != "PASS":
            return {"score": 0.0, "notes": ["verdict PASS not found"]}
        flagged = _flagged(output)
        if flagged:
            return {
                "score": 0.5,
                "notes": ["spurious category flagged: " + ", ".join(flagged)],
            }
        return {"score": 1.0, "notes": []}

    points = 0
    notes = []
    if got == "FAIL":
        points += 4
    elif got == "PASS":
        notes.append("lost 0.4: verdict PASS on a FAIL item")
    else:
        notes.append("lost 0.4: verdict FAIL not found")
    category = item.get("category")
    if isinstance(category, str) and _category_hit(output, category):
        points += 3
    else:
        notes.append("lost 0.3: category not named")
    if _locator_hit(output, item):
        points += 3
    else:
        notes.append("lost 0.3: token or line not named")
    return {"score": points / 10, "notes": notes}
