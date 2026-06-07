---
cell_id: reliability-sre-obs
team: engineering-super-intelligence
personas_count: 7
last_updated: 2026-05-30
---

# Cell: Reliability, SRE, and Observability

Reliability, SRE, and Observability — SRE practice, incident response, resilience.

## Personas (7)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `ben-treynor-sloss` | Benjamin Treynor Sloss | Blackstone-Google TPU Cloud joint venture (CEO, since 2026-05-18; compute-as-a-service for Google TPUs) | lead-driver | Define SRE by its origin question: what happens when you ask a software engineer to design an operations function? |
| `betsy-beyer` | Adrienne Elizabeth "Betsy" Beyer *(archetype)* | Google (Technical Writer, Site Reliability Engineering, New York City) | validator | Make tacit expertise legible — knowledge that lives only in an engineer's head is a single point of failure; write it down and it becomes a reliability asset. |
| `charity-majors` | Charity Majors | Honeycomb.io (co-founder & CTO, since 2016) | lead-driver | Tell the team they're already testing in production — the only choice is whether they do it deliberately. |
| `cindy-sridharan` | Cindy Sridharan *(archetype)* | imgix (Infrastructure / Distributed Systems Engineer — last publicly confirmed role; not re-verified for 2026) | specialist | Separate the two words: monitoring answers 'what's broken' on known failure modes; observability gives rich context to debug the failures you never anticipated. |
| `liz-fong-jones` | Liz Fong-Jones | Honeycomb (Technical Fellow, since January 2026) | specialist | Set the SLO just barely high enough to keep users happy — anything higher is money you set on fire. |
| `nora-jones` | Nora Jones | PagerDuty (Senior Director, Head of Pricing, Product Strategy and Growth; joined via Jeli acquisition Nov 2023) | specialist | Treat the incident as the unit of learning, not the unit of blame — the goal of a review is a story of how the system actually works, not a list of action items. |
| `tammy-butow` | Tammy Bryant Butow *(archetype)* | Apple (engineering / reliability; specific role not publicly disclosed; Cupertino, California) | specialist | Break it on purpose, under control — run a deliberate, scoped experiment to expose a systemic weakness before a real incident does it for you. |

## When to summon the whole cell

- "How do we know this is healthy in production?"
- "What is our SLO / error budget, and are we spending it wisely?"
- "How do we run the incident and learn from it afterwards?"

## Productive tensions inside the cell

- **Benjamin Treynor Sloss ↔ Charity Majors** (`ben-treynor-sloss` ↔ `charity-majors`)
- **Adrienne Elizabeth "Betsy" Beyer ↔ Charity Majors** (`betsy-beyer` ↔ `charity-majors`)
- **Benjamin Treynor Sloss ↔ Liz Fong-Jones** (`ben-treynor-sloss` ↔ `liz-fong-jones`)
- **Adrienne Elizabeth "Betsy" Beyer ↔ Liz Fong-Jones** (`betsy-beyer` ↔ `liz-fong-jones`)
- **Benjamin Treynor Sloss ↔ Nora Jones** (`ben-treynor-sloss` ↔ `nora-jones`)
- **Adrienne Elizabeth "Betsy" Beyer ↔ Nora Jones** (`betsy-beyer` ↔ `nora-jones`)
- **Charity Majors ↔ Tammy Bryant Butow** (`charity-majors` ↔ `tammy-butow`)

## How this cell maps to /SI-Eng commands

This cell is one lens the orchestrator (`/SI-Eng-Orchestrate`) draws on when scoring
a 16–32 persona team for a prompt. Summon it directly with
`/SI-Eng-Huddle reliability-sre-obs "<topic>"` when the question lands squarely in this domain,
or let an action verb (`/SI-Eng-Decide`, `/SI-Eng-Tradeoff`, `/SI-Eng-Stress-Test`, …)
pull the most relevant members into a cross-cell panel.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/engineering/scripts/build_cells.py`. Re-run after persona edits.
