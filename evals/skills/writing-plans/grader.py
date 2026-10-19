"""Grader for the writing-plans pilot. Deterministic: no model calls, no network.

grade(item, output) scores an implementation plan against the spec it was written from.

    score = 0.2 * structure + 0.15 * test_step + 0.15 * files + 0.5 * coverage

The result is capped at 1 and rounded to four places.

structure   1 when the plan has at least 3 steps: numbered lines ("1.", "1)", "1.1",
            "### 1.", "**1.**"), checkbox lines ("- [ ]"), or "Step N" / "Task N" lines.
test_step   1 when the plan names a test command (pytest, unittest, npm test, go test
            and similar) or a test file (a tests/ path, test_*.py, *_test.go, *.spec.ts).
files       1 when at least one file path written in the spec appears in the plan.
coverage    Fraction of the item's requirements that are covered. A requirement is
            covered when at least 60% of its content words appear in the plan. Words are
            lowercased, split on non-alphanumerics, mapped from number words to digits
            ("three" is "3"), stripped of common plural and verb endings, and filtered
            through a short stopword list.

Only the first 200,000 characters of a reply are read.
"""
import re

W_STRUCTURE, W_TEST, W_FILES, W_COVERAGE = 0.2, 0.15, 0.15, 0.5
MIN_STEPS, COVERED_AT = 3, 0.6
MAX_CHARS = 200_000  # bounds the work a runaway reply can cause

_STEP = re.compile(
    r"^[ \t]*(?:"
    r"(?:#{1,6}[ \t]*)?(?:\*\*|__)?(?:\d+[.)]|\d+(?:\.\d+)+[.)]?)(?:\*\*|__)?[ \t]+\S"
    r"|[-*+][ \t]+\[[ xX]\][ \t]*\S"
    r"|(?:#{1,6}[ \t]*)?(?:[-*+][ \t]+)?(?:\*\*|__)?(?:step|task)[ \t]+\d+\b)",
    re.I | re.M)
_TEST = re.compile(
    r"\b(?:pytest|py\.test|unittest|nosetests|tox|jest|vitest|mocha|rspec|phpunit|ctest"
    r"|go test|cargo test|npm (?:run )?test|yarn test|pnpm test|make test|mvn test|gradle test)\b"
    r"|\btests?/[\w./-]+|\btest_\w+\.py\b|\b\w+_test\.(?:py|go|js|ts|rb)\b|\b\w+\.(?:test|spec)\.(?:js|ts|jsx|tsx)\b",
    re.I)
_PATH = re.compile(r"[\w.-]+(?:/[\w.-]+)+\.\w+")
_WORD = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "a an the and or but if than so as of to in on at by for from with into per is are was were be been "
    "do does did has have had it its this that these those there which who what when where how must "
    "should will would can could may might shall".split())
_NUMBERS = {w: str(n) for n, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}
_NUMBERS.update(thirty="30", forty="40", fifty="50", sixty="60", seventy="70", eighty="80", ninety="90",
                hundred="100")


def _stem(word):
    for suffix in ("ies", "ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) >= len(suffix) + 3:
            word = word[:-len(suffix)] + ("y" if suffix == "ies" else "")
            break
    return word[:-1] if word.endswith("e") and len(word) > 3 else word


def _words(text):
    return {_NUMBERS.get(w) or _stem(w) for w in _WORD.findall(text.lower()) if w not in _STOP}


def grade(item, output):
    output = (output if isinstance(output, str) else "")[:MAX_CHARS]
    steps = len(_STEP.findall(output))
    has_steps = steps >= MIN_STEPS
    has_test = bool(_TEST.search(output))
    lowered = output.lower()
    paths = sorted(set(_PATH.findall(item["input"])))
    has_file = any(p.lower() in lowered for p in paths)

    # ponytail: coverage is word overlap, so a plan that only repeats the spec counts as
    # covered (such a plan scores 0.8: only the step check fails). Upgrade path: count only
    # the words that follow the first step.
    plan_words = _words(output)
    reqs = item["requirements"]
    missed = []
    for req in reqs:
        wanted = _words(req)
        if wanted and len(wanted & plan_words) / len(wanted) < COVERED_AT:
            missed.append(req)
    coverage = (len(reqs) - len(missed)) / len(reqs) if reqs else 1.0

    raw = (W_STRUCTURE * has_steps + W_TEST * has_test + W_FILES * has_file
           + W_COVERAGE * coverage)
    notes = []
    if not has_steps:
        notes.append("%d step(s), need at least %d numbered or checkbox steps" % (steps, MIN_STEPS))
    if not has_test:
        notes.append("no test command or test file named")
    if not has_file:
        notes.append("none of the spec's file paths appear in the plan")
    if missed:
        notes.append("requirements covered %d/%d, missing: %s" % (len(reqs) - len(missed), len(reqs), "; ".join(missed)))
    return {"score": round(min(1.0, raw), 4), "notes": notes}
