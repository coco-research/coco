# Architecture Review Board Submission — {{PROJECT_NAME}}

**Submitted By:** {{OWNER}}
**Date:** {{DATE}}
**ProdID:** {{PROD_ID}}
**Data Classification:** {{DATA_CLASSIFICATION}}
**Review Type:** {{New Product / Major Change / Periodic Review}}

---

## 1. Executive Summary

<!-- 2-3 sentences: What is this product/change and why does it need ARB review? -->

---

## 2. Architecture Overview

### System Context
<!-- Where does this product sit in the Coco Inc technology landscape? -->
<!-- Include: upstream systems, downstream consumers, integration points -->

### Component Diagram
<!-- Module/component breakdown. For vendor SaaS: which modules are deployed, how they connect -->

### Data Flow
<!-- How does data enter, move through, and leave the system? -->
<!-- For Purple Data: explicitly trace the data path from source to storage to consumption -->

---

## 3. Technology Stack

| Layer | Technology | Hosting | Managed By |
|-------|-----------|---------|-----------|
| Application | {{e.g., a SaaS application}} | {{Cloud/On-prem/Hybrid}} | {{Vendor/Coco Inc/Shared}} |
| Database | {{e.g., Vendor-managed}} | {{Cloud}} | {{Vendor}} |
| Integration | {{e.g., REST API, SAML 2.0}} | {{N/A}} | {{Coco Inc}} |
| Identity | {{e.g., Okta SSO}} | {{Cloud}} | {{Coco Inc}} |
| Analytics | {{e.g., Snowflake}} | {{Cloud}} | {{Coco Inc}} |

---

## 4. Security Architecture

### Authentication & Authorization
- **SSO:** {{SAML 2.0 / OIDC / Other}} via {{Okta / Azure AD / Other}}
- **MFA:** {{Yes/No — describe}}
- **RBAC Model:** {{Describe role hierarchy}}
- **License Model:** {{N licenses, M user types}}

### Data Protection
- **Encryption at Rest:** {{Describe}}
- **Encryption in Transit:** {{TLS version}}
- **Data Residency:** {{Region/Country}}
- **Data Retention:** {{Policy}}
- **Backup:** {{Frequency, retention, location}}

### Network Security
- **Network Segmentation:** {{Describe}}
- **API Security:** {{Authentication method, rate limiting}}
- **Firewall/WAF:** {{Describe}}

---

## 5. Integration Architecture

| Integration | Direction | Protocol | Frequency | Data Exchanged | Owner |
|------------|-----------|----------|-----------|---------------|-------|
| {{System}} | {{Inbound/Outbound/Bidirectional}} | {{REST/SFTP/SAML/etc.}} | {{Real-time/Batch/On-demand}} | {{What data}} | {{Who maintains}} |

### Error Handling
- **Retry policy:** {{Describe}}
- **Dead letter queue:** {{Yes/No}}
- **Alerting:** {{How failures are detected and reported}}

---

## 6. Scalability & Performance

- **Expected users:** {{N concurrent / N total}}
- **Expected data volume:** {{Rows/GB/Transactions per period}}
- **SLA from vendor:** {{Uptime %, response time}}
- **Performance baselines:** {{If established}}

---

## 7. Disaster Recovery & Business Continuity

- **RTO:** {{Hours}}
- **RPO:** {{Hours}}
- **DR Strategy:** {{Vendor-managed / Coco Inc-managed / Hybrid}}
- **DR Plan Location:** {{Link or "To be created"}}
- **Last DR Test:** {{Date or "Not yet tested"}}

---

## 8. Compliance & Governance

- **Data Classification:** {{Purple/Red/Green}}
- **PSR Status:** {{Completed/In Progress/Not Started}}
- **SOC 2 Type II:** {{Received/Requested/Not Available}}
- **CUECs Reviewed:** {{Yes/No}}
- **Regulatory Requirements:** {{SOX, GDPR, etc. — describe applicability}}

---

## 9. Architecture Decisions (ADRs)

### ADR-1: {{Decision Title}}
- **Context:** {{Why this decision was needed}}
- **Decision:** {{What was decided}}
- **Alternatives Considered:** {{What else was evaluated}}
- **Consequences:** {{Trade-offs accepted}}

### ADR-2: {{Decision Title}}
<!-- Repeat for each significant architecture decision -->

---

## 10. Open Questions for ARB

| # | Question | Impact if Unresolved |
|---|----------|---------------------|
| 1 | {{Question}} | {{Impact}} |

---

## 11. Review Outcome

<!-- Filled in by ARB reviewers -->

| Reviewer | Role | Decision | Date |
|----------|------|----------|------|
| {{Name}} | {{Role}} | {{Approved / Approved with Conditions / Rejected}} | {{Date}} |

### Conditions (if applicable)
1. {{Condition}}

### Action Items from Review
| # | Action | Owner | Due Date | Status |
|---|--------|-------|----------|--------|
| 1 | {{Action}} | {{Owner}} | {{Date}} | {{Open/Closed}} |

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | {{DATE}} | {{AUTHOR}} | Initial submission |
