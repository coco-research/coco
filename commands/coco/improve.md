---
allowed-tools: Read, Glob, Bash(python3 evals/skills/improve.py:*)
argument-hint: "<skill> [--executor ollama|stub] [--apply]"
description: Run one scored improvement round on one skill and show the proposed SKILL.md diff. Trigger as /coco-improve or /coco:improve.
---

# Coco Improve

Run one improvement round on one skill. Arguments: **$ARGUMENTS** (the first
word is the skill name).

## Check the skill first

The skill needs `evals/skills/<skill>/items.jsonl` and
`evals/skills/<skill>/grader.py`, plus `skills/<skill>/SKILL.md`. Skills with
items today: `c4-architecture`, `code-verification`, `generate-tests`,
`humanizer`, `prd-generator`, `writing-plans`. Check with Glob before running;
the list grows as items are added.

If the skill has no items, say so plainly, run nothing, and point at
`evals/skills/README.md`, which explains how to write items and a grader.
Folders starting with `_` are test fixtures, not skills.

## Run

```bash
python3 evals/skills/improve.py --skill <skill>
```

`COCO_PROPOSER_CMD` must name the command that proposes an edit (it reads the
prompt on stdin and prints the new SKILL.md). If it is unset, stop and say so.
The round also needs a baseline held-out record in
`evals/skills/<skill>/runs/`; if it is missing, the error prints the exact
`score.py` line that makes one. Show that line to the user.

## What the round does, in plain words

1. **Score.** It scores the current SKILL.md on the dev items.
2. **Dev-only proposal.** The proposer sees the skill and the dev cases it got
   wrong, never the held-out items. Each proposal is scored on dev, and only
   one that beats the current skill by a clear margin goes forward.
3. **Held-out gate.** The chosen change is scored once on the held-out items,
   which nobody tuned on. It is kept only if it also does better there. A
   change that helps dev but hurts held-out is rejected as overfitting.

The last line of output is JSON with `outcome` (`kept`, `no change` or
`aborted`), `reason` and `out`. Report the outcome and the reason.

## Applying a kept change

A kept change is NOT applied by default: without `--apply` the repository's
SKILL.md is untouched. The kept SKILL.md and its run records wait in
`<out>/branch/`. Show the user `<out>/skill.diff` and wait for them to read
it. Never pass `--apply` before the user has read a diff and said yes.

Once they say yes, copy the reviewed files in with `cp -R <out>/branch/. .`
(the SKILL.md and run records `--apply` writes, plus a copy of the round
record already in `evals/skills/_rounds/`). `--apply` writes a kept change
during the round itself, so use it only when the user asks for that. Each
round that reaches the held-out gate with a real executor spends one of the
five held-out peeks the item set allows, and a new round may propose a
different change.

## Other flags

`--executor stub` scores offline without a model server. `--max-proposals`,
`--dev-margin`, `--max-changed-lines`, `--out`, `--root`, `--base-ref` and
`--baseline-heldout` tune the round; `python3 evals/skills/improve.py --help`
lists them.
