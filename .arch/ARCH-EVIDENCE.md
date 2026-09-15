# Architecture Index Evidence — chore/self-hosted-ci-main — 2026-09-04T00:00:00Z

## Pin
- index pinnedCommit: 992abf3489adf5bb229b17a4a3036cd1690795f5
- git rev-parse HEAD:  992abf3489adf5bb229b17a4a3036cd1690795f5
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
| 8 | connections bidirectional | PASS | 8 edges symmetric |
| 9 | connectionLabels keys resolve to real edges | PASS | 8/8 |
| 10 | no negative or wishful titles | PASS | 0 matches |
| 11 | no pure-infrastructure titles | PASS | 0 matches |
| 12 | every rationale non-empty | PASS | 6/6 |

paths verified: 10 | paths missing: 0 | untracked-but-present: 0

## Gate: drift (`python3 skills/arch-index/scripts/arch_drift.py --repo-root .`)
gate: FULL_REBUILD
files changed since pin: 533 | lines changed: 65521

| Component | Verdict | Surviving | Dead |
|---|---|---|---|
| (rebuild triggered — no per-component verdicts) | — | — | — |

unclaimed added files: 26
unclaimed top-level directories: (see DRIFT.json)

## Tree
depth used: 4 | files seen: 728 | truncated: false

## Scope limit
Structural drift only. Semantic drift — a datastore swapped inside an already-claimed
directory, a component rewritten end to end, a boundary violated entirely within
claimed paths — is NOT detected by this gate. A `NO DRIFT` result means no structural
drift was found, and licenses no broader claim.

Read budgets are prose-enforced and are NOT verified here; there is no way to count a
subagent's tool calls from outside it.