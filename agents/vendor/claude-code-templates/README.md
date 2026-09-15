# Vendored agents — claude-code-templates

This directory contains twenty-two agent definitions vendored verbatim from the
[claude-code-templates](https://github.com/davila7/claude-code-templates) project by Daniel (San) Ávila.
They are third-party files. CoCo does not author or maintain their contents, and they are kept
separate from the CoCo-authored agents in `agents/` so that the provenance boundary stays obvious.

## Provenance

| Field | Value |
|---|---|
| Upstream repository | https://github.com/davila7/claude-code-templates |
| Upstream path | `cli-tool/components/agents/` |
| Upstream branch | `main` |
| Fetched via | `claude-code-templates` CLI version 1.29.4 |
| Fetched on | 2026-08-07 |
| License | MIT — see [`LICENSE`](LICENSE) |

The upstream MIT licence requires that the copyright notice and permission notice accompany any
redistribution. That notice is preserved unmodified in [`LICENSE`](LICENSE) alongside these files.
CoCo's own MIT licence at the repository root covers CoCo-authored material and does not extend to
the files in this directory.

## Contents

Agents are grouped below by the upstream category they were published under. The category is
recorded here for traceability only; it has no effect on how the agents are loaded, because
Claude Code reads every agent from a flat directory.

### Development team

| Agent | Purpose |
|---|---|
| [`backend-architect`](backend-architect.md) | Backend service architecture, API paradigm selection, and monolith decomposition. |
| [`frontend-developer`](frontend-developer.md) | Frontend application development across React, Vue, and Angular. |
| [`fullstack-developer`](fullstack-developer.md) | Features spanning database, API, and frontend layers as one unit. |
| [`ui-ux-designer`](ui-ux-designer.md) | Interface design critique and usability review. |

### Architecture and review

| Agent | Purpose |
|---|---|
| [`architect-review`](architect-review.md) | Architectural consistency, SOLID principles, and layering review. |
| [`code-reviewer`](code-reviewer.md) | General code review for correctness and quality. |
| [`database-architect`](database-architect.md) | Data modelling, schema design, and database technology selection. |

### AI and data

| Agent | Purpose |
|---|---|
| [`ai-engineer`](ai-engineer.md) | End-to-end AI system architecture, training pipelines, and deployment. |
| [`prompt-engineer`](prompt-engineer.md) | Prompt design, optimisation, evaluation, and production prompt infrastructure. |
| [`search-specialist`](search-specialist.md) | Multi-source web research, fact-checking, and competitive intelligence. |

### Programming languages

| Agent | Purpose |
|---|---|
| [`rust-engineer`](rust-engineer.md) | Rust systems programming, ownership patterns, and performance work. |
| [`rust-pro`](rust-pro.md) | Idiomatic Rust, async/await, and safe concurrency. |

### Infrastructure and operations

| Agent | Purpose |
|---|---|
| [`cloud-architect`](cloud-architect.md) | Cloud infrastructure design, migration planning, and cost optimisation. |
| [`terraform`](terraform.md) | Terraform authoring and HCP Terraform workflow orchestration. |
| [`github-actions-expert`](github-actions-expert.md) | Secure CI/CD workflows, action pinning, OIDC, and least-privilege permissions. |
| [`dynatrace-expert`](dynatrace-expert.md) | Observability analysis across traces, logs, and Dynatrace findings. |
| [`incident-responder`](incident-responder.md) | Production incident coordination, mitigation, and post-mortems. |

### Security

| Agent | Purpose |
|---|---|
| [`security-auditor`](security-auditor.md) | Security audits, compliance gap analysis, and risk prioritisation. |
| [`penetration-tester`](penetration-tester.md) | Authorised offensive security testing and exploitation validation. |

### Product and visual analysis

| Agent | Purpose |
|---|---|
| [`product-manager`](product-manager.md) | Product strategy, prioritisation frameworks, and roadmap definition. |
| [`screenshot-ui-analyzer`](screenshot-ui-analyzer.md) | Visual component, layout, and design pattern analysis from screenshots. |
| [`screenshot-reviewer`](screenshot-reviewer.md) | Review of synthesised task lists for completeness and consistency. |

## Two things to be aware of

First, `architect-review.md` declares `name: architect-reviewer` in its front matter. Claude Code
identifies an agent by that `name` field rather than by its filename, so this agent must be invoked
as `architect-reviewer`. The mismatch originates upstream and has been left as-is to keep the
vendored files byte-identical to their source.

Second, these agents do not appear in [`agents/INDEX.md`](../../INDEX.md). The index generator at
`scripts/build-index.py` globs `agents/*.md` and `systems/*/agents/*.md`, neither of which matches a
nested vendor directory. This table is the catalogue for these twenty-two agents. The generator was
deliberately left unmodified so that vendoring third-party files does not change how CoCo's own
agent catalogue is built.

## Installing these agents locally

Claude Code discovers agents in `~/.claude/agents/` (user scope) and `<project>/.claude/agents/`
(project scope), both of which are flat directories. To use these agents, copy them into one of
those locations:

```bash
cp agents/vendor/claude-code-templates/*.md ~/.claude/agents/
```

Four of these filenames — `ai-engineer.md`, `code-reviewer.md`, `database-architect.md`, and
`ui-ux-designer.md` — collide with CoCo-authored agents of the same name. If `~/.claude/agents/`
contains symlinks back into this repository, copying over them will follow the symlink and overwrite
the CoCo originals in the working tree. Remove or rename those symlinks before copying.

## Re-syncing from upstream

To refresh these files against upstream, re-run the installer into a scratch directory and copy the
results back in. Setting `CCT_NO_TRACKING` suppresses the installer's telemetry, which otherwise
reports the component names and the target directory path to a third-party endpoint.

```bash
CCT_NO_TRACKING=true npx claude-code-templates@latest --agent development-team/ui-ux-designer,development-team/backend-architect,ai-specialists/prompt-engineer,development-team/fullstack-developer,development-team/frontend-developer,development-tools/code-reviewer,database/database-architect,expert-advisors/architect-review,data-ai/ai-engineer,programming-languages/rust-engineer,devops-infrastructure/cloud-architect,business-marketing/product-manager,programming-languages/rust-pro,ai-specialists/search-specialist,ui-analysis/screenshot-ui-analyzer,ui-analysis/screenshot-reviewer,security/security-auditor,security/penetration-tester,security/incident-responder,security/github-actions-expert,security/terraform,security/dynatrace-expert --directory <scratch-dir> --yes
```

The installer writes to `<scratch-dir>/.claude/agents/`. After it finishes, update the version and
date in the provenance table above, and copy the refreshed `LICENSE` if upstream has changed it.
