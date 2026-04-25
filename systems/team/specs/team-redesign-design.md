# /team Redesign — Cross-Functional Product Team with Learning Loop

**Date:** 2026-03-19
**Author:** Coco Inc
**Status:** Approved
**Scope:** Complete redesign of `/team` command system

## Problem

The current `/team` skill spawns identical clone agents (reviewer-1, reviewer-2, etc.) with the same prompt and perspective. Five identical reviewers find the same bugs five times instead of finding five different categories of issues. There's no seniority hierarchy, no domain specialization, no learning from past runs, and no integration with existing tools (PM Studio, Superpowers, GSD).

## Goal

A cross-functional product team system that:
1. Spawns diverse specialists (not clones) with distinct roles, seniority, and domain expertise
2. Runs a 4-layer pipeline (Research → Execute → Review → Synthesize) like an enterprise team
3. Adapts role selection to the project domain and action type
4. Uses a swappable toolkit registry so new tools/repos can be added without rewriting skills
5. Learns from every run via a feedback loop that improves output quality over time

## Architecture

```
┌─────────────────────────────────────────────────┐
│  /team <action> <scope> [--domain X] [--roles X]│
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Domain Detector    │ ← README, CLAUDE.local.md, file types
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Role Selector      │ ← picks from 34-role roster
         │                     │   based on domain + action + overrides
         └─────────┬──────────┘
                   │
    ┌──────────────▼──────────────────┐
    │     LAYER 1: RESEARCH           │
    │  2-6 analysts/researchers       │
    │  Output: CONTEXT-BRIEF.md       │
    └──────────────┬──────────────────┘
                   │ orchestrator compresses handoff
    ┌──────────────▼──────────────────┐
    │     LAYER 2: EXECUTION          │
    │  2-5 specialists                │
    │  Reads: team-toolkit.md         │
    │  Reads: team-feedback.md        │
    │  Uses best available tools      │
    │  Output: deliverables           │
    └──────────────┬──────────────────┘
                   │ orchestrator compresses handoff
    ┌──────────────▼──────────────────┐
    │     LAYER 3: SPECIALIST REVIEW  │
    │  2-3 review specialists         │
    │  Critiques Layer 2 output       │
    │  Output: CRITIQUE-SUMMARY.md    │
    └──────────────┬──────────────────┘
                   │ orchestrator compresses handoff
    ┌──────────────▼──────────────────┐
    │     LAYER 4: SYNTHESIS          │
    │  1-2 principals                 │
    │  Final output + feedback report │
    │  Appends to team-feedback.md    │
    │  Updates team-toolkit.md notes  │
    └──────────────────────────────────┘
```

### Handoff Documents

| Handoff | Content | Max Size |
|---------|---------|----------|
| L1 → L2 | `CONTEXT-BRIEF.md`: domain, key files, constraints, risks | ~200 lines |
| L2 → L3 | `REVIEW-PACKAGE.md`: what was built, tools used, decisions | ~300 lines |
| L3 → L4 | `CRITIQUE-SUMMARY.md`: findings by severity, file paths, quotes | ~200 lines |
| L4 → User | Final output + feedback entry appended to team-feedback.md | varies |

---

## Actions

| Action | Purpose | L1 Size | L2 Size | L3 Size | L4 Size |
|--------|---------|---------|---------|---------|---------|
| `/team research <topic>` | Deep multi-angle investigation | 4-6 | 1-2 | 1 | 1 |
| `/team think <problem>` | Analysis, brainstorm, options | 3-4 | 2-3 | 2 | 1 |
| `/team develop <feature>` | Build working code/config | 2 | 3-5 | 2-3 | 1 |
| `/team review <scope>` | Audit existing work | 2 | 3-5 | 2 | 1 |
| `/team document <what>` | Create documents (PRD, guide) | 2 | 2-3 | 3 | 1 |
| `/team present <what>` | Build presentations | 2 | 3-4 | 2 | 1 |
| `/team communicate <what>` | Stakeholder comms | 1-2 | 2-3 | 2-3 | 1 |
| `/team test <scope>` | Write tests, find gaps | 2 | 3-4 | 1-2 | 1 |
| `/team fix <issue>` | Debug and fix | 2 | 2-4 | 2 | 1 |
| `/team plan <scope>` | Project plans, roadmaps | 2-3 | 2-3 | 2 | 1 |

---

## Role Roster (34 Roles)

### Leadership — Layer 4 (Synthesis)

| # | Role ID | Role | Seniority | Focus | Domain Tags |
|---|---------|------|-----------|-------|-------------|
| 1 | principal-architect | Principal Architect | 20+ yr | System design, trade-offs, final technical synthesis | all |
| 2 | principal-pm | Principal Product Manager | 20+ yr | Business logic, requirements, stakeholder strategy | all |
| 3 | principal-ux | Principal UX Director | 20+ yr | Information architecture, design systems, UX strategy | frontend, docs, product |

### Research & Analysis — Layer 1

| # | Role ID | Role | Seniority | Focus | Domain Tags |
|---|---------|------|-----------|-------|-------------|
| 4 | domain-researcher | Domain Researcher | 10+ yr | Industry context, competitive analysis, prior art | all |
| 5 | technical-analyst | Technical Analyst | 10+ yr | Codebase mapping, dependency analysis, architecture | backend, frontend, infra |
| 6 | business-analyst | Business Analyst | 10+ yr | Requirements traceability, gap analysis, stakeholder mapping | product, pm |
| 7 | ux-researcher | UX Researcher | 10+ yr | User flows, onboarding analysis, navigation audit | frontend, docs, product |
| 8 | security-analyst | Security Analyst | 10+ yr | Threat modeling, OWASP scan, compliance gaps | all |

### Engineering — Layer 2 (Execution)

| # | Role ID | Role | Seniority | Focus | Domain Tags |
|---|---------|------|-----------|-------|-------------|
| 9 | senior-cloud-architect | Senior Cloud Architect | 15+ yr | AWS/Azure/GCP, scalability, cost, DR, IaC | infrastructure, backend |
| 10 | senior-backend-eng | Senior Backend Engineer | 15+ yr | API design, data modeling, performance, microservices | backend, api |
| 11 | senior-frontend-eng | Senior Frontend Engineer | 15+ yr | React/Vue, component patterns, state, a11y | frontend |
| 12 | senior-data-eng | Senior Data Engineer | 15+ yr | Pipelines, schemas, ETL, analytics | data, backend |
| 13 | senior-mobile-eng | Senior Mobile Engineer | 15+ yr | iOS/Android, React Native, Flutter | mobile |
| 14 | sre-devops | SRE / DevOps Specialist | 12+ yr | CI/CD, monitoring, incident response, Terraform | infrastructure |
| 15 | mcp-integration | MCP / Integration Specialist | 10+ yr | MCP servers, API connectors, Jira/Confluence/SharePoint | integrations |
| 16 | qa-test-architect | QA / Test Architect | 12+ yr | Coverage strategy, test design, edge cases, regression | all |
| 17 | performance-eng | Performance Engineer | 12+ yr | Load testing, latency profiling, optimization | backend, frontend |

### Content & Communications — Layer 2 (Execution)

| # | Role ID | Role | Seniority | Focus | Domain Tags |
|---|---------|------|-----------|-------|-------------|
| 18 | senior-pm | Senior Product Manager | 12+ yr | PRDs, roadmaps, prioritization, stakeholder management | product, pm |
| 19 | senior-ux-designer | Senior UX Designer | 12+ yr | Wireframes, design patterns, accessibility, user testing | frontend, product |
| 20 | technical-writer | Technical Writer | 10+ yr | Documentation structure, API docs, onboarding guides | docs, all |
| 21 | comms-specialist | Communications Specialist | 10+ yr | Launch emails, status updates, stakeholder announcements | comms, product |
| 22 | marketing-specialist | Marketing Specialist | 10+ yr | Positioning, messaging, go-to-market, pitch decks | comms, product |
| 23 | confluence-specialist | Confluence Specialist | 8+ yr | Page structure, space organization, templates, macros | docs, integrations |
| 24 | jira-specialist | Jira Specialist | 8+ yr | Workflow design, story writing, sprint planning, JQL | pm, integrations |

### Presentation — Layer 2 (Execution)

| # | Role ID | Role | Seniority | Focus | Domain Tags |
|---|---------|------|-----------|-------|-------------|
| 25 | coco-inc-presentation | Coco Inc Presentation Specialist | 15+ yr | Pyramid principle, MECE, SCR, action titles, one message per slide | docs, comms, product |
| 26 | apple-presentation | Apple/Keynote Design Specialist | 15+ yr | Minimalist storytelling, hero imagery, progressive reveal, whitespace | docs, comms, product |
| 27 | data-viz-specialist | Data Visualization Specialist | 12+ yr | Chart selection, data-ink ratio, Tufte principles, waterfall/bridge charts | docs, data, product |
| 28 | narrative-architect | Presentation Narrative Architect | 15+ yr | Storyline flow, audience framing, executive vs technical decks | docs, comms, product |

### Review Specialists — Layer 3

| # | Role ID | Role | Seniority | Focus | Domain Tags |
|---|---------|------|-----------|-------|-------------|
| 29 | doc-quality | Document Quality Specialist | 12+ yr | Structure, completeness, clarity, section flow | docs, all |
| 30 | grammar-editor | Grammar & Style Editor | 10+ yr | Tone, grammar, readability, consistency, Coco Inc voice | all |
| 31 | standards-reviewer | Standards Compliance Reviewer | 10+ yr | Template conformance, branding, formatting standards | docs, comms |
| 32 | domain-accuracy | Domain Accuracy Reviewer | 15+ yr | Technical claims, factual correctness, architecture validity | all |
| 33 | accessibility-specialist | Accessibility Specialist | 10+ yr | WCAG, screen readers, keyboard nav, inclusive design | frontend |
| 34 | slide-quality | Slide Quality Reviewer | 12+ yr | Action titles, one takeaway per slide, source citations, alignment | docs, comms |

### Layer Assignment Rules

- **Layer 1** picks from Research & Analysis (roles 4-8)
- **Layer 2** picks from Engineering + Content + Presentation (roles 9-28) based on action
- **Layer 3** picks from Review Specialists (roles 29-34) based on what Layer 2 produced
- **Layer 4** picks 1-2 from Leadership (roles 1-3) based on whether output is technical or product-focused

### Role Selection: Domain + Action Matrix

For each action, the selector uses domain tags to filter eligible roles, then picks the most relevant:

**`/team develop` in a `backend, aws, api` project:**
- L1: technical-analyst, security-analyst
- L2: senior-backend-eng, senior-cloud-architect, qa-test-architect
- L3: domain-accuracy, doc-quality
- L4: principal-architect

**`/team present ARB deck` in a `backend, aws` project:**
- L1: technical-analyst, business-analyst
- L2: coco-inc-presentation, data-viz-specialist, narrative-architect
- L3: slide-quality, grammar-editor
- L4: principal-pm

**`/team communicate launch email` in a `product` project:**
- L1: business-analyst
- L2: comms-specialist, marketing-specialist
- L3: grammar-editor, standards-reviewer
- L4: principal-pm

User can override with `--roles "security-analyst,performance-eng"` to force specific roles.

---

## Toolkit Registry

File: `~/.claude/commands/team-toolkit.md`

Maps capabilities to best available tools. Layer 2 agents read this before doing work.

### Structure per Entry

```markdown
## Capability: [Name]
- **Best tool:** [skill or command]
- **Quality notes:** [accumulated feedback from Layer 3 reviews]
- **Alternative:** [fallback tool]
- **When to skip:** [when to just do it directly]
```

### Starter Entries

| Capability | Best Tool | Alternative |
|-----------|-----------|-------------|
| PRD Generation | /pmstudio-prd | core/skills/pm-core/prd-generator |
| Stakeholder Comms | /pmstudio-comms | direct writing |
| Architecture Decks | /pmstudio-arb | direct writing |
| Meeting Notes | /pmstudio-meeting-notes | direct writing |
| Change Logs | /pmstudio-changelog | direct writing |
| DR Plans | /pmstudio-dr | direct writing |
| Incident Response | /pmstudio-irp | direct writing |
| Recovery Runbooks | /pmstudio-recovery | direct writing |
| Code Implementation | superpowers (brainstorm → plan → execute) | direct coding |
| Project Orchestration | GSD (/gsd:plan-phase → execute) | manual phasing |
| TDD | superpowers:test-driven-development | direct testing |
| Debugging | superpowers:systematic-debugging | direct debugging |
| Code Review | superpowers:requesting-code-review | manual review |
| Doc Sync | /pmstudio-sync | manual sync |
| NFR Audit | /pmstudio-nfr | manual audit |

---

## Feedback Loop

File: `~/.claude/commands/team-feedback.md`

### How It Works

1. Layer 3 review specialists produce critiques of Layer 2 output
2. Layer 4 principal reads critiques, produces final output + a feedback entry
3. Feedback entry appended to `team-feedback.md`
4. If finding is tool-specific, orchestrator also updates `team-toolkit.md` quality notes
5. Next `/team` run: Layer 2 agents read both files before starting work

### Entry Format

```markdown
### YYYY-MM-DD | /team <action> | <scope>
- **Tool reviewed:** [skill/command name]
- **Reviewer role:** [which Layer 3 specialist]
- **Finding:** [what was wrong]
- **Recommendation:** [specific fix]
- **Status:** applied | pending
- **Impact:** high | medium | low
```

### The Compounding Effect

- Run 1: Tool produces baseline output → Layer 3 finds 5 issues → 5 feedback entries
- Run 2: Layer 2 reads feedback, applies corrections → Layer 3 finds 2 new issues
- Run 5: Layer 2 output is high quality → Layer 3 finds only minor polish items
- Run N: Team output quality exceeds any individual tool because corrections accumulate

---

## Orchestration Flow (What team.md Router Does)

```
Step 1: PARSE
  Extract action and scope from arguments
  Check for --domain and --roles overrides

Step 2: DETECT DOMAIN
  Read: README.md, CLAUDE.local.md, package.json, file types
  Produce: { languages, framework, cloud, domain, tags[] }
  User --domain override replaces auto-detected domain

Step 3: READ TOOLKIT + FEEDBACK
  Read: team-toolkit.md → available tools and quality notes
  Read: team-feedback.md → past findings and recommendations

Step 4: SELECT ROLES (from team-roles.md)
  Filter roster by: domain tags matching project + action type
  Apply layer sizing rules for the action
  Apply --roles override if specified
  Produce: { L1: [roles], L2: [roles], L3: [roles], L4: [roles] }

Step 5: EXECUTE LAYER 1
  TeamCreate(team_name="{action}-squad")
  Spawn L1 agents in parallel (mode: default, read-only)
  Wait for all L1 agents to complete
  Orchestrator writes CONTEXT-BRIEF.md (compressed L1 output)

Step 6: EXECUTE LAYER 2
  Spawn L2 agents in parallel (mode: bypassPermissions for build/fix,
  default for review/document)
  Each L2 agent prompt includes: CONTEXT-BRIEF.md + toolkit entries
  + feedback entries relevant to their tools
  Wait for all L2 agents to complete
  Orchestrator writes REVIEW-PACKAGE.md (compressed L2 output)

Step 7: EXECUTE LAYER 3
  Spawn L3 agents in parallel (mode: default, read-only)
  Each L3 agent reviews REVIEW-PACKAGE.md + actual deliverables
  Wait for all L3 agents to complete
  Orchestrator writes CRITIQUE-SUMMARY.md

Step 8: EXECUTE LAYER 4
  Spawn L4 agent (1-2 principals)
  Reads: CONTEXT-BRIEF + REVIEW-PACKAGE + CRITIQUE-SUMMARY
  Produces: final output + feedback entries
  Orchestrator appends feedback to team-feedback.md
  Updates team-toolkit.md quality notes if warranted

Step 9: REPORT + CLEANUP
  Present final output to user
  Shutdown all agents
  TeamDelete
```

---

## File Structure

### Files to Create

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `~/.claude/commands/team-roles.md` | 34 roles with full system prompts | ~600 |
| `~/.claude/commands/team-toolkit.md` | Capability → tool registry | ~80 |
| `~/.claude/commands/team-feedback.md` | Learning loop entries | ~20 (starter) |
| `~/.claude/commands/team-develop.md` | Build pipeline | ~120 |
| `~/.claude/commands/team-document.md` | Documentation pipeline | ~100 |
| `~/.claude/commands/team-present.md` | Presentation pipeline | ~100 |
| `~/.claude/commands/team-communicate.md` | Comms pipeline | ~100 |
| `~/.claude/commands/team-think.md` | Analysis/brainstorm pipeline | ~100 |

### Files to Modify

| File | Change | Est. Lines |
|------|--------|-----------|
| `~/.claude/commands/team.md` | Complete rewrite — new router with domain detection, role selection, 4-layer orchestration | ~150 |
| `~/.claude/commands/team-review.md` | Rewrite with 4-layer pipeline + diverse roles | ~120 |
| `~/.claude/commands/team-research.md` | Rewrite with 4-layer pipeline | ~100 |
| `~/.claude/commands/team-test.md` | Rewrite with 4-layer pipeline | ~100 |
| `~/.claude/commands/team-fix.md` | Rewrite with 4-layer pipeline | ~100 |
| `~/.claude/commands/team-plan.md` | Rewrite with 4-layer pipeline | ~100 |
| `~/.claude/commands/team-reanalyse.md` | Rewrite with 4-layer pipeline | ~100 |
| `~/.claude/commands/team-scrape.md` | Rewrite with 4-layer pipeline | ~100 |

### Files to Delete

| File | Reason |
|------|--------|
| `~/.claude/commands/team-build.md` | Replaced by team-develop.md |

### Total Scope

~2,000 lines across 17 files (8 new, 8 modified, 1 deleted).

---

## Success Criteria

- [ ] `/team review` spawns diverse specialists (not clones) with role-specific prompts
- [ ] `/team develop` runs 4-layer pipeline with research → build → review → synthesis
- [ ] `/team present` activates presentation specialists (Coco Inc, Apple, data viz, narrative)
- [ ] `/team document` integrates with PM Studio via toolkit registry
- [ ] Domain auto-detection correctly identifies project context from files
- [ ] `--domain` and `--roles` overrides work
- [ ] team-toolkit.md is read by Layer 2 agents before executing
- [ ] team-feedback.md is appended after every run
- [ ] Handoff documents (CONTEXT-BRIEF, REVIEW-PACKAGE, CRITIQUE-SUMMARY) stay under size limits
- [ ] All 10 actions route correctly through team.md
- [ ] Backward compatible: existing `/team stop` still works
