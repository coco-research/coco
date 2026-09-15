# Architecture Index Evidence — work/169 — 2026-09-15T14:59:47Z

## Pin
- index pinnedCommit: 6a22fe8a72bcb848263385f80a6bd22089fe9173
- git rev-parse HEAD:  6a22fe8a72bcb848263385f80a6bd22089fe9173
- currency: CURRENT

This rebuild resolves a merge conflict rather than a stale pin. Two branches had
each independently rebuilt `.arch/index.json` against the same upstream commit,
`992abf3489adf5bb229b17a4a3036cd1690795f5`, with different generated text and,
on one side, a missing trailing newline in `pinned-commit`. Both were discarded
in favor of a fresh synthesis against the fully merged tree, per the FULL_REBUILD
gate below, rather than hand-merging either side's JSON.

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
gate: FULL_REBUILD (computed against the prior shared pin, 992abf3489adf5bb229b17a4a3036cd1690795f5)
files changed since pin: 552 | lines changed: 46670

| Component | Verdict | Surviving | Dead |
|---|---|---|---|
| skill-library | KEEP | skills | — |
| command-surface | KEEP | commands | — |
| system-bundles | KEEP | systems | — |
| agent-roster | KEEP | agents, rules | — |
| install-adapters | KEEP | adapters, bin, Formula, install.sh | — |

unclaimed added files: 40
unclaimed top-level directories: .arch, .github, assets, docs, mcps, scripts, tests

Every component survived reconciliation at FULL_REBUILD scale, so no identifier
changed and no component was pruned; the scale-up was entirely growth inside
already-claimed directories (ten new adapters under `adapters/`, seven new
Super Intelligence departments under `systems/superintelligence/`, and their
personas/registries) rather than a new architectural shape. The unclaimed
top-level directories are excluded by the runtime-only rule rather than
overlooked: `assets/` is site media, `docs/` is the generated catalog,
`scripts/` and `.github/` are build and CI tooling, `tests/` is the test suite,
`mcps/` is reference documentation cataloguing MCP connectors rather than
runtime code, and `.arch/` is this artifact.

## Tree
depth used: 4 | files seen: 819 | truncated: False

## Scope limit
Structural drift only. Semantic drift — a datastore swapped inside an already-claimed
directory, a component rewritten end to end, a boundary violated entirely within
claimed paths — is NOT detected by this gate. A `NO DRIFT` result means no structural
drift was found, and licenses no broader claim.

Read budgets are prose-enforced and are NOT verified here; there is no way to count a
subagent's tool calls from outside it.
