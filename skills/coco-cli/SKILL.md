---
name: coco-cli
description: Install, update, version-check, or uninstall the Coco open-source AI workflow framework via bin/coco.js. Use when setting up Coco on a machine, checking out the pinned release tag into an existing clone, checking the installed version, or removing it. Do not npx cocosuperintelligence until that name is published. Triggers on "install coco", "update coco", "set up coco", "coco cli", "uninstall coco".
domain: meta
---

<!-- Wrapper generated with the cli-anything skill. Methodology: HKUDS/CLI-Anything (https://github.com/HKUDS/CLI-Anything) — Apache-2.0. -->

# coco-cli — manage the Coco framework

Thin agent wrapper over `bin/coco.js` (package name `cocosuperintelligence`).
Drives the real CLI; does not reimplement it.

The npm name is reserved but **not published** on npmjs.com (registry 404). Do
not run `npx cocosuperintelligence` until it is — npx would execute whatever
first claims that name. From a clone, invoke `node bin/coco.js` instead.
`install` / `update` check out the release tag matching `package.json`
(`v1.2.0` today), not floating `main`.

## Commands

| Command | Purpose | Invocation |
|---|---|---|
| (default) | clone + install, auto-detecting the adapter | `node bin/coco.js` |
| `install` | clone + install with explicit flags | `node bin/coco.js install [flags]` |
| `update` | check out the pinned release tag | `node bin/coco.js update [dir]` |
| `uninstall` | remove symlinks + the clone | `node bin/coco.js uninstall [dir]` |
| `version` | print version + check for updates | `node bin/coco.js version` |
| `--help` | print usage | `node bin/coco.js --help` |

## Install flags (passed through to install.sh)

- `--adapter <name>` — one of `claude-code` | `cursor` | `codex` | `generic`
- `--systems <list>` — comma-separated, e.g. `gsd,brain,team`
- `--dry-run` — preview only, no writes

## Examples

- Install for Cursor: `node bin/coco.js install --adapter cursor`
- Selective systems: `node bin/coco.js install --systems gsd,brain --adapter claude-code`
- Preview without writing: `node bin/coco.js install --dry-run`
- Update an existing clone: `node bin/coco.js update`

## Output contract

This CLI is human-output-oriented; it has **no native `--json` mode**. For agent use:

- Treat **exit code 0 = success**, non-zero = failure.
- `version` prints `cocosuperintelligence vX.Y.Z` plus an update hint — parse the `vX.Y.Z` token.
- Capture stdout/stderr and branch on the exit code; do not assume machine-readable JSON.

## Errors

- A non-zero exit means an underlying git or `install.sh` step failed — surface the captured stdout + stderr to the user.
- Update checks contact `github.com` only; on network failure the version check degrades quietly and the command still runs.

## Notes

- Side effects: `install` clones the pinned release tag and creates symlinks; `uninstall` removes them. `install`/`update` re-fetch, so they are not no-ops. Branch checkouts still `git pull --ff-only` and are not force-moved onto an older pin.
- Network egress: `github.com` only. No telemetry. Disable update checks with `COCO_NO_UPDATE_CHECK=1`.
- Prerequisites: `node`, `git`, and `bash`. Do not use `npx cocosuperintelligence` until the name is published on npmjs.com.
