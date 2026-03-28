"""coco_teach, coco_forget, coco_people -- Brain knowledge management."""

import re

from app.mcp.server import mcp
from app.config import BRAIN_JSON_PATH
from app.services.json_store import read_json, write_json


def _slugify(name: str) -> str:
    """Convert a name to a slug: 'John Smith' -> 'john-smith'."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


@mcp.tool()
def coco_teach(fact: str) -> dict:
    """Parse a natural language fact and add it to CoCo's brain (brain.json).

    Supports two kinds of facts:
    - People: 'Alice is a PM on Cross Risk' adds/updates a person entry.
    - Rules: 'Always escalate budget changes' adds an attention rule.

    Args:
        fact: A natural language statement to teach CoCo.
    """
    brain = read_json(BRAIN_JSON_PATH)
    brain.setdefault("people", {})
    brain.setdefault("attention_rules", [])

    fact_lower = fact.lower().strip()

    # Heuristic: if the fact mentions a person with "is a" / "is the" / "works on", treat as person
    person_match = re.match(
        r"^(.+?)\s+(?:is\s+(?:a|the|an)\s+|works\s+(?:on|at|in)\s+|leads?\s+|owns?\s+)(.+)$",
        fact,
        re.IGNORECASE,
    )

    if person_match:
        name = person_match.group(1).strip()
        role_info = person_match.group(2).strip()
        slug = _slugify(name)

        existing = brain["people"].get(slug, {})
        existing["full_name"] = name
        existing["role"] = role_info
        brain["people"][slug] = existing
        write_json(BRAIN_JSON_PATH, brain)

        return {
            "type": "person",
            "slug": slug,
            "person": existing,
            "message": f"Learned about {name} ({role_info}).",
        }
    else:
        # Treat as attention rule
        # Avoid exact duplicates
        if fact not in brain["attention_rules"]:
            brain["attention_rules"].append(fact)
            write_json(BRAIN_JSON_PATH, brain)

        return {
            "type": "rule",
            "rule": fact,
            "total_rules": len(brain["attention_rules"]),
            "message": f"Added rule: {fact}",
        }


@mcp.tool()
def coco_forget(person_slug: str) -> dict:
    """Remove a person from CoCo's brain by their slug (e.g. 'john-smith').

    Args:
        person_slug: The slug identifier of the person to remove.
    """
    brain = read_json(BRAIN_JSON_PATH)
    people = brain.get("people", {})

    if person_slug not in people:
        return {"error": f"Person '{person_slug}' not found. Known: {list(people.keys())}"}

    removed = people.pop(person_slug)
    brain["people"] = people
    write_json(BRAIN_JSON_PATH, brain)

    return {
        "removed": person_slug,
        "name": removed.get("full_name", person_slug),
        "remaining_count": len(people),
    }


@mcp.tool()
def coco_people() -> dict:
    """List all people from CoCo's brain with their roles, projects, and metadata."""
    brain = read_json(BRAIN_JSON_PATH)
    people = brain.get("people", {})

    entries = []
    for slug, info in people.items():
        entries.append({
            "slug": slug,
            **info,
        })

    return {"people": entries, "total": len(entries)}
