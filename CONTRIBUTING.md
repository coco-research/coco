# Contributing

Coco gets better when its skills do. Open a PR.

---

## What to contribute

- **A new skill** — battle-tested prompt or workflow you'd run again
- **A new command** — namespaced slash prompt
- **A new agent** — specialized subagent role
- **A new adapter** — wires Coco into another AI tool
- **A bug fix** — improve an existing artifact
- **Docs** — clarify, expand, fix examples

---

## Open a PR

```bash
gh repo fork coco-research/coco --clone
cd coco
git checkout -b feat/your-thing
# ... make changes ...
git commit -m "feat: short description"
gh pr create
```

**A bug you find is a bug you fix.** If installing Coco, or anything around it, turns up
something broken, do not file it and move on — reproduce it, fix it at the source, add the
gate that would have caught it, and open the pull request. Generated output, built
bundles and deployed copies do not count as a fix; the next rebuild erases them.

The same instruction is in [`AGENTS.md`](AGENTS.md), which is loaded into every agent
session opened in this repo, so an agent working here follows it without being told.

---


## Add a skill

```
skills/<name>/
  SKILL.md          # required — frontmatter + body
  references/       # optional — supporting docs
  scripts/          # optional — helper scripts
  templates/        # optional — skill-specific templates
```

`SKILL.md` frontmatter (required fields in **bold**):

```yaml
---
name: my-skill                                            # required
description: One-line description (used for relevance)    # required
domain: pm | engineering | design | ops | foundational | meta   # required
supports: [claude-code, cursor, codex, generic]           # required
version: 0.1.0                                            # required

# optional
tags: [tag1, tag2]
inputs: [arg1, arg2]
output: what it produces
requires: [other-skill]
external: [npm:package, pip:package]
---

# Skill body in markdown
```

Spec: [`docs/architecture.md`](docs/architecture.md).

---

## Add a command

```
commands/<namespace>/<name>.md
```

Namespaces: `team/`, `email/`, `design/`, `eng/`, `pm/`, `util/`. Add a new one if needed — keep them tight.

---

## Add an agent

```
agents/<name>.md
```

One agent = one specialized role. Examples in [`agents/`](agents/).

---

## Add an adapter

```
adapters/<ide>/
  install.sh        # wires artifacts into target IDE
  manifest.json     # declares targets + transforms
  README.md         # how to install for this IDE
```

Adapter contract: [`docs/architecture.md`](docs/architecture.md#adapter-contract).

---

## Style

- Markdown. No IDE-specific syntax.
- Vendor-neutral. Use frontmatter to declare adapter support.
- One sentence per line in long docs (cleaner diffs).
- No emojis unless functionally required.

---

## Test before PR

```bash
bash adapters/<ide>/install.sh --dry-run     # for any adapter touched
```

Frontmatter must validate against [`docs/architecture.md`](docs/architecture.md).

---

## Licensing

CoCo is open-core. Contributions to the **core** are MIT-licensed under the project's [LICENSE](LICENSE); by submitting a PR touching the core, you agree your contribution is so licensed.

The **Super Intelligence System** (`systems/superintelligence/`) is proprietary — see [`systems/superintelligence/LICENSE`](systems/superintelligence/LICENSE). It is not accepting external contributions under an open-source license; please open an issue before proposing changes there.

---

## Code of conduct

Be respectful. Argue ideas, not people. Give credit. We're a small project and a kind community goes far.
