# Architecture Index Evidence — skills/research-and-brag — 2026-07-31T19:45:00Z

## Pin
- index pinnedCommit: e5c673f3fbe35d86cceb6d2f3811302388b488d1
- git rev-parse HEAD:  e5c673f3fbe35d86cceb6d2f3811302388b488d1
- currency: CURRENT

## Gate: validate (`python3 skills/arch-index/scripts/validate_index.py .arch/index.json --repo-root .`)
exit: 0

| # | Check | Result | Detail |
|---|-------|--------|--------|
| 1 | schemaVersion known | PASS | 1.0 |
| 2 | component count in 3..8 | PASS | 5 |
| 3 | ids unique, kebab-case | PASS | 5 unique of 5 |
| 4 | every component has primary paths | PASS | 5/5 |
| 5 | every primary path resolves on disk | PASS | 9/9 verified |
| 6 | every shared path resolves on disk | PASS | 1/1 verified |
| 7 | no orphan components | PASS | 5/5 connected |
| 8 | connections bidirectional | PASS | 7 edges symmetric |
| 9 | connectionLabels keys resolve to real edges | PASS | 7/7 |
| 10 | no negative or wishful titles | PASS | 0 matches |
| 11 | no pure-infrastructure titles | PASS | 0 matches |
| 12 | every rationale non-empty | PASS | 6/6 |

paths verified: 10 | paths missing: 0 | untracked-but-present: 0

## Gate: drift (`python3 skills/arch-index/scripts/arch_drift.py --repo-root .`)
gate: NONE
files changed since pin: 0 | lines changed: 0

| Component | Verdict | Surviving | Dead |
|---|---|---|---|
| skill-library | KEEP | `skills` | — |
| command-surface | KEEP | `commands` | — |
| system-bundles | KEEP | `systems` | — |
| agent-roster | KEEP | `agents`, `rules` | — |
| install-adapters | KEEP | `adapters`, `bin`, `Formula`, `install.sh` | — |

unclaimed added files: 0
unclaimed top-level directories: none

## Tree
depth used: 4 | files seen: 756 | truncated: false

Depth was chosen by measurement rather than by a fixed cap. At depth 4 this repository
presents 756 files, and at depth 5 it presents 1,403, which exceeds the 1,200-file
budget. Depth 4 is therefore the deepest view that fits.

## Negative controls
Both were executed rather than assumed.

- A fabricated primary path (`deliberately-broken` added to `agent-roster`) produced
  exit 1 naming that exact path, and `.arch/pinned-commit` did **not** advance.
- The validator's own fixture suite passes six of six assertions, including that a
  missing index file reports `CHECK 0` and exits 1 rather than passing silently
  (`bash skills/arch-index/scripts/run_fixtures.sh`).

## Scope limit
Structural drift only. Semantic drift — a datastore swapped inside an already-claimed
directory, a component rewritten end to end, a boundary violated entirely within
claimed paths — is NOT detected by this gate. A `NO DRIFT` result means no structural
drift was found, and licenses no broader claim.

Read budgets are prose-enforced and are NOT verified here; there is no way to count a
subagent's tool calls from outside it.

Currency was compared by hand at step 2 of `team:architecture.md`. No script performs
that comparison.
