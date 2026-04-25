# PRD — Internal API Gateway

**Status:** Draft
**Author:** Platform Engineering PM
**Last Updated:** 2026-03-19

---

## 1. Problem Statement

**Problem:** Coco Inc's internal microservices ecosystem has grown to 80+ services across 6 product teams, each implementing its own authentication, rate limiting, logging, and routing logic. This leads to inconsistent security posture, duplicated infrastructure code, and no centralized observability for cross-service traffic.

**Current State:** Each service team manages its own ingress (mix of ALB rules, custom middleware, and ad-hoc API keys). Auth logic is copy-pasted across services with varying token validation approaches. Rate limiting exists in 3 services; the rest have none. There is no unified way to trace a request across service boundaries.

**Impact:**
- 2-3 weeks of boilerplate per new service for auth, rate limiting, and routing
- 4 security incidents in the last year traced to inconsistent token validation
- No cross-service request tracing, making production debugging take 3-5x longer than necessary
- Compliance team cannot audit API access patterns across the platform

## 2. Target Users

### Primary: Platform Engineers
- **Role:** Build and maintain shared infrastructure for product teams
- **Needs:** Centralized control plane for routing, auth policies, and traffic management
- **Pain Points:** "Every team re-invents the wheel for auth and rate limiting. We patch the same CVE in 12 different places."

### Secondary: Service Owners
- **Role:** Develop and operate individual microservices
- **Needs:** Self-service onboarding, clear documentation, zero-downtime deployments
- **Pain Points:** "I spend 2 weeks on infrastructure plumbing before I write a single line of business logic."

### Tertiary: Security & Compliance
- **Role:** Audit API access, enforce data classification policies
- **Needs:** Centralized access logs, policy enforcement, anomaly detection
- **Pain Points:** "I cannot answer 'who accessed what API, when' without asking 6 different teams."

## 3. User Stories

### Epic: Service Onboarding
- **P0** As a service owner, I want to register my service via a YAML config file so that the gateway starts routing traffic to it within minutes
  - AC: Config accepts service name, upstream URL, health check path, and auth policy
  - AC: Gateway validates config and returns errors before applying
  - AC: Traffic begins routing within 60 seconds of config apply

- **P0** As a service owner, I want to define route-level auth requirements so that public, internal, and admin endpoints use appropriate policies
  - AC: Supports JWT validation, API key, mTLS, and no-auth (public) modes
  - AC: Auth policy can be set per route prefix
  - AC: Invalid tokens return 401 with a structured error body

### Epic: Traffic Management
- **P1** As a platform engineer, I want to configure rate limits per consumer and per route so that no single client can degrade service for others
  - AC: Rate limits configurable as requests/second and requests/minute
  - AC: Supports per-API-key and per-IP limiting
  - AC: 429 responses include Retry-After header

- **P1** As a platform engineer, I want canary routing so that I can shift 5% of traffic to a new service version before full rollout
  - AC: Weight-based traffic splitting between two upstream versions
  - AC: Automatic rollback if error rate exceeds threshold
  - AC: Canary status visible in the admin dashboard

### Epic: Observability
- **P0** As a platform engineer, I want distributed tracing headers injected on every request so that I can trace calls across service boundaries
  - AC: W3C Trace Context headers (traceparent, tracestate) propagated
  - AC: Gateway adds span for its own processing time
  - AC: Traces exportable to AWS X-Ray and OpenTelemetry collectors

- **P1** As a security analyst, I want a centralized access log with consumer identity, route, response code, and latency so that I can audit API usage
  - AC: Logs written to Kinesis Firehose in structured JSON
  - AC: Consumer identity resolved from JWT claims or API key metadata
  - AC: Logs retained for 90 days in S3, queryable via Athena

## 4. Functional Requirements

### Authentication & Authorization
- JWT validation with configurable issuer, audience, and key rotation
- API key management: create, rotate, revoke via admin API
- mTLS support for service-to-service communication
- RBAC policy engine: define roles per consumer, enforce per route
- Token introspection caching (configurable TTL, default 60s)

### Routing & Load Balancing
- Path-based routing with prefix matching and regex support
- Header-based routing for A/B testing and tenant isolation
- Weighted traffic splitting for canary deployments
- Health-check-aware upstream selection (active and passive checks)
- Request/response transformation (header injection, path rewriting)

### Rate Limiting
- Token bucket algorithm with configurable burst
- Per-consumer, per-route, and global rate limit tiers
- Distributed rate limiting via Redis cluster
- Customizable 429 response bodies per service

### Admin & Configuration
- Declarative YAML/JSON configuration with GitOps workflow
- Admin REST API for runtime config queries (read-only in prod)
- Configuration validation and dry-run mode
- Audit log of all configuration changes

## 5. Non-Functional Requirements

| Dimension | Requirement | Measurement |
|-----------|------------|-------------|
| Latency | < 5ms p50 added latency, < 15ms p99 | Gateway-internal span timing |
| Throughput | 50,000 requests/second sustained | Load test with k6 |
| Availability | 99.95% uptime (< 22 min/month downtime) | CloudWatch composite alarm |
| Scalability | Horizontal auto-scale 2-20 pods based on CPU/RPS | EKS HPA metrics |
| Recovery | RTO < 5 min, RPO = 0 (stateless) | DR drill quarterly |
| Security | Zero plaintext secrets; all config encrypted at rest | Vault integration audit |
| Compliance | SOC 2 Type II audit trail for all auth decisions | Centralized logging |

## 6. System Architecture

```
                    ┌─────────────────────────────────┐
                    │         AWS NLB (Layer 4)        │
                    └───────────────┬─────────────────┘
                                    │
                    ┌───────────────▼─────────────────┐
                    │     API Gateway (EKS Pods)       │
                    │  ┌──────────┐  ┌──────────────┐ │
                    │  │  Auth    │  │   Rate Limit  │ │
                    │  │  Plugin  │  │    Plugin     │ │
                    │  └────┬─────┘  └──────┬───────┘ │
                    │       │               │         │
                    │  ┌────▼───────────────▼───────┐ │
                    │  │      Router / Proxy         │ │
                    │  └────────────┬────────────────┘ │
                    └──────────────┬──────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
     ┌────────▼──────┐  ┌────────▼──────┐  ┌─────────▼──────┐
     │  Service A    │  │  Service B    │  │  Service C     │
     │  (EKS)       │  │  (Lambda)     │  │  (ECS)         │
     └──────────────┘  └──────────────┘  └────────────────┘
```

**Core Components:**
- **Gateway Runtime:** Envoy-based proxy running on EKS, extended with custom Lua/WASM filters
- **Control Plane:** Go service that compiles YAML configs into Envoy xDS resources
- **Auth Plugin:** Validates JWTs against JWKS endpoints, checks API keys in DynamoDB, terminates mTLS
- **Rate Limit Service:** Distributed rate limiting backed by ElastiCache Redis cluster
- **Config Store:** Git repository (GitOps) with DynamoDB for runtime state
- **Observability Pipeline:** OpenTelemetry Collector sidecar exporting to X-Ray, CloudWatch, and S3

## 7. Data Model

### Service Registry (DynamoDB)
| Attribute | Type | Description |
|-----------|------|-------------|
| service_id | String (PK) | Unique service identifier |
| service_name | String | Human-readable name |
| upstream_url | String | Target service URL |
| health_check_path | String | Health endpoint path |
| auth_policy | Map | Route-level auth configuration |
| rate_limit_policy | Map | Rate limit tiers |
| owner_team | String | Owning team for escalation |
| created_at | String (ISO 8601) | Registration timestamp |
| updated_at | String (ISO 8601) | Last config update |

### API Keys (DynamoDB)
| Attribute | Type | Description |
|-----------|------|-------------|
| key_hash | String (PK) | SHA-256 hash of the API key |
| consumer_id | String (GSI) | Consumer identity |
| scopes | StringSet | Authorized scopes/routes |
| rate_limit_tier | String | Assigned rate limit tier |
| expires_at | String (ISO 8601) | Expiration timestamp |
| status | String | active / revoked / expired |

### Access Log (S3 / Athena)
| Field | Type | Description |
|-------|------|-------------|
| timestamp | ISO 8601 | Request timestamp |
| trace_id | String | W3C trace ID |
| consumer_id | String | Resolved consumer identity |
| method | String | HTTP method |
| path | String | Request path |
| service_id | String | Target service |
| status_code | Integer | Response status |
| latency_ms | Float | End-to-end latency |
| rate_limited | Boolean | Whether request was throttled |

## 8. API Design

### Service Registration
```
POST /admin/v1/services
Content-Type: application/json

{
  "service_name": "risk-scoring",
  "upstream_url": "http://risk-scoring.internal:8080",
  "health_check_path": "/healthz",
  "auth_policy": {
    "/api/v1/scores": { "mode": "jwt", "required_scopes": ["risk:read"] },
    "/api/v1/admin/*": { "mode": "jwt", "required_roles": ["admin"] },
    "/health": { "mode": "none" }
  },
  "rate_limit_policy": {
    "default": { "requests_per_second": 100, "burst": 150 },
    "premium": { "requests_per_second": 500, "burst": 750 }
  }
}
```

### API Key Management
```
POST   /admin/v1/keys              # Create key
GET    /admin/v1/keys/:consumer_id  # List keys for consumer
DELETE /admin/v1/keys/:key_id       # Revoke key
POST   /admin/v1/keys/:key_id/rotate  # Rotate key
```

### Traffic Control
```
POST /admin/v1/services/:id/canary
{
  "target_version": "v2.1.0",
  "target_upstream": "http://risk-scoring-v2.internal:8080",
  "weight_percent": 5,
  "error_threshold_percent": 2.0,
  "auto_rollback": true
}
```

### Error Response Format
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded for consumer risk-dashboard",
    "retry_after_seconds": 12,
    "trace_id": "00-abcdef1234567890-abcdef12-01"
  }
}
```

## 9. Security

**Authentication:**
- All admin API endpoints require mTLS + JWT with `gateway:admin` scope
- JWT signing keys rotated automatically via AWS Secrets Manager
- API keys stored as SHA-256 hashes; plaintext never persisted

**Network:**
- Gateway pods in private subnets; NLB in public subnet with WAF
- Service-to-gateway traffic over mTLS within the VPC
- No direct internet access to upstream services

**Data Protection:**
- Access logs encrypted at rest (S3 SSE-KMS) and in transit (TLS 1.3)
- PII fields (client IP, user ID) masked in non-production environments
- DynamoDB encryption at rest with customer-managed KMS key

**Compliance:**
- All auth decisions logged with consumer identity, decision outcome, and policy applied
- Configuration changes require PR approval and produce audit trail
- Quarterly access review of admin credentials

## 10. Testing Strategy

| Layer | Tool | Coverage Target |
|-------|------|----------------|
| Unit | Go test (control plane), pytest (config validator) | 90% line coverage |
| Integration | Testcontainers (Envoy + Redis + DynamoDB Local) | All auth modes, rate limit scenarios |
| Contract | Pact | Gateway-to-upstream API contracts |
| Load | k6 | Sustained 50K RPS for 30 minutes |
| Chaos | AWS FIS | Redis failure, upstream 5xx, pod eviction |
| Security | OWASP ZAP + custom auth bypass suite | All auth modes |
| E2E | Newman (Postman collections) | Golden path for onboarding, auth, rate limit |

**CI Pipeline:**
1. Unit + lint on every PR
2. Integration tests on merge to main
3. Load test nightly on staging
4. Security scan weekly
5. Chaos tests monthly

## 11. Launch Plan

| Phase | Duration | Scope | Success Gate |
|-------|----------|-------|-------------|
| Alpha | 2 weeks | Gateway + JWT auth + 1 service (risk-scoring) | < 5ms p50 latency, zero auth bypass |
| Beta | 3 weeks | Add rate limiting, 3 more services, canary routing | 10K RPS sustained, < 0.01% error rate |
| GA | 2 weeks | All 15 priority services migrated, admin dashboard | 50K RPS sustained, runbook tested |
| Scale | Ongoing | Remaining services self-service onboard | < 30 min onboarding time |

**Rollback Plan:**
- Each service retains its existing ingress during migration
- Feature flag to bypass gateway per service
- DNS-level failover: swap CNAME back to direct ALB within 2 minutes

## 12. Success Metrics

**North Star Metric:** Percentage of internal API traffic routed through the gateway

| Metric | Target | Timeline | Measurement |
|--------|--------|----------|-------------|
| Services onboarded | 15 (priority tier) | GA + 2 weeks | Service registry count |
| P50 added latency | < 5ms | Ongoing | Gateway span metrics |
| Auth incidents | 0 (gateway-routed services) | Post-GA | Security incident tracker |
| Onboarding time | < 30 minutes | Post-GA | Time from PR to first routed request |
| Developer satisfaction (NPS) | > 40 | GA + 1 month | Survey |
| API traffic through gateway | > 80% | GA + 3 months | Traffic counters |
| Rate limit effectiveness | < 0.1% false positives | Ongoing | Rate limit decision logs |

## 13. Open Questions

| Question | Context | Owner | Deadline |
|----------|---------|-------|----------|
| Envoy vs Kong vs custom proxy | Envoy preferred for WASM extensibility, but Kong has richer plugin ecosystem | Platform Arch | Week 1 |
| Multi-region strategy | Do we need active-active gateway in eu-west-1 for GDPR-resident services? | Compliance + Platform | Week 2 |
| API key migration path | 40+ existing API keys across services; bulk migration or gradual? | Platform Eng | Week 2 |
| Cost model | Charge-back per service or shared platform cost? | Engineering Leadership | Week 3 |
| GraphQL support | 2 services use GraphQL; do we support query-level auth in Phase 1? | Platform Arch | Week 2 |
| Secrets Manager vs Vault | Team prefers Vault but org standard is Secrets Manager | Security + Platform | Week 1 |

---

*This PRD was generated using the prd-generator skill from the how-i-pm-with-ai framework.*
