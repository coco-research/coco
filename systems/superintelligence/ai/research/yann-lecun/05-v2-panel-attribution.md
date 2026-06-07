# Yann LeCun — Marvin Memory v2 Panel Attribution

Source artifacts:
- `/Users/Rijul_Kalra/Marvin/docs/architecture/marvin-memory-master-phased-plan.html`
- `/Users/Rijul_Kalra/Marvin/docs/architecture/marvin-memory-v3-merged-spec.html`

In the Marvin Memory v2 → v3 reconciliation panel synthesis (2026-05-26 / 2026-05-27), LeCun participated as a **Cell A** persona alongside Karpathy, Wei, Dao. Within Cell A, he is specifically credited with two micro-phase items: **P5** (open-vocabulary entity extension) and **P6** (contradiction detection — opinion-network seam).

## Attribution 1 — Open-vocabulary entity extension path (P5)

**Source:** `marvin-memory-master-phased-plan.html`, line 753–757, v3.10 micro-phase.

**Direct excerpt from master plan:**
> "Cell A LeCun P5. 10 hand-crafted classes won't capture 50K-user diversity. Splink Stage-B surfaces patterns outside taxonomy. Ontology curator approves new class via canonical_identity_admin_audit workflow."

**Cross-reference:** `marvin-memory-v3-merged-spec.html`, line 536, v2.3 deep-dive:
> "Open-vocabulary entity extension path (Cell A LeCun) — Splink Stage-B surfaces patterns not in 10-class taxonomy, ontology curator approves new classes via canonical_identity_admin_audit workflow."

**Why this is a LeCun stance:**
LeCun's deep work on representation learning (CNNs, then JEPA) is precisely about **learning representations from data rather than enumerating them by hand**. A 10-class hand-crafted entity taxonomy is exactly the kind of hand-engineering he has railed against since Bell Labs (Optimal Brain Damage, end-to-end gradient learning). The P5 stance — let Splink Stage-B *surface* patterns outside the closed taxonomy, with a human curator promoting them — is the open-vocabulary analog of self-supervised representation learning: don't constrain the space; let observation push the ontology.

**Co-signers in panel:** N/A explicit; the v2.3 phase is owned by Cell A but P5 is specifically Lecun-attributed.

## Attribution 2 — Contradiction detection / opinion-network seam (P6)

**Source:** `marvin-memory-master-phased-plan.html`, line 598, Open questions list:
> "Contradiction detection ownership decision — opinion-network seam (Cell A LeCun P6)"

**Why this is a LeCun stance:**
LeCun's energy-based model framework (EBM, 2006 tutorial) is fundamentally about scoring **consistency** of joint configurations of variables — including contradictions in a knowledge graph. The "opinion-network seam" framing — where contradictory claims from different sources need to be reconciled, not silently overwritten — aligns with his consistent argument that **planning systems require explicit world models that can hold multiple hypotheses**. Naive autoregressive systems lose this; energy-based / JEPA-style systems retain it.

**Status in v3:** Open question (not resolved in v2.3). LeCun's position is essentially: contradictions are signals, not bugs. Surface them; don't paper over them.

## General Cell A Posture (LeCun aligned)

The Cell A vote also influenced several broader items in the v2.3 reconciliation:
- **AAR Distillation Worker** — "Cell A + B unanimous biggest gap" (line 259/688). LeCun aligned with the "Marvin gets smarter the more I use it" framing as table stakes — consistent with his world-models position that memory + adaptation, not pure scale, is the missing piece.
- **SR-3 verification gate** (Cell A, B, D, E co-signed). LeCun is on record (see public stances) that systems must be verified empirically, not just argued from architecture diagrams.

## v3 Spec Acceptance

Per `marvin-memory-v3-merged-spec.html` line 463–466, the v2.3 deep-dive includes the open-vocabulary entity extension as a confirmed deliverable, locking LeCun's P5 stance into the v3 plan.

## Suggested phrasing for convene synthesis

When `/superintelligenceTeam-convene` cites LeCun on Marvin, prefer:

1. **P5 — Open-vocabulary entity extension.** "Ten hand-crafted classes won't survive 50K-user diversity. Let Splink Stage-B surface new patterns; gate promotion behind a human curator." (Cell A, v2.3)
2. **P6 — Contradiction detection at the opinion-network seam.** "Conflicting claims are data, not noise. Hold them in the graph; don't overwrite. Resolution is a separate decision layer." (Cell A, v2.3, open question)

Both should be cited with explicit attribution to LeCun, not collapsed into a generic "Cell A position." This matters because Karpathy (also Cell A) drove different reversals (hot-path 3-tier default, NER triage gate) — the cell letter is shared but the lead-driver roles are distinct.
