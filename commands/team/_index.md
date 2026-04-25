# /team — Cross-Functional Product Team

> **You ARE the team lead.** You orchestrate, monitor, and synthesize.
> No separate lead agent. You manage handoffs between layers.

## Quick Reference

| Action | Purpose |
|--------|---------|
| `/team research <topic>` | Deep multi-angle investigation |
| `/team think <problem>` | Analysis, brainstorm, options exploration |
| `/team develop <feature>` | Build working code/config |
| `/team review <scope>` | Audit existing work |
| `/team document <what>` | Create documents (PRD, guide, runbook) |
| `/team present <what>` | Build presentations (Consulting, Apple, data) |
| `/team communicate <what>` | Stakeholder comms (emails, announcements) |
| `/team test <scope>` | Write tests, find coverage gaps |
| `/team fix <issue>` | Debug and fix issues |
| `/team plan <scope>` | Project plans, roadmaps |
| `/team ship <idea>` | Idea to shipped product (research→plan→build→verify) |
| `/team verify <scope>` | Verify deliverables match spec/plan |
| `/team reanalyse [phases]` | Re-review completed work for regressions |
| `/team scrape <urls/topics>` | Parallel web research |
| `/team stop` | Shutdown active team |
| `/team <free text>` | Ad-hoc: auto-parse into tasks |

---

## Step 1: Parse Command

Extract from `$ARGUMENTS`:
- **First token** → action (research, think, develop, build, review, verify, document, present, communicate, test, fix, plan, reanalyse, scrape, ship, stop)
- `build` is a synonym for `develop` — route to team-develop.md
- **Remaining tokens** → scope
- **Flags:** `--domain <value>` overrides auto-detection, `--roles <comma-list>` forces specific role IDs

If first token doesn't match any action → **ad-hoc mode** (see below).

### Input Validation

**Scope required for:** develop, build, fix, test, verify, scrape, document, present, communicate
**Scope optional for:** review (whole project), think (open brainstorm), plan (whole project), research (project domain), reanalyse (all phases)

If scope is required but empty → ask user: "What should I {action}? Example: `/team {action} {example}`" and STOP.

### --roles Validation

If `--roles` flag provided, validate each role ID against team-roles.md.
If any ID not found → report: "Unknown role(s): {list}. Check team-roles.md for valid IDs." and STOP.

## Action Selection Guide

Not sure which action to use? Follow this:

**Building something?** → `develop` (or `build`)
**Fixing bugs?** → `fix`
**Need tests?** → `test`

**Checking quality?**
- Built something and want to verify it matches the spec? → `verify`
- Want a general quality/architecture audit? → `review`
- Re-checking previously reviewed work for regressions? → `reanalyse`

**Researching?**
- Have specific URLs to fetch? → `scrape`
- Need broad investigation on a topic? → `research`
- Evaluating options for a decision? → `think`

**Want it all done?** → `ship` (research → plan → [approval] → build → verify)

**Creating content?**
- Writing docs (PRD, guide, runbook)? → `document`
- Building a presentation? → `present`
- Writing stakeholder comms (emails, updates)? → `communicate`
- Creating a project plan/roadmap? → `plan`

### /team stop (Special — No Pipeline)

If action is `stop`:
1. Send `shutdown_request` to all active teammates via SendMessage
2. Wait briefly for responses
3. TeamDelete to clean up
4. Report: "Team shutdown complete."
5. STOP — do not proceed to pipeline.

## Fast Path

Not every action needs 4 layers. Simple tasks collapse to 2 layers for speed.

### When to Use Fast Path

A task qualifies for fast path when ALL of these are true:
- Scope is simple (single URL, single file, single paragraph)
- No file ownership conflicts (one agent can handle it)
- Single deliverable expected

### Fast Path Actions

| Action | Fast Path Trigger | Pipeline |
|--------|------------------|----------|
| scrape | Single URL | L1 (1 agent fetches) → L4 (orchestrator summarizes) |
| communicate | Short update (< 3 paragraphs) | L2 (1 writer) → L3 (1 grammar check) |
| fix | Single-file bug with known cause | L2 (1 engineer) → L3 (1 reviewer) |
| test | Single module | L2 (1 test writer) → L3 (1 reviewer) |

### How It Works

1. After parsing action + scope, check fast-path eligibility
2. If eligible, skip L1 research and reduce L2-L4 to minimum agents
3. Report: "Fast path: 2 agents instead of 8. Full pipeline available with --full flag."
4. User can force full pipeline: `/team scrape --full https://example.com`

---

## Step 2: Detect Domain

Read these project files (skip any that don't exist):
- `README.md` — project description, tech stack
- `CLAUDE.local.md` — project memory, conventions
- `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` — language + deps
- `Dockerfile` / `terraform/` / `cdk/` — infrastructure signals
- `.planning/ROADMAP.md` — GSD project context
- `.planning/PROJECT.md` — GSD project definition

Produce a domain profile:
```
{
  languages: ["typescript", "python", ...],
  framework: "next.js" | "fastapi" | ...,
  cloud: "aws" | "azure" | "gcp" | null,
  domain: "risk-management" | "e-commerce" | ...,
  tags: ["backend", "frontend", "infrastructure", "data", "mobile", "api",
         "product", "pm", "docs", "comms", "integrations"],
  gsd_active: true/false (does .planning/ exist?)
}
```

If `--domain` flag provided, use it to override the `domain` and `tags` fields.

---

## Step 3: Read Toolkit + Feedback

Read these files (if missing, log warning and continue):
- `~/.claude/commands/team-toolkit.md` — available tools and quality notes
- `~/.claude/commands/team-feedback.md` — past findings and recommendations

If `team-toolkit.md` missing or empty → log: "No toolkit entries available. Agents will use default approaches."
If `team-feedback.md` missing or empty → log: "No feedback history. Expected for first /team run."

### Feedback File Enforcement

Before extracting entries, check file health:
1. Count active entries (status ≠ `applied`)
2. If active entries > 50 OR file > 200 lines:
   - Archive `applied` + `low` impact entries first (regardless of age)
   - Then `applied` + `medium` entries
   - Only archive `high` impact entries if critically over budget
   - Write archived entries to `~/.claude/commands/team-feedback-archive.md`
3. Then proceed with extraction

### Extraction

Extract entries relevant to the current action. For example:
- `/team document PRD` → extract toolkit entries for "PRD Generation" + any feedback entries mentioning PRDs
- `/team develop` → extract toolkit entries for "Code Implementation", "TDD" + relevant feedback

These extracts will be inlined into Layer 2 agent prompts (I8: agents don't read these files — orchestrator provides relevant excerpts).

**Context budget (I6):** Toolkit excerpt ≤ 30 lines. Feedback excerpt ≤ 20 lines. Truncate oldest/lowest-impact entries if over budget.

---

## Step 4: Select Roles

Read `~/.claude/commands/team-roles.md`.

### Selection Algorithm

1. **Filter by domain tags:** Only roles whose domain tags overlap with the project's tags (or tagged "all")
2. **Filter by action:** Each action command (team-develop.md, team-review.md, etc.) specifies which role categories are relevant
3. **Apply layer sizing:** Each action specifies L1/L2/L3/L4 agent counts
4. **Apply --roles override:** If user specified `--roles`, force those role IDs into the selection (adding to layers, not replacing the whole selection)
5. **Produce team roster:**
   ```
   L1: [role-id, role-id]
   L2: [role-id, role-id, role-id]
   L3: [role-id, role-id]
   L4: [role-id]
   ```

### Selection Heuristics

- If domain has both `backend` and `frontend` → include both senior-backend-eng and senior-frontend-eng in L2
- If action is `present` → always include narrative-architect + at least one format specialist (consulting or apple)
- If action is `document` and domain includes `docs` → include confluence-specialist
- If domain includes `infrastructure` → include senior-cloud-architect and sre-devops
- If action is any type → always include at least one `all`-tagged reviewer in L3 (grammar-editor or doc-quality)

---

## Step 5: Execute 4-Layer Pipeline

### Pre-flight

1. **TeamCreate** with `team_name="{action}-squad"`
2. **TaskCreate** for each agent — include role name and layer in description

### Layer 1: Research (parallel)

Spawn all L1 agents in parallel:
- **Mode:** `default` (read-only + web tools)
- **Prompt template:**
  ```
  [Role system prompt from team-roles.md]

  MISSION: {scope}
  DOMAIN: {domain profile}
  ACTION: {action}

  Your research will be used by execution specialists in the next layer.
  Focus your analysis on what's most relevant to this specific mission.
  ```

Wait for all L1 agents to complete.

**Handoff compression (I5):**
Orchestrator reads all L1 outputs and writes `CONTEXT-BRIEF.md`:
- Max 200 lines
- Sections: Domain Context, Technical Landscape, Requirements, Risks, Recommendations
- Deduplicate overlapping findings
- Preserve dissenting opinions (if analysts disagree, note both views)

### Layer 1 Failure Handling (C3)

If any L1 agent fails or times out:
- Log which agent failed and why
- Continue with remaining agents' output
- Note the gap in CONTEXT-BRIEF.md: "⚠️ {role} analysis unavailable: {reason}"
- Only abort Layer 1 if ALL agents fail

### Layer 2: Execution (parallel where independent)

Spawn all L2 agents:
- **Mode:** `bypassPermissions` for develop/fix/test/build actions, `default` for review/document/present/communicate/research/think/plan
- **Prompt template:**
  ```
  [Role system prompt from team-roles.md]

  MISSION: {scope}
  DOMAIN: {domain profile}

  CONTEXT FROM RESEARCH TEAM:
  {contents of CONTEXT-BRIEF.md}

  AVAILABLE TOOLS (from team-toolkit.md):
  {relevant toolkit entries — max 30 lines}

  PAST LEARNINGS (from team-feedback.md):
  {relevant feedback entries — max 20 lines}

  Apply the quality notes and past learnings BEFORE producing your output.
  These corrections were identified by specialist reviewers in previous runs.

  FILE OWNERSHIP:
  YOUR FILES: {list of files this agent owns}
  DO NOT TOUCH: {files owned by other L2 agents}
  ```

Wait for all L2 agents to complete.

**Handoff compression (I5):**
Orchestrator reads all L2 outputs and writes `REVIEW-PACKAGE.md`:
- Max 300 lines
- Sections: What Was Built, Tools Used, Key Decisions, Files Changed, Open Questions
- Include file paths for all deliverables so L3 reviewers can read them directly

### Layer 2 Failure Handling (C3)

If any L2 agent fails:
- Log failure details
- Check if failed agent's work can be completed by another L2 agent (reassign if possible)
- If not reassignable, note gap in REVIEW-PACKAGE.md
- Ask user: "Agent {role} failed on {task}. Options: (A) Retry, (B) Skip and continue, (C) Abort"

### Layer 3: Specialist Review (parallel)

Spawn all L3 agents in parallel:
- **Mode:** `default` (read-only)
- **Prompt template:**
  ```
  [Role system prompt from team-roles.md]

  You are reviewing the output of a team of specialists.

  MISSION: {scope}
  REVIEW PACKAGE:
  {contents of REVIEW-PACKAGE.md}

  Review the actual deliverable files listed in the review package.
  Apply your specialist lens. Classify every finding as:
  CRITICAL | MAJOR | MINOR | SUGGESTION

  Include file path and specific quote for every finding.
  Suggest specific fixes — not "this is unclear" but "rewrite as: [fix]".
  ```

Wait for all L3 agents to complete.

**Handoff compression (I5):**
Orchestrator compiles all L3 outputs into `CRITIQUE-SUMMARY.md`:
- Max 200 lines
- Group by severity (CRITICAL first)
- Deduplicate overlapping critiques
- Note which reviewer found each issue

### Layer 3 Failure Handling (C3)

If any L3 agent fails:
- Continue with remaining reviewers
- Note gap: "⚠️ {role} review unavailable"
- This is non-critical — L4 principal can still synthesize with partial reviews

### Layer 4: Synthesis (sequential)

Spawn 1-2 L4 agents:
- **Mode:** `default`
- **Prompt template:**
  ```
  [Role system prompt from team-roles.md]

  You are the principal synthesizer for this team run.

  CONTEXT BRIEF:
  {CONTEXT-BRIEF.md — abbreviated to key points}

  REVIEW PACKAGE:
  {REVIEW-PACKAGE.md}

  CRITIQUE SUMMARY:
  {CRITIQUE-SUMMARY.md}

  Produce:
  1. FINAL OUTPUT — The synthesized, polished deliverable
  2. FEEDBACK ENTRIES — For each significant finding from Layer 3,
     produce a feedback entry for team-feedback.md (see entry format below)
  3. TOOLKIT UPDATES — If any tool/skill quality notes should be updated,
     specify the exact change

  Feedback entry format:
  ### YYYY-MM-DD | /team {action} | {scope}
  - **Tool reviewed:** [tool name]
  - **Reviewer role:** [L3 role that found this]
  - **Finding:** [what was wrong]
  - **Recommendation:** [specific fix]
  - **Status:** pending
  - **Impact:** high | medium | low
  ```

### Layer 4 Failure Handling (C3)

If L4 agent fails:
- This is critical — synthesis cannot be skipped
- Retry once with the same principal
- If retry fails, orchestrator performs manual synthesis:
  present CRITIQUE-SUMMARY.md findings to user directly

---

## Step 6: Post-Pipeline

1. **Apply feedback:** Append L4's feedback entries to `~/.claude/commands/team-feedback.md`
2. **Update toolkit:** If L4 recommended toolkit updates, apply them to `~/.claude/commands/team-toolkit.md`
3. **Report:** Present final output to user with summary table
4. **Cleanup:** TeamDelete

### Report Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 TEAM ► {ACTION} COMPLETE ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Team: {N} agents across 4 layers
Domain: {detected domain}
Duration: {time}

| Layer | Agents | Key Output |
|-------|--------|-----------|
| L1 Research | {roles} | {summary} |
| L2 Execute | {roles} | {summary} |
| L3 Review | {roles} | {N} findings ({X} critical) |
| L4 Synthesize | {role} | Final deliverable + {N} feedback entries |

Feedback entries added: {N}
Toolkit updates applied: {N}
```

---

## Ad-Hoc Mode (C2: Free-Text Preserved)

When `$ARGUMENTS` doesn't start with a known action:

1. Treat entire `$ARGUMENTS` as a work description
2. Parse into discrete tasks (what needs to be done)
3. For each task, identify files it touches
4. Group tasks into non-overlapping file sets
5. Run the same 4-layer pipeline:
   - L1: 1-2 analysts assess what's being asked
   - L2: Agents assigned per task group (mode: `bypassPermissions`)
   - L3: 1-2 reviewers check the work
   - L4: 1 principal synthesizes
6. Use the same report format

---

## GSD Integration (C4)

When `gsd_active: true` (`.planning/` exists):

- `/team develop` reads `.planning/ROADMAP.md` for phase context
- `/team plan` aligns with GSD phases — creates PLAN.md files compatible with `/gsd:execute-phase`
- `/team review` maps findings back to GSD requirements from REQUIREMENTS.md
- L2 agents working on GSD projects include `.planning/STATE.md` and `CLAUDE.local.md` in their context

The toolkit registry handles tool selection — if GSD is the best orchestration tool,
Layer 2 agents will use it. If a simpler approach is better, they'll use that instead.

---

## Regression Tests

After Layer 2 completes (before Layer 3), auto-detect and run regression tests:
- `pyproject.toml` → `uv run pytest tests/ -x`
- `package.json` with `test` script → `npm test`
- `Makefile` with `test` target → `make test`
- `Cargo.toml` → `cargo test`

If tests fail → include failure details in REVIEW-PACKAGE.md for Layer 3 to assess.

---

## Context Window Management (I6)

Total prompt budget per agent: ~4000 tokens (role prompt + context + instructions)
- Role system prompt: ~500-800 tokens (from team-roles.md)
- Context brief: ~800 tokens (compressed L1 output)
- Toolkit excerpt: ~300 tokens (relevant entries only)
- Feedback excerpt: ~200 tokens (relevant entries only)
- Mission + domain: ~200 tokens
- Instructions + file ownership: ~500 tokens

If approaching limits:
- Truncate feedback to only HIGH impact entries
- Summarize toolkit to one-line per entry
- Compress context brief further

ARGUMENTS: {{ARGUMENTS}}
