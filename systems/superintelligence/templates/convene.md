# Convene Template — Multi-Persona Session

This file is the source-of-truth structure that `/superintelligenceTeam-convene <topic>` produces. It defines how 5–20 personas are coordinated into a single synthesized verdict on a high-stakes prompt, with full per-persona attribution.

A convene session has three phases: **inputs**, **per-cell stances**, and **synthesis**. Each persona's voice must remain identifiable end-to-end — never collapse multiple personas into "the panel said."

---

## Frontmatter (machine-readable)

```yaml
---
convene_id: 2026-05-27-marvin-memory-v3-synthesis   # ISO date + topic-slug
topic: "Marvin Memory v2 → v3 — substrate, hot path, erasure"
caller: rijul-kalra
date: 2026-05-27
mode: full-panel                                    # full-panel (20) | cell (4) | duo (2) | solo (1)
cells_active: [A, B, C, D, E]                       # which cells participated
personas_active:                                    # explicit roster for the session
  - andrej-karpathy
  - yann-lecun
  - jason-wei
  - tri-dao
  # ...
artifacts_reviewed:                                 # what the panel was asked to review
  - path: /Users/user/Marvin/docs/architecture/marvin-memory-old-vs-new.html
    role: source
  - path: /Users/user/Marvin/docs/architecture/partner-profile-memory-handoff.html
    role: counterproposal
verdict_format: reversals-fixes-pending             # reversals-fixes-pending | take-leave | go-no-go | decision-matrix
status: ratified                                    # draft | ratified | superseded
supersedes: []                                      # IDs of earlier convene sessions this overrides
---
```

---

## Section 1 — Inputs

State the prompt verbatim. Quote the user's actual ask, do not paraphrase. List all referenced artifacts with absolute paths. Note any prior convene sessions this builds on.

```markdown
## Prompt

> {verbatim user prompt}

## Artifacts reviewed

- `{absolute path}` — {one-line role}

## Prior convene sessions

- `{convene_id}` ({date}) — {one-line outcome}, supersedes/superseded-by status
```

---

## Section 2 — Per-cell stances

One subsection per active cell. Inside each cell, attribute every claim to a named persona. Cite the persona's `public_stances` or `v2_panel_attribution` entries from their persona file. Do NOT invent stances.

Each cell subsection follows this structure:

```markdown
### Cell {X} — {cell name}

**Members participating:** {persona-slug}, {persona-slug}, {persona-slug}, {persona-slug}.

**Cell consensus:** one-paragraph summary of where this cell lands. Mark UNANIMOUS or SPLIT explicitly.

**Per-persona positions:**

- **{Real Name}** ({cell_role}): {one-sentence stance}. Backed by {persona-file-stance-reference}. {evidence URL or panel artifact}.
- **{Real Name}** ({cell_role}): ...

**Cell-level dissent:** if any persona dissents from the cell consensus, note it explicitly. Convene MUST surface dissent rather than smooth it over.
```

---

## Section 3 — Cross-cell disagreement

A short section listing the points where cells disagree. Every disagreement names BOTH cells and a representative persona on each side, with evidence.

```markdown
## Cross-cell disagreement

1. **{Topic}** — Cell {X} ({lead-persona}) says {position}, citing {evidence}. Cell {Y} ({lead-persona}) says {opposing position}, citing {evidence}. Resolution: {resolved by | unresolved | needs gate test}.
```

---

## Section 4 — Synthesis verdict

The final verdict, structured by `verdict_format` from the frontmatter. Every line of the verdict MUST cite which persona or cell drove it.

For `reversals-fixes-pending` format (the format used by the Marvin v2→v3 synthesis):

```markdown
## Synthesis verdict — reversals/fixes/pending

### Reversals (v_prior said X; v_new says Y)
1. **{Topic}** — Was: {prior position}. Now: {new position}.
   - **Driven by:** {lead-driver persona-slug}
   - **Validated by:** {validator persona-slug(s)}
   - **Why:** {1–2 sentences with evidence}
   - **Source artifact:** {path or URL}

### Fixes (bugs / gaps closed without reversal)
1. **F{n}: {Title}** — {one-paragraph problem statement}.
   - **Surfaced by:** {persona-slug}
   - **Fix:** {what changes}
   - **Cell:** {X}

### Pending (decisions deferred to a later gate)
1. **P{n}: {Topic}** — {what needs to land before this decides}.
   - **Gate:** {trigger condition}
   - **Owners:** {persona-slug(s) responsible for the gate}
```

For `take-leave` format:

```markdown
## Synthesis verdict — take/leave

### Take ({n})
- **T{n}: {Title}** — {what we adopt}. Source: {persona-slug or cell}. Evidence: {URL or artifact}.

### Leave ({n})
- **L{n}: {Title}** — {what we explicitly reject}. Source: {persona-slug or cell}. Evidence: {URL or artifact}.
```

For `go-no-go`:

```markdown
## Synthesis verdict — go/no-go

**Decision:** {GO | NO-GO | CONDITIONAL GO}

**Conditions (if conditional):**
- {persona-slug}: {condition this persona requires before GO}

**Lead voice:** {persona-slug} carried the verdict; {persona-slug} formally dissented.
```

For `decision-matrix`:

```markdown
## Synthesis verdict — decision matrix

| Option | Cell A | Cell B | Cell C | Cell D | Cell E | Verdict |
|---|---|---|---|---|---|---|
| {Option 1} | {lead persona's take} | ... | ... | ... | ... | {final} |
| {Option 2} | ... | ... | ... | ... | ... | {final} |
```

---

## Section 5 — Anchor quotes

A final section preserving exact wording from the panel. Each quote attributed to a persona and a source location. Convene calls re-use these in future syntheses to keep voices consistent over time.

```markdown
## Anchor quotes

- **{Real Name}** ({cell}): "{quote}" — {source artifact, section}.
- ...
```

---

## Rules for `/superintelligenceTeam-convene`

1. **Always cite who said what.** No bare "the panel agreed." Either name a persona or name a cell.
2. **Mine `v2_panel_attribution` first.** If a persona has a stance recorded from the Marvin v2 panel, USE IT verbatim before generating new opinion in their voice.
3. **Surface dissent explicitly.** Smoothing over disagreement loses signal. Convene's job is to make disagreement legible.
4. **Cell-role hierarchy.** Lead-drivers > validators > specialists > swings. In a tie, lead-drivers prevail. Mark this explicitly.
5. **Recency bias** — when a persona's `recent_signal_12mo` contradicts an older `canonical_works` entry, recent wins. Note the shift in synthesis.
6. **No invented citations.** If a stance cannot be traced to a persona file's `public_stances`, `canonical_works`, `recent_signal_12mo`, or `v2_panel_attribution`, do not attribute it. State "extrapolated from {field}" instead.
7. **Save the convene transcript** under `superintelligenceTeam/convenes/<convene_id>.md` so future calls can supersede or cite it.

---

## See also

- `superintelligenceTeam/templates/persona.md` — schema every persona file follows.
- `superintelligenceTeam/registry.json` — roster + cell + role machine source.
- `superintelligenceTeam/SKILL.md` — user-facing entry point and command surface.
