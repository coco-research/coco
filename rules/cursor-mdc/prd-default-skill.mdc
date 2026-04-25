---
description: "MANDATORY: On ANY PRD task, you MUST read the prd-generator skill file FIRST. Do NOT write PRD content until you have read it."
globs:
alwaysApply: true
---

# Default PRD Skill

When creating, writing, or revising a Product Requirements Document (PRD), always use the **prd-generator** skill.

**CRITICAL — WHY CURSOR "FORGETS"**: The skill lives in a file; it is NOT in the model's context until you read it. Each new chat has no memory of the skill content. So:

- **Your first action on any PRD task MUST be**: Read the skill file (see path below). Do not skip this. Do not assume you know the workflow.
- This skill does NOT appear in `available_skills` (installed via `npx skills add`). You must read it by path every time.

## Skill Location

- **Skill file**: `~/.cursor/skills/prd-generator/SKILL.md`
- **Template**: `~/.cursor/skills/prd-generator/references/prd_template.md`
- **Validation**: `bash ~/.cursor/skills/prd-generator/scripts/validate_prd.sh <file> --verbose`

## Workflow (after reading SKILL.md, follow it strictly)

1. **First**: Read `~/.cursor/skills/prd-generator/SKILL.md` (required every PRD task).
2. Then follow its 5-step workflow strictly:
   - **Step 1**: Gather context via discovery questions
   - **Step 2**: Generate PRD using the template at `~/.cursor/skills/prd-generator/references/prd_template.md`
   - **Step 3**: Create user stories with priority, effort, dependencies
   - **Step 4**: Define success metrics using a named framework (AARRR, HEART, OKR)
   - **Step 5**: Validate with `bash ~/.cursor/skills/prd-generator/scripts/validate_prd.sh`
3. Include all 13 required sections + Stakeholder Sign-Off + Change Log

**Check**: If you have not read `~/.cursor/skills/prd-generator/SKILL.md` in this conversation yet, do it now before writing or revising any PRD.

## Do NOT use these older skills for PRDs

- `~/.cursor/skills/prd/SKILL.md` (superseded)
- `~/.cursor/skills/PRD Mastery.../SKILL.md` (superseded)
- `~/.cursor/skills/task-prd-creator/SKILL.md` (superseded)
- `~/.cursor/skills/ralph-tui-prd/SKILL.md` (superseded)
