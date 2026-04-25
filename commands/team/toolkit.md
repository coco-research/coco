# Team Toolkit Registry

> **Purpose:** Maps capabilities to the best available tool/skill.
> Layer 2 agents consult this before doing work — they use the best tool
> available, not a hardcoded one.
>
> **How it's used:** The orchestrator (team.md) reads this file, extracts
> entries relevant to the current action, and inlines them into Layer 2
> agent prompts. Agents never read this file directly.
>
> **Updating:** After every /team run, Layer 4 principals may recommend
> toolkit updates based on Layer 3 review findings. The orchestrator
> applies these updates.
>
> **Adding new tools:** When you discover a new repo, skill, or tool,
> add an entry here. It becomes available to all future /team runs.

---

## PRD Generation

- **Best tool:** /pmstudio-prd
- **Quality notes:**
  - Always include a rollback plan in the launch section
  - Make success metrics measurable (not "improve UX" — use quantitative targets)
  - NFR section tends to be generic — add project-specific NFRs
- **Alternative:** Direct writing by senior-pm role
- **When to skip tool:** PRD < 3 sections or highly specialized format

## Stakeholder Communications

- **Best tool:** /pmstudio-comms
- **Quality notes:**
  - Subject lines sometimes too formal — shorten and make actionable
  - Add TL;DR for emails > 3 paragraphs
- **Alternative:** Direct writing by comms-specialist role
- **When to skip tool:** Simple 1-paragraph updates

## Architecture Review Decks

- **Best tool:** /pmstudio-arb
- **Quality notes:**
  - 11-slide consulting format is solid
  - Data visualization sections need improvement — pair with data-viz-specialist
- **Alternative:** Direct creation by structured-presentation + narrative-architect roles
- **When to skip tool:** Non-consulting format presentations

## Meeting Notes

- **Best tool:** /pmstudio-meeting-notes
- **Quality notes:** No findings yet
- **Alternative:** Direct writing by business-analyst role
- **When to skip tool:** Quick standup notes (< 5 bullet points)

## Change Logs

- **Best tool:** /pmstudio-changelog
- **Quality notes:** No findings yet
- **Alternative:** Direct writing from git log
- **When to skip tool:** Single-item changes

## Disaster Recovery Plans

- **Best tool:** /pmstudio-dr
- **Quality notes:** No findings yet
- **Alternative:** Direct writing by senior-cloud-architect + sre-devops roles
- **When to skip tool:** Non-SaaS products

## Incident Response Plans

- **Best tool:** /pmstudio-irp
- **Quality notes:** No findings yet
- **Alternative:** Direct writing by sre-devops role
- **When to skip tool:** Internal tools with no SLA requirements

## Recovery Runbooks

- **Best tool:** /pmstudio-recovery
- **Quality notes:** No findings yet
- **Alternative:** Direct writing by sre-devops role
- **When to skip tool:** When DR plan doesn't exist yet

## Code Implementation

- **Best tool:** Superpowers pipeline (brainstorming → writing-plans → executing-plans)
- **Quality notes:**
  - TDD enforcement is strong
  - Plan granularity could be finer for complex features
- **Alternative:** Direct coding by engineering roles
- **When to skip tool:** Single-file changes or < 30 lines of code

## Project Orchestration (Multi-Phase)

- **Best tool:** GSD (/gsd:plan-phase → /gsd:execute-phase → /gsd:verify-work)
- **Quality notes:**
  - Good for multi-phase projects with persistent state
  - Overkill for single-session tasks
- **Alternative:** Manual phasing with /team plan
- **When to skip tool:** Single-session scope or < 3 phases

## Test-Driven Development

- **Best tool:** superpowers:test-driven-development
- **Quality notes:** No findings yet
- **Alternative:** Direct test writing by qa-test-architect role
- **When to skip tool:** When adding tests to existing test suite (just follow patterns)

## Systematic Debugging

- **Best tool:** superpowers:systematic-debugging
- **Quality notes:** No findings yet
- **Alternative:** Direct debugging by relevant engineering role
- **When to skip tool:** Obvious bugs (typos, wrong variable names)

## Code Review

- **Best tool:** superpowers:requesting-code-review
- **Quality notes:** No findings yet
- **Alternative:** /team review action (uses full 4-layer pipeline)
- **When to skip tool:** Quick sanity checks on < 50 lines

## Document Sync

- **Best tool:** /pmstudio-sync
- **Quality notes:** No findings yet
- **Alternative:** Manual sync
- **When to skip tool:** Single-document updates

## NFR Audit

- **Best tool:** /pmstudio-nfr
- **Quality notes:** No findings yet
- **Alternative:** Manual checklist review
- **When to skip tool:** Early-stage projects (not enough artifacts to audit)

## Confluence Publishing

- **Best tool:** Direct curl REST API calls (v2)
- **Quality notes:**
  - MCP tools don't reliably load as deferred tools in Claude Code
  - Always fetch current version before updating (version increment required)
  - Images use ac:image storage format — upload as attachments first
- **Alternative:** Manual publishing
- **When to skip tool:** N/A — curl is the reliable path

---

## Adding New Tools

When you discover a new tool, repo, or skill, add an entry following this template:

```
## [Capability Name]

- **Best tool:** [skill name or command]
- **Quality notes:** [empty until first review]
- **Alternative:** [fallback approach]
- **When to skip tool:** [when direct work is faster]
```
