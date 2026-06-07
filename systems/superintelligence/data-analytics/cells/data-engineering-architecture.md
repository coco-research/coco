---
cell_id: data-engineering-architecture
team: data-analytics-super-intelligence
personas_count: 4
last_updated: 2026-06-01
---

# Cell: Data Engineering Architecture

Pipelines, warehouses, lakehouse, data mesh, modeling, orchestration.

## Personas (4)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `bill-inmon` | William H. (Bill) Inmon *(archetype)* | Founder and owner, Forest Rim Technology (Textual ETL / textual disambiguation) | validator | Define the noun before the verb — pin down what a data warehouse *is* (subject-oriented, integrated, non-volatile, time-variant) before arguing about how to build it. |
| `maxime-beauchemin` | Maxime Beauchemin | Founder & CEO, Preset (commercial Apache Superset) | specialist | Names an emerging role or pattern in an essay, then builds the tool that operationalizes it |
| `ralph-kimball` | Ralph Kimball *(archetype)* | Kimball Group (founder; consultancy dissolved December 2015, body of work remains canonical) | validator | Four-step dimensional design process (select business process, declare grain, identify dimensions, identify facts) |
| `zhamak-dehghani` | Zhamak Dehghani | Founder and CEO, Nextdata (data-mesh-native platform; creator of Nextdata OS) | lead-driver | Reframing data problems as sociotechnical (organization + architecture together), never purely technical |

## When to summon the whole cell

- "What does the Data Engineering Architecture lens say about this?"
- "Pipelines, warehouses, lakehouse, data mesh, modeling, orchestration" — where does this decision touch that?
- "Who in Data Engineering Architecture would push back hardest, and why?"

## Productive tensions inside the cell

- **William H. (Bill) Inmon ↔ Ralph Kimball** (`bill-inmon` ↔ `ralph-kimball`)
- **William H. (Bill) Inmon ↔ Zhamak Dehghani** (`bill-inmon` ↔ `zhamak-dehghani`)
- **William H. (Bill) Inmon ↔ Maxime Beauchemin** (`bill-inmon` ↔ `maxime-beauchemin`)
- **Maxime Beauchemin ↔ Ralph Kimball** (`maxime-beauchemin` ↔ `ralph-kimball`)
- **Ralph Kimball ↔ Zhamak Dehghani** (`ralph-kimball` ↔ `zhamak-dehghani`)

## How this cell maps to /SI-Data commands

Summon with `/SI-Data-Huddle data-engineering-architecture "<topic>"`, or let an action verb
(`/SI-Data-Decide`, `/SI-Data-Tradeoff`, `/SI-Data-Stress-Test`, …) pull
members into a cross-cell panel via `/SI-Data-Orchestrate`.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/data-analytics/scripts/build_cells.py`. Personas are illustrative
composites of real public figures — see `superintelligence/DISCLAIMER.md`.
