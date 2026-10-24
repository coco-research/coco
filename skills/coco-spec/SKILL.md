---
name: coco-spec
description: Use when a feature will land as more than about three PRs and needs a signed PRD, architecture and plan before any code is written
domain: foundational
---

# Coco Spec

Turn a feature request into a signed spec, then into small builds. Every stage has an exit: a named signer on exact file bytes. The gate refuses the next stage until that signature is valid.

## When to use

Use it when the change is a feature:

- it needs more than about three PRs, or more than one layer, or
- someone has to agree to a decision before code exists, or
- you would have to guess what "done" means.

Skip it when the change is small: a typo, a config value, a one file fix, a dependency bump. Those go straight to a branch and a PR.

The one line test: if you can describe the whole change in one sentence and ship it in one PR under 800 lines, skip this skill.

## Stages

Each stage has an entry condition, one artifact, and a stop point. Stop means stop. Do not roll into the next stage because the artifact looks good.

| # | Stage | Enters when | Artifact | Stops after |
|---|---|---|---|---|
| 1 | index | a branch exists and the request is written down | a map of the code the feature touches, every claim carrying `file:line` | the map shows where the feature lands |
| 2 | interview | the map exists | answers, one question at a time, at most 8 | the open questions are closed |
| 3 | prd | the answers are in | `prd.md` | the PRD is signed |
| 4 | arch | the PRD is signed | `arch.md` and `arch-diagram.html` | the architecture is signed |
| 5 | plan | the architecture is signed | `plan.md`, numbered tasks | the plan is signed |
| 6 | build | the plan is signed | one task of code, one entry in `build-log.md` | the task passes its test, then stop |

Only stages 3 to 6 write files. The map and the answers live in the conversation and flow into the PRD.

### 1. Index

Use any indexer you already have: a grep, a code map, an existing arch index. The point is evidence, not coverage. If you write "the handler calls the store", cite the file and line. A claim without a citation is not done.

### 2. Interview

One question per turn. Never a list of questions. Eight is the ceiling, and most features need fewer. Ask about the user, the trigger, the failure case, the data, and what is out of scope. Never ask something the request or the code already answers.

### 3. PRD

Write `prd.md` at `docs/specs/<feature>/prd.md`, using the sections in `references/artifacts.md`. What and why only: no file names, no components, no implementation. Every requirement must be able to fail a check. Stop for sign-off.

### 4. Architecture

Write `arch.md` and `arch-diagram.html`. The diagram is required and must be real HTML or SVG that opens in a browser on its own. An ASCII only diagram is refused. Put the current state and the change in the same picture so a reviewer can see what moves. Cite files and symbols for every claim. Stop for sign-off.

### 5. Plan

Numbered tasks, starting at 1. Each task names its files, its test, and when it counts as done. One task is one PR, and one PR stays under 800 lines. A task that needs two "and then"s is two tasks. The first tasks are the working set; later tasks may change after the first build. Stop for sign-off.

### 6. Build

One task at a time. Run its test, write the real result into `build-log.md`, then stop and report. Do not start the next task in the same turn. If a task turns out to be wrong, the plan is wrong: stop and revise the plan, not the task in flight.

## Gates

After the PRD, the architecture and the plan, a named signer signs the artifact:

```sh
coco-gate sign --stage prd  --signer <id>
coco-gate sign --stage arch --signer <id>
coco-gate sign --stage plan --signer <id>
```

- The signature covers the artifact's exact bytes. Editing it after signing voids the signature, so the stage returns to unsigned.
- Stages are ordered. An arch sign-off is refused until the PRD sign-off is valid, and a plan sign-off is refused until the architecture is signed. Skipping a gate is refused, not warned about (see Where the gate stops).
- A requested change counts as a rejection. Revise the artifact in place, same path, and sign again. Never write a second PRD at a new path to dodge a review.
- After a rejection, every later stage waits until the rejected stage is signed again.

Who signs is recorded in the sign-off. The owner signs the PRD. The architect (or a review council) signs the architecture and the plan. Whoever builds the feature never signs its own gate, and a build agent is never given a signing key. A signer is a person or a named role key, never an anonymous edit.

## State

Artifacts live under one directory per feature:

```text
docs/specs/<feature>/
  prd.md
  arch.md
  arch-diagram.html
  plan.md
  build-log.md
```

The gate file sits at `.coco/gates/<branch>.json`, with every `/` in the branch name replaced by `__`. Branch `feat/login` gives `.coco/gates/feat__login.json`.

- Only `coco-gate` writes the gate file. Never edit it, never hand-write a signature, never add a key on the branch.
- One gate file per branch, so two features never argue over one file.
- A feature starts with `coco-gate init --size feature`. The size is inside every signature, so changing it voids them. A branch matching the feature pattern (`feat/*` by default) needs a gate file, and so does any change over 300 lines of code, so leaving the file out is not a way around the stages. Calling a feature branch `small` needs its own sign-off.
- `coco-gate status` prints the next action. When unsure, run it and do that one thing.

## Commands

| Command | What it does |
| --- | --- |
| `/coco-spec` | resumes at the first stage that is not signed, and runs it |
| `/coco-spec <stage>` | runs one stage only: `index`, `interview`, `prd`, `arch`, `plan`, `build` |
| `approve` | sends the current artifact to its signer, who signs with `coco-gate sign` |
| `reject <reason>` | records a rejection, holds later stages, revises the artifact in place |

## Where the gate stops

Locally the gates are tamper-evident, not tamper-proof. An agent running as the same OS user can read any key file that user can read, so a determined local agent could sign as someone else. A local gate proves a step happened and shows when bytes changed after signing. It cannot stop a process that already has the user's file access.

What gives it teeth is the pull request. A required check, `coco-workflow`, verifies the gate with the signer keys, the policy and the verifier taken from the base branch, so a key, a looser rule or an edited checker added on the feature branch proves nothing. The final lock is the merge, made by a person from their own account and machine. This holds only if the repo makes `coco-workflow` a required check and limits who can merge. GitHub admins can bypass branch rules unless that's turned off. Each role has its own key, so one leaked key affects only that role.

In this version a human approver's yes is relayed: a signer records it with a reference to a written decision that must already be on the base branch. Approvers who want to sign directly can turn on hardware-backed keys (`sk-` keys) in the policy.

## Credits

MetaGPT (https://github.com/FoundationAgents/MetaGPT, MIT) is the source of the idea: a software company run as a standard operating procedure, with a role packet for each stage. Coco Spec is fresh text and a different mechanism, a signed gate file checked by `coco-gate`, not a chat between agents. No MetaGPT code, prompt or command line tool is used, and none is required. Coco Research isn't affiliated with MetaGPT or FoundationAgents.
