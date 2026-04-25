# Coco Inc ARB 11-Slide Format

## Slide-by-Slide Detail

### Slide 1: Title & Context
- Product / platform name
- ProdID (from product registry)
- Review type: New Product | Major Change | Periodic Review | Decommission
- Date of review
- Presenters: PM, Technical Lead, Security POC
- Slide footer: data classification badge (Purple/Red/Yellow/Green)

### Slide 2: Business Context
- Problem statement (from PRD Section 2)
- Strategic alignment — which firm initiative does this support
- Sponsor name and org
- Business impact: quantified if possible (users, processes, risk reduction)
- Why now: what triggered this review

### Slide 3: Current State Architecture (AS-IS)
- Mermaid diagram showing current system components
- Existing integrations (SSO, ServiceNow, Snowflake, etc.)
- Data flows between components
- Pain points / limitations highlighted in red
- Technology stack labels on each component

### Slide 4: Proposed Architecture (TO-BE)
- Mermaid diagram showing proposed state
- Delta from current state highlighted (new components in green, removed in red, modified in amber)
- Key architectural decisions annotated
- If no change from current: label "Architecture Unchanged — Review for Continued Compliance"

### Slide 5: Data Architecture
- Data classification per data store (Purple/Red/Yellow/Green badges)
- Data flow diagram: where data enters, where it's processed, where it's stored, where it exits
- Data residency: which regions, any cross-border transfer
- Data retention: how long, where, deletion procedures
- Encryption: at rest (AES-256), in transit (TLS 1.2+)
- Data backup: frequency, location, retention
- PII/sensitive data handling

### Slide 6: Security & Access
- Authentication: SSO (SAML 2.0 / OIDC), MFA, service accounts
- Authorization: RBAC model, role definitions, permission matrix
- Network: VPN, IP allowlisting, WAF, DDoS protection
- Encryption: transit + rest details
- CUECs: Complementary User Entity Controls from SOC 2 Type II
- Audit logging: what's logged, retention, access to logs
- Vulnerability management: scanning cadence, patching SLA

### Slide 7: Integration Points
- Table format:

| System | Direction | Protocol | Frequency | Data Exchanged | Error Handling | Owner |
|--------|-----------|----------|-----------|---------------|----------------|-------|

- Highlight single points of failure
- API rate limits and throttling
- Authentication method per integration

### Slide 8: NFRs & SLAs
- Table format:

| Category | Requirement | Target | Current | Source |
|----------|-------------|--------|---------|--------|

- Categories: Performance, Availability, Scalability, Reliability, Security, Compliance
- RTO/RPO targets (from DR plan if exists)
- Vendor SLA vs Coco Inc requirement (if gap, highlight)

### Slide 9: Risk Assessment
- Table format:

| Risk | Likelihood | Impact | Risk Rating | Mitigation | Residual Risk | Owner |
|------|-----------|--------|-------------|------------|---------------|-------|

- Architecture-specific risks (not project/budget risks)
- Include: single points of failure, vendor lock-in, data portability, scalability ceiling, security gaps
- Residual risk acceptance: who accepts, under what conditions

### Slide 10: Implementation Plan
- Phased approach with timeline
- Rollback strategy per phase
- Blast radius analysis: if this fails, what else breaks
- Migration plan (if changing existing architecture)
- Testing strategy: unit, integration, UAT, performance, DR test

### Slide 11: Decision Request
- Clear statement of what you need: "We request approval to proceed with [specific action]"
- Options if applicable:
  - Option A: [description] — recommended
  - Option B: [description] — alternative
  - Option C: [description] — do nothing / defer
- Conditions: any conditions on approval (e.g., "subject to SOC 2 review completion")
- Next steps: what happens after approval, with dates

## Design Notes

- Use Mermaid.js for all architecture diagrams (slides 3, 4, 5)
- Color coding: existing (blue), new (green), removed (red), modified (amber)
- Every slide should be understandable in 60 seconds
- Appendix slides (after 11) for detailed tables, full integration specs, etc.
