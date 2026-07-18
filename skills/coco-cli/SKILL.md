---
name: coco-cli
description: Install, update, version-check, or uninstall the Coco open-source AI workflow framework via its CLI (@coco-research/coco-cli, run with npx). Use when setting up Coco on a machine, pulling the latest into an existing clone, checking the installed version, or removing it. Triggers on "install coco", "update coco", "set up coco", "coco cli", "uninstall coco".
---

<!-- Wrapper generated with the cli-anything skill. Methodology: HKUDS/CLI-Anything (https://github.com/HKUDS/CLI-Anything) — Apache-2.0. -->

# coco-cli — manage the Coco framework

Thin agent wrapper over `@coco-research/coco-cli` (run via `npx`). Drives the real CLI; does not reimplement it.

## Commands

| Command | Purpose | Invocation |
|---|---|---|
| (default) | clone + install, auto-detecting the adapter | `npx @coco-research/coco-cli` |
| `install` | clone + install with explicit flags | `npx @coco-research/coco-cli install [flags]` |
| `update` | pull latest in an existing clone | `npx @coco-research/coco-cli update [dir]` |
| `uninstall` | remove symlinks + the clone | `npx @coco-research/coco-cli uninstall [dir]` |
| `version` | print version + check for updates | `npx @coco-research/coco-cli version` |
| `--help` | print usage | `npx @coco-research/coco-cli --help` |

## Install flags (passed through to install.sh)

- `--adapter <name>` — one of `claude-code` | `cursor` | `codex` | `generic`
- `--systems <list>` — comma-separated, e.g. `gsd,brain,team`
- `--dry-run` — preview only, no writes

## Examples

- Install for Cursor: `npx @coco-research/coco-cli install --adapter cursor`
- Selective systems: `npx @coco-research/coco-cli install --systems gsd,brain --adapter claude-code`
- Preview without writing: `npx @coco-research/coco-cli install --dry-run`
- Update an existing clone: `npx @coco-research/coco-cli update`

## Output contract

This CLI is human-output-oriented; it has **no native `--json` mode**. For agent use:

- Treat **exit code 0 = success**, non-zero = failure.
- `version` prints `@coco-research/coco-cli vX.Y.Z` plus an update hint — parse the `vX.Y.Z` token.
- Capture stdout/stderr and branch on the exit code; do not assume machine-readable JSON.

## Errors

- A non-zero exit means an underlying git or `install.sh` step failed — surface the captured stdout + stderr to the user.
- Update checks contact `github.com` only; on network failure the version check degrades quietly and the command still runs.

## Notes

- Side effects: `install` clones the repo and creates symlinks; `uninstall` removes them. `install`/`update` re-pull, so they are not no-ops.
- Network egress: `github.com` only. No telemetry. Disable update checks with `COCO_NO_UPDATE_CHECK=1`.
- Prerequisites: `node`/`npx`, `git`, and `bash`.
