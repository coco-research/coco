# Jason Wei — Marvin Memory v2 Panel Attribution (2026-05-26 / 2026-05-27)

Jason Wei participated as a **Cell A (AI / research)** panelist in the 20-persona review of the Marvin Memory v1 → v2 architecture and subsequent v2 → v3 reconciliation. His role was **specialist / co-signer**, not lead-driver. He shows up in the panel artifacts on three specific stances.

## Source artifacts

- `/Users/Rijul_Kalra/Marvin/docs/architecture/marvin-memory-master-phased-plan.html`
- `/Users/Rijul_Kalra/Marvin/docs/architecture/marvin-memory-v3-merged-spec.html`
- `/Users/Rijul_Kalra/Marvin/docs/architecture/marvin-memory-old-vs-new.html`

## Stance 1 — L5 entity-extraction NER triage gate (co-signed Karpathy)

Master phased plan, v1.6 micro-phase reasoning section, explicit attribution:

> "Cell A Wei + Cell B Chalef. L5 entity-extraction LLM is expensive (4-6 LLM calls per chunk per GraphRAG benchmarks). Gate it on cheap NER on query side. Costs ~$0.0001 per check."

Karpathy's `andrej-karpathy.md` v2_panel_attribution credits this stance as "Karpathy + Wei + Chalef on NER triage gate." Wei is a co-signer / validator on Karpathy's lead-driver call.

**Decision text (D4):** "Triage-gated only. Trigger conditions: NER density > N/100 tokens OR doc tagged person/decision/event. NOT every doc. GraphRAG indexing 4-6 LLM calls/chunk = 20-100× embedding cost without triage."

**Source:** `marvin-memory-master-phased-plan.html`, v1.6 micro-phase reasoning, and the panel synthesis section that lists Wei as co-signer.

## Stance 2 — Don't single-vendor on the recall layer; keep MemoryProvider Protocol pluggable

Master phased plan, v2 architecture justification section, "kept from v2" list:

> "Hindsight as 1-of-N behind MemoryProvider Protocol (Cell A Wei: don't single-vendor)."

This is Wei's load-bearing independent stance in the panel. He argues that wrapping Hindsight (or any single recall provider) behind a Protocol with at least one alternative implementation is the right hedge against vendor lock-in and against a single research bet collapsing the system. Reflects his broader "diversify the bet at the substrate layer" instinct.

**Source:** `marvin-memory-master-phased-plan.html`, Section "what we kept from v2," bullet 4.

## Stance 3 — SR-3 load-test must use power-law-correct synthetic graph at scale

v3.0 gate criteria, list of artifacts required before shipping multi-hop graph queries:

> "SR-3 load-test report with hub-and-spoke power-law-correct synthetic graph (Cell A Wei)."

Wei flagged that random-graph synthetic load tests will not stress the actual production scaling behaviour because real partner/engagement networks follow power laws (high-degree hubs, long tails). The load test must reproduce that degree distribution or it under-tests the path that will actually break at 50M+ edges.

**Source:** `marvin-memory-master-phased-plan.html`, v3.0 gate-criteria list ("SR-3 load-test report").

## Stance 4 — CoT-retrieval token budget interplay (P14)

v3.0 open issues list:

> "CoT-retrieval interplay token budget (Cell A Wei P14)."

Wei is the originator of Chain-of-Thought as a technique. He flagged at v3.0 that the system has not specified how CoT reasoning tokens compete with retrieval context tokens inside the model's context window. If retrieval pumps 8K tokens of context and CoT then consumes 4K tokens of reasoning, the model still has to fit into the context budget — and the system needs an explicit token budget for each.

This is the kind of issue only Wei would flag — it sits at the intersection of CoT (his work) and retrieval (the system being designed). Classic "specialist co-signer" pattern.

**Source:** `marvin-memory-master-phased-plan.html`, v3.0 open issues, P14.

## Wei's cell role

**Cell A (AI / research), cell_role = specialist.**

He is not a lead-driver (Karpathy and LeCun are the Cell A drivers in v2). He is a credited co-signer on the L5 NER gate, an independent voice on MemoryProvider Protocol pluggability, and the specific specialist who flagged power-law load testing and CoT-token-budget concerns. The `specialist` cell_role fits him cleanly.

## Pairings in the panel

- **Tight pair with Karpathy:** co-signed the NER triage gate, both Cell A on the hot-path reversal. In `andrej-karpathy.md` Wei is listed as a co-signer on Stance 3.
- **Working pair with Daniel Chalef:** Cell B persona, also co-signed the NER triage gate.
- **Productive conflict with LeCun:** same cell, opposing schools on emergence (Wei believes it; LeCun is skeptical). LeCun drove the open-vocab entity extension; Wei did not co-sign that one publicly in the panel.

## Anchor quotes from the panel

Direct attribution lines from the source artifacts:

- "Cell A Wei + Cell B Chalef. L5 entity-extraction LLM is expensive… Gate it on cheap NER on query side." (`marvin-memory-master-phased-plan.html`, v1.6)
- "Hindsight as 1-of-N behind MemoryProvider Protocol (Cell A Wei: don't single-vendor)." (`marvin-memory-master-phased-plan.html`, kept-from-v2 list)
- "SR-3 load-test report with hub-and-spoke power-law-correct synthetic graph (Cell A Wei)." (`marvin-memory-master-phased-plan.html`, v3.0 gate criteria)
- "CoT-retrieval interplay token budget (Cell A Wei P14)." (`marvin-memory-master-phased-plan.html`, v3.0 open issues)

When `/superintelligenceTeam-convene` cites Wei in future sessions, prefer these stances first, then fall back to his public stances from jasonwei.net essays and 2025 talks.
