# SaaS DR Patterns

## Key Difference: SaaS vs Self-Hosted DR

When Coco Inc is the **customer** of a SaaS product (not the operator), the DR plan shifts focus:

| Concern | Self-Hosted | SaaS Customer |
|---------|------------|---------------|
| Infrastructure recovery | Your problem | Vendor's problem |
| Data backup | Your problem | Shared — verify vendor backup + maintain your own exports |
| Application restore | Your problem | Vendor's problem |
| Access recovery | Your problem | Shared — SSO is yours, app access is vendor |
| Business continuity | Your problem | Your problem |
| Vendor failure | N/A | Your problem (new concern) |

## SaaS-Specific Recovery Patterns

### Pattern 1: Vendor Platform Outage
**Trigger:** Vendor status page shows outage, or users report service unavailable.

1. Confirm via vendor status page (bookmark the URL)
2. Open vendor support ticket (SEV1 if business-critical)
3. Notify stakeholders: "Vendor outage, ETA per vendor, manual workaround available at [location]"
4. Activate manual workaround (Excel/SharePoint fallback)
5. Monitor vendor status page for updates
6. When vendor restores: verify Coco Inc data integrity
7. Reconcile any manual work back into the platform
8. Close incident, notify stakeholders

**Key risk:** Vendor gives optimistic ETAs. Set your own internal deadlines for when to escalate.

### Pattern 2: Data Corruption / Bad Data
**Trigger:** Users report incorrect data, integration sync produced wrong values.

1. Identify scope: which records, which time range, which source
2. Immediately: stop any integrations feeding bad data (pause sync jobs)
3. Identify last-known-good state (Snowflake export timestamp, last verified backup)
4. If vendor-side: open support ticket for data restore from their backups
5. If Coco Inc-side (integration error): restore from Snowflake/backup
6. Validate restored data against source-of-truth
7. Re-enable integrations with monitoring
8. Spot-check for 24 hours

**Key risk:** Cascading corruption — bad data in Layer 1 feeds Layer 2 feeds Layer 3. Check the full chain.

### Pattern 3: Access Loss
**Trigger:** SSO failure, license revocation, permission misconfiguration.

Sub-scenarios:
- **SSO down:** Users can't log in to anything. Contact Okta/Azure AD team. Vendor may have bypass login.
- **License revoked:** Vendor disabled access. Contact account manager immediately.
- **Permission misconfiguration:** Admin accidentally removed access. Check audit log, restore permissions.

1. Identify the access failure type
2. If SSO: escalate to identity team (usually outside your control)
3. If license: contact vendor account manager (phone, not email)
4. If permissions: check vendor audit log, identify the change, revert
5. If vendor has emergency/bypass login: use it for admin access only
6. Verify users can access after fix

**Key risk:** No bypass login. If SSO is the only way in and SSO is down, you're locked out. Confirm vendor emergency access exists.

### Pattern 4: Integration Failure
**Trigger:** Data not flowing between systems (e.g., ServiceNow → SaaS, SaaS → data warehouse).

1. Identify which integration failed and in which direction
2. Check: is the upstream system working? Is the downstream system working? Is the integration middleware working?
3. Check integration logs (vendor admin console, middleware logs)
4. If vendor API issue: open support ticket
5. If middleware issue: restart, check credentials, check rate limits
6. Queue: most integrations can catch up on missed data. Confirm catch-up mechanism.
7. Verify data consistency after restoration

**Key risk:** Silent failure. Integration looks fine but data is stale. Implement freshness checks (last sync timestamp).

### Pattern 5: Security Breach
**Trigger:** Unauthorized access detected, suspicious activity, vendor notification.

1. **Contain immediately:** Disable suspected compromised accounts, revoke API keys if needed
2. Preserve evidence: screenshots, audit logs, timestamps
3. Notify Security POC and Legal (for privilege/regulatory products)
4. Vendor: open SEV1 ticket, request their investigation
5. Assess scope: what data was accessed, for how long, by whom
6. If data breach: follow firm data breach notification procedure
7. Remediate: password resets, permission audit, access review
8. PIR mandatory

**Key risk:** Under-scoping the breach. Assume worst case until proven otherwise.

### Pattern 6: Vendor Business Failure
**Trigger:** Vendor acquired, shuts down product, end-of-life announcement.

This is a **slow-motion disaster** with months of lead time, not an acute incident.

1. Assess timeline: how long until service ends
2. Export ALL data immediately (don't wait for the deadline)
3. Evaluate migration options: competing products, custom build
4. Negotiate with vendor: extended support, data portability assistance
5. Document: all custom configurations, integrations, workflows
6. Plan migration: typically 3-6 months for a GRC platform
7. Communicate: stakeholders need early warning and migration timeline

**Key risk:** Data format portability. Can you actually use your data outside this vendor's platform? Test this before you need it.

## Manual Workaround Design Principles

Every scenario should have a "what do people do while the product is down" answer:

1. **Identify the critical process** — what absolutely can't stop (e.g., tax filing deadlines)
2. **Map to manual equivalent** — usually Excel + SharePoint + email
3. **Pre-build the template** — don't make people create spreadsheets during an outage
4. **Document the reconciliation** — how to merge manual work back into the product
5. **Set a sustainability limit** — manual workaround works for 48 hours, not 2 weeks
