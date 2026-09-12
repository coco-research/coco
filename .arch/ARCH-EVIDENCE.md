# Architecture Index Evidence — chore/arch-index-rebuild — 2026-09-12T04:49:55Z

## Pin
- index pinnedCommit: 992abf3489adf5bb229b17a4a3036cd1690795f5
- git rev-parse HEAD:  992abf3489adf5bb229b17a4a3036cd1690795f5
- currency: CURRENT

This rebuild replaces an index whose two artifacts disagreed with each other and
with HEAD: `index.json` claimed `e5c673f3` (generated 2026-07-31) while
`.arch/pinned-commit` held `3dc71a3`. The drift scan below was taken against
`3dc71a3`, the pin the tree actually carried.

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
gate: FULL_REBUILD
files changed since pin: 533 | lines changed: 65521

| Component | Verdict | Surviving | Dead |
|---|---|---|---|
| skill-library | KEEP | skills | — |
| command-surface | KEEP | commands | — |
| system-bundles | KEEP | systems | — |
| agent-roster | KEEP | agents, rules | — |
| install-adapters | KEEP | adapters, bin, Formula, install.sh | — |

unclaimed added files: 26
unclaimed top-level directories: .arch, assets, coco, docs

Every component survived reconciliation, so no identifier changed. The unclaimed
top-level directories are excluded by the runtime-only rule rather than overlooked:
`assets/` and `coco/` are site media, `docs/` is the generated catalog, `tests/` is
the test suite, and `.arch/` is this artifact.

## Tree
depth used: 4 | files seen: 706 | truncated: False

## Scope limit
Structural drift only. Semantic drift — a datastore swapped inside an already-claimed
directory, a component rewritten end to end, a boundary violated entirely within
claimed paths — is NOT detected by this gate. A `NO DRIFT` result means no structural
drift was found, and licenses no broader claim.

Read budgets are prose-enforced and are NOT verified here; there is no way to count a
subagent's tool calls from outside it.
