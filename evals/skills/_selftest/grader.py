"""Fixture grader: 1 when the item's expected token appears in the output, else 0."""


def grade(item, output):
    hit = item["expect"] in output
    return {"score": 1.0 if hit else 0.0, "notes": ["hit" if hit else "miss"]}
