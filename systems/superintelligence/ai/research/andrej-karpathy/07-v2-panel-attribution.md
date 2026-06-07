# Karpathy — Marvin Memory v2 Panel Attribution (2026-05-26 / 2026-05-27)

Karpathy participated as a Cell A (AI / research) panelist in the 20-persona review of the Marvin Memory v1 → v2 architecture and subsequent v2 → v3 reconciliation. The following stances are attributed to him directly in the source artifacts. They anchor his persona to actual panel material rather than Claude's inference.

## Source artifacts

- `/Users/user/Marvin/docs/architecture/marvin-memory-master-phased-plan.html`
- `/Users/user/Marvin/docs/architecture/marvin-memory-v3-merged-spec.html`
- `/Users/user/Marvin/docs/architecture/marvin-memory-old-vs-new.html`
- `/Users/user/Marvin/docs/architecture/marvin-memory-why-we-changed.html`
- `/Users/user/Marvin/docs/architecture/SESSION-2026-05-26.md`

## Karpathy's panel stances

### Stance 1 — Hot path default is L4 floor + L1 drill-up + L5 NER-gated, NOT full 5-layer fan-out

Decision **D2** (Marvin v2 → v3): "Schema stores all 5 layers (L0-L4 + L5 cross-cut) always at ingest. Hot path default = L4 floor + L1 drill-up + L5 NER-gated. L2/L3 opt-in or re-rank only. L4 = floor (hard error if fails); all others = silent fallback. Each layer in separate partition with 50ms timeout."

**Panel attribution:** "Karpathy + Cockcroft + Vogels"
**Source:** `marvin-memory-old-vs-new.html`, v2.1 reversals table.

### Stance 2 — "Make the right thing the default"

Master phased plan, Reversal 2 reasoning: "Karpathy's 'make the right thing the default' — default = floor + drill-up."

**Panel attribution:** Karpathy + Cockcroft (Cells A + C) led Reversal 2; tech lead co-signed.
**Source:** `marvin-memory-master-phased-plan.html`, Section 2 Reasoning, Reversal 2.

### Stance 3 — L5 entity extraction must be triage-gated, not run on every doc

Decision **D4**: "Triage-gated only. Trigger conditions: NER density > N/100 tokens OR doc tagged person/decision/event. NOT every doc. GraphRAG indexing 4-6 LLM calls/chunk = 20-100× embedding cost without triage."

**Panel attribution:** Cell A Wei + Karpathy + Cell B Chalef on the NER gate at query side.
**Source:** `marvin-memory-master-phased-plan.html`, v1.6 micro-phase reasoning.

### Stance 4 — Tail-latency amplification is the killer; 50ms per-provider deadline

The "why-we-changed" slide on hot path cites Karpathy's framing: "make the right thing the default. Default = fast. Want depth? Opt in."

**Source:** `marvin-memory-why-we-changed.html`, Slide 4 "Hot path = top-10 only" — why-this-is-best-option section.

### Stance 5 — Open-vocabulary entity extension (with LeCun)

v2.3 ships open-vocab entity extension path. Decision attributed to "Cell A LeCun" but Karpathy is on the same cell and co-signs the position. (LeCun lead-driver, Karpathy validator on this one.)

**Source:** `marvin-memory-v3-merged-spec.html`, v2.3 deep dive.

## Karpathy's cell role

**Cell A (AI / research), cell_role = lead-driver.**

He drove the hot-path reversal alongside Cockcroft (Cell C). When pairs_well_with is computed, Cockcroft and Wei are his strongest pairs. Productive conflict with LeCun (different philosophical priors on world models vs autoregressive LLMs) — same cell, opposing schools.

## Anchor quotes from the v2 panel

The panel artifacts paraphrase Karpathy's L4-floor stance from his "make the right thing the default" frame (Software 3.0 talk, July 2025), not from the panel itself. So in `andrej-karpathy.md` the "Anchor quotes from the v2 panel" section will reference the master plan's attribution rather than a verbatim transcript line.
