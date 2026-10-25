---
name: coco-workflow
description: Use when a piece of work must move from a request to shown work, to see the ten stages, who signs each one, and which check applies
domain: foundational
---

# Coco Workflow

Ten stages from intake to learn. Every stage has one artifact and a named signer. A small gate file under `.coco/gates/` records who signed what.

## When to use

Use it when:

- the work will land as more than one pull request, or
- someone asks who signs a stage, or
- you need to know which check applies on a branch.

For the spec stages themselves, read `coco-spec`. It carries the detail: the sign commands, the artifact paths, the gate schema, the rejection rule. This skill says which stage you are in, what it produces and who signs the exit.

## The stages

| # | Stage | Artifact | Signer | Check |
|---|---|---|---|---|
| 0 | intake | a story, sized small or feature | owner | none |
| 1 | understand | the code the work touches, each claim carrying `file:line` | owner | none |
| 2 | design, front ends only | journeys, versioned mocks, copy | designer signs the mock; the approver's yes is relayed | mock and approval sign-offs |
| 3 | spec, features only | PRD, then architecture with a diagram, then plan | owner signs the PRD; architect or council signs the architecture and the plan | `coco-gate` signatures |
| 4 | build | one task per PR, under 800 lines, its test in the same PR | none, the plan sign-off covers it | the task's own test |
| 5 | review | review notes on the diff | reviewer | the review record |
| 6 | merge | the pull request | merger | `coco-workflow` plus the repo's review rules |
| 7 | release | a tag and a changelog | owner | the tag |
| 8 | show | the running app, walked against a checklist | architect and one reviewer | `coco-gate check-show` |
| 9 | learn | a decision record | owner | none |

Design covers front ends only. Spec covers features only. Nothing after spec is optional.

## Small versus feature

A small change is a few PRs at most, each under the no-gate limit (300 changed lines, Markdown excluded), on a branch outside the feature pattern (`feat/*` by default): a typo, a config value, a dependency bump, a one file fix. It skips design and spec. It never skips build, review, merge, release or show.

Everything else is a feature and runs every stage. Size is part of every signature, so changing it in the gate file voids them.

## The checks

**The `coco-workflow` check on pull requests.** `.github/workflows/coco-workflow.yml` runs on every pull request. It reads `.coco/gates/<branch>.json`, with each `/` in the branch name replaced by `__`. It verifies every signature with `ssh-keygen -Y verify` against `.coco/allowed_signers` read from the base branch, and names the missing stage when one fails.

**The Claude Code hook.** A `PreToolUse` hook holds Claude Code's edit tools, `Edit`, `Write`, `MultiEdit` and `NotebookEdit`, on code paths while the current branch's gate says `feature` and the plan is not signed. A second hook, `UserPromptSubmit`, prints the stage and the next artifact each turn. The hook lines go into `.claude/settings.local.json` by default; the installer prints them and never writes that file.

**The git pre-commit hook.** It warns only. While a feature's plan isn't validly signed, it prints a warning naming the stage and the next artifact, and it never stops a commit itself. It lives in `.git/hooks` and is never committed. An existing pre-commit hook is kept: it runs after the warning, and its own result decides.

**The show check.** `coco-gate check-show <checklist.md>` needs every box ticked and two sign-offs over the checklist's current bytes, from two different signers: one architect-role signature and one reviewer-role signature (a reviewer, design or council role). An unticked box, or only one sign-off, refuses the ready line.

## Roles and separation

Whoever builds never signs their own gate, and a build agent is never given a signing key. The gate names its builder, so a sign-off by that id is invalid even with a real key. The architecture and the plan are signed by an architect or a council, not by the person building. A human approver's yes is recorded as a decision that must already be on the base branch, then relayed by a signer, and the decision must name the mock it approves. When a repo's policy turns on direct approver signing, the approver needs a hardware-backed key.

The Claude Code hook holds those four edit tools on code paths, which is a stop for an editor session. Shell commands are not intercepted, so a write through a shell command gets through. Treat that hook as a guide, not a lock.

## Where it stops

Locally the gate is tamper-evident, not tamper-proof: an agent running as the same OS user can read any key that user can read, so a local process could sign as someone else. Keys on one machine show that a step happened and when bytes changed after signing. They do not stop same-user access.

GitHub runs the workflow file as the pull request has it. A change to `.github/workflows/coco-workflow.yml` is therefore only as strong as the code-owner review it needs, so require code-owner review on `.github/` and `.coco/`. The required check plus a person's merge, from their own account and machine, is the lock. Every local hook is a guide.

## Helpers per stage

| Stage | Skill |
|---|---|
| understand | `graphify`, `arch-index` |
| design | `design-taste-frontend` |
| spec | `coco-spec` |
| build | `ponytail`, `test-driven-development` |
| review | `ocr`, `requesting-code-review`, `code-verification` |

Only skills that ship in this repo are listed. Helpers that live outside this repo are not named here.
