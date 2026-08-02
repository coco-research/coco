# The architecture index contract

This document defines the schema of `.arch/index.json` and the twelve checks that
`scripts/validate_index.py` enforces against it. The validator is the authority: if a
rule appears in this document but not as a numbered check in the script, the rule is
not enforced, and this document must say so explicitly rather than implying otherwise.

## What the index is, and what it is not

The index is a reverse-engineered, commit-pinned map from each architectural component
of a repository to the real directories and files that implement it. It describes what
exists. It is not a design document, not a specification for future work, and not a
work-assignment manifest.

Two consequences follow from that, and both are enforced.

The index is **reverse-only**. There is no mode in which a component may describe code
that has not been written yet, because the validator's central check is that every
claimed path resolves on disk. A component whose paths do not exist is a defect, not a
plan. Forward-looking design work belongs in `/team think`, the `SI-*-Design` councils,
or `/util:create-architecture-documentation`.

The index is at **C4-Container altitude**, which is coarser than the altitude at which
work is sharded among agents. A component may legitimately own a directory containing
a thousand files. Consumers must therefore treat the index as a conformance and triage
aid, never as a mechanism for dividing work between parallel agents. The `notes` field
carries this caveat so that a future reader cannot mistake the artifact's purpose.

## Top-level shape

| Field | Type | Required | Meaning |
|---|---|---|---|
| `schemaVersion` | string | Yes | Contract version. Only `"1.0"` is currently known. |
| `pinnedCommit` | string | Yes | The full commit SHA the index describes. Advanced only after the validator exits zero. |
| `generatedAt` | string | Yes | ISO 8601 timestamp of generation. |
| `source` | string | Yes | Where the structural facts came from: `gsd-codebase-map`, `gitnexus`, `crawl`, or `fixture`. |
| `ecosystem` | object | Yes | Detected manifest, languages, framework, and the tree parameters actually used. |
| `components` | array | Yes | Three to eight components. See below. |
| `connectionLabels` | object | No | Maps `<id>-to-<id>` keys to a short edge label. |
| `notes` | string | No | Free text. Carries the altitude caveat. |

The `ecosystem.treeTruncated` flag matters more than its size suggests. When the file
tree fed to generation was truncated, the index was built from a partial view, and
drift reconciliation must refuse to run against it — deletion-first reconciliation
treats the tree as the source of truth, so a partial tree would delete components whose
code is merely unseen. This is the specific failure the upstream project captured as a
flag and then never read.

## Component shape

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | Yes | Stable kebab-case identifier. Survives across rebuilds. |
| `title` | string | Yes | `[Business Function] + [Implementation Context]`. |
| `purpose` | string | Yes | What the component delivers, in one or two full sentences. |
| `connections` | array of id | Yes | Other components it relates to. Must be symmetric. |
| `codeOwnership` | object | Yes | The `primary` tier is required; `shared` is optional. |

Each `codeOwnership` tier carries `directories` (array), `files` (array), and
`rationale` (non-empty string). The `primary` tier means *this code is the component*.
The `shared` tier means *this code is used by the component and by others*. There is
deliberately no third tier and no numeric confidence value, because nothing in this
system reads either one; the tier names are load-bearing only because whether a
disappearing path kills a component depends on which tier claimed it.

## Naming discipline

The title formula is `[Business Function] + [Implementation Context]`, and it bans
failure in both directions at once. A title that is too technical names a framework or
a file class rather than a capability: `Next.js App Router` and `Static Assets` are
both wrong. A title that is too vague names an entire business rather than a component:
`Customer System` and `Data Platform` are both wrong. `Agent Skill Library` and
`Editor Install Adapters` are right, because each names a capability and the shape of
its implementation.

Check 10 enforces the aspirational half of this mechanically by rejecting titles
containing words such as `recommended`, `proposed`, `planned`, or `missing`. Check 11
rejects titles that name pure infrastructure or pure file classes. The remaining
calibration — whether a title is too vague — is a judgement the review layer makes, and
no check enforces it.

## Component count

Three to eight, enforced by check 2. Fewer than three means the decomposition collapsed
into an unhelpful monolith. More than eight means the index has descended below
container altitude and is describing modules. A monorepo with dozens of packages does
not fit this ladder; the eventual answer is one index per workspace package plus a root
index whose components are the packages, and that is out of scope for version 1.0.

## Path resolution

A claimed path resolves when git tracks it or when it exists on disk. For a directory,
"git tracks it" means git tracks at least one file beneath it, because `git ls-files`
lists files only and directory claims are therefore matched by prefix.

The on-disk condition is a deliberate hole. A generated or gitignored directory that is
genuinely part of the running system will pass on that condition alone, so the validator
counts those separately and reports them as `untracked-but-present`. The hole stays
visible rather than silent.

## The twelve checks

| # | Check | Fails when |
|---|---|---|
| 1 | `schemaVersion` known | The version is absent or not `"1.0"` |
| 2 | Component count in 3..8 | Fewer than three or more than eight components |
| 3 | Ids unique and kebab-case | An id repeats, or does not match `^[a-z0-9]+(-[a-z0-9]+)*$` |
| 4 | Every component has primary paths | `codeOwnership.primary` declares no directories and no files |
| 5 | Every primary path resolves | A primary directory or file does not resolve |
| 6 | Every shared path resolves | A shared directory or file does not resolve |
| 7 | No orphan components | A component declares no connections while others exist |
| 8 | Connections bidirectional | An edge is one-directional, or points at an unknown id |
| 9 | `connectionLabels` keys resolve | A label key is malformed or names an edge that does not exist |
| 10 | No wishful titles | A title contains an aspirational word |
| 11 | No pure-infrastructure titles | A title names files or infrastructure rather than a capability |
| 12 | Every rationale non-empty | A declared ownership tier has a blank rationale |

Check 0 is implicit: an index that cannot be read or parsed is reported as a violation
and exits non-zero, because a validator that cannot run must never be interpreted as a
pass.

## What the validator does NOT check

These rules are real, and they are enforced by the caller rather than by the script.
Any document that claims the validator enforces them is wrong.

**Currency.** The script does not compare `pinnedCommit` to `git rev-parse HEAD`. An
index can be internally valid and three weeks stale at the same time. The currency
comparison is the caller's responsibility and is defined in `team:architecture.md`.

**Semantic drift.** The script sees structural facts only. A commit that swaps a
component's datastore, rewrites it end to end, or violates a declared boundary entirely
inside already-claimed paths produces no violation. The gate is narrower than the phrase
"architecture drift" suggests, and every artifact it writes says so in those words.

**Whether the decomposition is any good.** Checks 10 and 11 catch two mechanical naming
failures. Whether the components carve the system at sensible joints, whether coupling
is reasonable, and whether a component is wishful in substance rather than in wording
are review-layer judgements.

## Fixtures

Three fixtures under `scripts/fixtures/` pin the validator's behaviour, and
`scripts/run_fixtures.sh` asserts all three.

| Fixture | Expected |
|---|---|
| `good.json` | Exit 0, zero violations, nine paths verified against this repository |
| `bad-paths.json` | Exit 1, naming `src/nonexistent` and `src/nonexistent/handler.py` |
| `bad-invariants.json` | Exit 1 with exactly four violation lines: checks 2, 7, 8, and 10 |

## Attribution

The component-to-code ownership taxonomy, the component-count ladder, and the two-sided
naming formula are adapted from devildev by lak7 (Apache-2.0),
<https://github.com/lak7/devildev>, principally `prompts/ReverseArchitecture.ts`.

Modifications, per Apache-2.0 § 4(b): numeric confidence bands were removed because
nothing consumes them; the third ownership tier was removed for the same reason; all
presentation fields (`icon`, `color`, `borderColor`, `position`) were removed because
upstream overrides them from a hardcoded palette immediately after the model invents
them; and the exact-path-matching instruction was promoted from prose into checks 5 and
6 with a process exit code, because upstream stated the rule emphatically and never
verified a single path.
