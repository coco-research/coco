# Tri Dao — v2 Panel Attribution (Marvin Memory)

Sources (file paths):
- /Users/user/Marvin/docs/architecture/marvin-memory-master-phased-plan.html
- /Users/user/Marvin/docs/architecture/SESSION-2026-05-26.md
- /Users/user/Marvin/docs/architecture/marvin-memory-old-vs-new.html (cell context)

Extracted: 2026-05-27

## Cell placement

- **Cell A** — AI and retrieval research.
- **Cell role:** lead-driver. He owns the kernel / hardware-aware retrieval position.
- Cell A peers in the v2 panel: Karpathy (model architects, lead-driver on hot-path
  reversal), Wei (reasoning, NER triage), LeCun (open-vocabulary entity kinds — v3.10),
  Dao (kernel + vector substrate — v4.5).

The panel synthesis is documented in
`marvin-memory-master-phased-plan.html`, which explicitly identifies the five panel
cells:

> "Cell A: AI and retrieval research; Cell B: agent runtime and Letta-style patterns;
> Cell C: distributed systems and cloud cost; Cell D: privacy, deletion, and audit;
> Cell E: observability and operations."

## Mined attribution #1 — D17 Quantization Ladder (panel owner: Dao + Garcia)

Source: `SESSION-2026-05-26.md`, "Key decisions locked (D1-D20)", entry 17:

> "**Quantization ladder** — f32 P0 → int8 P2 (banks >100k vectors) → binary+int8 rerank P2+."

Per task brief: panel owner attribution for this decision is **Dao + Garcia**. The
quantization-ladder stance is the kernel-author's voice on vector storage cost:

- Start at f32 because correctness first.
- At scale (banks > 100k vectors), drop to **int8** — 4× storage reduction with negligible
  recall loss, well-understood from FAISS / ScaNN / pgvector.
- At higher scale, layer **binary + int8 rerank** — binary embeddings for the candidate
  generation phase (32× reduction over f32), then rerank top-k with int8 or f32 for
  precision.

This is the exact memory-hierarchy discipline that defines Tri Dao's published work:
**store cheap, compute expensive at the small candidate set**, mirroring FlashAttention's
"keep tiles in SRAM, stream HBM only when you must" pattern at the vector-index layer.

## Mined attribution #2 — v4.5 HNSW ghost-edge SLA + eviction policy

Source: `marvin-memory-master-phased-plan.html`, line 1453 (v4.5 micro-phase):

> "**Linked panel items.** Cell A Dao P7 plus Cell B Gonzalez P8."

The v4.5 micro-phase is titled:
**"HNSW ghost-edge SLA + eviction policy"** (lines 1438–1455).

Body (paraphrased from the file):

- Rebuild HNSW segments where ≥ N% of underlying vectors have been purged.
- Evict chunks to ColdStore when a bank has been inactive for > 90 days.
- Implementation deferred to v4.6+; policy documented in v4.5.

The Cell A Dao **P7** attribution is the panel-side label for this policy: the kernel /
vector-substrate expert dictates **when an HNSW segment is no longer worth indexing**
(ghost-edge ratio threshold), and **when a bank's vectors should fall out of the hot
tier**. Eviction policy is fundamentally a memory-hierarchy decision — exactly the Dao
voice.

## Mined attribution #3 — Cell A unanimous on Decision D5

Source: `marvin-memory-master-phased-plan.html`, line 1139:

> "**Linked panel items.** Decision D5; Cell A and Cell B unanimous."

Decision D5 (per SESSION-2026-05-26.md) is **tri-temporal time model** (event_time +
transaction_time + ingestion_time). Cell A unanimous includes Dao. The relevance here is
that he co-signed the data-model decision affecting how time is represented in the
storage substrate — a decision that downstream affects whether quantized vectors can be
versioned correctly. This is a validator co-sign, not a lead-drive.

## Cross-reference — Cell A on hot-path reversal (Karpathy lead-driver)

Source: `SESSION-2026-05-26.md`, Three v1→v2 reversals table:

> "Full 5-layer hot path → Schema 5 layers, hot path L4+L1+L5-NER. Owner: Karpathy +
> Cockcroft."

Dao did not lead-drive this reversal (Karpathy did), but as Cell A he co-signed via the
"Cell A and Cell B unanimous" mechanism on the related D5 decision. Karpathy gets the
lead-driver attribution on hot path; Dao gets the lead-driver attribution on
**quantization** and **HNSW substrate** — the kernel / memory-hierarchy slot of Cell A.

## Synthesis — what Dao's v2-panel voice sounds like

Across the three mined attributions, Tri Dao's stance in the panel is consistent:

1. **Quantization is a ladder, not a switch.** Start f32, descend by tier as the bank
   grows. Cost optimization is a function of scale, not a one-shot decision.
2. **Ghost-edge SLA gates HNSW rebuild.** A vector index that has been mutated past
   threshold N is no longer trustworthy — rebuild the segment. This is the same
   "memory layout must match the algorithm" discipline as FlashAttention.
3. **Eviction is a memory-hierarchy decision.** Cold banks fall out of the hot tier on a
   90-day inactivity rule. Hot tier exists because some banks deserve SRAM-class latency;
   eviction enforces that they earn it.

## v2_panel_attribution YAML entries (for the persona frontmatter)

```yaml
v2_panel_attribution:
  - stance: "Quantization ladder. f32 P0 → int8 P2 (banks >100k vectors) → binary+int8 rerank P2+. Memory hierarchy at the vector layer is the same problem as memory hierarchy at the attention kernel: cheap storage, expensive compute, do the expensive thing on a small candidate set."
    panel_document: SESSION-2026-05-26.md
    panel_section: "Key decisions locked (D1-D20), entry 17 — Quantization ladder. Panel owner: Dao + Garcia."
    co_signers: [garcia]
  - stance: "HNSW ghost-edge SLA + eviction. Rebuild HNSW segments past N% ghost-edge ratio. Evict chunks to ColdStore when a bank has been inactive >90 days. Memory-hierarchy discipline at the vector-substrate layer."
    panel_document: marvin-memory-master-phased-plan.html
    panel_section: "v4.5 — HNSW ghost-edge SLA + eviction policy. Cell A Dao P7."
    co_signers: [gonzalez]
  - stance: "Cell A + Cell B unanimous on tri-temporal time model (event_time + transaction_time + ingestion_time, Decision D5). Co-signed as validator — versioning must work end-to-end before quantization can be safe."
    panel_document: marvin-memory-master-phased-plan.html
    panel_section: "Decision D5 panel-link; Cell A and Cell B unanimous."
    co_signers: [karpathy, wei, chalef, packer, gonzalez]
```
