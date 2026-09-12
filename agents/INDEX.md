# Agents Index

Auto-generated. Run `python3 scripts/build-index.py` to refresh.

**Total: 34 agents** — 10 core, 24 across 1 bundles.

## Core agents (10)

| Agent | Description |
|-------|-------------|
| [ai-engineer](ai-engineer.md) | Senior AI engineer for architecting, implementing, and optimizing end-to-end AI systems — from model selection and training pipelines to production deployment,  |
| [code-reviewer](code-reviewer.md) | Senior code and architecture reviewer for comprehensive quality, security, performance, and architectural integrity analysis. Use proactively after writing or m |
| [data-specialist](data-specialist.md) | Senior data specialist covering exploratory analysis, statistical modeling, machine learning, experimentation, SQL optimization, query design, and performance t |
| [database-architect](database-architect.md) | Database architecture and design specialist. Use PROACTIVELY for database design decisions, data modeling, scalability planning, microservices data patterns, da |
| [mcp-specialist](mcp-specialist.md) | MCP (Model Context Protocol) specialist covering server/client development, configuration, troubleshooting, tool setup, architecture, transport layers, and prot |
| [pm-advisor](pm-advisor.md) | Product management advisor for feature planning, issue creation, prioritization, and data-driven product decisions. Use proactively when planning features, writ |
| [refactoring-specialist](refactoring-specialist.md) | Senior refactoring specialist for transforming complex, poorly structured code into clean, maintainable systems. Use proactively when complexity metrics spike,  |
| [test-guardian](test-guardian.md) | Ensures tests actually test what they claim. Catches tautological assertions, mock leakage, tests that pass for wrong reasons, missing edge cases. Run after wri |
| [typescript-pro](typescript-pro.md) | Advanced TypeScript specialist for type-level programming, complex generics, end-to-end type safety, monorepo architecture, and large-scale migrations. Use when |
| [ui-ux-designer](ui-ux-designer.md) | Research-backed UI/UX design critic providing opinionated, evidence-based feedback on interfaces. Use proactively when reviewing UI code, designing layouts, cho |

## Bundle: gsd (24 agents)

| Agent | Description |
|-------|-------------|
| [gsd-advisor-researcher](../systems/gsd/agents/gsd-advisor-researcher.md) | Researches a single gray area decision and returns a structured comparison table with rationale. Spawned by discuss-phase advisor mode. |
| [gsd-assumptions-analyzer](../systems/gsd/agents/gsd-assumptions-analyzer.md) | Deeply analyzes codebase for a phase and returns structured assumptions with evidence. Spawned by discuss-phase assumptions mode. |
| [gsd-code-fixer](../systems/gsd/agents/gsd-code-fixer.md) | Applies fixes to code review findings from REVIEW.md. Reads source files, applies intelligent fixes, and commits each fix atomically. Spawned by /gsd-code-revie |
| [gsd-code-reviewer](../systems/gsd/agents/gsd-code-reviewer.md) | Reviews source files for bugs, security issues, and code quality problems. Produces structured REVIEW.md with severity-classified findings. Spawned by /gsd-code |
| [gsd-codebase-mapper](../systems/gsd/agents/gsd-codebase-mapper.md) | Explores codebase and writes structured analysis documents. Spawned by map-codebase with a focus area (tech, arch, quality, concerns). Writes documents directly |
| [gsd-debugger](../systems/gsd/agents/gsd-debugger.md) | Investigates bugs using scientific method, manages debug sessions, handles checkpoints. Spawned by /gsd-debug orchestrator. |
| [gsd-doc-verifier](../systems/gsd/agents/gsd-doc-verifier.md) | Verifies factual claims in generated docs against the live codebase. Returns structured JSON per doc. |
| [gsd-doc-writer](../systems/gsd/agents/gsd-doc-writer.md) | Writes and updates project documentation. Spawned with a doc_assignment block specifying doc type, mode (create/update/supplement), and project context. |
| [gsd-executor](../systems/gsd/agents/gsd-executor.md) | Executes GSD plans with atomic commits, deviation handling, checkpoint protocols, and state management. Spawned by execute-phase orchestrator or execute-plan co |
| [gsd-integration-checker](../systems/gsd/agents/gsd-integration-checker.md) | Verifies cross-phase integration and E2E flows. Checks that phases connect properly and user workflows complete end-to-end. |
| [gsd-intel-updater](../systems/gsd/agents/gsd-intel-updater.md) | Analyzes codebase and writes structured intel files to .planning/intel/. |
| [gsd-nyquist-auditor](../systems/gsd/agents/gsd-nyquist-auditor.md) | Fills Nyquist validation gaps by generating tests and verifying coverage for phase requirements |
| [gsd-phase-researcher](../systems/gsd/agents/gsd-phase-researcher.md) | Researches how to implement a phase before planning. Produces RESEARCH.md consumed by gsd-planner. Spawned by /gsd-plan-phase orchestrator. |
| [gsd-plan-checker](../systems/gsd/agents/gsd-plan-checker.md) | Verifies plans will achieve phase goal before execution. Goal-backward analysis of plan quality. Spawned by /gsd-plan-phase orchestrator. |
| [gsd-planner](../systems/gsd/agents/gsd-planner.md) | Creates executable phase plans with task breakdown, dependency analysis, and goal-backward verification. Spawned by /gsd-plan-phase orchestrator. |
| [gsd-project-researcher](../systems/gsd/agents/gsd-project-researcher.md) | Researches domain ecosystem before roadmap creation. Produces files in .planning/research/ consumed during roadmap creation. Spawned by /gsd-new-project or /gsd |
| [gsd-research-synthesizer](../systems/gsd/agents/gsd-research-synthesizer.md) | Synthesizes research outputs from parallel researcher agents into SUMMARY.md. Spawned by /gsd-new-project after 4 researcher agents complete. |
| [gsd-roadmapper](../systems/gsd/agents/gsd-roadmapper.md) | Creates project roadmaps with phase breakdown, requirement mapping, success criteria derivation, and coverage validation. Spawned by /gsd-new-project orchestrat |
| [gsd-security-auditor](../systems/gsd/agents/gsd-security-auditor.md) | Verifies threat mitigations from PLAN.md threat model exist in implemented code. Produces SECURITY.md. Spawned by /gsd-secure-phase. |
| [gsd-ui-auditor](../systems/gsd/agents/gsd-ui-auditor.md) | Retroactive 6-pillar visual audit of implemented frontend code. Produces scored UI-REVIEW.md. Spawned by /gsd-ui-review orchestrator. |
| [gsd-ui-checker](../systems/gsd/agents/gsd-ui-checker.md) | Validates UI-SPEC.md design contracts against 6 quality dimensions. Produces BLOCK/FLAG/PASS verdicts. Spawned by /gsd-ui-phase orchestrator. |
| [gsd-ui-researcher](../systems/gsd/agents/gsd-ui-researcher.md) | Produces UI-SPEC.md design contract for frontend phases. Reads upstream artifacts, detects design system state, asks only unanswered questions. Spawned by /gsd- |
| [gsd-user-profiler](../systems/gsd/agents/gsd-user-profiler.md) | Analyzes extracted session messages across 8 behavioral dimensions to produce a scored developer profile with confidence levels and evidence. Spawned by profile |
| [gsd-verifier](../systems/gsd/agents/gsd-verifier.md) | Verifies phase goal achievement through goal-backward analysis. Checks codebase delivers what phase promised, not just that tasks completed. Creates VERIFICATIO |
