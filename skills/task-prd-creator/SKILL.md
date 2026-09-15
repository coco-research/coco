---
name: task-prd-creator
description: "Use when the user says I want to add X, implement Y, create a task for Z, or plan this feature. Writes a task file plus a PRD under .agent/, links them, and waits for approval before any implementation starts."
version: 1.0.0
tags:
  - planning
  - task-management
  - prd
  - workflow
  - documentation
  - project-management
auto_activate: true
domain: pm
---

# Task & PRD Creator

## Overview

Create structured task files and PRDs before implementing features. This ensures proper planning, documentation, and clear scope definition.

**CRITICAL RULE:** Never implement a feature without first creating the task + PRD files and getting user approval.

## When This Activates

- "I want to add [feature]"
- "Implement [feature]"
- "Create a task for [feature]"
- "Plan this feature"
- User describes a user story
- Bug that needs tracking

## The Workflow

### Step 1: Understand Request

- **Simple task:** <1 hour, few files
- **Complex feature:** >1 hour, multiple files/systems

### Step 2: Gather Requirements

- Which app/project?
- Priority? (CRITICAL/High/Medium/Low)
- Dependencies?

### Step 3: Check Existing System

- Read architecture docs
- Search for similar implementations

### Step 4: Create Files

**Task file:** `[project]/.agent/TASKS/[task-name].md`
**PRD file:** `[project]/.agent/PRDS/[task-name].md`

### Step 5: Get Approval

Present files, explain approach, **WAIT for user approval**.

## Task File Format

```markdown
## Task: [Feature Name]

**ID:** feature-name-slug
**Label:** [App]: [Feature Name]
**Description:** Brief description
**Type:** Feature | Bug | Enhancement
**Status:** Backlog | To Do | Testing | Done
**Priority:** High | Medium | Low
**Created:** YYYY-MM-DD
**Updated:** YYYY-MM-DD
**PRD:** [Link](../PRDS/feature-name.md)
```

## Critical Rules

1. Create task file
2. Create PRD file
3. Link them together
4. Present to user
5. Get approval
6. Then implement

## Red Flags (Stop and Ask)

- Breaking changes
- Affects multiple projects
- Security implications
- Unclear requirements

## Integration

- `writing-plans` - Implementation plan authoring
- `prd-generator` - Heavier PRD generation and validation

---

**For complete PRD template, naming conventions, status update workflow, Context7 integration, and example interactions, see:** `references/full-guide.md`
