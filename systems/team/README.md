# Team — Cross-Functional Multi-Agent Pipeline

Opinionated orchestration system for multi-agent workflows: research, plan, build, review, verify, ship.

## `/team` is core — there is nothing to install

**This directory ships no skills, agents or commands**, so `--systems team` installs
nothing and is not a valid bundle flag. Passing it has no effect.

It does hold tooling: the role roster's schema, its source of truth, and the validator
that gates it. None of that is installable, which is why the bundle list still excludes
this directory.

The `/team` commands are part of the core install. Every one of them is present after a plain:

```bash
bash install.sh
```

They live in `commands/team/` at the repository root, and `install.sh` installs the whole
`commands/` tree unconditionally. Nothing about `/team` is opt-in.

If you are looking for the design reasoning behind the pipeline, it is in `specs/`. That is
the only reason this directory still exists.

## What `/team` does

A four-layer role pipeline. Each command selects the appropriate role mix for its stage:

- **L1 — Research** — gather context, surface requirements, extract the spec
- **L2 — Execution** — domain-specific work by engineers, PMs and designers
- **L3 — Review** — audit L2's output for accuracy, standards and evidence
- **L4 — Synthesis** — principal-level verdict and recommended next action

## The role roster

The roster lives here, not in the command file:

| Path | What it is |
|---|---|
| `roles.yaml` | **Source of truth.** 37 roles, one record each. Edit this. |
| `roles.schema.json` | The contract: every field, its type, and the completion test. |
| `layer_rules.json` | The four-layer model, and the rules that decide membership. |
| `validate_roles.py` | One command that fails on a malformed roster or a broken layer rule, and prints declared capability gaps as results rather than failures. |
| `build_roster.py` | Renders [`commands/team/roles.md`](../../commands/team/roles.md) from `roles.yaml`. |
| `MIGRATION.md` | What changes for consumers of the deployed catalogue. |

`commands/team/roles.md` is generated. The router reads it and agents are handed prompt
text out of it, so it stays committed — but CI fails if it disagrees with `roles.yaml`.

```bash
python3 systems/team/validate_roles.py            # validate the roster
python3 systems/team/validate_roles.py --baseline # what today's data is missing
python3 systems/team/validate_roles.py --self-test# prove every rule fires
python3 systems/team/build_roster.py              # re-render the command file
```

Those roles are specific to `/team` and are distinct from both the core agents in
[`agents/`](../../agents/) and the GSD agents in [`systems/gsd/agents/`](../gsd/agents/).

## Commands

All of these are in [`commands/team/`](../../commands/team/) and are installed by default:

| Command | Purpose |
|---|---|
| `/team` | Router and index for every action below |
| `/team arch` | Build, reconcile or validate the architecture index |
| `/team plan` | Produce a phased implementation plan |
| `/team research` | Competitive and technical research brief |
| `/team scrape` | Web research pipeline |
| `/team think` | Architecture options and trade-off analysis |
| `/team develop` | Build the scoped work |
| `/team fix` | Address review findings |
| `/team test` | Author and run tests |
| `/team review` | Specialist review of a plan or a diff |
| `/team verify` | Check what was built against what was specified |
| `/team reanalyse` | Re-examine after a change, including architectural regression |
| `/team document` | Produce or update documentation |
| `/team communicate` | Stakeholder communications |
| `/team present` | Presentation and deck generation |
| `/team ship` | Idea to shipped: 6 stages, 7 test gates, 2 architecture gates |
| `/team toolkit` | Registry of tools available to a run |
| `/team evidence` | The Test Evidence Protocol every gate follows |
| `/team feedback` | Registry of learnings carried between runs |
| `/team roles` | The role roster and its layer assignments |
| `/team architecture` | Architecture conformance protocol reference |

## Gates worth knowing about

`/team ship` and `/team verify` enforce gates that cannot be satisfied by narration, because
each is a script with a real exit code:

- **Test Evidence Protocol** — a skipped test is `UNVERIFIED`, never a pass; coverage must be
  measured rather than asserted; and verification re-runs from a clean checkout rather than
  trusting the builder's summary.
- **Architecture conformance** — structural drift against `.arch/index.json` is failure mode
  `(e)` in `/team verify`.
- **Built as declared** — a component declared at planning time and then quietly dropped is a
  BLOCK, as is a file landing under a path the plan declared out of scope.

## Specs

Design decisions and architecture live in [`specs/`](specs/).
