---
name: pmstudio-dr
description: Generate a Disaster Recovery plan with RTO/RPO targets. Use when someone asks to "create a DR plan", "disaster recovery", "business continuity", or "RTO RPO". Do NOT use for step-by-step restoration runbooks — use /pmstudio-recovery instead. Designed for SaaS platform products where Coco Inc is the customer — focuses on service continuity, data recovery, and vendor dependency management rather than infrastructure rebuild.
---

# DR Plan — Disaster Recovery Plan

## Purpose

Generates a Disaster Recovery plan scoped to a specific product. For SaaS products (where the vendor owns infrastructure), this plan focuses on what Coco Inc controls: data exports, integration failover, access recovery, communication, and business continuity.

## Process

### Step 1: Read Context

**Read all that exist:**
- `CLAUDE.local.md` — architecture, integrations, vendor info, data strategy
- `PRD/*.html` or `PRD/*.md` — NFRs, technical considerations, integrations, data architecture
- `Architecture/` — system diagrams, data flows
- `Operational/IRP-*.html` — incident response plan (if exists, reference for communication)

### Step 2: Determine Product Type

From context, classify the product:

| Type | DR Focus | Example |
|------|----------|---------|
| **SaaS (customer)** | Vendor dependency, data portability, alternative workflows | (third-party SaaS)  |
| **Self-hosted** | Infrastructure recovery, backup/restore, failover | Custom app on EKS |
| **Hybrid** | Both vendor and self-hosted components | SaaS + custom middleware |

Adjust the plan scope accordingly. For SaaS, skip infrastructure sections (that's the vendor's problem). Add vendor SLA and data portability sections.

### Step 3: Ask Discovery Questions

Only ask what can't be inferred:

1. **Business criticality tier?** (Tier 1 critical / Tier 2 important / Tier 3 standard)
2. **What's the maximum tolerable downtime?** (This becomes RTO)
3. **What's the maximum tolerable data loss?** (This becomes RPO)
4. **Are there manual workarounds if the product is down?** (e.g., "we can use Excel for 48 hours")
5. **Vendor SLA?** (uptime commitment, support response times, data export capabilities)
6. **Backup strategy?** (Does data export to Snowflake/SharePoint? How often?)

### Step 4: Generate DR Plan

**Output:** `Operational/DR-Plan-{ProductName}-{Date}.html`

Self-contained HTML with clean typography and print CSS.

**11 sections:**

**1. Purpose & Scope**
- Product name, ProdID, instances covered
- What this plan covers and doesn't cover
- Relationship to vendor's own DR plan

**2. Service Classification**
- Business criticality tier with justification
- Data classification (Purple/Red/Yellow/Green)
- Regulatory or compliance requirements affecting recovery
- Business impact of downtime (per hour/day)

**3. RTO/RPO Targets**

Per-component target table:

| Component | RTO | RPO | Justification |
|-----------|-----|-----|---------------|
| Core platform | 4 hours | 24 hours | Vendor SLA: 99.9% uptime |
| Data in Snowflake | 2 hours | 0 (real-time sync) | Analytics feeds downstream |
| Integrations (SSO) | 1 hour | N/A | Users locked out |
| Integrations (ServiceNow) | 8 hours | N/A | Ticket creation manual fallback |

**4. Disaster Scenarios**

Ranked by likelihood x impact:

1. **Vendor platform outage** (most likely) — vendor is down, product inaccessible
2. **Data corruption** — bad data entered or sync error corrupts records
3. **Access loss** — SSO failure, license revocation, permission misconfiguration
4. **Integration failure** — upstream/downstream system breaks connection
5. **Security breach** — unauthorized access, data exfiltration
6. **Vendor business failure** — vendor acquired, shut down, or ends product

For each scenario: description, likelihood, impact, detection method.

**5. Recovery Procedures**

Per-scenario step-by-step. See `references/saas-dr-patterns.md` for SaaS-specific recovery patterns.

Structure per scenario:
- Trigger condition (how do we know this is happening)
- Immediate actions (first 15 minutes)
- Short-term recovery (first 4 hours)
- Full recovery (to meet RTO)
- Verification checklist

**6. Communication Plan**
- Who to notify per scenario and severity
- Templates (reference IRP if it exists, or provide standalone)
- Vendor communication (support ticket + account manager)
- Stakeholder updates cadence during outage

**7. Dependencies**
- External systems required for recovery
- Vendor contacts (support, account manager, escalation)
- SLA commitments and how to invoke them
- Third-party services (SSO provider, email, etc.)

**8. Data Backup & Restoration**
- What data is backed up (by vendor, by Coco Inc)
- Backup frequency and retention
- Where backups are stored
- Restoration procedure (step-by-step)
- Data validation after restoration

**9. Manual Workarounds**
- What business processes can continue without the product
- Excel/SharePoint fallback procedures
- Duration the workaround is sustainable
- Data reconciliation procedure when product is restored

**10. Testing Schedule**
- DR test cadence (annually minimum, semi-annually recommended)
- Test scenarios (tabletop, partial recovery, full recovery)
- Last test date and results
- Next scheduled test
- Test success criteria

**11. Review & Maintenance**
- Review cadence: semi-annually or after any DR event
- Approval chain (PM, Security POC, Sponsor)
- Version history
- Distribution list

### Step 5: Present for Review

Show the plan outline with key decisions highlighted:
- RTO/RPO targets
- Scenario prioritization
- Manual workaround availability

Ask for approval before writing.

## Critical Rules

1. **RTO/RPO must be numbers, not words.** "As fast as possible" is not an RTO. Push for specific hours.
2. **Vendor DR is not your DR.** The vendor's uptime SLA is an input to your plan, not a substitute for it. Your plan covers what happens on Coco Inc's side.
3. **Manual workarounds are critical.** For every scenario, document what the business does while the product is down. If there's no workaround, that's a risk to flag.
4. **Data portability is DR.** If you can't get data out of the product, you can't recover from vendor failure. Document export capabilities.
5. **Test the plan.** A plan that's never been tested is a wish list. Include a testing schedule and success criteria.
