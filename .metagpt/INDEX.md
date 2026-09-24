# INDEX - coco

**Repo:** `coco` (published as `cocosuperintelligence` v1.5.0) · `https://github.com/rkz91/coco.git`
**Indexed at:** `8fac7c0` on branch `site/spacex-vnext-draft`
**Method:** brownfield - ripwire (symbol map) + cartographer (code graph)
**Tree:** 3,576 tracked files, 2,212 markdown

---

## What this repository is

A **framework that installs instructions, not a service.** Its runtime is markdown an
agent reads on demand - skills, slash commands, subagent definitions, rules - plus the
installers that place those assets where each editor or CLI looks for them. There is no
application server, no database, and no long-running process in the core.

The product is the *content*; the shell scripts are the delivery mechanism.

## Languages and stack

| Concern | Technology | Notes |
|---|---|---|
| Authored assets | Markdown + YAML frontmatter | **2,212 files** - this is the product |
| Install logic | POSIX shell | 58 `.sh`, one per editor target |
| Generation | Python 3 (stdlib + PyYAML) | catalogs, SI command family |
| Package/bootstrap | Node, Ruby | `bin/coco.js` wrapper, Homebrew `Formula/` |
| CI | GitHub Actions | 5 workflows |

Counts above are the file mix by extension: `md` 2212, `ogg` 228, `html` 226, `mjs` 187,
`py` 134, `json` 120, `sh` 58, `ts` 39.

## How to read the ripwire files

`.metagpt/ripwire-map.txt` - the ranked symbol map, produced by `ripwire .`. Generated
output, so it is gitignored and rebuilt on demand rather than committed: run `ripwire . >
.metagpt/ripwire-map.txt` from the repository root. The same applies to
`.metagpt/ripwire-for.txt`, which `ripwire . --for="<intent>"` writes from the intent in
`GATE.json`. This file, not those, is the durable record.

**It is one line.** ripwire streams "deterministic minified XML" with **zero newlines**;
a 22 KB file reports as `0 lines` under `wc -l` and that is correct, not a truncation.
Read it with `grep -o`, or pipe through a formatter. 123 distinct source paths appear in
it; the default output is capped at `--top-k=200` symbols.

The header comment is the legend:

```
t=fn|method|cls|struct|iface|var|sec|macro   k=rank   c=call
p=path   n=name   sc=enclosing-scope   amb=ambiguous-calls
lpin=calls-pinned-by-locality-prior (a disclosed guess - read source)
overloads=N-same-name-defs-merged-into-this-row (absent if 1)
prov=per-EDGE-confidence (orthogonal to k)
```

Useful ripwire entry points for work in this repo:

```bash
ripwire . --for="<task>"        # signatures and bodies to read first
ripwire . --recall="<task>"     # search the DOCS, not the code - best for this repo
ripwire . --exemplar=<kind>     # the repo's best existing example to imitate
ripwire . --tree                # orient file by file
ripwire . --html                # interactive call graph
```

`--recall` is the important one here: this repo is 62% markdown, so the highest-value
context is usually a skill or a design doc, not a function.

`.metagpt/ripwire-for.txt` - written from the intent recorded in `GATE.json`. Generated
output, gitignored, rebuilt with `ripwire . --for="<intent>"`.

## How to read the cartographer artifacts

`.cartographer/` - the code graph, produced by `cartographer index --root . --out .cartographer`.

```text
Totals: 3578 files, 4638 nodes, 7611 edges, 0 findings
Docs: 2212   Files: 1366   Directories: 834   Package: 7
CONTAINS 4419 · IMPORTS 1661 · DOCUMENTS 1220 · TESTS 145 · USES_ENV 124
```

`graph.sqlite` (14 MB) is the queryable artifact. `.cartographer/CODEBASE_MAP.md` is the
human summary. Useful commands:

```bash
cartographer view                    # graph summary
cartographer brief                   # bounded agent-facing context
cartographer impact <path|node-id>   # what a change touches
cartographer preflight               # compact pre-edit context
cartographer slice <node>            # a subgraph
```

## Structural summary

Five asset trees at the root, one bundle tree, one adapter tree:

| Path | What it holds |
|---|---|
| `skills/` | 74 top-level skills, each `skills/<name>/SKILL.md` plus optional references, scripts, templates |
| `commands/` | 44 commands across 7 namespaces. Appear as `/<ns>-<name>` |
| `agents/` | subagent role definitions |
| `rules/` | Cursor `.mdc` behavioural rules |
| `workflows/` | 3 procedural documents, installed as skills |
| `systems/` | 9 bundle trees, each shipping **nested** skills/agents for opt-in install |
| `adapters/` | one directory per install target, each with `install.sh` + `manifest.json` |

## Three facts that surprise people

**1. The command surface is generated, not committed.** Most slash commands are stamped
out at install time by `scripts/generate-si-commands.sh` from the registries under
`systems/superintelligence/`. An adapter that does not call that script delivers only the
core commands - a fraction of the surface - **and no warning.** `adapters/INDEX.md`
measures the real numbers by running each installer.

**2. Skill discovery has three layouts, not one.** An adapter that walks only the first
two loses thirteen skills silently:

```
skills/<name>/SKILL.md
systems/<bundle>/skills/<name>/SKILL.md
systems/<bundle>/<team>/SKILL.md          <- Super Intelligence teams
```

**3. Counts are gated and they drift easily.** `docs/asset-counts.json` is generated and
`tests/check-asset-counts.sh` fails on any published count that disagrees with it. Adding
one skill moves numbers across README, `package.json`, `index.html`, `coco/index.html`
and `.claude-plugin.json`. Run the gates before pushing.

## Gates every change must pass

```bash
python3 scripts/build-index.py                # regenerate the catalogs
python3 scripts/build-delivery-index.py       # regenerate the delivery index (runs installers)
python3 systems/team/validate_roles.py        # validate the role roster
bash tests/check-command-refs.sh              # cross-references must resolve
bash tests/check-asset-counts.sh              # published counts must match generated truth
```

## Repo-state caveats recorded at index time

- **The branch name does not match its contents.** HEAD is on `site/spacex-vnext-draft`,
  but that branch carries **no commits of its own** - it sits 3 commits *behind*
  `origin/main`, and the tree contains no SpaceX-specific work. The name appears to be a
  leftover label. Verified: `git log origin/main..HEAD` is empty.
- **`.metagpt/` is new** and deliberately not gitignored, per the SOP.
- **`.cartographer/` was generated by this index** and is a build artifact (14 MB). Add it
  to `.gitignore` if it should not be committed.
- **Historical note:** `products/coco-research` is a second clone of this same remote,
  not a fork or a different project.
