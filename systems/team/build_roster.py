#!/usr/bin/env python3
"""Render `commands/team/roles.md` from the roster.

    python3 systems/team/build_roster.py           # write the markdown
    python3 systems/team/build_roster.py --check   # exit 1 if it is out of date

`systems/team/roles.yaml` is the source of truth. The markdown is a rendering of it,
committed because the router reads a file and agents are handed prompt text out of it,
and gated in CI because a generated file that nobody regenerates is a file that drifts.

The rendering keeps the shape the router depends on: one `## <Name>` section per role,
a `- **ID:**` line it validates `--roles` against, `- **Layer:**`, and the
`### System Prompt` block verbatim.
"""

import argparse
import os
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROSTER = os.path.join(ROOT, "systems/team/roles.yaml")
TARGET = os.path.join(ROOT, "commands/team/roles.md")

# The original section order and headings, reproduced from (layer, family) so the
# document reads the same as it always has.
SECTIONS = [
    ("synthesis", "leadership", "Leadership — Layer 4 (Synthesis)"),
    ("research", None, "Research & Analysis — Layer 1"),
    ("execution", "engineering", "Engineering — Layer 2 (Execution)"),
    ("execution", "content", "Content & Communications — Layer 2 (Execution)"),
    ("execution", "presentation", "Presentation — Layer 2 (Execution)"),
    ("review", None, "Review Specialists — Layer 3"),
]

HEADER = """# Team Roles — Cross-Functional Product Team Roster

> **Purpose:** This file defines all available roles for the /team system.
> The router (team.md) reads this to select roles based on action + domain.
> Each role has a system prompt that gets injected into the agent's spawn prompt.
>
> **Generated file.** `systems/team/roles.yaml` is the source of truth, and this
> document is rendered from it by `python3 systems/team/build_roster.py`. Edit the
> YAML, never this file; CI fails if the two disagree.
>
> **How agents use this:** The orchestrator (user's own session) reads this file,
> selects relevant roles, and copies each role's system prompt into the Agent tool's
> `prompt` parameter. Agents never read this file directly.
>
> **Adding new roles:** add a record to `systems/team/roles.yaml` and run
> `python3 systems/team/validate_roles.py` until it exits 0, then regenerate this
> file. A role that cannot state a distinct mission should be merged or retired
> rather than added.

---

## Role Template

<!-- The schema is systems/team/roles.schema.json. Every field below is required. -->
<!--
id:            kebab-case-id                    (stable; never changes)
name:          Human Readable Name
family:        leadership | research | engineering | content | presentation | review
layer:         research | execution | review | synthesis   (rule: systems/team/layer_rules.json)
mission:       one sentence — what the role is FOR
selection:     the condition under which the router picks it
does_not_do:   [boundaries a reviewer could catch a violation of]
inputs:        [{artifact, from}]               from: a role id, user, orchestrator, all-layer-1
outputs:       [{artifact, acceptance_criteria: [...]}]
decision_rights: [what it may decide alone]
handoffs:      [role ids that consume its output]
competence:    {level, meaning}
capabilities:  [skill ids that resolve to a SKILL.md]
capability_gaps: [{id, why}]                    when nothing in this repo fits
escalation:    {to, when}
overlap:       [{with: [peer ids], decision: merge|differentiate|retire, rule}]
-->

---
"""


def bullet(label, value):
    return f"- **{label}:** {value}"


def render_role(role):
    lines = [f"## {role['name']}", ""]
    lines.append(bullet("ID", role["id"]))
    lines.append(bullet("Seniority", role["competence"]["level"]))
    lines.append(bullet("Layer", role["layer"]))
    lines.append(bullet("Category", role.get("category", role.get("family", ""))))
    tags = role.get("domain_tags") or []
    lines.append(bullet("Domain Tags", ", ".join(tags) if tags else "all"))
    lines.append(bullet("When Selected", role["selection"]))
    lines.append(bullet("Mission", role["mission"]))

    lines.append(bullet("Does Not Do", "; ".join(role.get("does_not_do") or [])))

    ins = "; ".join(f"{i['artifact']} from {i['from']}" for i in role.get("inputs") or [])
    lines.append(bullet("Inputs", ins))

    outs = []
    for o in role.get("outputs") or []:
        criteria = "; ".join(o.get("acceptance_criteria") or [])
        outs.append(f"{o['artifact']} — {criteria}")
    lines.append(bullet("Outputs", " | ".join(outs)))

    lines.append(bullet("Decision Rights", "; ".join(role.get("decision_rights") or [])))
    lines.append(bullet("Handoffs", ", ".join(role.get("handoffs") or []) or "none (terminal)"))

    caps = role.get("capabilities") or []
    gaps = role.get("capability_gaps") or []
    if caps:
        cap_line = ", ".join(caps)
    else:
        cap_line = "none"
    if gaps:
        cap_line += " | gaps: " + ", ".join(g["id"] for g in gaps)
    lines.append(bullet("Capabilities", cap_line))

    esc = role.get("escalation") or {}
    lines.append(bullet("Escalation", f"to {esc.get('to')} — {esc.get('when')}"))

    for o in role.get("overlap") or []:
        lines.append(bullet("Overlap", f"{o['decision'].upper()} with {', '.join(o['with'])} — {o['rule']}"))

    lines += ["", "### System Prompt", "", role["system_prompt"].strip(), "", "---", ""]
    return "\n".join(lines)


def build(roster):
    out = [HEADER]
    for layer, family, heading in SECTIONS:
        members = [r for r in roster
                   if r["layer"] == layer and (family is None or r.get("family") == family)]
        if not members:
            continue
        out.append(f"\n## {heading}\n")
        for r in members:
            out.append(render_role(r))
    return "\n".join(out).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description="Render commands/team/roles.md from the roster.")
    ap.add_argument("--check", action="store_true", help="exit 1 if out of date")
    args = ap.parse_args()

    data = yaml.safe_load(open(ROSTER, encoding="utf-8"))
    roster = data["roles"] if isinstance(data, dict) else data
    rendered = build(roster)

    if args.check:
        current = open(TARGET, encoding="utf-8").read() if os.path.isfile(TARGET) else ""
        if current != rendered:
            print("commands/team/roles.md is out of date.")
            print("Run: python3 systems/team/build_roster.py")
            return 1
        print(f"commands/team/roles.md is up to date ({len(roster)} roles).")
        return 0

    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(rendered)
    print(f"Wrote commands/team/roles.md ({len(roster)} roles, {len(rendered)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
