---
name: pmstudio-comms
description: Generate templated stakeholder communications from project context. Use when someone asks to "write a go-live email", "create a status update", "onboard someone", "write an announcement", "steerco update", "incident summary", "change notification", or any stakeholder communication task. Reads project memory, stakeholder directory, PRD, and meeting notes to pre-fill real names, dates, and context. Produces ready-to-send Markdown.
---

# Stakeholder Comms — Templated Communications Generator

## Purpose

Generates stakeholder communications pre-filled with project context. Not generic templates — these pull real stakeholder names, real dates, real scope from project artifacts.

## Process

### Step 1: Identify Template

From user request or by asking:

| Command | Template | When to Use |
|---------|----------|-------------|
| `/stakeholder-comms go-live` | Go-Live Announcement | Product/feature launching |
| `/stakeholder-comms status` | Status Update | Periodic reporting (weekly/biweekly) |
| `/stakeholder-comms onboard {name}` | Onboarding Brief | New team member joining |
| `/stakeholder-comms change` | Change Notification | Planned change to live product |
| `/stakeholder-comms incident` | Incident Summary | Post-incident communication |
| `/stakeholder-comms steerco` | SteerCo Update | Leadership/governance meeting prep |

If no subcommand, ask: "What type of communication do you need?"

### Step 2: Read Context

**All templates read:**
- `CLAUDE.local.md` — project overview, key decisions, stakeholders, recent changes
- `.sync-watch.json` — project name

**Template-specific reads:**

| Template | Additional Sources |
|----------|-------------------|
| Go-Live | PRD (scope, success metrics), Meeting-Notes (launch decisions) |
| Status | PRD (milestones, timeline), Meeting-Notes (recent), Change-Log (recent entries) |
| Onboard | Stakeholder Directory, PRD (overview), Presentations (links to share) |
| Change | PRD (affected components), DR-Plan (rollback procedures if exists) |
| Incident | IRP (severity definitions if exists), Meeting-Notes (incident details) |
| SteerCo | PRD (timeline, risks), Change-Log (period changes), all recent Meeting-Notes |

### Step 3: Ask Clarifying Questions

Only ask what can't be inferred from context:

- **Audience:** Who receives this? (all stakeholders / specific group / leadership)
- **Tone:** Formal (board) / professional (cross-team) / casual (own team)
- **Period:** For status updates — what date range?
- **Specific content:** For incident — what happened? For change — what's changing?

### Step 4: Generate Communication

**Output location:** `Comms/{Type}-{Date}-{Audience}.md`

If `Comms/` directory doesn't exist, create it.

### Templates

See `references/templates.md` for the full template content for each type. Summary:

#### Go-Live Announcement
- Subject line, TL;DR (2 sentences), What's Live (scope), Who It Affects, What To Do (action items per audience group), Known Limitations, Support Contacts, Timeline (what's next)

#### Status Update
- Period, RAG Status (Red/Amber/Green with explanation), Key Accomplishments (bulleted), Decisions Made, Risks & Blockers (with owners), Upcoming Milestones (next 2 weeks), Action Items (table: item/owner/due), Help Needed

#### Onboarding Brief
- Welcome, Product Overview (2-paragraph summary), Your Role, Key Contacts (table: name/role/email/when-to-contact), Access Setup Checklist, Key Documents (links), First-Week Actions, Glossary (10 most-used terms)

#### Change Notification
- What's Changing, When, Why, Who's Affected, What You Need To Do, Rollback Plan, Support Contacts

#### Incident Summary
- Severity, Timeline (bullet list: detected/responded/resolved), Impact, Root Cause, Resolution, Prevention (what we're doing so this doesn't happen again), Action Items

#### SteerCo Update
- Executive Summary (3 bullets max), RAG Status with trend arrow, Decisions Needed (numbered, with context and recommendation), Budget & Timeline (table), Key Risks (top 3 with mitigation status), Accomplishments Since Last SteerCo, Next Period Focus

### Step 5: Present and Refine

Show the generated communication. Ask:
- "Ready to save, or would you like to adjust anything?"
- For emails: "Want me to include a subject line suggestion?"

## Critical Rules

1. **Use real data.** Pull actual names, dates, and scope from project files. Never use placeholders like "[Name]" if the information exists in context.
2. **Appropriate detail level.** SteerCo updates are concise (1 page). Onboarding briefs are comprehensive. Match the template.
3. **Action-oriented.** Every communication should make clear what the reader should DO. No information-only dumps.
4. **Tone matching.** Leadership comms use formal language. Team comms can be direct. Incident comms are factual and calm.
5. **Don't fabricate.** If you don't have incident details, ask. Don't guess root causes or timelines.
