# External Integrations Template

Template for `.planning/codebase/INTEGRATIONS.md` - captures external service dependencies.

**Purpose:** Document what external systems this codebase communicates with. Focused on "what lives outside our code that we depend on."

---

## File Template

```markdown
# External Integrations

**Analysis Date:** [YYYY-MM-DD]

## APIs & External Services

**Payment Processing:**
- [Service] - [What it's used for: e.g., "subscription billing, one-time payments"]
  - SDK/Client: [e.g., "stripe npm package v14.x"]
  - Auth: [e.g., "API key in STRIPE_SECRET_KEY env var"]
