# The architecture plan contract

`.team-ship/ARCH-PLAN.json` is the forward counterpart to `.arch/index.json`. The index
records what a repository contains. The plan records what a single ship intends to build
and where it intends to put it, so that the build can be held to it afterwards.

`scripts/verify_arch_plan.py` is the authority. Anything this document asserts that the
script does not check is called out explicitly below.

## Why this artifact is allowed to exist

An earlier analysis rejected forward architecture specifications, and the reasoning was
sound as far as it went: the central check on an architecture artifact is that every path
it claims is real, and for a system that has not been built yet, no path is real. Turning
that check off leaves a JSON shape validator and nothing of substance.

The flaw in that reasoning is the assumption that the check happens when the document is
written. Here it does not. Declaration and verification are separate modes run at
different points in the pipeline:

| Mode | When | Checks | Does not check |
|---|---|---|---|
| `--declare` | Stage 3, before the build | Shape: identifiers, statuses, symmetry, non-empty declarations, repo-relative paths, scope self-consistency | Path existence, because nothing is built |
| `--verify` | After Stage 6, before the pull request | Every declared path now exists; nothing landed out of scope | Whether the code at those paths behaves correctly |

The existence check is deferred, not weakened. That single change is what makes a forward
declaration enforceable, and it is why this artifact is worth having when the rejected
design was not.

## Shape

```json
{
  "schemaVersion": "1.0",
  "declaredAt": "2026-08-02T02:00:00Z",
  "declaredAtCommit": "e5c673f3fbe35d86cceb6d2f3811302388b488d1",
  "basis": "extends-index",
  "components": [
    {
      "id": "webhook-ingest",
      "title": "Webhook Ingestion Service",
      "purpose": "Accepts inbound provider callbacks and dispatches each to the handler that owns it; validates signatures before any handler runs.",
      "status": "new",
      "connections": ["command-surface"],
      "intendedPaths": {
        "directories": ["services/webhooks"],
        "files": ["services/webhooks/handler.py"],
        "rationale": "New service tree; the dispatcher entry point is named explicitly because the gate should fail if only the directory appears."
      }
    },
    {
      "id": "command-surface",
      "title": "Slash Command Surface",
      "purpose": "Exposes the new capability as a namespaced slash command dispatched by the existing router.",
      "status": "modified",
      "connections": ["webhook-ingest"],
      "intendedPaths": {
        "directories": ["commands"],
        "files": [],
        "rationale": "The command file and the router registration both live under the existing commands tree."
      }
    }
  ],
  "outOfScope": ["systems", "adapters"],
  "notes": "Free text. Record anything a reviewer at the approval gate would want to push back on."
}
```

| Field | Required | Meaning |
|---|---|---|
| `schemaVersion` | Yes | Only `"1.0"` is known. |
| `declaredAt` | Yes | ISO 8601 timestamp of declaration. |
| `declaredAtCommit` | Yes | HEAD before the build. The out-of-scope check diffs this against HEAD. |
| `basis` | Yes | `new` for a greenfield declaration, `extends-index` when built on an existing `.arch/index.json`. |
| `components` | Yes | At least one. See below. |
| `outOfScope` | No | Paths this ship must not touch. Enforced by `--verify`. |
| `notes` | No | Free text. |

## Component fields

| Field | Required | Meaning |
|---|---|---|
| `id` | Yes | Kebab-case. Reuse the id from `.arch/index.json` when modifying an existing component, so the two artifacts line up. |
| `title` | Yes | `[Business Function] + [Implementation Context]`, per `component-rules.md`. |
| `purpose` | Yes | What it will deliver, in full sentences. |
| `status` | Yes | `new`, `modified`, or `unchanged`. |
| `connections` | Yes | Must be symmetric and resolve to declared ids. |
| `intendedPaths` | Yes | `directories`, `files`, and a non-empty `rationale`. |

## The `status` field decides what gets checked

This is the field that makes the artifact usable, so it is worth being precise about.

`new` and `modified` components are checked by `--verify`. Every path they declare must
exist after the build. Declaring a component and then not building it is the exact failure
this artifact exists to catch, and it is invisible to every test gate, because tests fail
when behaviour breaks rather than when work is quietly dropped.

`unchanged` components are exempt from the existence check. They are present so the plan
reads as a complete architecture rather than a diff, and so `connections` can reference
them without a dangling id. A ship never claimed to build them, so it is not held to them.

Name individual files in `intendedPaths.files`, not just the containing directory, wherever
you want the gate to be strict. A directory claim is satisfied by the directory existing at
all. If the plan says `services/webhooks/handler.py`, the gate fails when the directory
appears empty, which is usually what you want.

## Choosing `outOfScope`

The out-of-scope list is the plan's way of saying "this ship should not go here". It is
enforced by diffing `declaredAtCommit..HEAD` and reporting any changed file underneath a
listed path.

Be deliberate. Listing a tree that ordinary work touches produces a wall of violations that
teaches everyone to ignore the gate, which is worse than not having it. In practice the
useful entries are the trees a ship has no business in: another team's bundle, a vendored
dependency, a generated catalog.

A path may not appear in both `outOfScope` and a component's `intendedPaths`. That plan is
unsatisfiable, and `--declare` rejects it before the approval gate rather than after the
build.

## What is not checked

**Whether the code is any good.** The gate proves the declared paths are real and nothing
landed out of bounds. It proves nothing about whether the code at those paths implements
what the component's `purpose` described. That is a review judgement and carries no exit
code.

**Whether the declared architecture was a good idea.** `--declare` checks that a plan is
internally consistent and satisfiable, not that its decomposition is sensible. That is what
the approval gate and `architecture-reviewer` are for.

**Files added inside a claimed path.** A component that declares `services/webhooks` passes
regardless of what appears beneath it. Path-level granularity is deliberate: anything finer
would fail on ordinary work.

**Out-of-scope enforcement when git cannot resolve the pin.** If `declaredAtCommit` is
missing or unresolvable, the script reports the out-of-scope check as `UNVERIFIED` rather
than passing it silently.

## Relationship to `.arch/index.json`

The two artifacts are complementary and neither replaces the other.

`.arch/index.json` is committed, long-lived, and describes the repository as it stands. It
is what `/team verify` failure mode (e) checks against, and what `/team arch drift`
reconciles.

`.team-ship/ARCH-PLAN.json` is per-ship, lives in the ship workspace, and describes one
intended change. It is discarded once the ship completes.

After a successful ship, run `/team arch drift` to fold the newly built components into the
committed index. The plan does not update the index by itself, deliberately: the index
should record what exists, verified by the validator against the real tree, not what a plan
predicted would exist.

## Attribution

The component naming and purpose formulas, and the component-count guidance, are adapted
from devildev by lak7 (Apache-2.0), <https://github.com/lak7/devildev>. See
`component-rules.md` for the full modification notice.

The declare-then-verify split is not from devildev, which had no forward mode. It exists
because deferring the path-existence check to after the build is what makes a forward
declaration enforceable at all.
