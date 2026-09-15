# PI-Desktop adapter

Wires Coco into the three folders PI-Desktop reads natively, so the framework
shows up in the app's own UI — the `/` composer menu, the Skills page, and the
Subagents page — with no plugin to install and nothing to drag and drop.

## One command

```bash
bash install.sh                 # from the repo root; auto-detects PI-Desktop
bash install.sh --adapter pi-desktop
```

`npx cocosuperintelligence` works the same way: it forwards to `install.sh`, so
`npx cocosuperintelligence --adapter pi-desktop` is equivalent.

## Where things land

| Coco source | PI-Desktop surface | Destination |
|---|---|---|
| `commands/<ns>/<name>.md` | `/` composer menu | `~/.pi/agent/prompts/<ns>-<name>.md` |
| `commands/<ns>/_index.md` | the bare `/<ns>` command | `~/.pi/agent/prompts/<ns>.md` |
| `skills/<name>/` | Skills page | `~/.agents/skills/<name>/` |
| `systems/<b>/skills/<name>/` | Skills page (with `--systems`) | `~/.agents/skills/<name>/` |
| `workflows/*.md` | Skills page | `~/.agents/skills/coco-workflow-<name>/` |
| `agents/*.md` | Subagents page | `~/.agents/subagents/coco-<name>.md` |
| `systems/<b>/agents/*.md` | Subagents page (with `--systems`) | `~/.agents/subagents/coco-<name>.md` |

Restart PI-Desktop, or open a new session, and the commands and skills appear.

## Options

| Flag | Effect |
|---|---|
| `--systems gsd,brain` | Add system bundles. Bundles are opt-in; the core install is skills, commands, agents and workflows. |
| `--dry-run` | Print the plan and write nothing. |
| `--uninstall` | Remove every file this adapter wrote, and nothing else. |
| `--force` | Replace files that are not ours. |
| `--source <dir>` | Install from a different checkout. |

`PI_AGENT_HOME` and `AGENTS_HOME` override the two target roots, which is what the
adapter's own tests use.

## Two deliberate behaviours

**It will not clobber your own work.** `~/.agents/skills` is a shared user
directory — the Skills page puts hand-written skills there too. Every file the
adapter writes carries a `Coco PI-Desktop adapter` marker, and it only ever
replaces or deletes a file carrying that marker. Anything else is reported and
left alone:

```
Left 1 existing path(s) untouched — not written by this adapter:
  ~/.agents/skills/my-skill
Re-run with --force to replace them.
```

**Descriptions are rewritten.** PI-Desktop caps skill descriptions at 240
characters, and several Coco skills exceed that. The adapter rewrites each
front matter block to `name` + `description` (+ `domain` where present), clipping
the description on a word boundary. Subagents get `name`, `description`, a tool
list (`Read, Glob, Grep, Bash` for reviewers, plus `Edit` and `Write` for the
agents that produce code) and `maxTurns: 80`, the host's own ceiling.

## Why this is a script and not a plugin

A PI-Desktop plugin may only reach the workspace or a directory the user picks at
runtime — `manifest.fs.root` accepts `"workspace"` or `"userSelected"` and nothing
else — so a plugin cannot write into `~/.agents` or `~/.pi/agent`. Files are the
interface, and this script writes them.

## Uninstall

```bash
bash adapters/pi-desktop/install.sh --uninstall
```

Removes the commands, skills and subagents it created. Skills you wrote yourself
are left in place.
