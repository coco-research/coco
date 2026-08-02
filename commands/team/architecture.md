# Architecture Conformance Protocol

> **Purpose:** One canonical definition of what "follows the architecture",
> "component X owns Y", and "no boundary violations" mean inside the `/team`
> pipeline. Referenced by `team:arch.md`, `team:verify.md`, `team:develop.md`,
> `team:reanalyse.md`, `team:fix.md`, `team:plan.md`, and `team:ship.md`. Whenever
> any of those pipelines makes an architectural claim, it must follow this protocol
> and produce the `.arch/ARCH-EVIDENCE.md` artifact described below.
>
> **Guiding principle — Paths or it does not exist.** Every architectural claim must
> be backed by a captured validator invocation and its exit code. A component that
> claims a path which does not resolve on disk is a defect, not a plan. Any claim
> without matching evidence is deleted from the deliverable or blocks the pull
> request.

This protocol exists because a pipeline can satisfy every requirement identifier and
every test gate while having silently abandoned the module boundaries it was built
against. Tests do not fail when a component is relocated, merged into another, or
deleted outright — they fail only when behaviour changes. Nothing in the four
existing `verify` failure modes can detect structural abandonment, because all four
are test-evidence traps. The steps below remove that blind spot, and only that one.

This protocol is also written against a specific upstream failure. The design it
draws on stated its path-matching rule emphatically, in prose, with a validation
checklist of unchecked boxes, and then never verified a single path in roughly
thirteen hundred lines of code. The lesson taken from that is structural rather than
rhetorical: **every rule in this document either maps to a numbered check in a
script, or is listed in "What is not mechanically enforced" below.** There is no
third category, and a rule that cannot be pointed at a check must be deleted from
this file rather than left to be narrated.

---

## The protocol

### 1. Determine the authoritative artifact

The authoritative artifact is `.arch/index.json` at the commit recorded in
`.arch/pinned-commit`. It is never a prose restatement of the architecture, never a
diagram, and never a subagent's summary of what the components are. `.arch/INDEX.md`
is a rendering for humans; if the two disagree, the JSON wins and `INDEX.md` must be
regenerated.

If `.arch/index.json` does not exist, this protocol does not apply and no
architectural claim may be made. Run `/team arch build` first, or state plainly that
the run has no architectural baseline.

### 2. Establish currency

Compare `pinnedCommit` in the index to `git rev-parse HEAD`.

- Equal — the index is `CURRENT` and conformance claims may rest on it.
- Different — the index is `STALE`. Run `/team arch drift` to reconcile it. Until
  that reconciliation completes and the validator exits zero, every conformance claim
  is `UNVERIFIED`, not clean. A stale index trusted as fact produces confidently
  wrong verdicts, which is worse than having no index at all.

The validator does not perform this comparison. It is the caller's responsibility,
and it is the single largest correctness risk in this protocol.

**The baseline convention.** A pipeline that records the pin *before* it changes anything
and checks *after* is a different case, and the rule above would misread it. There the pin
is expected to be behind HEAD by the end, and `git diff <pin>..HEAD` is precisely the set
of changes that pipeline made, which is what makes any drift attributable to it rather than
to unrelated history. `team:ship.md` works this way: it captures currency at Stage 1 and
evaluates its gate after Stage 6. Under this convention `STALE` means the pin was already
behind HEAD *at capture time*, never at check time. State which convention a run is using
and do not mix them.

### 3. Run and capture

Execute the validator and capture its command line, exit code, and per-check results:

```bash
python3 skills/arch-index/scripts/validate_index.py .arch/index.json --repo-root .
```

For a drift assessment, additionally execute the deterministic scan, which makes no
model calls:

```bash
python3 skills/arch-index/scripts/arch_drift.py --repo-root .
```

The orchestrator runs these commands and captures the output itself. A subagent's
prose summary ("the architecture is being followed") is not a substitute for a
captured exit code. Violation lines print to standard output, one per violation; the
per-check summary table prints to standard error.

### 4. Apply the pass rules

These rules are absolute — they are the definition of architectural conformance.
Each one names the check that enforces it.

- Any failed validator check is a **BLOCK.** (checks 1 through 12)
- A component with no primary paths is a **BLOCK.** (check 4)
- A primary path that does not resolve on disk is a **BLOCK.** (check 5)
- A shared path that does not resolve on disk is a **BLOCK.** (check 6)
- A one-directional or dangling connection is a **BLOCK.** (check 8)
- A wishful or aspirational component title is a **BLOCK.** (check 10) The index is
  reverse-only; it describes what exists.
- A validator that cannot be executed is a **BLOCK, never a pass.** (check 0) There
  is no prose fallback. A fallback that an agent can narrate is precisely the failure
  mode this gate exists to remove.
- An index whose pin is behind HEAD is **STALE**, and drift must be reconciled before
  any conformance claim. (step 2, caller-enforced)
- Drift detected but not reconciled is **UNVERIFIED, never a pass.**
  (`arch_drift.py` gate, caller-enforced)
- A component with zero surviving primary paths is a **BLOCK.** (`arch_drift.py`
  verdict `REMOVE`)
- An index built from a truncated file tree may not be used for drift reconciliation
  at all. (`ecosystem.treeTruncated`) Deletion-first reconciliation treats the tree as
  the source of truth, so reconciling against a partial tree deletes components whose
  code is merely unseen.

### 5. Write `.arch/ARCH-EVIDENCE.md`

Write the artifact using the template below. This file is the single source of truth
for every architectural claim that reaches a deliverable, a review summary, or a pull
request body.

---

## `.arch/ARCH-EVIDENCE.md` template

```markdown
# Architecture Index Evidence — <branch> — <ISO timestamp>

## Pin
- index pinnedCommit: <sha>
- git rev-parse HEAD:  <sha>
- currency: CURRENT | STALE

## Gate: validate (`python3 skills/arch-index/scripts/validate_index.py .arch/index.json --repo-root .`)
exit: 0

| # | Check | Result | Detail |
|---|-------|--------|--------|
| 1 | schemaVersion known | PASS | 1.0 |
| ... | ... | ... | ... |

paths verified: <n> | paths missing: <n> | untracked-but-present: <n>

## Gate: drift (`python3 skills/arch-index/scripts/arch_drift.py --repo-root .`)
gate: NONE | INCREMENTAL | FULL_REBUILD
files changed since pin: <n> | lines changed: <n>

| Component | Verdict | Surviving | Dead |
|---|---|---|---|
| <id> | KEEP | <paths> | — |

unclaimed added files: <n>

## Scope limit
Structural drift only. Semantic drift — a datastore swapped inside an
already-claimed directory, a rewritten component, a violated boundary entirely
within claimed paths — is NOT detected by this gate.
```

---

## Claim rule

Every architectural claim in a deliverable, a pull-request body, or a review summary
— "follows the architecture", "component X owns Y", "no boundary violations",
"respects module boundaries", "architecturally sound" — must correspond to an entry
in `.arch/ARCH-EVIDENCE.md`. If it does not, **delete the claim.**

A `NO DRIFT` result licenses exactly one sentence: that no structural drift was
found. It does not license "the architecture is intact", "the build follows the
design", or any statement about quality, coupling, or correctness.

---

## What is not mechanically enforced

Listed here rather than left implicit, because a gate that overstates its reach is
worse than one that does not exist.

**Semantic drift.** The scan sees structural facts only. A commit that swaps a
component's datastore, rewrites it end to end, or violates a declared boundary
entirely inside already-claimed paths returns `NO DRIFT`. This is a labelling
mitigation, not a technical one: the words "structural drift only" appear in
`ARCH-EVIDENCE.md`, in `INDEX.md`, and in this file, and no consumer may drop them.

**Currency.** Step 2 is caller-enforced. No script compares the pin to HEAD.

**Whether the decomposition is good.** Checks 10 and 11 catch two mechanical naming
failures. Whether components carve the system at sensible joints, whether coupling is
reasonable, and whether a title is too vague are Layer 3 review judgements made by
`architecture-reviewer`, and they carry no exit code.

**Work allocation.** The index is at C4-Container altitude and a single component may
own thousands of files. It is a conformance and triage aid. It is **not** a mechanism
for dividing files among parallel agents, and no consumer derives file ownership from
it.

**Read budgets.** The tool-frugality protocol in `arch-index` bounds how many files
the exploration stage may read. There is no transcript API and no way to count a
subagent's tool calls from outside it, so that budget is prose-enforced. It is stated
as guidance and never reported as a verified constraint.

---

## Hard gate semantics (shared by all pipelines)

- **BLOCK is real.** A failed gate stops the pipeline and loops back for a fix
  (bounded to a maximum of 3 rounds). It is never advisory.
- **Stale ≠ current.** An index behind HEAD is `UNVERIFIED` until reconciled, never
  clean.
- **Paths or it does not exist.** No matching `.arch/ARCH-EVIDENCE.md` entry → the
  claim is deleted.
- **A validator that cannot run is a BLOCK.** Never a pass, and never satisfied by
  narration.

---

## Attribution

The deletion-first reconciliation algorithm and the component anti-pattern list are
adapted from devildev by lak7 (Apache-2.0), <https://github.com/lak7/devildev>,
principally `prompts/ReverseArchitecture.ts`. The exact-path-matching rule is
upstream's; its implementation as a process exit code is not, because upstream never
verified a path. See `skills/arch-index/references/schema.md` for the full
modification notice required by Apache-2.0 § 4(b).
