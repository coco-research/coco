# Rules

Cross-IDE coding/process rules. Markdown is the source of truth; per-IDE formats are derived during adapter install.

## Layout

```
rules/
├─ README.md           — this file
├─ cursor-mdc/         — Cursor-format rules (.mdc with frontmatter)
└─ <markdown rules>    — derived/exported rules in other adapter formats
```

## Categories (15 rules currently)

- **agents-md-creation** — when and how to create AGENTS.md
- **code-quality** — documentation, error handling, logging conventions
- **dependency-management** — version pinning, audit cadence, doc requirements
- **file-organization** — directory structure, naming conventions, colocation
- **git-conventions** — commit message format, branch naming, best practices
- **parallel-agents** — multi-wave orchestration patterns, verification rule
- **persistent-memory** — global + local memory layering, batching
- **prd-default-skill** — invoke prd-generator for any PRD work
- **prd-management** — PRD structure, lifecycle, update triggers
- **react-default-skills** — UI/UX, performance, frontend quality
- **security-rules** — secrets, env files, auth, input validation
- **senior-architect** — ADR template, common patterns, trade-offs
- **skill-router** — task→skill routing table
- **testing-standards** — AAA pattern, naming, mocking
- **verification-workflow** — pre-check, gate, batch sizes, anti-patterns

## Adapter behavior

Each adapter decides how to apply rules:

- **cursor** — copies/symlinks `cursor-mdc/*.mdc` to `~/.cursor/rules/`
- **claude-code** — appends rules to project `CLAUDE.md` or `~/.claude/CLAUDE.md`
- **codex** — embeds in `AGENTS.md` at install root
- **generic** — writes a single `AGENTS.md` containing all rules
