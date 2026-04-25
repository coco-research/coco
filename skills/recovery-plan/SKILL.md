---
name: pmstudio-recovery
description: Generate detailed service restoration runbooks with step-by-step procedures. Use when someone asks to "create recovery procedures", "restoration runbook", "recovery steps", "how to restore service", or needs tactical step-by-step procedures for recovering from disaster scenarios. This is the execution companion to the DR plan — DR defines what and when, recovery-plan defines exactly how. Requires a DR plan to exist (will prompt to run /pmstudio-dr first if missing).
---

# Recovery Plan — Service Restoration Runbooks

## Purpose

Generates step-by-step runbooks for each disaster scenario defined in the DR plan. These are **tactical execution documents** — meant to be followed during an actual incident by someone who may not be the person who wrote the plan.

## Prerequisites

**Hard dependency:** A DR plan must exist at `Operational/DR-Plan-*.html`. If not found, respond:

> "No DR plan found for this project. The recovery plan is built from DR plan scenarios and RTO/RPO targets. Run `/dr-plan` first to create one, then run `/recovery-plan` to generate the runbooks."

## Process

### Step 1: Read Context

**Required:**
- `Operational/DR-Plan-*.html` — scenarios, RTO/RPO targets, dependencies, communication plan
- `CLAUDE.local.md` — architecture, contacts, integrations

**Optional (enriches the runbooks):**
- `Operational/IRP-*.html` — escalation matrix, communication templates
- `PRD/*.html` — integrations detail, technical considerations
- `Architecture/` — system diagrams for reference

### Step 2: Extract Scenarios

From the DR plan, extract:
- Each disaster scenario (name, description, trigger condition)
- RTO/RPO targets per component
- Dependencies and contacts
- Manual workarounds

### Step 3: Generate Runbooks

**Output:** `Operational/Recovery-Procedures-{ProductName}-{Date}.html`

Self-contained HTML. **Zero CDN dependencies** — this must work offline during recovery.

**Structure:** One runbook per disaster scenario, plus a general section.

**General Section:**
```markdown
## Before Any Recovery

### Emergency Contacts
| Role | Name | Phone | Email |
|------|------|-------|-------|
| PM / Incident Commander | ... | ... | ... |
| Technical Lead | ... | ... | ... |
| Vendor Support | ... | ... | ... |
| Security POC | ... | ... | ... |

### Tools Needed
- Access to vendor admin console
- Access to monitoring/status page
- Access to communication channel (Slack/Teams/email)
- Access to backup location (Snowflake/SharePoint)

### Recovery Principles
1. Communicate first, then fix
2. Document every action and timestamp
3. Verify each step before proceeding to next
4. If stuck for >15 minutes on any step, escalate
```

**Per-Scenario Runbook:**

```markdown
## Scenario: {Name}

**Trigger:** {How you know this is happening}
**Target RTO:** {time} | **Target RPO:** {time}
**Severity:** {from IRP if exists}

### Pre-Conditions
- [ ] Incident declared and logged
- [ ] Incident Commander assigned
- [ ] Stakeholders notified (initial)

### Recovery Steps

| # | Action | Owner | How to Verify | Est. Time |
|---|--------|-------|--------------|-----------|
| 1 | {action} | {role} | {verification} | {minutes} |
| 2 | ... | ... | ... | ... |

**Cumulative time: {sum} — within RTO: {yes/no}**

### Decision Points
- After step N: If {condition}, go to step M instead
- After step N: If {condition}, escalate to {person}

### Verification Checklist
- [ ] Service accessible to users
- [ ] Data integrity confirmed (spot-check N records)
- [ ] All integrations responding
- [ ] No error alerts in last 15 minutes
- [ ] Stakeholders notified of restoration

### If Recovery Fails
- At step N: {rollback action}
- Escalation: {who to call}
- Alternative: {manual workaround from DR plan}

### Post-Recovery
- [ ] Update incident log with recovery timeline
- [ ] Schedule PIR within 48 hours
- [ ] Document any deviations from this runbook
- [ ] Update this runbook with lessons learned
```

### Step 4: Validate Timing

For each runbook, sum the estimated step times. Compare to RTO:
- If total < RTO: Good.
- If total > RTO: Flag as risk. Ask user: "Steps total {X} but RTO is {Y}. Should we adjust the RTO or find ways to parallelize steps?"

### Step 5: Present for Review

Show all runbook outlines with step counts and timing. Ask for approval before writing.

## Critical Rules

1. **Written for execution, not understanding.** Each step should be a clear action ("Open {URL} and click Settings > Backup > Export"), not a description ("The admin should initiate a backup process").
2. **Every step has verification.** Don't move to step N+1 without confirming step N succeeded.
3. **Include decision trees.** Real recovery rarely follows a straight line. Document branch points.
4. **Timing must be realistic.** Don't estimate "1 minute" for something that requires vendor response. Use pessimistic estimates.
5. **Offline-capable.** Zero CDN dependencies. Print-friendly CSS. Someone may be reading this on a phone with spotty internet.
6. **Contacts are phone numbers, not just emails.** During a crisis, email is slow. Include phone numbers for all critical contacts.
