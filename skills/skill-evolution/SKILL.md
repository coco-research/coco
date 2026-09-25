---
name: skill-evolution
description: "Use when running, reviewing or changing coco's self-evolution cycle: the 30-day loop that observes how skills are actually used, proposes evidence-backed edits to them as one branch and one pull request, and lands nothing without the owner's merge. Also use when asked why a skill changed, what the loop would propose next, or how to reject a proposal so it is not raised again."
domain: meta
---

# Skill Evolution

A cycle that improves this repository's own skills from observed use, and proposes every
change for a human to merge. It never writes to `main` and never merges.

**Status:** the scripts this file documents, `scripts/evolve.py` and the steps it runs, are
not on `main` yet, so the commands below do not run today. They land with plan tasks 2 to 9
in `.metagpt/plan.md`: task 2 `ledger.py` through task 8 `evolve.py`, and task 9
`run_fixtures.sh` with the CI join.

## The one rule

**The loop proposes. The owner decides.** There is no confidence level, budget or green gate
that lets it land a change on its own. This is a design invariant, not a setting: a system
that edits the repository that measures it has no natural stopping point.

## What a cycle does

Five steps, and only the second one calls a model.

| Step | Script | Model? | Output |
| --- | --- | --- | --- |
| 1. Observe | `scripts/observe.py` | no | `signals/<cycle>.json`, pinned to one commit |
| 2. Propose | `scripts/propose.py` | yes, one lane | `proposals/<id>.json` and `proposals/<id>.patch` |
| 3. Validate | `scripts/validate.py` | no | accept or refuse, with a reason |
| 4. Open | `scripts/evolve.py` | no | one branch, one pull request |
| 5. Record | `scripts/ledger.py` | no | a ledger row per event, and `CYCLE.md` |

Run it:

```
python3 scripts/evolve.py run --window 30d            # the real cycle, needs credentials
python3 scripts/evolve.py run --window 30d --dry-run   # stops before opening a branch
python3 scripts/evolve.py run --window 30d --lane stub # no network at all
python3 scripts/evolve.py status                       # last cycle, open proposals
```

## What the guard refuses

`validate.py` is the only thing standing between a model's output and a branch. It refuses,
with the reason named, when any of these hold:

- **Out of scope.** v1 may change a skill's `description` frontmatter, its `references/` and
  its `SKILL.md` prose, and may add or remove example blocks. A persona file, a command file,
  a count file, a workflow or this skill's own scripts are all out of bounds.
- **An unresolvable citation.** Every proposal cites its evidence by file and line, or by
  receipt id, and the citation must resolve at the pinned commit.
- **Over a cap.** Proposals per cycle and diff size per proposal are both capped in
  `references/lanes.json`. A cycle that hits the cap states the remainder rather than
  truncating silently.
- **Already rejected.** A diff whose hash a ledger row rejected inside the two cycle window
  is not proposed again.
- **A count that moved alone.** If a proposal changes a published number, the coupled files
  must move with it, checked by running the repository's own checkers rather than a private
  copy of their rules. See `docs/rules.md` R7.

## Exit codes

Three valued, like every gate in this repository: **0** pass, **1** blocked by a guard,
**2** unrunnable or unmeasured. An empty cycle is exit 0 with nothing to propose, which is a
valid result and not a failure.

## Cost

Every model call goes through `scripts/lane.py`, which reads `references/lanes.json`, checks
the cycle budget **before** spending, obeys the model routing policy, and records the lane id
and token count on the proposal it produced. The expensive review lane refuses unless the
owner has explicitly authorised it for that cycle.

## Where things live

- `references/lanes.json` - the allowed lanes and their budgets.
- `references/proposal-schema.json` - the proposal shape, and the only fields a proposal may carry.
- `references/signal-sources.md` - what `observe.py` reads and what it deliberately does not.
- `state/ledger.jsonl` - the committed ledger. Append only. One record per event, and the
  record of why something was rejected is the part that matters.
- `state/CYCLE.md` - the rendered human artifact for the most recent cycle.

## Testing

`bash scripts/run_fixtures.sh` runs every suite and prints `N/N passed`. Every case uses the
stub lane, so the suite needs no network and no model. CI runs the same command, so a
proposal pipeline that stops working fails the build rather than shipping quietly.

## Changing this skill

Changing the loop's own scripts is out of scope for a loop proposal by design, which means a
change here is an ordinary pull request from a human or an agent working under review. If a
change alters a rule in this file, say so in the PR title and update `docs/rules.md` in the
same commit.
