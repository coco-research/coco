# AGENTS.md — instructions for agents working in this repository

This file is loaded into every agent session opened in this repo, in PI-Desktop and in
any other tool that reads `AGENTS.md`. It is short on purpose: it is context, not
documentation.

---

## Standing rule: a bug you find is a bug you fix

**If you find a bug while installing this repository, or in anything related to it, fix
it and open a pull request. Do not report it and move on.**

A finding that stays in a chat message is a finding that gets lost. This repository has
learned that the expensive way, twice:

- A generated index silently advertised a bundle that no longer existed. It cost twenty
  unrelated pull requests a failed CI gate, because the cause was never written down
  where the next person could find it.
- An adapter generated 242 of the 280 slash commands and said nothing. It was invisible
  for months — not because the code was subtle, but because the defect only existed at
  install time and no gate measured what an install actually delivered.

Both were cheap to fix and expensive to discover. Fixing on discovery is the whole point.

### What counts as a bug

- An install that delivers less than it advertises, or less than its siblings.
- A path, count, command, or skill reference that does not resolve.
- A gate that cannot fail, or one that measures the wrong thing.
- A silent fallback where a loud failure belongs.
- Documentation that contradicts the code.

### How to fix one

1. **Reproduce it first.** Install into a throwaway `HOME` and count what lands. A bug
   you cannot reproduce is a bug you cannot verify a fix for.
2. **Fix it at the source**, not at the artifact. Editing generated output, a built
   bundle, or a deployed copy is erased by the next rebuild.
3. **Add the gate that would have caught it.** A fix without a test is a fix that comes
   back. If no test can catch it, that absence is itself worth a sentence in the commit
   message.
4. **Run the full `ci.yml` mirror before pushing.** Every step. The delivery-index gate
   runs real installers and is the one that catches an install that quietly got smaller;
   do not skip it because it is slow.
5. **Open the pull request** with what broke, why it was invisible, and the command that
   proves the fix.

### Scope

- **This repository:** fix and PR. Always.
- **Another repository, including a product that consumes this one:** report findings to
  the owner and stop. Do not open a pull request against a repo you were not asked to
  change. Findings for other repos belong in their `docs/`, not in their code.

---

## What this repository is

A framework that installs instructions, not a service. Its runtime is markdown an agent
reads on demand: skills, slash commands, subagent definitions, rules. See `.arch/` for
the structural index and `adapters/INDEX.md` for what each adapter actually delivers.

## Two facts that surprise people

**The command surface is generated, not committed.** Most of the slash commands are stamped
out at install time by `scripts/generate-si-commands.sh` from the registries under
`systems/superintelligence/`. An adapter that does not call that script delivers only the
core commands — a fraction of the surface — and no warning. `adapters/INDEX.md` measures
the real numbers by running each installer. This is the single most common way an install goes quietly wrong.

**Skill discovery has three layouts, not one.** `build-index.py` knows all three, and an
adapter that walks only the first two loses thirteen skills without failing:

```
skills/<name>/SKILL.md
systems/<bundle>/skills/<name>/SKILL.md
systems/<bundle>/<team>/SKILL.md
```

## Before you change anything

```bash
python3 scripts/build-index.py                # regenerate the catalogs
python3 scripts/build-delivery-index.py       # regenerate the delivery index (runs installers)
python3 systems/team/validate_roles.py        # validate the role roster
bash tests/check-command-refs.sh              # cross-references must resolve
```

CI gates every one of these. A diff to a generated file without the regeneration is a red
build.
