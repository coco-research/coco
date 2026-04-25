# Incident Response Plan — {{PROJECT_NAME}}

**Version:** 0.1 (Draft)
**Owner:** {{OWNER}}
**Last Updated:** {{DATE}}
**Classification:** {{DATA_CLASSIFICATION}}
**Next Review:** {{NEXT_REVIEW_DATE}}

---

## 1. Severity Classification

| Severity | Definition | Response Time | Examples |
|----------|-----------|---------------|----------|
| **P1 — Critical** | Complete service outage or data breach affecting all users | 15 minutes | Platform down, data exfiltration, security breach |
| **P2 — Major** | Significant degradation affecting multiple users/workflows | 1 hour | Key module unavailable, integration failure, data corruption |
| **P3 — Moderate** | Limited impact affecting individual users or non-critical features | 4 hours | Single user access issue, report generation failure, UI bug |
| **P4 — Minor** | Cosmetic or informational issues with no operational impact | Next business day | Documentation error, minor UI inconsistency |

---

## 2. Escalation Paths

### P1 — Critical Incident

```
Detection (any team member)
  → Incident Commander: {{NAME}} ({{PHONE}})
    → Backup: {{NAME}} ({{PHONE}})
  → Notify within 15 min:
    ├─ Technical Lead: {{NAME}}
    ├─ Product Owner: {{NAME}}
    ├─ Security POC: {{NAME}}
    └─ Vendor Support: {{VENDOR_SUPPORT_NUMBER}}
  → Escalate at 1 hour if unresolved:
    ├─ Department Lead: {{NAME}}
    └─ Vendor Account Manager: {{NAME}}
  → Escalate at 4 hours if unresolved:
    └─ Executive Sponsor: {{NAME}}
```

### P2 — Major Incident

```
Detection
  → Technical Lead: {{NAME}}
  → Notify within 1 hour:
    ├─ Product Owner: {{NAME}}
    └─ Vendor Support (if vendor-side)
  → Escalate at 4 hours if unresolved:
    └─ Incident Commander: {{NAME}}
```

### P3/P4 — Moderate/Minor

```
Detection
  → Log in {{TICKETING_SYSTEM}}
  → Assign to: {{TEAM/QUEUE}}
  → SLA: P3 = 4 hours response / P4 = next business day
```

---

## 3. On-Call Rotation / Contact List

| Role | Primary | Phone | Email | Backup |
|------|---------|-------|-------|--------|
| Incident Commander | {{NAME}} | {{PHONE}} | {{EMAIL}} | {{BACKUP}} |
| Technical Lead | {{NAME}} | {{PHONE}} | {{EMAIL}} | {{BACKUP}} |
| Product Owner | {{NAME}} | {{PHONE}} | {{EMAIL}} | {{BACKUP}} |
| Security POC | {{NAME}} | {{PHONE}} | {{EMAIL}} | {{BACKUP}} |
| Vendor Liaison | {{NAME}} | {{PHONE}} | {{EMAIL}} | {{BACKUP}} |

### Vendor Contacts

| Vendor | Support Channel | Hours | Escalation |
|--------|----------------|-------|------------|
| {{VENDOR}} | {{Portal/Phone/Email}} | {{Hours}} | {{Account Manager}} |

---

## 4. Communication Templates

### Internal — Incident Detected (P1/P2)

```
Subject: [P{{N}}] {{PRODUCT_NAME}} — {{Brief Description}}

Team,

An incident has been detected affecting {{PRODUCT_NAME}}.

Severity: P{{N}}
Impact: {{Who is affected and how}}
Status: Investigating
Incident Commander: {{Name}}

Next update in {{X}} minutes.

Do NOT contact the vendor directly — all vendor communication goes through {{Vendor Liaison}}.
```

### Internal — Status Update

```
Subject: [P{{N}}] {{PRODUCT_NAME}} — Update #{{N}}

Status: {{Investigating / Identified / Monitoring / Resolved}}
Duration: {{X}} hours since detection

What we know:
- {{Finding 1}}
- {{Finding 2}}

What we're doing:
- {{Action 1}}
- {{Action 2}}

Next update in {{X}} minutes/hours.
```

### Internal — Resolution

```
Subject: [RESOLVED] {{PRODUCT_NAME}} — {{Brief Description}}

The P{{N}} incident has been resolved.

Duration: {{X}} hours
Root Cause: {{Brief description}}
Resolution: {{What was done}}
Users Affected: {{Number/scope}}

Post-mortem will be conducted on {{DATE}}.
```

### External — Customer/Stakeholder Notification
<!-- Only if regulatory or contractual obligation requires external notification -->

```
Subject: {{PRODUCT_NAME}} Service Update

We experienced a temporary disruption to {{SERVICE}}.

Impact: {{Plain language description}}
Duration: {{Start time}} to {{End time}}
Current Status: Fully restored

We apologize for any inconvenience. A review is underway to prevent recurrence.
```

---

## 5. Runbooks

### Runbook 1: {{COMMON_FAILURE_MODE}}
<!-- Example: "SSO Authentication Failure" -->

**Symptoms:** {{What users report or monitoring detects}}
**Impact:** {{Who is affected}}

**Diagnosis Steps:**
1. {{Check X}}
2. {{Check Y}}
3. {{Check Z}}

**Resolution Steps:**
1. {{Step 1}}
2. {{Step 2}}
3. {{Step 3}}

**Verification:**
- {{How to confirm the issue is resolved}}

**Workaround (if resolution is delayed):**
- {{Temporary mitigation}}

### Runbook 2: {{COMMON_FAILURE_MODE}}
<!-- Repeat for each known failure mode -->

---

## 6. Root Cause Analysis Process

After every P1/P2 incident, conduct a blameless post-mortem within **5 business days**.

### Post-Mortem Template

```
# Post-Mortem: {{Incident Title}}

Date: {{DATE}}
Duration: {{X}} hours
Severity: P{{N}}
Author: {{Name}}

## Timeline
- HH:MM — {{Event}}
- HH:MM — {{Event}}

## Root Cause
{{Description — be specific and technical}}

## Impact
- Users affected: {{N}}
- Data affected: {{Description}}
- Revenue/operational impact: {{Description}}

## What Went Well
- {{Item}}

## What Went Wrong
- {{Item}}

## Action Items
| # | Action | Owner | Due Date | Status |
|---|--------|-------|----------|--------|
| 1 | {{Action}} | {{Owner}} | {{Date}} | Open |

## Lessons Learned
- {{Lesson}}
```

---

## 7. Regulatory Notification Requirements

| Regulation | Trigger | Notification Window | To Whom | Owner |
|-----------|---------|--------------------|---------|----- |
| {{GDPR/CCPA/SOX/etc.}} | {{What triggers notification}} | {{Hours/Days}} | {{Authority/Regulator}} | {{Name}} |

### Coco Inc Legal Involvement
- **Any data breach:** Notify {{Legal Contact}} immediately
- **Client data involved:** Notify {{Client Relationship Lead}} within 1 hour
- **Regulatory implications:** Legal determines notification obligations

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | {{DATE}} | {{AUTHOR}} | Initial draft |
