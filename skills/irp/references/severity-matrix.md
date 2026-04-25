# Severity Matrix Framework

## Base Matrix (Customize Per Product)

| Severity | Service Impact | Data Impact | User Impact | Response SLA |
|----------|---------------|-------------|-------------|-------------|
| **SEV1 — Critical** | Complete outage or core function broken | Data breach, corruption, or loss | All users affected, no workaround | 15 min response, continuous until resolved |
| **SEV2 — High** | Major feature unavailable | Data integrity concern, potential loss | >50% users affected or key workflow blocked | 1 hour response, 4 hour update cadence |
| **SEV3 — Medium** | Minor feature unavailable, workaround exists | No data impact, potential for escalation | <50% users, workaround available | 4 hour response, daily updates |
| **SEV4 — Low** | Cosmetic or minor, no workflow impact | No data impact | Single user or edge case | Next business day |

## Data Classification Override

The product's data classification sets a minimum severity floor:

| Data Classification | Minimum Severity for Any Data Incident |
|--------------------|-----------------------------------------|
| Purple Data | SEV1 — auto-escalate to legal and security |
| Red Data | SEV2 — security team notified |
| Yellow Data | SEV3 — standard process |
| Green Data | No override |

## Example Incidents by Severity (SaaS GRC Platform)

### SEV1 Examples
- Unauthorized user gains access to audit/compliance data
- Complete platform outage during regulatory filing deadline
- Data exfiltration detected
- SSO breach affecting all users
- Vendor reports data center incident affecting customer data

### SEV2 Examples
- Primary workflow module down (e.g., risk register unavailable)
- Integration failure causing data sync halt (>2 hours)
- Bulk permission misconfiguration exposing data across teams
- Failed data export during scheduled backup window
- Vendor deploys breaking change without notice

### SEV3 Examples
- Single module partially degraded (e.g., reports slow but functional)
- Non-critical integration intermittent
- Single user locked out (non-admin)
- Report generation failing for specific date range
- UI rendering issue in one browser

### SEV4 Examples
- Formatting errors in exported reports
- Non-functional link in notification email
- Minor UI alignment issue
- Help text displays incorrect version number
