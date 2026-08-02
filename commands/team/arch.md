# /team arch — Architecture Index Pipeline

> Called by team.md router when action is `arch`.
> Builds and validates `.arch/index.json`, the commit-pinned map from each
> architectural component to the real files that implement it, and detects when that
> map has stopped being true.
>
> Governed by `team:architecture.md`. **Paths or it does not exist.**

## Usage

```
/team arch [build|drift|check] [scope] [--full] [--roles <ids>]
```

Default subcommand: `drift` when `.arch/pinned-commit` exists, `build` when it does not.
Scope is optional; when given it narrows the analysis to a subtree.

| Subcommand | Purpose |
|---|---|
| `build` | Produce a fresh index from scratch |
| `drift` | Reconcile an existing index against the current tree |
| `check` | Run the validator alone and capture evidence. No model calls, no writes to `index.json`. |

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst; security-analyst if domain includes api/backend/infrastructure; repo-cartographer only on the fallback crawl | 0-2 |
| L2 | solution-architect | 1 |
| L3 | architecture-reviewer, domain-accuracy | 2 |
| L4 | principal-architect | 1 |

Layer 1 is **zero agents** when `.planning/codebase/` exists. That is the intended
common case, not a degradation.

## Pipeline Customization

### Stage 0: Deterministic gate — no agents, runs before pre-flight

This stage exists so that the most common invocation costs nothing.

1. Resolve the subcommand. Record `git rev-parse HEAD` as the pin candidate.
2. Detect the ecosystem from whichever manifest exists: `package.json`,
   `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, `Gemfile`, `*.csproj`.
3. Check for `.planning/codebase/` and for a gitnexus index.
4. For `drift`, run the scan and evaluate its gate:

```bash
python3 skills/arch-index/scripts/arch_drift.py --repo-root .
```

| Gate | Action |
|---|---|
| `NONE` | Report `NO DRIFT — structural only`, write `.arch/ARCH-EVIDENCE.md`, and **end the run here**. No team is created, no agent is spawned. |
| `FULL_REBUILD` | Report that more than 300 files or 50,000 lines changed since the pin, so a rebuild is cheaper than a patch. Re-enter as `build`. |
| `INCREMENTAL` | Continue to pre-flight. |
| exit 2 | The scan could not run. Report why. This is **never** `NO DRIFT`. |

### Layer 1: Structural context (parallel, mode `default`)

**Skipped entirely when `.planning/codebase/` exists.** Read `ARCHITECTURE.md`,
`STRUCTURE.md`, `STACK.md`, and `INTEGRATIONS.md` from there directly and report the
skip. Spawning agents to re-derive a map that `gsd-map-codebase` already wrote is the
exact waste this action was built to remove.

Otherwise, if gitnexus is available, call `mcp__gitnexus__context` and
`mcp__gitnexus__group_list`. Record how many commits behind the index is in
`ecosystem.sourceCommitsBehind`. Stale grouping advice is tolerable here because every
path is checked against the working tree by the validator, so staleness can date the
decomposition but cannot introduce a path that does not exist.

Only if neither exists, spawn `repo-cartographer` under the three-phase read budget in
`skills/arch-index/references/tool-frugality.md`, writing `.arch/ANALYSIS.md` against the
seven-section skeleton in `references/analysis-taxonomy.md`.

Always run `python3 skills/arch-index/scripts/repo_tree.py --repo-root .` for the
authoritative current tree. If it reports truncation, propagate that into
`ecosystem.treeTruncated` and **do not run `drift`** — reconciling against a partial
tree deletes components whose code is merely unseen.

### Layer 2: Synthesis (1 agent, `solution-architect`, mode `bypassPermissions`)

**Writes confined to `.arch/`.** This agent does not touch source files.

No tool use during synthesis. Read only the gathered summary plus the tree, and emit
`.arch/index.json` per `references/schema.md`, bound by `references/component-rules.md`.
Separating exploration from formatting is why the structured output stays in schema.

For `drift`, apply the `DRIFT.json` verdicts as settled fact: `REMOVE` deletes the
component and every connection to it, `PRUNE` drops the dead paths and keeps the
identifier, `KEEP` changes nothing. Preserve surviving identifiers. Then answer the one
open question the script cannot: do the unclaimed added files constitute a component
that should exist?

### Validation gate: deterministic, and a real BLOCK

```bash
python3 skills/arch-index/scripts/validate_index.py .arch/index.json --repo-root .
```

Capture the command line, the exit code, and the per-check table into
`.arch/ARCH-EVIDENCE.md` per the template in `skills/arch-index/templates/`.

Exit 0 proceeds. Non-zero loops back to Layer 2 with the exact violation lines, bounded
to three rounds, then stops and reports what remains. **A validator that cannot be
executed is a BLOCK, not a pass.** There is deliberately no prose fallback here: a
fallback an agent can narrate is the failure mode this gate exists to remove. See
`team:architecture.md`.

### Layer 3: Review (parallel, read-only, mode `default`, 2 agents)

- **architecture-reviewer** — decomposition, coupling, boundary coherence, wishful
  components, vague titles, altitude drift.
- **domain-accuracy** — does each component's described capability match what the code
  at those paths actually does?

Findings use `CRITICAL | MAJOR | MINOR | SUGGESTION` with the component id and a quote,
compressed into `CRITIQUE-SUMMARY.md` at the standard 200-line cap. Any CRITICAL blocks
back to Layer 2.

Neither reviewer may treat a passing validator as evidence that the architecture is
sound. The validator proves the paths exist and the graph is well-formed, and nothing
more.

### Layer 4: Finalise (1 agent, `principal-architect`)

Apply the critique, re-run the validator, write `.arch/INDEX.md` from the template, and
emit the Mermaid `C4Container` source for rendering through `design:mermaid`
(beautiful-mermaid).

**Advance `.arch/pinned-commit` only after the validator exits 0.** A failed run leaves
the previous pin untouched, so a broken index can never present itself as current.

Emit feedback entries in the format at `_index.md`.

## Fast path

`build` is **not** fast-path eligible. An index that skips its review layer is worse
than no index, mirroring the evidence carve-out in the router.

`drift` is fast-path eligible in a stronger sense than any other action: Stage 0 can
complete the entire run with zero agents, and on an unchanged tree it always does.

## Artifacts

All of `.arch/` is committed except `DRIFT.json`, which is derived scratch and
gitignored. The index is only useful if it is diffable across runs and present in the
clean checkout that `team:ship.md` verifies from.

## Scope limit

This action detects **structural** drift: components whose code was deleted, moved, or
never claimed. It does not detect semantic drift, such as a component whose datastore
was swapped inside its own already-claimed directory. Every artifact it writes says so
in those words, and no consumer may drop them.

## GSD Integration

When `.planning/` exists, Layer 1 reads `.planning/codebase/` in preference to crawling,
and `plan.md` may use the index to populate the `files_modified` frontmatter field of
generated phase plans.
