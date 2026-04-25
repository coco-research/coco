# Team Feedback Registry

> **Purpose:** Accumulated learnings from /team runs. Layer 2 agents read
> relevant entries before starting work so they don't repeat past mistakes.
>
> **How it's used:** The orchestrator reads this file, extracts entries
> relevant to the current action/tools, and inlines them into Layer 2
> agent prompts alongside toolkit entries.
>
> **Entry lifecycle:**
> - New entries appended by Layer 4 principals after every /team run
> - Status: `pending` → `applied` (when toolkit quality notes updated)
> - Entries older than 90 days with status `applied` can be archived
> - Maximum 50 active entries (oldest applied entries archived first)
>
> **Context window budget:** This file should stay under 200 lines.
> When approaching the limit, archive old `applied` entries to
> `team-feedback-archive.md`.

---

## Entries

### 2026-03-19 | /team review | framework cleanup (pre-redesign)

- **Tool reviewed:** Manual parallel agents (identical reviewer clones)
- **Reviewer role:** N/A (human observation)
- **Finding:** Identical clone agents produce redundant findings — 5 reviewers find the same 3 bugs instead of 5 different categories of issues
- **Recommendation:** Use diverse specialist roles with distinct review focus areas
- **Status:** applied (this redesign)
- **Impact:** high — fundamental architecture change

---

## Entry Template

```
### YYYY-MM-DD | /team <action> | <scope>

- **Tool reviewed:** [skill or command name]
- **Reviewer role:** [which Layer 3 specialist found this]
- **Finding:** [what was wrong — specific, with examples]
- **Recommendation:** [specific fix — not "improve" but "add X to section Y"]
- **Status:** pending | applied
- **Impact:** high | medium | low
```
