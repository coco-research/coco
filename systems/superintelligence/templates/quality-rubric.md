# Quality Rubric for SI Persona Semantic Review

Used by `llm_judge.py` (Phase 4 Tier 2). Each dimension scored 0-100.

## Dimensions

### 1. Voice Fidelity (weight: 25)
Does the persona's signature_moves, public_stances, and narrative body authentically capture
how this person actually speaks, thinks, and argues? Are the quotes and paraphrases consistent
with their known public communication style?

**Score 90-100:** Signature moves are instantly recognizable; stances use the person's actual
framing and vocabulary; narrative body reads like their writing/speaking style.
**Score 70-89:** Generally captures the person's perspective but some moves feel generic or
could apply to multiple people in the same domain.
**Score 50-69:** Mix of accurate and generic content; voice is inconsistent across sections.
**Score 0-49:** Does not sound like the person; reads like a Wikipedia summary.

### 2. Factual Accuracy (weight: 30)
Are affiliations, publications, career history, and claims verifiable against public records?
Are there any hallucinated URLs, invented publications, or incorrect dates?

**Score 90-100:** All facts verified; every URL resolves to relevant content; dates correct.
**Score 70-89:** Core facts accurate; minor date discrepancies or one broken URL.
**Score 50-69:** Some affiliations outdated or unverifiable; 2+ broken URLs.
**Score 0-49:** Significant factual errors; hallucinated sources; wrong career history.

### 3. Schema Compliance (weight: 15)
Does the markdown body follow the expected structure? Are all required frontmatter fields
present and correctly typed? Is the YAML valid?

**Score 90-100:** All required fields present with correct types; YAML parses cleanly.
**Score 70-89:** Minor type mismatches or optional fields missing.
**Score 50-69:** Required fields missing or incorrectly typed.
**Score 0-49:** YAML parse failure or major structural issues.

### 4. Recency & Relevance (weight: 15)
Are recent_signal_12mo entries actually from the last 12 months and materially relevant?
Do they reflect genuine public activity rather than filler?

**Score 90-100:** 3+ signals post-cutoff; each is a substantive talk/paper/interview.
**Score 70-89:** Signals present but some are stale or low-relevance.
**Score 50-69:** Fewer than 3 signals or mostly stale.
**Score 0-49:** No signals or all pre-date cutoff by >6 months.

### 5. Cross-team Coherence (weight: 15)
If cross-listed, is the persona's role consistent across teams? Does the archetype align
with actual domain contributions?

**Score 90-100:** Perfectly consistent across all team listings; archetype precise.
**Score 70-89:** Minor inconsistencies in cell role or description.
**Score 50-69:** Conflicting roles across teams; archetype too broad.
**Score 0-49:** Fundamentally misassigned to wrong team/cell.

## Verdict Rules
- weighted_total >= 80 → PASS
- weighted_total >= 60 → NEEDS-REVISION
- weighted_total < 60 → FAIL
