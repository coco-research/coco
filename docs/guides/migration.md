# Migration guide: from raw prompts → Coco skills

You've been writing prompts for months. They live in your notes, in `.txt` files, copied into AI chats. They work, but they're scattered. Coco gives them a home.

This guide shows how to migrate.

---

## Why migrate

| Before Coco | After Coco |
|---|---|
| Prompts copy-pasted into chats | Invoked with `/<name>` |
| Each prompt re-typed every session | Persistent across sessions |
| Prompts trapped in your local machine | Shareable as markdown files |
| No version history | Git-tracked, atomic commits |
| Each prompt re-tuned independently | Frontmatter spec validates consistency |
| No discovery for collaborators | `skills/INDEX.md` lists everything |

---

## Migrate a single prompt → skill

You have a prompt that works. Make it a Coco skill.

### Step 1 — Identify the prompt

Pick one prompt you use often. Example: a "code reviewer" prompt you've refined over months.

### Step 2 — Wrap it as a SKILL.md

```bash
mkdir -p skills/my-code-reviewer
cat > skills/my-code-reviewer/SKILL.md <<'YAML'
---
name: my-code-reviewer
description: Custom code review focused on perf, security, and our team conventions. Use before merging any PR.
domain: engineering
supports: [claude-code, cursor, codex, generic]
version: 0.1.0
---

# My Code Reviewer

[paste your existing prompt here]

YAML
```

### Step 3 — Wire it

```bash
bash install.sh
```

Done. Your AI now invokes the skill on relevant context (review, audit, PR, merge, etc.) — and you can call it explicitly with `/my-code-reviewer`.

---

## Migrate a prompt collection → namespace

You have 10 prompts for stakeholder communications. Make them a namespace.

```
prompts/
├── go-live-email.txt
├── status-update.txt
├── steerco-brief.txt
├── ...
```

Becomes:

```
commands/comms/
├── go-live-email.md
├── status-update.md
├── steerco-brief.md
├── ...
```

Each file:

```markdown
[paste prompt body — use $ARGUMENTS for parameters]
```

After install, invoke as `/comms:go-live-email`, `/comms:status-update`, etc.

---

## Migrate a workflow (multi-step prompt sequence)

You have a sequence: research → analyze → write. Currently you copy 3 prompts in order.

Becomes a single workflow file:

```bash
mkdir -p workflows
cat > workflows/research-then-write.md <<'YAML'
# Research-then-write workflow

## Step 1 — Research
[research prompt]

## Step 2 — Analyze findings
[analyze prompt]

## Step 3 — Write the deliverable
[write prompt]

## Use
Invoke each step in sequence. Or wrap as a single skill that calls all three.
YAML
```

For full automation, convert the workflow into a skill that orchestrates the steps internally.

---

## Migrate a multi-agent pattern

You used to spawn helper agents manually:

```
"Spawn a researcher agent to analyze X, then a reviewer to check Y..."
```

In Coco, define the agents once:

```bash
cat > agents/my-researcher.md <<'YAML'
# My Researcher

You are a specialized researcher. Your job: ...
[full role spec]
YAML

cat > agents/my-reviewer.md <<'YAML'
# My Reviewer

You are a specialized reviewer. Your job: ...
[full role spec]
YAML
```

Then any skill or command can spawn them by name without re-specifying the role each time.

---

## Migrate to a project orchestration system

You've been managing a multi-week project with ad-hoc prompts and notes. Move to GSD:

```bash
bash install.sh --systems gsd
/gsd-new-project
```

GSD asks about your project, creates `.planning/` with PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md. From here, every phase has research → plan → execute → verify gates. State persists across sessions.

Migrate existing notes by:
1. Run `/gsd-import` to ingest external plans (Notion exports, markdown notes, etc.) — handles conflict detection
2. Or paste them into `.planning/PROJECT.md` and `ROADMAP.md` directly

---

## Migrate a knowledge base

You have a project Wiki / Notion / scattered notes. Brain bundle gives you a SQLite-backed local knowledge tracker.

```bash
bash install.sh --systems brain
/brain-init
```

Then either:
- `/brain-rescan` — incremental scan of project files, auto-extracts entities
- `/coco teach <fact>` — manually add facts
- Paste notes into `.brain/raw/` for ingestion

`/brain-wiki` generates Wikipedia articles per entity. `/brain-export` regenerates `CLAUDE.local.md` from the DB.

---

## Frontmatter cheatsheet

Every skill needs:

```yaml
---
name: <slug>                           # required
description: <one line, used for AI relevance scoring>   # required
domain: foundational | pm | engineering | design | ops | meta   # required
supports: [claude-code, cursor, codex, generic]   # required
version: 0.1.0                         # required
---
```

Optional fields:

```yaml
---
tags: [tag1, tag2]                     # for filtering
inputs: [arg1, arg2]                   # named arguments
output: what it produces
requires: [other-skill]                # dependencies on other Coco skills
external: [npm:package, pip:package]   # external runtime deps
deprecated: <reason>                   # hides from default views
---
```

Full spec: [`docs/architecture.md`](../architecture.md).

---

## Once migrated

- Run `python3 scripts/build-index.py` to regenerate `skills/INDEX.md`
- Open a PR if you'd like to contribute the migrated skill back to Coco
- Keep your `~/.claude/CLAUDE.md` clean — the personal stuff stays, the reusable skills move into Coco

---

## Common questions

**Q: My prompt has placeholders like `{name}`. Will those work?**
A: Use `$ARGUMENTS` for command arguments. For more complex templating, write the skill to ask for inputs interactively.

**Q: Can I keep using my prompts the old way?**
A: Yes. Coco doesn't replace anything — it adds a curated library. Your existing prompts still work; you just have a tidier home for the ones worth keeping.

**Q: My prompt has 500 lines. Is that too long?**
A: No. Skills can be arbitrarily long. Recommend splitting into a `SKILL.md` body + `references/` subfolder for supplementary material.

**Q: Can I share my migrated skill with my team?**
A: Yes. Either fork Coco and add it, or maintain a private skill repo and point your team at it. The frontmatter spec is the only contract.
