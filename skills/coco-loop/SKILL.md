---
name: coco-loop
description: >
  Start a safe, governed autonomous loop from a plain-language goal. Use when the
  user says /coco-loop, "run an autonomous loop", "keep my build green for N hours",
  "work on X autonomously for a while", or wants a bounded self-improving loop that
  proposes fixes and never commits on its own. Turns a vague goal into a readable
  charter the user confirms, then arms and runs the loop propose-only under the
  coco-loops governance framework.
---

# coco-loop

Turn a plain-language goal into a governed, propose-only loop. You compile the goal
into a charter, the person confirms it, and the loop runs under the coco-loops
framework: it proposes changes, a separate verifier judges them, and nothing is
committed. The loop stops itself when its lifetime cap of active work is spent.

The framework enforces an immutable constitution underneath every charter. You cannot
write a charter that disables the verifier, commits without approval, edits the
constitution, sends content to raw public-cloud endpoints, or runs unattended
destructive operations. The `coco-loops charter` command rejects any charter that
tries. Do not attempt to work around it. Present the floor to the person as a feature.

## Prerequisites

`coco-loops` must be on the PATH. Install it from
[coco-research/coco-loops](https://github.com/coco-research/coco-loops):

```bash
git clone https://github.com/coco-research/coco-loops
pip install -e coco-loops
```

Check with `coco-loops --help`. If it is missing, tell the person how to install it and stop.

## Flow

### 1. Understand the goal

Read the person's goal. Ask at most one or two clarifying questions, and only when the
answer genuinely changes the charter:

- Which repository or worktree should the loop work in? A loop needs a clean git tree,
  so a dedicated worktree is strongly recommended (the loop reverts its own changes
  each cycle and refuses to run on a dirty tree, to avoid clobbering uncommitted work).
- How long should it run? This becomes the lifetime cap of active work, for example
  `4h`. The clock only advances while the loop is actually working, so a closed laptop
  or an idle wait does not burn it.

Do not over-question. If the goal is clear, proceed.

### 2. Compile the charter

Get the exact field list with `coco-loops charter --schema`, then produce a charter as
JSON. Derive the principles from the goal, and add sensible safe defaults. Keep
principles readable: they are what the person confirms and what we audit the loop
against.

Example, for "keep my frontend build green for the next 4 hours":

```json
{
  "loop_id": "keep-build-green",
  "objective": "Make failing frontend tests pass and keep the build green.",
  "principles": [
    "Only touch code covered by a failing test; keep the diff as small as possible.",
    "If a test is genuinely stale, propose updating it rather than weakening it silently.",
    "Prefer fixing the code over changing the test when a real regression is likely."
  ],
  "guardrails": [
    "No dependency or lockfile changes.",
    "No CI or build-config edits."
  ],
  "context": ["the frontend test suite"],
  "inputs": ["failing tests detected each cycle"],
  "lifetime": "4h",
  "level": "L1"
}
```

Rules for the charter you produce:

- `level` is always `L1`. New loops are propose-only. Higher maturity is earned through
  the promotion gate, never declared here.
- `loop_id` is a slug: lowercase letters, digits, and hyphens.
- Give at least one principle. Three to five is usually right.
- Set `lifetime` from what the person asked, defaulting to `4h`.

### 3. Show the charter and confirm

Write the charter JSON to a temporary file, then run:

```
coco-loops charter --from-json <file>
```

This validates the charter against the constitution floor and prints a readable
version. If validation fails, it prints why (with the invariant it violated); fix the
charter and try again. Show the rendered charter to the person and ask them to confirm
before anything is armed.

### 4. Install and arm

On confirmation:

```
coco-loops charter --from-json <file> --install
```

This writes `<loop_id>.contract.md` into the loops directory, arms the lifetime cap,
and clears the kill-switch. The loop is now defined and armed, propose-only.

### 5. Give it work and run it

The loop reads tasks from a JSON queue (a list of `{"id", "name", "instruction"}`
objects). Seed the queue with concrete, grounded tasks, for example one task per
failing test with the file and the assertion. A loop is only as good as its task list;
vague tasks produce no-ops.

Run it in the chosen worktree:

```
coco-loops run <loop_id> --repo <worktree> --tasks <queue.json>
```

Each cycle it pops a task, asks the maker (cursor-agent by default) to propose a change,
has the verifier judge it, logs the proposal, and reverts the tree. Use `--once` to run
a single cycle first and watch what it does. Recommend a dedicated worktree so the
loop's revert can never touch the person's uncommitted work.

### 6. Monitor and hand back

```
coco-loops status <loop_id>
```

shows the recent proposals, the verifier verdicts, and how much of the lifetime is
spent. Everything is propose-only: the person reviews the batch of proposals and
applies what they want. When the lifetime is spent the loop stops itself. To run
another session, re-arm with `coco-loops start <loop_id> --for <duration>` (or run
`charter --install` again).

## What to tell the person

- The loop proposes, it does not commit. They stay in control of what lands.
- It stops itself after its lifetime of active work. It will not run forever.
- The constitution floor is always on and cannot be overridden by a charter.
- A dedicated worktree keeps their main checkout safe.
