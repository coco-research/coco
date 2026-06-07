---
cell_id: cloud-architecture
team: engineering-super-intelligence
personas_count: 8
last_updated: 2026-05-30
---

# Cell: Cloud Architecture

Cloud Architecture — cloud-scale system design, infra primitives, build-vs-managed lens.

## Personas (8)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `adrian-cockcroft` | Adrian Cockcroft | OrionX.net (Partner; Technology and Strategy Advisor) | specialist | Ask whether it's actually loosely coupled and independently deployable — if not, it isn't a microservice, it's a distributed monolith. |
| `brendan-burns` | Brendan Burns | Microsoft (Corporate VP and Technical Fellow, Azure OSS and Cloud Native) | specialist | Find the missing shared interface, standardize it in the open, and let community pressure replace individual judgment. |
| `colm-maccarthaigh` | Colm MacCárthaigh | Amazon Web Services (VP & Distinguished Engineer, EC2 Networking & Cryptography) | specialist | Rank trade-offs in a fixed order — security, durability, availability, speed — and never reorder them under pressure. |
| `eric-brewer` | Eric Brewer | Google (VP of Infrastructure & Google Fellow, since 2011) | validator | State the trade-off as a theorem, not a preference — name exactly which two of the three you keep and when. |
| `james-hamilton` | James Hamilton | Amazon (Senior Vice President & Distinguished Engineer, S-team, since 2009) | lead-driver | Open with the cost model — 'let's look at where the money actually goes' before debating any design. |
| `marc-brooker` | Marc Brooker | Amazon Web Services (VP and Distinguished Engineer, spec-driven AI-assisted development) | specialist | Turn every reliability question into a distribution and obsess over the tail, not the median demo. |
| `radia-perlman` | Radia Joy Perlman | Dell Technologies (Fellow, network protocol and security design) | validator | Design the protocol so the operator never has to understand it — plug it together and it just works. |
| `werner-vogels` | Werner Vogels | Amazon.com (Chief Technology Officer & VP, since 2005) | lead-driver | Assume failure first. Design for the datacenter that is already on fire, not the one that runs forever. |

## When to summon the whole cell

- "Build it ourselves or use the managed service?"
- "How does this behave at cloud scale / under partial failure?"
- "What are the real cost and reliability economics of this infra choice?"

## Productive tensions inside the cell

- No within-cell productive-conflict pairs recorded. Tension in this cell comes primarily from cross-cell pairings surfaced by the orchestrator.

## How this cell maps to /SI-Eng commands

This cell is one lens the orchestrator (`/SI-Eng-Orchestrate`) draws on when scoring
a 16–32 persona team for a prompt. Summon it directly with
`/SI-Eng-Huddle cloud-architecture "<topic>"` when the question lands squarely in this domain,
or let an action verb (`/SI-Eng-Decide`, `/SI-Eng-Tradeoff`, `/SI-Eng-Stress-Test`, …)
pull the most relevant members into a cross-cell panel.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/engineering/scripts/build_cells.py`. Re-run after persona edits.
