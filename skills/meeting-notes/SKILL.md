---
name: pmstudio-meeting-notes
description: Generate structured meeting notes from transcripts or pasted text. Use when someone says "meeting notes", "process this transcript", "summarize this call", "notes from today's meeting", or pastes/references a meeting transcript. Auto-enriches attendees from stakeholder directory, routes output to correct project subfolder, flags downstream artifact impacts (PRD, deck, architecture), and proposes CLAUDE.local.md updates. Produces date-first Markdown files.
---

# Meeting Notes — Transcript-to-Artifact Generator

## Purpose

Transforms raw meeting transcripts (pasted text, audio transcription output, or file references) into structured, stakeholder-enriched meeting notes. Not generic summaries — these cross-reference project context, known stakeholders, and existing artifacts to produce notes that integrate into the project's documentation ecosystem.

## Process

### Step 1: Determine Input Source

From user request:

| Input | How to Handle |
|-------|---------------|
| Transcript pasted in chat | Process directly |
| File path provided | Read the file |
| `/pmstudio-meeting-notes <path>` | Read file at path |
| `/pmstudio-meeting-notes <path> <output-dir>` | Read file, write to specified directory |
| No transcript provided | Ask: "Paste the transcript or provide a file path" |

### Step 2: Read Project Context

**Always read (skip any that don't exist):**

1. **`CLAUDE.local.md`** — critical for:
   - Folder structure & routing guide (determines where to save notes)
   - Recent Changes (avoid duplicating known information)
   - Key Decisions (cross-reference decisions mentioned in transcript)
   - Open Questions (check if any were answered in this meeting)
   - File naming conventions

2. **Stakeholder Directory** — scan for:
   - `**/Stakeholder*.xlsx` or `**/Stakeholder*.md`
   - `**/Data/Stakeholder*`
   - Known stakeholder names, roles, emails, groups

3. **Recent meeting notes** — read the last 1-2 meeting note files to:
   - Match format and depth conventions
   - Identify follow-ups from previous meetings
   - Detect recurring topics

4. **PRD files** — scan for `**/*PRD*.html` or `**/*PRD*.md` to:
   - Know current PRD version
   - Identify if meeting content impacts requirements

### Step 3: Extract & Enrich

Process the transcript to extract:

#### 3a. Metadata
- **Date** — from transcript or user context. Use absolute date (YYYY-MM-DD), never relative.
- **Attendees** — every person mentioned or speaking. Cross-reference against stakeholder directory to enrich with:
  - Full name (resolve first-name-only references)
  - Title/Role
  - Group/Team
  - If NOT in directory → flag as "New Stakeholder"
- **Duration** — estimate from transcript length if not stated (~150 words/minute for conversation)
- **Subject** — synthesize from discussion topics

#### 3b. Content Extraction

| Element | What to Capture | How to Identify |
|---------|----------------|-----------------|
| **Key Discussion Topics** | Major themes discussed, numbered with detail | Topic shifts, agenda items, extended discussion |
| **Decisions Made** | Explicit choices, agreements, approvals | "We'll go with...", "Let's do...", "Agreed", "Decision:" |
| **Action Items** | Tasks assigned with owner and deadline | "Can you...", "I'll...", "Next step is...", "Action:" |
| **Direct Quotes** | Significant statements worth preserving verbatim | Strategic vision, strong opinions, commitments, memorable framing |
| **New Information** | Facts, data points, context not previously documented | Numbers, dates, names, technical details, process descriptions |
| **New Stakeholders** | People mentioned who aren't in the stakeholder directory | Names with roles/context that suggest ongoing involvement |
| **Open Questions** | Questions raised but not answered | "We need to find out...", "TBD", "I'll check...", unanswered questions |
| **Emotional/Political Signals** | Frustrations, enthusiasm, concerns, tensions | Strong language, repeated emphasis, criticism, praise |

#### 3c. Cross-Reference

- **Against CLAUDE.local.md Open Questions**: Did this meeting answer any? Mark as "Resolved" with the answer.
- **Against CLAUDE.local.md Key Decisions**: Did this meeting produce new decisions? Capture with date.
- **Against PRD**: Does anything discussed change requirements, scope, timeline, or stakeholders?
- **Against previous meeting action items**: Were any completed or discussed?

### Step 4: Generate Meeting Notes

**File naming convention:** `YYYY-MM-DD-Attendee1-Attendee2.md` (date-first for chronological sort, key attendee names for identification)

**If 3+ attendees**, use the most senior or topic-relevant names, not all names.

#### Output Structure

```markdown
# Meeting Notes — {Topic / Key Attendees}

**Date:** {YYYY-MM-DD} ({Day of Week})
**Attendees:** {Name1 (Role)}, {Name2 (Role)}, {Name3 (Role)}
**Subject:** {Project} — {Topic Summary}
**Duration:** ~{N} minutes

---

## Summary

{2-3 sentence executive summary: what was the meeting about, what was decided, what's the main takeaway}

---

## {N}. {Topic Title}

{Detailed notes on this topic. Include:
- Context and background discussed
- Key points made by specific people (attribute statements)
- Data points, numbers, dates mentioned
- Sub-sections if the topic has distinct parts}

### {Sub-topic if needed}
- {Detail}
- {Detail}

> **"{Direct quote}"** — {Speaker Name}

{Repeat for each major topic}

---

## Decisions Made

| # | Decision | Made By | Impact | Notes |
|---|----------|---------|--------|-------|
| 1 | {Decision} | {Person} | {What it affects} | {Context} |

---

## New Stakeholders Identified

| Name | Role | Email | Context |
|------|------|-------|---------|
| {Name} | {Role} | {email or TBD} | {How they came up in discussion} |

*Omit this section if no new stakeholders were identified.*

---

## Action Items

| # | Action | Owner | Due | Status |
|---|--------|-------|-----|--------|
| 1 | {Action} | {Name} | {Date or "TBD"} | Pending |

---

## Open Questions

- {Question that wasn't answered — include who raised it and why it matters}

---

## Key Takeaways for Artifacts

{Flag what needs updating in other project documents. Be specific:}

| Artifact | What Needs Updating | Priority |
|----------|-------------------|----------|
| {PRD vX.Y} | {Specific section or requirement} | {High/Med/Low} |
| {Presentation} | {Specific slide or section} | {High/Med/Low} |
| {Architecture Map} | {Specific view or layer} | {High/Med/Low} |
| {Stakeholder Directory} | {New people to add} | {High/Med/Low} |

*Omit this section if no artifact impacts identified.*

---

## Transcript Notes

- {Note about transcript quality: complete/partial, any gaps, audio issues}
- {Which portions of the meeting are covered vs. missing}
```

### Step 5: Route Output File

Use the routing guide from `CLAUDE.local.md` to determine the correct output directory:

**Routing logic:**
1. If meeting is about ProductB / Tax / {Stakeholder} → `ProductB-Control-Framework/Meeting-Notes/`
2. If meeting is about ProductA / ComplianceApp / {Stakeholder} / {Stakeholder} → `ProductA-Steady-State/`
3. If meeting is about platform / cross-cutting → `Platform-Overview/`
4. If routing guide doesn't exist or doesn't match → ask the user
5. If output directory was specified in the command → use that

**Before writing:** Show the user:
- Proposed file name
- Proposed output location
- Brief summary of what will be in the notes

Then write the file.

### Step 6: Propose CLAUDE.local.md Update

After writing the meeting notes, propose a `Recent Changes` entry for `CLAUDE.local.md`:

```markdown
- [YYYY-MM-DD] `{relative-path-to-notes}` — **NEW FILE**: {Meeting type} notes from {date} {attendees} call (~{N} min). {1-2 sentence summary of key topics}. {Count} action items. {Key decision or stakeholder if notable}.
```

**Also propose updates to:**
- **Key Decisions** section — if new decisions were made
- **Open Questions** section — if questions were answered or new ones raised

Ask: "Should I update CLAUDE.local.md with this entry?"

### Step 7: Surface Sync Opportunities

If the meeting produced information that should propagate to other documents, mention it:

> "This meeting discussed {topic} which may impact:
> - **{PRD vX.Y}** — {what section}
> - **{Presentation}** — {what slide}
> Run `/pmstudio-sync` to propagate changes, or I can update specific artifacts now."

## Quality Rules

1. **Attribute statements to speakers.** Don't write "it was discussed that..." — write "{Stakeholder} explained that..." or "{Stakeholder} noted that..."
2. **Preserve significant quotes verbatim.** If someone said something strategic, memorable, or committal, quote it exactly with attribution.
3. **Convert relative dates to absolute.** "Next Thursday" → "2026-03-20 (Thursday)". "Last week" → "week of 2026-03-10".
4. **Don't invent information.** If the transcript is unclear or incomplete, say so. Use "[inaudible]" or "[unclear]" markers.
5. **Don't over-summarize.** Meeting notes should be comprehensive enough that someone who wasn't there can understand what happened. Err on the side of more detail, not less.
6. **Separate facts from interpretation.** Use clear language: "{Stakeholder} stated..." (fact) vs. "This suggests..." (interpretation).
7. **Action items need owners.** If an action was discussed but no owner assigned, flag it: "Owner: TBD — needs assignment".
8. **Match existing format.** If prior meeting notes exist in the project, match their depth, style, and section structure for consistency.
9. **Handle partial transcripts.** If the transcript is clearly incomplete (starts mid-conversation, cuts off), note what's missing in the Transcript Notes section.
10. **Cross-reference, don't duplicate.** If a topic was covered extensively in previous meeting notes, reference that file rather than re-explaining: "See 2026-03-13-{Stakeholder1}-{Stakeholder2}.md §3 for full {Audit Firm} tool walkthrough."

## Handling Edge Cases

| Scenario | Approach |
|----------|----------|
| **Multiple meetings in one transcript** | Split into separate files, one per meeting |
| **Very short meeting (<10 min)** | Use abbreviated format: Summary + Decisions + Actions only |
| **No clear decisions or actions** | Still capture — note "Informational/exploratory call — no decisions or actions" |
| **Sensitive/privileged content** | Flag to user: "This transcript contains potentially privileged content (legal, litigation). Confirm before writing to file." |
| **Poor transcript quality** | Do your best, mark uncertain sections with [?], note quality issues prominently |
| **Attendees not in stakeholder directory** | List them in "New Stakeholders" table with whatever context is available |
| **Meeting references documents not yet read** | Note: "{Stakeholder} referenced {document} — not yet reviewed. Action: obtain and review." |

## Integration with PM Studio

This skill is part of the PM Studio ecosystem:

| Related Skill | When to Suggest |
|---------------|----------------|
| `/pmstudio-sync` | Meeting produced changes that should propagate to PRD/deck/architecture |
| `/pmstudio-changelog` | Meeting produced a significant decision or change worth logging |
| `/pmstudio-comms` | Meeting requires a follow-up communication (status update, stakeholder notification) |
| `/pmstudio-prd` | Meeting revealed requirements not yet in the PRD |
| `/pmstudio-nfr` | After processing several meetings, audit document completeness |
