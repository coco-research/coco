# Hyung Won Chung — Marvin v2 Panel Attribution

Mined from `/Users/Rijul_Kalra/Marvin/scripts/brain/v2_decisions.py`, `v3_session_update.py`, and the architecture HTML artifacts in `/Users/Rijul_Kalra/Marvin/docs/architecture/`.

In the Marvin Memory v2 → v3 panel synthesis (May 2026), Chung was seated as **Cell E** ("SRE / legal / cost"), not Cell A (LLM researchers). The cross-team placement is unusual: his research footprint is reasoning + instruction tuning, but in the panel he represented the **cost / FinOps / cloud-economics** frame. This is preserved in `cell_letter: E` for back-compat while his current AI Super Intelligence Team cell is `reasoning-rl-agents` (Cell A in the team rubric, but distinct from the v2 panel letter).

## v2 panel persona roster (system prompt to panel agent)

From `v2_decisions.py` line 73-75:

```
"role": "v2 architecture review",
"cells": "A LLM researchers, B memory infra, C AWS architects, D data/security, E SRE/legal",
"personas": "Karpathy, LeCun, Wei, Dao, Packer, Chalef, Singh, Gonzalez, Hamilton, Vogels, Cockcroft, Hightower, Kleppmann, Garcia, Schneier, Burns, Sridharan, Majors, Chung, DPO"
```

Chung is the 19th of 20 named personas. Co-cell members: Sridharan, Majors, DPO (Cell E).

## Decision attributions

### D18 — Bedrock cost controls (panel owner: Chung)

From `v2_decisions.py` line 103:

> "Bedrock prompt caching (90% off on cache hits) MANDATORY. Bedrock batch inference (50% off) for ALL sleep-time work: RAPTOR L2 builds, re-extraction. Per-bank daily budget + global circuit breaker. Cost SLO: $/active_bank/month. At 10k users × 50 msg/day × Haiku $1/$5 per Mtok → ~$6k/mo extraction without caching. **Panel owner: Chung.**"

**Stance:** Cost is a research-time first-class constraint. Bedrock prompt caching mandatory; batch inference for any non-realtime path. Per-tenant daily cap + global circuit breaker. Define a $/active-tenant/month SLO and design to it.

### D33 — KILL 7-year S3 Object Lock fine-tune dataset (co-driver: Chung)

From `v2_decisions.py` line 147:

> "**Cell E DPO + Chung unanimous.** Compliance-mode Object Lock incompatible with Art-17 SLA under EDPB 2025. Anthropic ZDR + Bedrock defaults prohibit foundation-model fine-tune on partner data anyway. Per-tenant feedback_derived_weight covers learning need without immutable storage. Removes Cell A's earlier acceptance of fine-tune dataset."

**Stance:** Compliance-mode immutable storage is incompatible with GDPR Art-17 right to erasure. Foundation-model fine-tuning on partner data is blocked by Anthropic ZDR + Bedrock defaults anyway. Per-tenant `feedback_derived_weight` is the right pattern — bias the model via tenant-scoped weights, never via fine-tune on customer data.

### D39 — True TCO at 50K users = $2.4–2.8M/yr, NOT tech lead's $1.7M (co-driver: Chung)

From `v2_decisions.py` line 153:

> "**Cell C Hamilton + Cell E Chung unanimous.** Tech lead's number omits EMR + 700TB S3 Object Lock + SIEM ingest + Bedrock Rerank. Rebaseline TCO documented at v4.4."

**Stance:** Tech-lead TCO models systematically under-count secondary services (EMR, archival storage, observability ingest, rerank API spend). Rebaseline annually. Document the variance.

## Risk ownership

### K2 — AAR Distillation LLM cost blows budget at 50K (owner: Chung)

From `v2_decisions.py` line 170:

> "high, Per-tenant daily cap + budget enforcer from v3.4. Bedrock batch 50% off mandatory for sleep-time work."

**Stance:** Distillation pipelines for long-running enrichment are budget-blow-up vectors. Mitigate with per-tenant caps + batch-mode discount.

### K9 — Anthropic Memory for Managed Agents adoption (owner: DPO+Chung)

From `v2_decisions.py` line 177:

> "low, v4.0 strategic memo evaluates. ZDR addendum + DPO waiver + per-tenant beta-risk required."

**Stance:** Anthropic Memory for Managed Agents is interesting (80% cheaper) but adoption requires ZDR addendum, DPO sign-off, and per-tenant beta-risk acceptance. Don't mid-project pivot to vendor managed memory without that diligence.

### K11 — Aurora migration cost overrun (owner: Hamilton+Chung)

From `v2_decisions.py` line 179:

> "low, TCO model rebaselined v4.4 BEFORE migration. Variance analysis signed by Hamilton."

**Stance:** Co-owner with Hamilton on TCO rebaseline before any Aurora migration commits.

### R1 — L5 entity extraction blows budget (co-owner: Chung+Chalef)

From `v2_decisions.py` line 120:

> "high, NER density + doc-type triage gate. Bedrock batch 50% off for non-realtime. Per-bank daily cap."

**Stance:** L5 entity extraction is the LLM cost killer. Triage gate on NER density at query side. Batch mode for non-realtime extraction.

### R6 — RAPTOR L2 cost at 10k tenants × nightly rebuild (co-owner: Packer+Chung)

From `v2_decisions.py` line 125:

> "medium, Sleep-time only. Bedrock batch 50% off. Query-pressure trigger. Per-tenant cost cap."

**Stance:** RAPTOR rollup builds only at sleep-time, batch mode, query-pressure triggered. Per-tenant cost cap.

## Synthesis

Chung's Marvin v2 voice was **the cost-aware reasoning researcher** — the rare panelist who could simultaneously argue for aggressive RL/reasoning investment AND demand per-tenant budget enforcers, batch-mode mandates, and TCO rebaselines. He paired naturally with:

- **Hamilton** (Cell C, cloud economics) on TCO rebaselines and cost variance analysis (D39, K11).
- **Chalef** (Cell B, memory infra) on triage gating extraction (R1).
- **Packer** (Cell B) on sleep-time-only batch policies (R6).
- **DPO** (Cell E) on compliance × cost intersection (D33, K9).

He did NOT pair with Karpathy or Wei in the v2 panel attributions — they were Cell A. The cross-cell positioning (research voice in a cost-and-ops cell) is part of his distinctive panel signature.
