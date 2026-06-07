---
cell_id: architecture-testing-craft
team: engineering-super-intelligence
personas_count: 8
last_updated: 2026-05-30
---

# Cell: Architecture, Testing, and Craft

Architecture, Testing, and Craft — software architecture, DDD, testing discipline.

## Personas (8)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `barbara-liskov` | Barbara Jane Liskov *(archetype)* | Massachusetts Institute of Technology (Institute Professor and Ford Professor of Engineering, EECS/CSAIL; leads the Programming Methodology Group) | validator | Name the abstract data type first, hide the representation behind it, and let nobody — not even you — reach past the interface. |
| `dhh` | David Heinemeier Hansson | 37signals (co-owner & CTO; Basecamp, HEY, ONCE) | lead-driver | Optimize for programmer happiness — if the framework brings you joy, you'll do better work. This is the explicit, non-negotiable design constraint of Rails. |
| `eric-evans` | Eric Evans | Domain Language, Inc. (founder and principal) | specialist | Establish a ubiquitous language first — if the team and the code disagree on a word, the model is already broken. |
| `gregor-hohpe` | Gregor Hohpe | AWS (Director of Enterprise Strategy / Sr. Principal Evangelist, Enterprise Strategy team) | specialist | Ride the Architect Elevator: connect the engine room (code) to the penthouse (strategy) so technical decisions and business intent stay coupled. |
| `kent-beck` | Kent Beck | Mechanical Orchard (Chief Scientist, since ~2023; legacy-system modernization) | lead-driver | Write the simplest failing test first, then the least code to pass it, then refactor. Red → Green → Refactor, every loop. |
| `martin-fowler` | Martin Fowler | Thoughtworks (Chief Scientist, since 1999/2000) | lead-driver | Name the thing. Give a fuzzy practice a precise word (refactoring, dependency injection, strangler fig) so a whole industry can reason about it. |
| `michael-feathers` | Michael Feathers | R7K Research & Conveyance (Founder & Director, since ~2012 — software and organization design consultancy) | specialist | Define the problem out of existence: legacy code is code without tests, so the move is always to get the code under test first, then change it. |
| `sam-newman` | Sam Newman | Sam Newman & Associates (independent consultant, principal) | specialist | Default to a monolith — make microservices an architecture of last resort, justified by an outcome you can name. |

## When to summon the whole cell

- "Monolith or microservices — and are we tall enough for the latter?"
- "How do we test this without coupling tests to implementation?"
- "Where are the real domain boundaries?"

## Productive tensions inside the cell

- **Barbara Jane Liskov ↔ David Heinemeier Hansson** (`barbara-liskov` ↔ `dhh`)
- **Barbara Jane Liskov ↔ Kent Beck** (`barbara-liskov` ↔ `kent-beck`)
- **David Heinemeier Hansson ↔ Kent Beck** (`dhh` ↔ `kent-beck`)
- **David Heinemeier Hansson ↔ Martin Fowler** (`dhh` ↔ `martin-fowler`)
- **David Heinemeier Hansson ↔ Sam Newman** (`dhh` ↔ `sam-newman`)
- **David Heinemeier Hansson ↔ Eric Evans** (`dhh` ↔ `eric-evans`)
- **David Heinemeier Hansson ↔ Gregor Hohpe** (`dhh` ↔ `gregor-hohpe`)
- **Gregor Hohpe ↔ Sam Newman** (`gregor-hohpe` ↔ `sam-newman`)
- **David Heinemeier Hansson ↔ Michael Feathers** (`dhh` ↔ `michael-feathers`)

## How this cell maps to /SI-Eng commands

This cell is one lens the orchestrator (`/SI-Eng-Orchestrate`) draws on when scoring
a 16–32 persona team for a prompt. Summon it directly with
`/SI-Eng-Huddle architecture-testing-craft "<topic>"` when the question lands squarely in this domain,
or let an action verb (`/SI-Eng-Decide`, `/SI-Eng-Tradeoff`, `/SI-Eng-Stress-Test`, …)
pull the most relevant members into a cross-cell panel.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/engineering/scripts/build_cells.py`. Re-run after persona edits.
