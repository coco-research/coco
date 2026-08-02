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

- **Best tool:** prd-generator (skill; the PM Studio suite refers to it as /pmstudio-prd, but the skill declares itself as `prd-generator` and that is the name that resolves)
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
  - This entry is a presentation generator, not an architecture tool. It formats an architecture for a review board audience; it does not analyse or decide one. For analysis use the Architecture Audit entry, and for the underlying structural facts use the Codebase Mapping and Code Graph Queries entries.
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

## Test Evidence Protocol

- **Best tool:** `team:evidence.md` (the canonical Test Evidence Protocol)
- **Quality notes:**
  - Any quality claim (tests pass, lint clean, coverage N%) MUST follow this protocol and produce `EVIDENCE.md`. Evidence or it didn't happen.
  - Determine the authoritative gate from CI config (`.github/workflows`, `Makefile`); use the CI-pinned tool versions, never a weaker local equivalent.
  - Skipped tests are `UNVERIFIED`, never a pass. Provision integration deps (e.g. Postgres + DSN) so gated tests actually run, or label the gap.
  - Coverage must be measured (`--cov --cov-branch`) and captured, not narrated.
- **Alternative:** None — this is mandatory for any pipeline that reports test/lint/coverage results.
- **When to skip tool:** Never for code that ships via PR. (Pure-docs runs have no test gate.)

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

## Architecture Conformance

- **Best tool:** `team:architecture.md` (the canonical Architecture Conformance Protocol), enforced by `skills/arch-index/scripts/validate_index.py`
- **Quality notes:**
  - Paths or it does not exist. The validator exit code is the gate, and a validator that cannot be executed is a BLOCK rather than a pass. There is deliberately no prose fallback, because a fallback an agent can narrate is the failure this gate exists to remove.
  - Structural drift only. A component whose datastore was swapped inside its own already-claimed directory produces no violation, so never report a clean drift result as evidence that the architecture is sound.
  - An index whose pinned commit is behind HEAD is `STALE`, and every conformance claim resting on it is `UNVERIFIED` until reconciled. Check currency before quoting the index.
  - The index sits at C4-Container altitude. Do not derive per-agent file ownership from it; a single component can legitimately own more than a thousand files.
- **Alternative:** None — this is mandatory for any action that consumes or produces `.arch/index.json`.
- **When to skip tool:** Never for an action that makes an architectural claim. Actions that make no such claim have no architecture gate.

## Codebase Mapping

- **Best tool:** gsd-map-codebase
- **Quality notes:**
  - Spawns four parallel mapper agents that write seven structured documents to `.planning/codebase/`: `STACK.md`, `INTEGRATIONS.md`, `ARCHITECTURE.md`, `STRUCTURE.md`, `CONVENTIONS.md`, `TESTING.md`, and `CONCERNS.md`. The orchestrator receives only confirmations, which keeps context usage low.
  - Prefer reading an existing `.planning/codebase/` map over re-deriving codebase structure inside an agent prompt. Re-deriving it wastes the tokens this tool exists to save.
- **Alternative:** technical-analyst reading the dependency manifest and directory tree directly
- **When to skip tool:** The repository already has a current `.planning/codebase/` map

## Code Graph Queries

- **Best tool:** gitnexus MCP (`context`, `impact`, `api_impact`, `detect_changes`, `route_map`, `tool_map`, `shape_check`, `query`, `cypher`)
- **Quality notes:**
  - A graph that knows real call edges cannot hallucinate a file path, which makes it strictly more reliable than any model-authored description of how modules relate.
  - Use `impact` and `api_impact` before changing a shared interface, and `detect_changes` to establish what actually moved between two commits.
- **Alternative:** `git diff --name-status` plus Grep for call sites
- **When to skip tool:** The repository is not indexed by gitnexus

## Architecture Diagrams

- **Best tool:** c4-architecture
- **Quality notes:**
  - Tabulates the five C4 levels with the audience and the when-to-create rule for each, so it prevents the common error of drawing a component diagram for a stakeholder who needed a context diagram.
  - Render the resulting Mermaid through `design:mermaid` (beautiful-mermaid), never through the standard Mermaid CDN.
- **Alternative:** Direct Mermaid authoring by an engineering role
- **When to skip tool:** A current diagram already exists for the level being asked about

## Interface Contract Design

- **Best tool:** api-design-principles
- **Quality notes:** No findings yet
- **Alternative:** Direct design by senior-backend-eng
- **When to skip tool:** The change introduces no new or modified public interface

## Architecture Audit

- **Best tool:** /util:architecture-review
- **Quality notes:**
  - Offers a six-part analysis framework with `--modules`, `--patterns`, `--dependencies`, and `--security` scopes, so pass the scope that matches the question rather than running the full audit by default.
- **Alternative:** /team review action (full 4-layer pipeline)
- **When to skip tool:** A full architectural audit is out of scope for the run

## Architecture Doc Suite

- **Best tool:** /util:create-architecture-documentation
- **Quality notes:**
  - Produces C4 model, arc42, ADR, PlantUML, and Structurizr output. Prefer this over hand-authoring whenever the deliverable is a formal published architecture document.
- **Alternative:** /team document action with technical-writer in Layer 2
- **When to skip tool:** No formal published document is required

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
