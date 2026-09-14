# Vendored bundle — reverse-skill

This directory contains a curated, reference-only subset of
[reverse-skill](https://github.com/zhaoxuya520/reverse-skill) by zhaoxuya520, a large security-skills
pack covering reverse engineering, penetration testing, and mobile/firmware/protocol analysis. It
follows the same bundle shape as `systems/hyperframes/` and `systems/gsd/`: one upstream licence at
the bundle root, a `skills/` tree underneath, and this README as the provenance and scope record.

## Provenance

| Field | Value |
|---|---|
| Upstream repository | https://github.com/zhaoxuya520/reverse-skill |
| Upstream branch | `main` |
| Commit fetched | `a3bdfffcf2e6a611a1cbdcc9a312be44527ac043` (2026-08-20) |
| Fetch method | `git clone --depth 1`, curated by hand from the local checkout |
| Curated on | 2026-08-20 |
| License | MIT — see [`LICENSE`](LICENSE), Copyright (c) 2026 zhaoxuya520 |

GitHub's API reported no detected licence for the upstream repository. That was a detector miss, not
a real ambiguity: the repository ships a plain, standard MIT `LICENSE` file at its root, reproduced
here unmodified.

## Why this is a curated subset, not the whole repository

Upstream is a "skill router" designed to be read by a coding agent and acted on immediately. Its
control layer — `RULES.md`, `CLAUDE.md`, `AGENTS.md`, and the top-level `skills/SKILL.md` — is
explicitly written to defeat exactly the kind of pause-and-confirm behavior an agent should have. It
states, close to verbatim: if you only reply "understood" or "got it" without executing the steps
below, you have failed; do not wait for the user to say "continue." Upstream even has its own writeup
of the technique, `skills/llm-security/references/agent-obedience-engineering.md` — a methodology
for exploiting an LLM's attention decay and its bias toward "helpfulness" so that a coding agent
skips confirmation and installs/executes things unprompted. Separately, `skills/ida-reverse/scripts/
install-autostart.ps1` registers a hidden Windows scheduled task that respawns a watchdog every
minute for 3650 days.

None of that belongs in a shared repository, wired up or not. This bundle keeps the substantive
reverse-engineering and security methodology — playbooks, checklists, tool references — and drops
the entire router/compliance/persistence apparatus. Concretely, for every included topic, only
`SKILL.md` and `references/**/*.md` were copied; every `scripts/` and `agents/*.yaml` (persona)
subdirectory was excluded regardless of topic.

It turned out the same compliance-ritual language upstream describes in the abstract is stamped as a
literal template onto every single one of its `SKILL.md` files: an `## ACTION REQUIRED（读完后立刻
执行）` block at the top instructing immediate action, and `## 路由上下文` / `## 任务完成自检`
blocks at the bottom tying the file back into the router and into a "did you actually comply"
self-check. Several files also carry a `## 按需自举（On-Demand Bootstrap）` block with real install
commands (`bootstrap-reverse.ps1`, `npm install -g ...`, `git clone ...`). All of that was stripped
from every file in this bundle — not just excluded from copying, but removed from the files that were
otherwise kept, since it's woven into the same document as the real methodology.

## What's included

Thirty-six topics, each `references/**/*.md` plus a stripped `SKILL.md` (methodology only — no
router contract, no bootstrap block, no self-check ritual):

| Category | Topics |
|---|---|
| General & language-specific reverse engineering | `reverse-engineering`, `apk-reverse`, `dotnet-reverse`, `js-reverse`, `go-rust-reverse`, `macos-reverse`, `mobile-reverse`, `browser-extension-reverse`, `ghidra-reverse`, `radare2` |
| Binary & exploit analysis | `binary-diff`, `patch-diff-exploit`, `pwn-chain`, `protocol-reverse` |
| Hardware & embedded | `firmware-pentest`, `hardware-security`, `radio-sdr`, `wifi-wireless`, `ot-ics` |
| Network, cloud & identity | `pentest-tools`, `cloud-k8s`, `database-security`, `api-security`, `email-security`, `identity-federation`, `windows-ad`, `attack-chain` |
| Application & LLM security | `code-audit`, `thick-client`, `browser-automation`, `llm-security`, `supply-chain-security` |
| Investigation & reporting | `digital-forensics`, `malware-analysis`, `threat-hunting`, `docs-generator` |

Each `SKILL.md` carries `name` + `user-invocable: true` + `description`, so it's directly
slash-invocable by its existing topic name (e.g. `apk-reverse`, `ghidra-reverse`), the same
convention used for `skills/coco-ads/SKILL.md` and `skills/openai-agents/SKILL.md`. They also appear
automatically in `skills/INDEX.md` once `scripts/build-index.py` runs, because that generator already
globs `systems/*/skills/*/SKILL.md` — no change to the generator was needed.

## What's excluded, and why

| Excluded | Reason |
|---|---|
| `RULES.md`, `CLAUDE.md`, `AGENTS.md`, `skills/SKILL.md`, `MASTER-ROUTING.md`, `routing.md`, `skills/config/routing.json` | The router/identity contract — the "act immediately, don't wait for confirmation" apparatus described above. |
| `skills/ops/**` | Scope-gate, role-map, and self-check machinery that exists to serve the router, not to teach a domain. |
| Every `scripts/` directory, `kali/**`, `skills/scripts/**` | Bootstrap, case-init, case-guard, master-route, and refresh-tool-index executables — install/automation scripts, not reference material. |
| `skills/ida-reverse/scripts/install-autostart.ps1`, `watchdog.ps1`, `run-supervisor.py` | The persistence layer — a hidden, indefinite scheduled task. |
| `skills/llm-security/references/agent-obedience-engineering.md` | The agent-manipulation methodology named above. |
| `CTF-Sandbox-Orchestrator/` | A large router-coupled competition persona system; out of scope for a reference bundle. |
| `burp-mcp-full/` | A separate buildable Java/Gradle/Node project — a tool, not a skill. |
| `skills/pentest-tools/src-hunter/` | A nested third-party project with its own `.claude-plugin/marketplace.json`; not independently audited, so not vendored here. |
| `skills/field-journal/`, `examples/`, `reports/` | Real case notes and a real engagement report — not methodology. |
| `skills/attack-chain/references/lifecycle-checklist.md` | The one reference file that turned out to be entirely about the excluded `ops/` apparatus (case-init, role-map, scope-contract, timeline-workitem) with no attack-chain domain content of its own once those are gone. |
| Every `agents/*.yaml` file | Per-topic AI-persona configs tied to the excluded router/orchestrator. |

Applying this exclusion list to a repository that ships one is a little on the nose: upstream's own
`skills/ops/skill-supply-chain.md` names this exact threat model — malicious or poisoned skills,
hidden install commands, and prompt injection hidden in a skill's own body — as what to check before
vendoring third-party skill content. That threat model was used as the actual checklist here; nothing
below is a claim that upstream is a bad-faith project, just that its delivery mechanism (an
agent-directed, auto-executing router) isn't something to carry into a shared repository regardless
of intent.

## Known residue

A handful of reference files kept in this bundle still name an excluded path in passing — e.g.
`pentest-tools/references/recon-pipeline.md` mentions `scope.md` and `case-guard.ps1` as part of
describing upstream's overall methodology, and a few files mention `field-journal/` or `tool-index`
similarly. These are incidental, descriptive mentions inside otherwise substantive methodology docs —
none contain an executable bootstrap command or compliance-ritual directive; that content was
specifically checked for and removed. They were left rather than rewritten because scrubbing every
name-drop across 147 files would mean rewriting prose that's otherwise fine, for no real risk
reduction. If a fully self-contained copy matters for a specific file, treat it the same way: check
what it actually says before relying on the pointer.

## Installing these skills locally

Claude Code discovers skills project-wide once they're indexed; no separate install step is needed
inside this repository. To use one of these skills from a different project, copy its directory into
that project's `.claude/skills/` (or your user-level `~/.claude/skills/`):

```bash
cp -r systems/reverse-skill/skills/apk-reverse ~/.claude/skills/
```

## Re-syncing from upstream

Re-run the curation from a fresh clone rather than patching in place — the compliance-ritual
boilerplate is woven into the same files as the real content, so a raw file diff against a newer
upstream commit will not tell you whether new boilerplate was added:

```bash
git clone --depth 1 https://github.com/zhaoxuya520/reverse-skill.git /tmp/reverse-skill-src
```

Then, for each topic listed above, copy only `SKILL.md` and `references/**/*.md`, excluding any
`scripts/` or `agents/` subdirectory and the `agent-obedience-engineering.md` file, and re-check each
`SKILL.md` for the `## ACTION REQUIRED`, `## 路由上下文` / `## 路由注册`, `## 按需自举` /
`## On-Demand Bootstrap`, and `## 任务完成自检` / `## Skill 自检清单` template blocks before
including it — upstream may reword these, so treat this as a fresh audit rather than a mechanical
diff.
