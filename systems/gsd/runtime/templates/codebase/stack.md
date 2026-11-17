# Technology Stack Template

Template for `.planning/codebase/STACK.md` - captures the technology foundation.

**Purpose:** Document what technologies run this codebase. Focused on "what executes when you run the code."

---

## File Template

```markdown
# Technology Stack

**Analysis Date:** [YYYY-MM-DD]

## Languages

**Primary:**
- [Language] [Version] - [Where used: e.g., "all application code"]

**Secondary:**
- [Language] [Version] - [Where used: e.g., "build scripts, tooling"]

## Runtime

**Environment:**
- [Runtime] [Version] - [e.g., "Node.js 20.x"]
- [Additional requirements if any]

**Package Manager:**
- [Manager] [Version] - [e.g., "npm 10.x"]
- Lockfile: [e.g., "package-lock.json present"]

## Frameworks

**Core:**
- [Framework] [Version] - [Purpose: e.g., "web server", "UI framework"]

**Testing:**
- [Framework] [Version] - [e.g., "Jest for unit tests"]
- [Framework] [Version] - [e.g., "Playwright for E2E"]

**Build/Dev:**
- [Tool] [Version] - [e.g., "Vite for bundling"]
- [Tool] [Version] - [e.g., "TypeScript compiler"]

## Key Dependencies

[Only include dependencies critical to understanding the stack - limit to 5-10 most important]

**Critical:**
- [Package] [Version] - [Why it matters: e.g., "authentication", "database access"]
- [Package] [Version] - [Why it matters]

**Infrastructure:**
- [Package] [Version] - [e.g., "Express for HTTP routing"]
- [Package] [Version] - [e.g., "PostgreSQL client"]

## Configuration

**Environment:**
- [How configured: e.g., ".env files", "environment variables"]
- [Key configs: e.g., "DATABASE_URL, API_KEY required"]

**Build:**
- [Build config files: e.g., "vite.config.ts, tsconfig.json"]

## Platform Requirements

**Development:**
- [OS requirements or "any platform"]
- [Additional tooling: e.g., "Docker for local DB"]

**Production:**
- [Deployment target: e.g., "Vercel", "AWS Lambda", "Docker container"]
- [Version requirements]

---

*Stack analysis: [date]*
*Update after major dependency changes*
```

<good_examples>
```markdown
# Technology Stack

**Analysis Date:** 2025-01-20

## Languages

