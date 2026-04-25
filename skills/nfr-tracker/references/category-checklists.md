# NFR Category Checklists — Assessment Reference

This file defines the exact checklist used to assess each NFR category. The NFR tracker uses these checklists to calculate completeness scores.

## Scoring Rule

```
category_score = checked_items / total_items
```

A checklist item is "checked" when:
- A section header matching the item exists in the document, AND
- The section contains substantive content (at least 3 non-empty lines, or a table with data rows, or a list with 2+ items)

---

## PRD — Product Requirements Document

**Total items: 13**

```
[ ] Executive summary or problem statement
[ ] Goals and objectives (measurable)
[ ] User personas (at least 2 defined)
[ ] User stories with acceptance criteria
[ ] Functional requirements (table or numbered list)
[ ] Non-functional requirements
[ ] Success metrics with targets and measurement method
[ ] Scope — in-scope and out-of-scope explicitly defined
[ ] Timeline and milestones (dates, not just phases)
[ ] Risks with impact/probability and mitigation strategies
[ ] Dependencies listed with owners and status
[ ] Sign-off table with stakeholder names and dates
[ ] Evidence of stakeholder review (comments, meeting notes referencing review)
```

---

## ARB — Architecture Review Board

**Total items: 10**

```
[ ] Executive summary (what and why)
[ ] Architecture overview with diagrams
[ ] Technology stack documented
[ ] Security architecture (auth, encryption, network)
[ ] Integration architecture with protocols and data flows
[ ] Scalability and performance considerations
[ ] DR and business continuity summary
[ ] Compliance and governance status
[ ] Architecture decision records (ADRs) — at least 1
[ ] Review outcome recorded (approved/rejected/conditional)
```

---

## PSR — Product Security Review

**Total items: 8**

```
[ ] PSR questionnaire submitted
[ ] Data classification confirmed
[ ] Authentication method documented
[ ] Data encryption (at rest and in transit) confirmed
[ ] Access control model documented
[ ] Third-party/vendor security assessment
[ ] Findings list with remediation status
[ ] PSR approval received
```

---

## RAI — Responsible AI Assessment

**Total items: 7**

```
[ ] AI/ML features identified and described
[ ] Training data provenance documented
[ ] Bias assessment conducted
[ ] Transparency/explainability measures
[ ] Human oversight mechanisms
[ ] Data privacy impact for AI features
[ ] RAI review approval
```

---

## Pentest — Penetration Testing

**Total items: 6**

```
[ ] Pentest scope defined
[ ] Pentest conducted (report received)
[ ] Critical findings: zero open
[ ] High findings: zero open or accepted with timeline
[ ] Remediation plan for medium/low findings
[ ] Retest scheduled or completed for remediated items
```

---

## Vuln — Vulnerability Management

**Total items: 6**

```
[ ] SAST scan completed
[ ] DAST scan completed
[ ] No critical vulnerabilities open
[ ] No high vulnerabilities open (or accepted with timeline)
[ ] Dependency/supply chain scan completed
[ ] Scan cadence established (ongoing)
```

---

## DR — Disaster Recovery Plan

**Total items: 10**

```
[ ] Scope — systems and services covered
[ ] RTO defined per service tier
[ ] RPO defined per data classification
[ ] Recovery procedures (step-by-step for each scenario)
[ ] Backup strategy (frequency, location, retention)
[ ] Failover architecture described
[ ] Communication plan during disaster
[ ] Roles and responsibilities assigned
[ ] Testing schedule defined (annual minimum)
[ ] Last test date and results recorded
```

---

## IRP — Incident Response Plan

**Total items: 8**

```
[ ] Severity classification defined (P1-P4)
[ ] Escalation paths per severity level
[ ] On-call rotation or contact list
[ ] Communication templates (internal and external)
[ ] Runbooks for common failure modes (at least 2)
[ ] Root cause analysis process defined
[ ] Post-mortem template exists
[ ] Regulatory notification requirements documented
```

---

## Recovery — Recovery Procedures

**Total items: 6**

```
[ ] Failure modes enumerated
[ ] Step-by-step runbook for each failure mode
[ ] Verification steps after recovery
[ ] Workarounds documented for each scenario
[ ] Recovery time estimates per scenario
[ ] Runbooks tested (date of last test)
```

---

## PMA — Post-Mortem / After-Action

**Total items: 5**

```
[ ] Post-mortem template exists
[ ] Process documented (when to trigger, who participates)
[ ] Blameless culture statement
[ ] Action item tracking mechanism
[ ] Recent incidents reviewed (if any have occurred)
```

---

## Perf — Performance & SLAs

**Total items: 7**

```
[ ] SLIs (Service Level Indicators) defined
[ ] SLOs (Service Level Objectives) set with thresholds
[ ] Monitoring configured and producing data
[ ] Alerting thresholds set
[ ] Performance baseline established
[ ] Load testing results (if applicable)
[ ] Vendor SLA terms documented and verified
```

---

## DORA — DORA Metrics

**Total items: 4**

```
[ ] Deployment frequency tracked
[ ] Lead time for changes tracked
[ ] Mean time to recovery (MTTR) tracked
[ ] Change failure rate tracked
```

---

## Coverage — Test Coverage

**Total items: 5**

```
[ ] Unit test coverage meets threshold (e.g., >80%)
[ ] Integration test coverage documented
[ ] E2E test scenarios defined and passing
[ ] Coverage reporting automated in CI/CD
[ ] UAT plan and results (for implementation projects)
```

---

## Tech Arch — Technical Architecture

**Total items: 8**

```
[ ] System context diagram
[ ] Component or module diagram
[ ] Data flow diagram
[ ] Integration points documented
[ ] Architecture decisions recorded (ADRs)
[ ] Security architecture documented
[ ] Scalability considerations addressed
[ ] Deployment architecture described
```

---

## Stakeholder Comms — Stakeholder Communications

**Total items: 6**

```
[ ] Status update template
[ ] Escalation communication template
[ ] Go-live announcement template
[ ] Stakeholder distribution list maintained
[ ] Communication cadence defined
[ ] Approval workflow for external communications
```

---

## Training — Training & Enablement

**Total items: 6**

```
[ ] Training plan with phases and timeline
[ ] Target audiences segmented (admin, user, executive)
[ ] Training materials exist (guides, videos, references)
[ ] Completion tracking mechanism in place
[ ] Post-training assessment or feedback loop
[ ] Ongoing support channel defined
```

---

## Vendor Mgmt — Vendor Management

**Total items: 7**

```
[ ] Contract terms documented (start, end, renewal)
[ ] SLAs from vendor documented
[ ] Escalation paths to vendor defined
[ ] Vendor contact list maintained
[ ] Renewal dates tracked
[ ] Sub-processor list reviewed (if applicable)
[ ] Data processing agreement in place
```

---

## Change Mgmt — Change Management

**Total items: 7**

```
[ ] Change request template or process exists
[ ] Impact assessment framework defined
[ ] Approval workflow documented (who approves what tier)
[ ] Rollback procedure for each change type
[ ] Communication plan for affected stakeholders
[ ] Post-change verification process
[ ] Change log or audit trail maintained
```

---

## Coco Inc-Specific Categories

### CUEC — Complementary User Entity Controls

**Total items: 5**

```
[ ] SOC 2 Type II report received from vendor
[ ] CUECs extracted from SOC 2 report
[ ] Gap analysis: Coco Inc controls vs. required CUECs
[ ] Remediation plan for gaps
[ ] Evidence of CUEC compliance collected
```

### CF Controls — Complementary Framework Controls

**Total items: 6**

```
[ ] Encryption controls verified
[ ] Logging and monitoring controls verified
[ ] Network segmentation controls verified
[ ] Data residency controls verified
[ ] Backup and recovery controls verified
[ ] Vulnerability management controls verified
```

### Access Mgmt — Access Management

**Total items: 6**

```
[ ] SSO integration configured and tested
[ ] JML lifecycle process documented (Joiner/Mover/Leaver)
[ ] ServiceNow tile provisioned (or request submitted)
[ ] RBAC model documented and implemented
[ ] Recertification cadence established
[ ] Privileged access management defined
```

### Data Classification

**Total items: 5**

```
[ ] Data classification confirmed (Purple/Red/Green)
[ ] Hosting location verified against classification requirements
[ ] Data retention policy documented
[ ] Data flow diagram shows classification at each point
[ ] Classification registered in product registry
```

### Vendor Security — Vendor Security Posture

**Total items: 5**

```
[ ] SOC 2 Type II report received (current year)
[ ] Cyber insurance verification
[ ] Sub-processor list reviewed
[ ] Data processing agreement signed
[ ] Vendor security questionnaire completed
```
