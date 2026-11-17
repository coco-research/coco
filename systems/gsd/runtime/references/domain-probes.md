# Domain-Aware Probing Patterns

Shared reference for `/gsd-begin`, `/gsd:discuss-phase`, and domain exploration workflows.

When the user mentions a technology area, use these probes to ask insightful follow-up questions. Don't run through them as a checklist -- pick the 2-3 most relevant based on context. The goal is to surface hidden assumptions and trade-offs the user may not have considered yet.

---

## Authentication

| User mentions | Agent probes with domain knowledge |
|---|---|
| "login" or "auth" | OAuth (which providers?), JWT, or session-based? Do you need social login or just email/password? |
| "users" or "accounts" | MFA required? Password reset flow? Email verification? |
| "sessions" | Session duration and refresh strategy? Server-side sessions or stateless tokens? |
| "roles" or "permissions" | RBAC, ABAC, or simple role checks? How many distinct roles? |
| "API keys" | Key rotation strategy? Scoped permissions per key? Rate limiting per key? |

---

## Real-Time Updates

| User mentions | Agent probes with domain knowledge |
|---|---|
| "real-time" or "live updates" | WebSockets, SSE, or polling? What specifically needs to be real-time vs. eventual? |
| "notifications" | Push notifications (browser/mobile), in-app only, or both? Persistence and read receipts? |
| "collaboration" or "multiplayer" | Conflict resolution strategy? Operational transforms or CRDTs? Expected concurrent users? |
| "chat" or "messaging" | Message history and search? Typing indicators? Read receipts? |
| "streaming" | Reconnection strategy? What happens when the connection drops -- queue or discard? |

---

## Dashboard
