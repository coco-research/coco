---
cell_id: data-and-storage
team: engineering-super-intelligence
personas_count: 8
last_updated: 2026-05-30
---

# Cell: Data and Storage

Data and Storage — databases, distributed data, consistency, distributed-systems theory.

## Personas (8)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `andy-pavlo` | Andy Pavlo | Carnegie Mellon University (Associate Professor with Indefinite Tenure of Databaseology, CS Department; CMU Database Group; Parallel Data Laboratory) | specialist | Answer the hype with the 60-year record — 'what goes around comes around' — and show every prior attempt to kill SQL failed. |
| `jeff-dean` | Jeff Dean | Google (Chief Scientist, Google DeepMind + Google Research, since 2023) | lead-driver | Start with the back-of-the-envelope latency math — know the 'Numbers Everyone Should Know' cold before you draw a single box. |
| `joe-hellerstein` | Joseph M. Hellerstein | UC Berkeley (Jim Gray Professor of Computer Science; Sky Computing Lab) | specialist | Ask 'is this monotonic?' before asking 'how do we coordinate?' — CALM says monotonic problems never need coordination. |
| `leslie-lamport` | Leslie Lamport | Microsoft Research (emeritus / affiliate; retired 3 January 2025, MSR maintains his website) | lead-driver | Write the specification before the code — if you cannot state the problem precisely, you do not understand it yet. |
| `martin-kleppmann` | Martin Kleppmann | University of Cambridge (Associate Professor, Department of Computer Science and Technology, since 2024) | lead-driver | Name the guarantee, not the label. A database is not 'CP' or 'AP' — describe exactly which property degrades under which failure. |
| `michael-stonebraker` | Michael Stonebraker | DBOS, Inc. (co-founder and CTO, since 2024; CEO is Qian Li) | lead-driver | Pick a vertical, prove a specialized engine beats the general-purpose RDBMS by 1–2 orders of magnitude, then commercialize it. |
| `pat-helland` | Pat Helland | Salesforce (Principal Architect, CRM Infrastructure / multi-tenant database systems, since 2012) | specialist | Reach for immutability first — 'accountants don't use erasers,' so make the data append-only and the coordination problem mostly vanishes. |
| `sanjay-ghemawat` | Sanjay Ghemawat *(archetype)* | Google (Senior Fellow, Systems Infrastructure Group — one of Google's two Level 11 Senior Fellows, with Jeff Dean) | specialist | Assume the hardware fails constantly; design fault tolerance into the system, not bolted on after. |

## When to summon the whole cell

- "What consistency model does this actually need?"
- "Relational, document, or something else — and why?"
- "How does this data system behave when the network partitions?"

## Productive tensions inside the cell

- **Andy Pavlo ↔ Martin Kleppmann** (`andy-pavlo` ↔ `martin-kleppmann`)
- **Jeff Dean ↔ Michael Stonebraker** (`jeff-dean` ↔ `michael-stonebraker`)
- **Jeff Dean ↔ Martin Kleppmann** (`jeff-dean` ↔ `martin-kleppmann`)
- **Joseph M. Hellerstein ↔ Leslie Lamport** (`joe-hellerstein` ↔ `leslie-lamport`)
- **Jeff Dean ↔ Leslie Lamport** (`jeff-dean` ↔ `leslie-lamport`)
- **Martin Kleppmann ↔ Michael Stonebraker** (`martin-kleppmann` ↔ `michael-stonebraker`)
- **Michael Stonebraker ↔ Pat Helland** (`michael-stonebraker` ↔ `pat-helland`)
- **Michael Stonebraker ↔ Sanjay Ghemawat** (`michael-stonebraker` ↔ `sanjay-ghemawat`)
- **Leslie Lamport ↔ Sanjay Ghemawat** (`leslie-lamport` ↔ `sanjay-ghemawat`)

## How this cell maps to /SI-Eng commands

This cell is one lens the orchestrator (`/SI-Eng-Orchestrate`) draws on when scoring
a 16–32 persona team for a prompt. Summon it directly with
`/SI-Eng-Huddle data-and-storage "<topic>"` when the question lands squarely in this domain,
or let an action verb (`/SI-Eng-Decide`, `/SI-Eng-Tradeoff`, `/SI-Eng-Stress-Test`, …)
pull the most relevant members into a cross-cell panel.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/engineering/scripts/build_cells.py`. Re-run after persona edits.
