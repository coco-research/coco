# Agent Catalog

10 specialist agents consolidated from the original 19. Each agent provides deep domain expertise for specific tasks.

## When to Use Agents

Use agents when you need deep domain expertise beyond general-purpose AI. Each agent is a specialist role definition that can be loaded as context.

## What counts as an installable agent

An installable agent is a `.md` file with YAML frontmatter, living either directly in this
directory or in `systems/<bundle>/agents/`. Those are the files `install.sh` links and
`scripts/build-index.py` catalogs into `agents/INDEX.md`. There are **34**: 10 here and 24 in
`systems/gsd/agents/`.

A `find` for every `agents/*.md` in the repository returns **37**, and the extra three are not
missing or misplaced. They are `builder.md`, `director.md` and `finalize.md` under
`systems/hyperframes/skills/motion-graphics/agents/`. They carry no frontmatter and are not
role definitions; they are prompt bodies that the `motion-graphics` skill dispatches at named
stages of its own pipeline, listed in the `prompt` column of the stage table in that skill's
`SKILL.md`. They are internal to one skill, so they are deliberately neither linked nor
indexed, and moving them here would change behaviour rather than fix anything.

So a 37-versus-34 discrepancy is expected. The convention is that `agents/` nested inside a
skill directory belongs to that skill. If you add such a directory, keep the files free of
frontmatter so the indexer continues to skip them.

## Three separate role populations

Worth knowing, because they are easy to confuse and none is a subset of another:

- the **10 core agents** in this directory, plus the **24 GSD agents** in `systems/gsd/agents/`
- the **`/team` roles** defined inline in `commands/team/roles.md`, spawned by the `/team`
  commands across four layers (research, execution, review, synthesis). They share no names
  with the files here. No count is quoted because three different counting methods over that
  file disagree, depending on whether the `## Role Template` placeholder and each role's
  `### System Prompt` subheading are counted; read the file rather than trusting a figure.
- the **389 Super Intelligence personas** under `systems/superintelligence/*/personas/`

## Agents

| Agent | Domain | When to Use |
|-------|--------|-------------|
| pm-advisor | Product Management | Feature planning, user stories, prioritization, acceptance criteria |
| code-reviewer | Code & Architecture | Code quality, security, SOLID, API design, scalability review |
| ai-engineer | AI/ML Systems | Model selection, training pipelines, deployment, monitoring |
| data-specialist | Data & Analytics | EDA, statistical modeling, SQL optimization, ML experiments |
| database-architect | Database Design | Schema design, data modeling, migrations, microservices patterns |
| mcp-specialist | MCP Integration | Server development, configuration, protocol compliance |
| test-guardian | Test Quality | Test tautologies, mock correctness, assertion quality, flakiness |
| typescript-pro | TypeScript | Advanced generics, type-level programming, full-stack type safety |
| ui-ux-designer | UI/UX Design | Research-backed critique, accessibility, typography, layout |
| refactoring-specialist | Code Refactoring | Code smell detection, complexity reduction, incremental transformation |

## Consolidation Notes

These 10 agents were consolidated from 19 originals:
- **code-reviewer** ← code-reviewer + architect-review + backend-architect
- **data-specialist** ← data-scientist + sql-pro
- **mcp-specialist** ← mcp-developer + mcp-expert + mcp-server-architect
- **pm-advisor** ← se-product-manager-advisor (renamed)
- Removed: frontend-developer, fullstack-developer, nextjs-architecture-expert, verification-agent (covered by GSD agents)