#!/usr/bin/env python3
"""Validate the SI Team Role roster.

One command, three modes:

    python3 systems/team/validate_roles.py              # validate the roster
    python3 systems/team/validate_roles.py --baseline   # what today's roster is missing
    python3 systems/team/validate_roles.py --self-test  # prove every rule fires

The field list, the types and the enums are read from `roles.schema.json`; the layer
rules are read from `layer_rules.json`. Neither is restated here, so the contract and
its enforcement cannot drift apart.

Two severities, deliberately separated:

  ERROR  the roster is malformed, or a rule is broken.
  GAP    the roster is well-formed and a capability it needs does not exist yet.

A gap is a result, not a failure. Zero capability coverage used to be invisible because
nothing distinguished "this role needs nothing" from "nobody has filled this in yet";
here it is a named, counted list that the run prints and exits 0 on.

Stdlib plus PyYAML, matching the rest of the repository's tooling, so CI needs no new
dependency.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA = os.path.join(ROOT, "systems/team/roles.schema.json")
LAYERS = os.path.join(ROOT, "systems/team/layer_rules.json")
ROSTER = os.path.join(ROOT, "systems/team/roles.yaml")
LEGACY = os.path.join(ROOT, "commands/team/roles.md")

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# A description that only restates the role name, in the shape the deployed catalog
# currently uses for all 37 entries.
TEMPLATE_RE = re.compile(r"^\s*(.+?)\s+for the CoCo cross-functional team pipeline\.?\s*$", re.I)


# --------------------------------------------------------------------------- schema
def load_schema():
    return json.load(open(SCHEMA, encoding="utf-8"))


def load_layer_rules():
    return json.load(open(LAYERS, encoding="utf-8"))


def type_ok(value, spec):
    t = spec.get("type")
    if t == "string":
        return isinstance(value, str)
    if t == "array":
        return isinstance(value, list)
    if t == "object":
        return isinstance(value, dict)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def check_value(value, spec, path, errors):
    """The subset of JSON Schema this contract uses: type, enum, required, lengths,
    items, pattern, additionalProperties."""
    if not type_ok(value, spec):
        errors.append(f"{path}: expected {spec.get('type')}, got {type(value).__name__}")
        return
    if "enum" in spec and value not in spec["enum"]:
        errors.append(f"{path}: {value!r} is not one of {spec['enum']}")
    if isinstance(value, str):
        if "minLength" in spec and len(value) < spec["minLength"]:
            errors.append(f"{path}: {len(value)} chars, minimum {spec['minLength']}")
        if "maxLength" in spec and len(value) > spec["maxLength"]:
            errors.append(f"{path}: {len(value)} chars, maximum {spec['maxLength']}")
        if "pattern" in spec and not re.match(spec["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {spec['pattern']}")
    if isinstance(value, list):
        if "minItems" in spec and len(value) < spec["minItems"]:
            errors.append(f"{path}: {len(value)} items, minimum {spec['minItems']}")
        item_spec = spec.get("items")
        if item_spec:
            for i, item in enumerate(value):
                check_value(item, item_spec, f"{path}[{i}]", errors)
    if isinstance(value, dict):
        for field in spec.get("required", []):
            if field not in value:
                errors.append(f"{path}: missing required field {field!r}")
        props = spec.get("properties", {})
        if spec.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path}: unknown field {key!r}")
        for key, sub in props.items():
            if key in value:
                check_value(value[key], sub, f"{path}.{key}", errors)


# ------------------------------------------------------------------------ registry
def skill_registry():
    """Every skill id this repository actually implements."""
    ids = set()
    for base in ("skills", "systems"):
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, base)):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
            if "SKILL.md" in filenames:
                ids.add(os.path.basename(dirpath))
    return ids


# --------------------------------------------------------------------------- rules
def rule_descriptions(roles, errors, _ctx):
    """R2 — a templated or duplicated description. After 37 entries a reader must
    learn something about the role beyond its name restated."""
    seen = defaultdict(list)
    for r in roles:
        rid = r.get("id", "<no id>")
        mission = (r.get("mission") or "").strip()
        if TEMPLATE_RE.match(mission):
            errors.append(f"{rid}.mission: templated ('{mission}')")
        seen[" ".join(mission.lower().split())].append(rid)
    for text, ids in seen.items():
        if text and len(ids) > 1:
            errors.append(f"duplicate mission across {ids}: {text[:60]!r}")


def rule_handoffs(roles, errors, ctx):
    """R3 — a handoff to a role id that does not exist."""
    known = ctx["ids"]
    for r in roles:
        for target in r.get("handoffs", []) or []:
            if target not in known and target != "user":
                errors.append(f"{r.get('id')}.handoffs: unknown role {target!r}")
        esc = r.get("escalation") or {}
        if esc.get("to") and esc["to"] not in known and esc["to"] != "user":
            errors.append(f"{r.get('id')}.escalation.to: unknown role {esc['to']!r}")
        for inp in r.get("inputs", []) or []:
            src = inp.get("from")
            if src and src not in known and src not in ("user", "orchestrator", "all-layer-1"):
                errors.append(f"{r.get('id')}.inputs: unknown producer {src!r}")


def rule_layering(roles, errors, ctx):
    """R4 and R5 — a role in no layer, a duplicated role, and a layer whose membership
    breaks its own rule."""
    order = ctx["order"]
    by_id = {}
    for r in roles:
        rid = r.get("id", "<no id>")
        if rid in by_id:
            errors.append(f"duplicate role id {rid!r} — a role must appear once")
        by_id[rid] = r
        if r.get("layer") not in order:
            errors.append(f"{rid}.layer: {r.get('layer')!r} is not one of {order}")

    tokens = ctx["tokens"]
    for r in roles:
        rid, layer = r.get("id"), r.get("layer")
        if layer not in order:
            continue
        rights = " ".join(r.get("decision_rights", []) or []).lower()
        judges = any(t in rights for t in tokens)

        # forward-handoffs-only
        for target in r.get("handoffs", []) or []:
            other = by_id.get(target)
            if other and other.get("layer") in order and layer in order:
                if order.index(other["layer"]) < order.index(layer):
                    errors.append(
                        f"{rid} ({layer}) hands off backward to {target} ({other['layer']})")

        if layer == "research" and not (r.get("handoffs") or []):
            errors.append(f"{rid}: research role hands off to nobody, so nothing consumes it")
        if layer == "execution" and judges:
            errors.append(f"{rid}: execution role declares a verdict right, which is layer 3's")
        if layer == "review" and not judges:
            errors.append(f"{rid}: review role declares no verdict right, so it cannot gate")
        if layer == "synthesis":
            if r.get("handoffs"):
                errors.append(f"{rid}: synthesis is terminal but hands off to {r['handoffs']}")
            if (r.get("escalation") or {}).get("to") != "user":
                errors.append(f"{rid}: synthesis must escalate to the user")


def rule_capabilities(roles, errors, ctx):
    """R6 — a capability id that does not resolve, and a role with no coverage at all."""
    known = ctx["skills"]
    for r in roles:
        rid = r.get("id")
        caps = r.get("capabilities") or []
        gaps = r.get("capability_gaps") or []
        for cap in caps:
            if cap not in known:
                errors.append(f"{rid}.capabilities: {cap!r} resolves to no SKILL.md")
        if not caps and not gaps:
            errors.append(
                f"{rid}: no capabilities and no declared gaps — the role is not executable "
                f"and nobody has said what is missing")


def rule_overlap(roles, errors, _ctx):
    """R7 — a same-family pair with no MERGE / DIFFERENTIATE / RETIRE decision."""
    by_family = defaultdict(list)
    for r in roles:
        by_family[r.get("family")].append(r)
    for family, members in by_family.items():
        if len(members) < 2:
            continue
        for r in members:
            decided = {w for o in (r.get("overlap") or []) for w in (o.get("with") or [])}
            missing = [m.get("id") for m in members if m.get("id") != r.get("id")
                       and m.get("id") not in decided]
            if missing:
                errors.append(
                    f"{r.get('id')}: shares family {family!r} with {missing} and records "
                    f"no merge/differentiate/retire decision")


RULES = [
    ("required-fields", "a missing required field, or a malformed value", None),
    ("templated-description", "a templated or duplicated mission", rule_descriptions),
    ("handoff-resolves", "a handoff to a role id that does not exist", rule_handoffs),
    ("layer-membership", "a role in no layer, or a layer breaking its own rule", rule_layering),
    ("capability-resolves", "a capability id that does not resolve", rule_capabilities),
    ("overlap-decided", "a same-family pair with no decision recorded", rule_overlap),
]


def validate(roster, schema, layers, skills):
    errors, gaps = [], []
    ids = {r.get("id") for r in roster if r.get("id")}
    ctx = {"ids": ids, "skills": skills,
           "order": layers["order"], "tokens": layers["verdict_tokens"]}

    for i, role in enumerate(roster):
        check_value(role, schema, role.get("id") or f"role[{i}]", errors)

    for name, label, fn in RULES:
        if fn is not None:
            fn(roster, errors, ctx)

    for r in roster:
        for g in r.get("capability_gaps") or []:
            gaps.append((r.get("id"), g.get("id"), g.get("why", "")))
    return errors, gaps


# ------------------------------------------------------------------------ baseline
def legacy_roles():
    """Parse today's commands/team/roles.md into loose records, for --baseline."""
    if not os.path.isfile(LEGACY):
        return []
    text = open(LEGACY, encoding="utf-8").read()
    roles, current, in_template = [], None, False
    for line in text.split("\n"):
        if line.startswith("<!--"):
            in_template = True
        if line.startswith("-->"):
            in_template = False
        if in_template:
            continue
        heading = re.match(r"^## (.+)$", line)
        if heading:
            if current:
                roles.append(current)
            current = {"name": heading.group(1).strip(), "fields": {}, "prompt": []}
            continue
        if current is None:
            continue
        field = re.match(r"^- \*\*(ID|Seniority|Layer|Category|Domain Tags|When Selected):\*\*\s*(.*)$", line)
        if field:
            current["fields"][field.group(1)] = field.group(2).strip()
        elif not line.startswith("### System Prompt"):
            current["prompt"].append(line)
    if current:
        roles.append(current)
    return [r for r in roles if "ID" in r["fields"]]


def baseline(schema):
    roles = legacy_roles()
    required = schema["required"]
    present = {
        "id": lambda r: r["fields"].get("ID"),
        "name": lambda r: r["name"],
        "layer": lambda r: r["fields"].get("Layer"),
        "category": lambda r: r["fields"].get("Category"),
        "domain_tags": lambda r: r["fields"].get("Domain Tags"),
        "system_prompt": lambda r: "".join(r["prompt"]).strip(),
        "competence": lambda r: r["fields"].get("Seniority"),
        "selection": lambda r: r["fields"].get("When Selected"),
    }
    missing = Counter()
    per_role = []
    for r in roles:
        gaps = [f for f in required if present.get(f, lambda _r: None)(r) in (None, "")]
        gaps += [f for f in required if f not in present]
        per_role.append((r["fields"]["ID"], sorted(set(gaps))))
        missing.update(set(gaps))

    print(f"source      : {os.path.relpath(LEGACY, ROOT)}")
    print(f"roles       : {len(roles)}")
    print(f"schema wants: {len(required)} fields per role")
    print()
    print("fields the current roster has no representation for, and how many roles need them:")
    for field, count in missing.most_common():
        print(f"  {field:20s} {count:2d}/{len(roles)}")
    print()
    print("capability coverage: 0/%d roles reference any skill — the roster has no field for it"
          % len(roles))
    print(f"layer distribution : {dict(Counter(r['fields'].get('Layer') for r in roles))}")
    print(f"distinct prompts   : {len({''.join(r['prompt']).strip() for r in roles})} of {len(roles)}")
    lengths = [len("".join(r["prompt"]).strip()) for r in roles]
    print(f"prompt length      : {min(lengths)}-{max(lengths)} chars")
    print()
    print("sample of what a role is missing today:")
    for rid, gaps in per_role[:3]:
        print(f"  {rid}: {', '.join(gaps)}")
    return 0


# ------------------------------------------------------------------------ self-test
FIXTURES = [
    ("required-fields", {"id": "x-role", "name": "X"},
     "missing required field 'family'"),
    ("templated-description",
     {"id": "x-role", "name": "X", "family": "review", "layer": "review",
      "mission": "X Role for the CoCo cross-functional team pipeline.",
      "selection": "when selected by the router for a task in its domain",
      "does_not_do": ["nothing in particular"], "inputs": [{"artifact": "A", "from": "user"}],
      "outputs": [{"artifact": "B", "acceptance_criteria": ["the artifact is complete"]}],
      "decision_rights": ["may approve the artifact it reviewed"],
      "handoffs": [], "competence": {"level": "8+ years", "meaning": "narrow scope, no approvals"},
      "capabilities": ["no-such-skill"], "escalation": {"to": "user", "when": "always"},
      "system_prompt": "x" * 300},
     "templated"),
    ("handoff-resolves",
     {"id": "x-role", "name": "X", "family": "review", "layer": "review",
      "mission": "Reviews something specific and reports findings with locations.",
      "selection": "when an artifact needs an independent verdict before release",
      "does_not_do": ["write the artifact under review"],
      "inputs": [{"artifact": "A", "from": "user"}],
      "outputs": [{"artifact": "B", "acceptance_criteria": ["a verdict is recorded"]}],
      "decision_rights": ["may approve the artifact it reviewed"],
      "handoffs": ["ghost-role"], "competence": {"level": "8+ years", "meaning": "narrow scope, no approvals"},
      "capabilities": ["local-llm"], "escalation": {"to": "user", "when": "always"},
      "system_prompt": "x" * 300},
     "unknown role"),
    ("layer-membership",
     {"id": "x-role", "name": "X", "family": "review", "layer": "execution",
      "mission": "Builds the artifact and also approves it, which layer 2 forbids.",
      "selection": "when the router needs the artifact built for a task in its domain",
      "does_not_do": ["nothing in particular"],
      "inputs": [{"artifact": "A", "from": "user"}],
      "outputs": [{"artifact": "B", "acceptance_criteria": ["the artifact is complete"]}],
      "decision_rights": ["may approve its own output"],
      "handoffs": [], "competence": {"level": "8+ years", "meaning": "narrow scope, no approvals"},
      "capabilities": ["local-llm"], "escalation": {"to": "user", "when": "always"},
      "system_prompt": "x" * 300},
     "execution role declares a verdict right"),
    ("capability-resolves",
     {"id": "x-role", "name": "X", "family": "review", "layer": "review",
      "mission": "Reviews something specific and reports findings with locations.",
      "selection": "when an artifact needs an independent verdict before release",
      "does_not_do": ["write the artifact under review"],
      "inputs": [{"artifact": "A", "from": "user"}],
      "outputs": [{"artifact": "B", "acceptance_criteria": ["a verdict is recorded"]}],
      "decision_rights": ["may approve the artifact it reviewed"],
      "handoffs": [], "competence": {"level": "8+ years", "meaning": "narrow scope, no approvals"},
      "capabilities": ["not-a-real-skill"], "escalation": {"to": "user", "when": "always"},
      "system_prompt": "x" * 300},
     "resolves to no SKILL.md"),
    ("overlap-decided",
     [{"id": "a-role", "name": "A", "family": "review", "layer": "review",
       "mission": "Reviews prose for structure and completeness and issues a verdict.",
       "selection": "when a document needs an independent structural verdict",
       "does_not_do": ["rewrite the document"], "inputs": [{"artifact": "A", "from": "user"}],
       "outputs": [{"artifact": "B", "acceptance_criteria": ["a verdict is recorded"]}],
       "decision_rights": ["may approve the artifact it reviewed"], "handoffs": [],
       "competence": {"level": "8+ years", "meaning": "narrow scope, no approvals"},
       "capabilities": ["local-llm"], "escalation": {"to": "user", "when": "always"},
       "system_prompt": "x" * 300},
      {"id": "b-role", "name": "B", "family": "review", "layer": "review",
       "mission": "Checks grammar and style and never gates a release on its own.",
       "selection": "when a document needs surface correction before publication",
       "does_not_do": ["gate a release"], "inputs": [{"artifact": "A", "from": "user"}],
       "outputs": [{"artifact": "C", "acceptance_criteria": ["a verdict is recorded"]}],
       "decision_rights": ["may approve the artifact it reviewed"], "handoffs": [],
       "competence": {"level": "8+ years", "meaning": "narrow scope, no approvals"},
       "capabilities": ["local-llm"], "escalation": {"to": "user", "when": "always"},
       "overlap": [{"with": ["b-role"], "decision": "differentiate",
                    "rule": "a-role gates on structure, b-role only on surface correctness"}],
       "system_prompt": "x" * 300}],
     "records no merge/differentiate/retire decision"),
]


def self_test(schema, layers):
    skills = skill_registry()
    ok = True
    for name, fixture, expect in FIXTURES:
        roster = fixture if isinstance(fixture, list) else [fixture]
        errors, _ = validate(roster, schema, layers, skills)
        hit = any(expect in e for e in errors)
        print(f"  {'PASS' if hit else 'FAIL'}  {name:22s} -> expects {expect!r}")
        if not hit:
            ok = False
            for e in errors:
                print(f"          got: {e}")
    print()
    print(f"{len(FIXTURES)} rule-fires cases: {'all fire' if ok else 'SOME DID NOT FIRE'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Validate the SI Team Role roster.")
    ap.add_argument("--baseline", action="store_true",
                    help="report today's commands/team/roles.md against the schema")
    ap.add_argument("--self-test", action="store_true",
                    help="prove every validation rule fires on a known-bad fixture")
    ap.add_argument("--roster", default=ROSTER)
    args = ap.parse_args()

    schema, layers = load_schema(), load_layer_rules()

    if args.baseline:
        return baseline(schema)
    if args.self_test:
        return self_test(schema, layers)

    if not os.path.isfile(args.roster):
        print(f"no roster at {args.roster}", file=sys.stderr)
        return 2
    roster = yaml.safe_load(open(args.roster, encoding="utf-8"))
    if isinstance(roster, dict):
        roster = roster.get("roles", [])
    errors, gaps = validate(roster, schema, layers, skill_registry())

    print(f"roster : {os.path.relpath(args.roster, ROOT)}")
    print(f"roles  : {len(roster)}")
    covered = sum(1 for r in roster if r.get("capabilities"))
    print(f"capability coverage: {covered}/{len(roster)} roles")
    print()
    if gaps:
        print(f"declared capability gaps ({len(gaps)}):")
        for rid, gid, why in gaps:
            print(f"  {rid:22s} needs {gid:26s} {why[:60]}")
        print()
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"OK — {len(roster)} roles valid, {len(gaps)} capability gap(s) declared.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
