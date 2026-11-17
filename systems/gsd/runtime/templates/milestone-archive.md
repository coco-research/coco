# Milestone Archive Template

This template is used by the complete-milestone workflow to create archive files in `.planning/milestones/`.

---

## File Template

# Milestone v{{VERSION}}: {{MILESTONE_NAME}}

**Status:** ✅ SHIPPED {{DATE}}
**Phases:** {{PHASE_START}}-{{PHASE_END}}
**Total Plans:** {{TOTAL_PLANS}}

## Overview

{{MILESTONE_DESCRIPTION}}

## Phases

{{PHASES_SECTION}}

[For each phase in this milestone, include:]

### Phase {{PHASE_NUM}}: {{PHASE_NAME}}

**Goal**: {{PHASE_GOAL}}
**Depends on**: {{DEPENDS_ON}}
**Plans**: {{PLAN_COUNT}} plans

Plans:

- [x] {{PHASE}}-01: {{PLAN_DESCRIPTION}}
- [x] {{PHASE}}-02: {{PLAN_DESCRIPTION}}
      [... all plans ...]

**Details:**
{{PHASE_DETAILS_FROM_ROADMAP}}

**For decimal phases, include (INSERTED) marker:**

### Phase 2.1: Critical Security Patch (INSERTED)

**Goal**: Fix authentication bypass vulnerability
**Depends on**: Phase 2
**Plans**: 1 plan

Plans:

- [x] 02.1-01: Patch auth vulnerability

**Details:**
{{PHASE_DETAILS_FROM_ROADMAP}}

---

## Milestone Summary

**Decimal Phases:**

- Phase 2.1: Critical Security Patch (inserted after Phase 2 for urgent fix)
- Phase 5.1: Performance Hotfix (inserted after Phase 5 for production issue)

**Key Decisions:**
{{DECISIONS_FROM_PROJECT_STATE}}
[Example:]

- Decision: Use ROADMAP.md split (Rationale: Constant context cost)
- Decision: Decimal phase numbering (Rationale: Clear insertion semantics)

