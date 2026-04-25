# Escalation Patterns

## Standard Escalation Matrix Template

```
SEV1 → PM (15 min) → Security POC (15 min) → Sponsor/Legal (30 min) → SteerCo (1 hr)
SEV2 → PM (1 hr) → Tech Lead (1 hr) → Security POC (2 hr) → Sponsor (4 hr)
SEV3 → PM (4 hr) → Tech Lead (next day)
SEV4 → PM (next business day)
```

## Per-Severity Playbook Structure

### Triage (All Severities)
1. Confirm the incident is real (not a false alarm, not a user error)
2. Classify severity using the severity matrix
3. Assign Incident Commander (usually PM for SEV1-2, Tech Lead for SEV3-4)
4. Open incident channel (Slack/Teams) or thread
5. Log: time detected, reporter, initial assessment

### SEV1 Playbook
**Goal: Contain and communicate within 15 minutes**

| Phase | Actions | Owner | Timeline |
|-------|---------|-------|----------|
| **Immediate** (0-15 min) | Confirm incident, classify SEV1, notify IC | Reporter → PM | 15 min |
| **Containment** (15-60 min) | Isolate affected system, preserve evidence, vendor ticket (phone) | Tech Lead | 1 hr |
| **Communication** (30 min) | Notify security POC, legal (if privilege/data), stakeholders (initial) | Comms Lead | 30 min |
| **Investigation** (1-4 hr) | Root cause analysis, vendor collaboration, impact assessment | Tech Lead + Vendor | 4 hr |
| **Resolution** (target: RTO) | Implement fix, verify, restore service | Tech Lead | Per RTO |
| **Post-incident** (within 48 hr) | PIR meeting, update runbooks, stakeholder summary | PM | 48 hr |

### SEV2 Playbook
**Goal: Restore within 4 hours, stakeholders updated hourly**

| Phase | Actions | Owner | Timeline |
|-------|---------|-------|----------|
| **Triage** (0-1 hr) | Confirm, classify, assign IC, open channel | PM | 1 hr |
| **Diagnosis** (1-2 hr) | Identify root cause, engage vendor if needed | Tech Lead | 2 hr |
| **Communication** (1 hr) | Notify affected stakeholders, set expectations | Comms Lead | 1 hr |
| **Resolution** (2-4 hr) | Fix, verify, service restored | Tech Lead | 4 hr |
| **Follow-up** (24 hr) | Update incident log, assess need for PIR | PM | 24 hr |

### SEV3-4 Playbook
- Log the incident
- Assign to Tech Lead or vendor
- Track to resolution
- No real-time communication needed
- Update stakeholders in next status update

## Vendor Escalation Pattern

```
Level 1: Standard support ticket (web/email)
   ↓ No response in SLA time
Level 2: Phone support + ticket escalation
   ↓ No resolution in 2x SLA time
Level 3: Account Manager direct contact
   ↓ No resolution / business-critical
Level 4: Executive escalation (Sponsor → Vendor VP)
```

## Communication Cadence by Severity

| Severity | Initial Notification | Update Cadence | Resolution Notice | PIR |
|----------|---------------------|---------------|-------------------|-----|
| SEV1 | Within 15 min | Every 30 min | Within 1 hr of resolution | Required (48 hr) |
| SEV2 | Within 1 hr | Every 2 hr | Within 4 hr of resolution | Recommended |
| SEV3 | Within 4 hr | Daily | In next status update | Optional |
| SEV4 | None | None | None | No |
