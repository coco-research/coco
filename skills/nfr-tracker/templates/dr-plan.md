# Disaster Recovery Plan — {{PROJECT_NAME}}

**Version:** 0.1 (Draft)
**Owner:** {{OWNER}}
**Last Updated:** {{DATE}}
**Classification:** {{DATA_CLASSIFICATION}}
**Next Review:** {{NEXT_REVIEW_DATE}}

---

## 1. Scope

### Systems Covered
<!-- List all systems, services, and data stores this DR plan covers -->

| System | Type | Criticality | Owner |
|--------|------|-------------|-------|
| {{SYSTEM_1}} | {{SaaS/Internal/Hybrid}} | {{P1/P2/P3}} | {{OWNER}} |

### Out of Scope
<!-- Explicitly list what this plan does NOT cover -->

---

## 2. Recovery Objectives

### RTO — Recovery Time Objective
<!-- Maximum acceptable downtime per system tier -->

| Tier | RTO | Systems |
|------|-----|---------|
| Critical (P1) | {{X}} hours | {{SYSTEMS}} |
| Important (P2) | {{X}} hours | {{SYSTEMS}} |
| Standard (P3) | {{X}} business days | {{SYSTEMS}} |

### RPO — Recovery Point Objective
<!-- Maximum acceptable data loss per data classification -->

| Data Classification | RPO | Backup Frequency |
|--------------------|-----|------------------|
| Purple Data | {{X}} hours | {{FREQUENCY}} |
| Red Data | {{X}} hours | {{FREQUENCY}} |
| Green Data | {{X}} hours | {{FREQUENCY}} |

---

## 3. Recovery Procedures

### Scenario 1: {{SCENARIO_NAME}}
<!-- Example: "Complete SaaS Platform Outage" -->

**Trigger:** {{What indicates this scenario is happening}}
**Impact:** {{What users/processes are affected}}

**Recovery Steps:**
1. {{Step 1 — Detection and confirmation}}
2. {{Step 2 — Immediate containment}}
3. {{Step 3 — Communication to stakeholders}}
4. {{Step 4 — Recovery action}}
5. {{Step 5 — Verification}}
6. {{Step 6 — Resumption of operations}}

**Estimated Duration:** {{X}} hours
**Decision Maker:** {{Name and role}}

### Scenario 2: {{SCENARIO_NAME}}
<!-- Repeat for each major failure scenario -->

---

## 4. Backup Strategy

| Data/System | Backup Method | Frequency | Retention | Location | Responsible |
|-------------|--------------|-----------|-----------|----------|-------------|
| {{DATA_1}} | {{Method}} | {{Freq}} | {{Days}} | {{Where}} | {{Who}} |

### Backup Verification
<!-- How do you verify backups are working? -->
- Verification frequency: {{Monthly/Quarterly}}
- Last verified: {{DATE}}
- Verification method: {{Test restore/Checksum/Audit}}

---

## 5. Failover Architecture

<!-- Describe the failover model -->
- **Type:** {{Active-Passive / Active-Active / Cold Standby / Vendor-Managed}}
- **Failover Time:** {{X minutes/hours}}
- **Automatic/Manual:** {{Describe trigger}}

### For Vendor SaaS Products
- **Vendor DR SLA:** {{From contract — e.g., "99.9% uptime, 4hr RTO"}}
- **Vendor DR Documentation:** {{Link to vendor's DR/BC page}}
- **Coco Inc-Side Failover:** {{What we do if vendor is down — manual workaround, alternative tool, etc.}}

---

## 6. Communication Plan During Disaster

### Notification Cascade

| Audience | Method | Within | Template | Owner |
|----------|--------|--------|----------|-------|
| Incident team | Slack/Teams | 15 min | See IRP | {{Name}} |
| Product stakeholders | Email | 1 hour | Appendix A | {{Name}} |
| Executive leadership | Email + call | 2 hours | Appendix B | {{Name}} |
| End users | Email/portal | 4 hours | Appendix C | {{Name}} |

### Status Update Cadence
- During active incident: Every {{X}} minutes
- During recovery: Every {{X}} hours
- Post-recovery: Closure communication within {{X}} hours

---

## 7. Roles and Responsibilities

| Role | Person | Backup | Responsibilities |
|------|--------|--------|-----------------|
| DR Coordinator | {{Name}} | {{Backup}} | Declares disaster, coordinates recovery |
| Technical Lead | {{Name}} | {{Backup}} | Executes recovery procedures |
| Communications Lead | {{Name}} | {{Backup}} | Stakeholder notifications |
| Business Owner | {{Name}} | {{Backup}} | Business impact decisions |
| Vendor Liaison | {{Name}} | {{Backup}} | Vendor escalation and status |

---

## 8. Testing Schedule

| Test Type | Frequency | Last Conducted | Next Scheduled | Result |
|-----------|-----------|---------------|----------------|--------|
| Tabletop exercise | Annual | {{DATE}} | {{DATE}} | {{Pass/Fail/N/A}} |
| Backup restore test | Quarterly | {{DATE}} | {{DATE}} | {{Pass/Fail/N/A}} |
| Full failover test | Annual | {{DATE}} | {{DATE}} | {{Pass/Fail/N/A}} |
| Communication test | Semi-annual | {{DATE}} | {{DATE}} | {{Pass/Fail/N/A}} |

---

## 9. Dependencies

| Dependency | Type | Impact if Unavailable | Mitigation |
|-----------|------|----------------------|------------|
| {{DEP_1}} | {{Internal/Vendor/Infrastructure}} | {{Impact}} | {{Mitigation}} |

---

## 10. Appendices

### Appendix A: Stakeholder Notification Template
<!-- Pre-written template for notifying product stakeholders -->

### Appendix B: Executive Notification Template
<!-- Pre-written template for leadership escalation -->

### Appendix C: User Communication Template
<!-- Pre-written template for end-user notification -->

### Appendix D: Vendor Contact Information
<!-- Vendor support numbers, escalation paths, account team -->

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | {{DATE}} | {{AUTHOR}} | Initial draft |
