---
name: arch-index
description: "Build and validate .arch/index.json — a committed map from each architectural component of this repository to the real directories and files that implement it, pinned to a git commit, with every path verified to exist. Also detects structural drift between that index and the current code. Use when asked to map a codebase, produce a component or code-ownership index, find which files implement a component, check whether architecture docs are stale, or detect architecture drift after a refactor. Triggers include 'map the codebase', 'component index', 'which files implement X', 'is the architecture still accurate', 'architecture drift', 'refresh the architecture index'."
domain: engineering
version: 1.0.0
---

# arch-index

Produces one artifact: `.arch/index.json`, a commit-pinned map from each architectural
component of a repository to the real directories and files that implement it. Every
claimed path is verified to exist by a script with an exit code, not by a promise in a
prompt.

**Guiding principle — Paths or it does not exist.** The protocol that consumers follow
is `team:architecture.md`. This file is the producer.

## What this skill is for, and what it is not for

It is for answering, mechanically: which files implement this component, and has that
stopped being true.

It is not a design tool. The index is **reverse-only** — it describes code that exists
on disk at a known commit. There is no mode for specifying a system that has not been
built, because the central check is that every path resolves. Forward design work
belongs in `/team think`, the `SI-*-Design` councils, or
`/util:create-architecture-documentation`.

It is not a codebase-mapping tool either, and it should not act like one. When
`.planning/codebase/` exists, `gsd-map-codebase` has already produced seven structured
documents covering the stack, integrations, architecture, structure, conventions,
testing, and concerns. This skill **reads those and skips crawling entirely.** Crawling
a repository that has already been mapped is the exact waste this skill was designed to
avoid, and duplicating `gsd-map-codebase` would make it a worse version of a tool that
already exists.

It is not a work-allocation mechanism. The index sits at C4-Container altitude, so a
single component can own thousands of files. Nothing derives per-agent file ownership
from it.

## Modes

Resolve the mode from the invocation. When none is given, use `drift` if
`.arch/pinned-commit` exists and `build` if it does not.

### `build`

**Step 1 — find prior art before doing any work.** In this order:

1. If `.planning/codebase/` exists, read `ARCHITECTURE.md`, `STRUCTURE.md`,
   `STACK.md`, and `INTEGRATIONS.md` from it. Set `source` to `gsd-codebase-map`. Skip
   to step 2. Do not crawl.
2. Otherwise, if gitnexus is available for this repository, call
   `mcp__gitnexus__context` and `mcp__gitnexus__group_list` for a deterministic view of
   module grouping. Set `source` to `gitnexus`. Skip to step 2.

   A gitnexus index that is behind HEAD is still usable here, and `list_repos` reports
   exactly how far behind it is. Record that number in `ecosystem.sourceCommitsBehind`.
   The reason staleness is tolerable is structural rather than optimistic: gitnexus
   informs *component grouping*, while every path the index claims is checked by the
   validator against the working tree. A path that moved since gitnexus was indexed
   fails check 5 and blocks the build. Stale grouping advice can therefore make the
   decomposition slightly dated, but it cannot introduce a path that does not exist.
   Still run `scripts/repo_tree.py` for the authoritative current tree.
3. Otherwise crawl. Run `scripts/repo_tree.py --repo-root .` for a filtered,
   depth-adaptive tree, then perform one exploration pass under
   `references/tool-frugality.md`, writing `.arch/ANALYSIS.md` against the seven-section
   skeleton in `references/analysis-taxonomy.md` under its ten-thousand-character cap.
   Set `source` to `crawl`.

If the tree came back truncated, say so at the top of the analysis and set
`ecosystem.treeTruncated` to `true` in the index. A truncated tree disables `drift`
mode entirely, by design.

**Step 2 — synthesise, with no tool use.** Read only the gathered summary plus the
tree. Emit `.arch/index.json` per `references/schema.md`, bound by
`references/component-rules.md`. This stage does not explore; separating exploration
from formatting is why the structured output stays in schema.

**Step 3 — validate.**

```bash
python3 skills/arch-index/scripts/validate_index.py .arch/index.json --repo-root .
```

Exit zero proceeds. Non-zero loops back to step 2 with the exact violation lines,
bounded to three rounds, then stops and reports the remaining violations. **If the
validator cannot be executed at all, that is a BLOCK, not a pass** — there is no prose
fallback, because a fallback an agent can narrate is the failure this gate exists to
remove.

**Step 4 — write the derived artifacts,** using `templates/`. Write
`.arch/ARCH-EVIDENCE.md` capturing the command, the exit code, and the per-check table.
Write `.arch/INDEX.md` for humans. Emit the Mermaid `C4Container` source and render it
through `design:mermaid` (beautiful-mermaid), never the standard Mermaid CDN.

**Step 5 — advance the pin.** Write `git rev-parse HEAD` to `.arch/pinned-commit`
**only after the validator has exited zero.** A failed run leaves the previous pin
untouched, so a broken index can never present itself as current.

### `drift`

**Deterministic first, and often only.**

```bash
python3 skills/arch-index/scripts/arch_drift.py --repo-root .
```

The script reads the pin, diffs it against HEAD with `--name-status` and `--numstat`,
tests every primary path, and writes `.arch/DRIFT.json` with a per-component verdict of
`REMOVE`, `PRUNE`, or `KEEP`, plus the files added outside every claimed path. It
resolves the gate itself:

| Gate | Meaning | What to do |
|---|---|---|
| `NONE` | Every verdict is `KEEP` and nothing unclaimed was added | Report `NO DRIFT` and stop. **Zero model calls.** |
| `FULL_REBUILD` | More than 300 files or 50,000 lines changed since the pin | A rebuild is cheaper than a patch. Run `build`. |
| `INCREMENTAL` | Anything else | Continue below. |

If the script exits 2, the scan could not run. That is never `NO DRIFT`; report why.

In the `INCREMENTAL` case the model receives `DRIFT.json` as **settled fact** and
answers exactly one open question: do the unclaimed added files constitute a component
that should exist? Apply the verdicts without re-deciding them, preserve surviving
component identifiers, prune connections to removed components, then validate and
advance the pin as in `build` steps 3 through 5.

Never preserve a component whose code is gone. See the deletion-first rule in
`references/component-rules.md`.

### `check`

Runs the validator alone and writes `.arch/ARCH-EVIDENCE.md`. Makes no model calls and
never writes `index.json`. This is what `/team verify` and `/team ship` call.

## Artifacts

| Path | Committed | Notes |
|---|---|---|
| `.arch/index.json` | Yes | The contract. Diffable history is the point. |
| `.arch/pinned-commit` | Yes | Advanced only on validator exit 0. |
| `.arch/INDEX.md` | Yes | Derived; regenerated every build. |
| `.arch/ARCH-EVIDENCE.md` | Yes | The captured gate. |
| `.arch/ANALYSIS.md` | Yes | Fallback path only; cached against the pin. |
| `.arch/DRIFT.json` | No | Derived scratch; gitignored. |

`.arch/` is committed deliberately. An untracked file cannot be diffed across runs, does
not exist in the clean checkout that `/team ship` verifies from, and would be silently
erased by `git clean`, reverting every consumer to a degraded path without saying so.

## Scope limits, stated plainly

**Structural drift only.** A commit that swaps a component's datastore, rewrites it end
to end, or violates a declared boundary entirely inside already-claimed paths returns
`NO DRIFT`. Every artifact carries these words, and no consumer may drop them.

**Currency is caller-enforced.** No script compares the pin to HEAD; the caller does,
per `team:architecture.md` step 2. An index behind HEAD is `STALE`, and claims resting
on it are `UNVERIFIED` rather than clean.

**The read budget is not enforced.** There is no transcript API and no way to count a
subagent's tool calls from outside it. `references/tool-frugality.md` is guidance, and
no artifact reports it as verified.

**Monorepos do not fit.** The three-to-eight ladder forces distinct concerns to merge in
a repository with dozens of packages. One index per workspace package plus a root index
whose components are the packages is the eventual answer, and is out of scope for 1.0.

## Files

| File | Purpose |
|---|---|
| `references/schema.md` | The contract and the twelve checks |
| `references/arch-plan.md` | The forward plan contract, and why declare-then-verify works |
| `references/component-rules.md` | What qualifies, naming, counting, merging |
| `references/tool-frugality.md` | The read budget for the fallback crawl |
| `references/analysis-taxonomy.md` | The seven-section exploration skeleton |
| `scripts/validate_index.py` | The gate. Twelve checks, stdlib only, exit 0 or 1 |
| `scripts/arch_drift.py` | Deterministic drift scan. Zero model calls |
| `scripts/verify_arch_plan.py` | Forward plan: `--declare` before a build, `--verify` after |
| `scripts/repo_tree.py` | Filtered, depth-adaptive tree |
| `scripts/run_fixtures.sh` | Regression suite for the validator |
| `templates/` | `INDEX.md` and `ARCH-EVIDENCE.md` skeletons |

Regression gate for any change to the validator:

```bash
bash skills/arch-index/scripts/run_fixtures.sh
```

## Attribution

The design this skill implements is adapted from **devildev** by lak7, licensed
**Apache-2.0**, <https://github.com/lak7/devildev>. No upstream source code was copied;
what was taken is prompt text, one schema idea, and four procedures.

| Borrowed | Upstream source |
|---|---|
| Component-to-code ownership taxonomy | `prompts/ReverseArchitecture.ts` |
| Component rules, count ladder, naming and purpose formulas, anti-patterns | `prompts/ReverseArchitecture.ts:278-371`, `:493-507` |
| Deletion-first reconciliation | `prompts/ReverseArchitecture.ts:578-641` |
| Two-stage explore-then-synthesise split | `actions/reverse-architecture.ts:696-805` |
| Tool-frugality read budget | `actions/reverse-architecture.ts:715-749` |
| Seven-section analysis taxonomy and character cap | `actions/reverse-architecture.ts:771-805` |

Per-file modification notices required by Apache-2.0 § 4(b) are recorded at the foot of
each reference file. The most significant modification is that upstream stated its
exact-path-matching rule emphatically in prose, with a validation checklist of unchecked
boxes, and never verified a single path in roughly 1,300 lines of code; here that rule
is `scripts/validate_index.py` checks 5 and 6, with a process exit code. Also not
carried across: all presentation fields, numeric confidence bands, the celebrity-persona
framing, the framework-only admission gate, and the credits economy.
