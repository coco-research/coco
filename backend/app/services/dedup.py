"""Fuzzy deduplication utilities for todos.

Uses only Python stdlib (difflib.SequenceMatcher) — no external deps.
"""

from difflib import SequenceMatcher


def similarity(a: str, b: str) -> float:
    """Normalized similarity score (0.0 to 1.0) between two strings.

    Compares lowercased, stripped versions using SequenceMatcher.
    """
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()


def find_duplicates(
    todos: list[dict], threshold: float = 0.75
) -> list[list[dict]]:
    """Group todos by fuzzy title similarity.

    Returns only groups with 2+ items. Each group is a list of
    near-duplicate todos. Uses a simple greedy clustering approach:
    for each unmatched todo, start a new group and pull in all
    remaining unmatched todos whose title is similar enough.
    """
    used: set[int] = set()
    groups: list[list[dict]] = []

    for i, todo_a in enumerate(todos):
        if i in used:
            continue
        group = [todo_a]
        used.add(i)

        for j, todo_b in enumerate(todos):
            if j in used:
                continue
            score = similarity(todo_a.get("title", ""), todo_b.get("title", ""))
            if score >= threshold:
                group.append(todo_b)
                used.add(j)

        if len(group) >= 2:
            groups.append(group)

    return groups


def _score_todo(todo: dict) -> tuple:
    """Score a todo for pick_best. Higher = better.

    Prefers: longest title, has assignee, has due_date, most recent created_at.
    """
    title_len = len(todo.get("title") or "")
    has_owner = 1 if todo.get("owner") else 0
    has_due = 1 if todo.get("due_date") else 0
    created = todo.get("created_at") or ""
    return (title_len, has_owner, has_due, created)


def pick_best(group: list[dict]) -> dict:
    """Pick the best todo from a duplicate group.

    Heuristic: prefer longest title, has assignee, has due date, most recent.
    """
    if not group:
        raise ValueError("Cannot pick from empty group")
    return max(group, key=_score_todo)


def group_similarity(group: list[dict]) -> float:
    """Average pairwise similarity within a group."""
    if len(group) < 2:
        return 1.0

    total = 0.0
    count = 0
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            total += similarity(
                group[i].get("title", ""), group[j].get("title", "")
            )
            count += 1

    return round(total / count, 3) if count > 0 else 1.0
