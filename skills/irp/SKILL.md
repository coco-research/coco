---
name: pmstudio-irp
description: Generate an Incident Response Plan (IRP) with severity classification, escalation procedures, and communication templates. Use when someone asks to "create an incident response plan", "IRP", "incident procedures", "escalation matrix", "incident playbook", or needs to document how to handle incidents for a product/platform. Reads PRD, stakeholder directory, and project memory to build product-specific response procedures. Complementary to DR plan (DR = restore service; IRP = manage the incident while it's happening).
---

# IRP — Incident Response Plan

## Purpose

Generates an Incident Response Plan specific to the product/platform. Not a generic IT incident template — this plan is scoped to the product, uses its real stakeholders as escalation contacts, and ties severity to its data classification.

## Process

### Step 1: Read Context

**Read all that exist:**
- `CLAUDE.local.md` — architecture, stakeholders, vendor contacts, data classification
- `PRD/*.html` or `PRD/*.md` — security section, RBAC, NFRs, integrations
- `Data/Stakeholder-Directory.*` — escalation contacts with roles and emails
- `Operational/DR-Plan*.html` — recovery procedures to reference (if exists)

### Step 2: Ask Discovery Questions

Only ask what can't be inferred:

1. **What constitutes an "incident" for this product?** (data breach, service outage, unauthorized access, integration failure, data corruption)
2. **Who is the Incident Commander?** (default: PM, but confirm)
3. **Vendor support model?** (SLA response times, escalation contacts, ticket system)
4. **Legal/privilege considerations?** (e.g., ProductB has legal privilege — incidents may require legal counsel)
5. **Existing Coco Inc incident process?** (does the team already report through ServiceNow, Slack, etc.)

### Step 3: Generate IRP Document

**Output:** `Operational/IRP-{ProductName}-{Date}.html`

Self-contained HTML with print-optimized CSS. No CDN dependencies — this document must work offline during an actual incident.

**12 sections:**

**1. Purpose & Scope**
- Which product/instance this plan covers
- What qualifies as an incident vs. a support request
- Relationship to firm-wide incident process

**2. Severity Classification**

Build product-specific severity matrix. See `references/severity-matrix.md` for the framework.

Key rule: **Data classification drives minimum severity.**
- Purple Data incident = auto-SEV1
- Red Data incident = minimum SEV2
- Yellow/Green = severity based on impact

| Severity | Definition | Response Time | Example |
|----------|-----------|---------------|---------|
| SEV1 — Critical | Data breach, complete service outage, legal/regulatory exposure | 15 min | Purple Data accessed by unauthorized user |
| SEV2 — High | Significant functionality loss, data integrity issue, >50% users affected | 1 hour | Integration failure causing data sync halt |
| SEV3 — Medium | Partial functionality loss, workaround available, <50% users affected | 4 hours | Single module unavailable, manual process possible |
| SEV4 — Low | Minor issue, cosmetic, single-user impact | Next business day | Report formatting error, UI glitch |

**3. Detection & Reporting**
- How incidents are typically detected (user report, monitoring, vendor notification)
- Reporting channel (email, Slack, ServiceNow ticket)
- What information to include when reporting

**4. Escalation Matrix**
- Per-severity: who to contact, in what order, with backup contacts
- Pull real names and emails from stakeholder directory
- Include vendor escalation path

**5. Response Procedures**
- Per-severity playbooks with triage, containment, investigation, resolution steps
- See `references/escalation-patterns.md` for playbook structure

**6. Communication Protocol**
- Internal (team Slack/Teams channel)
- Stakeholder (email using `/stakeholder-comms incident` template)
- Vendor (support ticket + phone for SEV1-2)
- Leadership (when to escalate to SteerCo)
- Per-severity: who communicates what, when, through which channel

**7. Evidence Preservation**
- What to capture: screenshots, logs, timestamps, affected records
- Where to store: incident folder in SharePoint, not in the product itself
- Chain of custody for legal/privilege incidents

**8. Resolution & Recovery**
- Handoff to DR/Recovery plan (if exists)
- Verification steps before declaring resolved
- Service restoration confirmation checklist

**9. Post-Incident Review (PIR)**
- PIR meeting within 48 hours of resolution
- Template: timeline, impact, root cause, contributing factors, what went well, what to improve, action items
- PIR document stored in `Meeting-Notes/PIR-{Date}-{Summary}.md`

**10. Roles & Responsibilities**
- Incident Commander (owns coordination)
- Communications Lead (owns stakeholder updates)
- Technical Lead (owns diagnosis and fix)
- Vendor Liaison (owns vendor communication)
- Legal Counsel (for privilege/regulatory incidents)

**11. Vendor Escalation**
- Vendor support tiers and SLA response times
- Escalation contacts (from project memory)
- Ticket creation procedure
- When to bypass normal support (SEV1 phone escalation)

**12. Review & Maintenance**
- Review cadence: semi-annually or after any SEV1-2 incident
- Tabletop exercise schedule: annually
- Contact list verification: quarterly
- Version history

### Step 4: Present for Review

Show the complete plan structure with key content decisions highlighted:
- Severity matrix with product-specific examples
- Escalation matrix with real names
- Any assumptions made

Ask for approval before writing the file.

## Critical Rules

1. **Zero external dependencies.** The HTML must render fully offline. No CDN links. During an incident, internet may be unreliable.
2. **Real contacts only.** Pull names/emails from project files. Leave blanks with "[TBD — add contact]" markers rather than guessing.
3. **Legal privilege awareness.** If the project involves legal privilege (like ProductB/Tax), include a section on when to involve legal counsel and how to protect privilege during incident response.
4. **Severity ties to data.** Always tie severity classification to the product's data classification. Don't create a severity matrix that ignores data sensitivity.
5. **Actionable, not aspirational.** Every procedure should be something the team can actually execute today with current tools and access. Don't include monitoring procedures if no monitoring exists yet.
