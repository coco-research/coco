---
cell_id: finops-cost
team: engineering-super-intelligence
personas_count: 4
last_updated: 2026-05-30
---

# Cell: FinOps and Cost

FinOps and Cost — cloud cost engineering and FinOps practice.

## Personas (4)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `corey-quinn` | Corey Quinn | Duckbill (founder & Chief Cloud Economist, since 2019) | lead-driver | Read the bill as the source of truth — it is the only complete inventory of what you actually built and run. |
| `erik-peterson` | Erik Peterson | CloudZero (Co-founder & CTO/CISO, since 2016) | specialist | Reframe the question from 'what did this cost?' to 'was it worth it?' — anchor every spend to a business unit before debating it. |
| `jr-storment` | J.R. Storment | FinOps Foundation (co-founder & Executive Director; a program of the Linux Foundation) | lead-driver | Reframe cost from a finance chore into a core engineering responsibility — 'like security, like reliability.' |
| `mike-fuller` | Mike Fuller | FinOps Foundation (CTO; FOCUS Steering Committee Chair & Maintainer) | specialist | Make the bill machine-readable first: a common schema (FOCUS) beats per-vendor heroics every time. |

## When to summon the whole cell

- "What is this actually costing us, per unit of value?"
- "Where is the cloud bill leaking, and who owns it?"
- "Is this spend an investment or waste?"

## Productive tensions inside the cell

- **Corey Quinn ↔ Erik Peterson** (`corey-quinn` ↔ `erik-peterson`)
- **Corey Quinn ↔ J.R. Storment** (`corey-quinn` ↔ `jr-storment`)
- **Corey Quinn ↔ Mike Fuller** (`corey-quinn` ↔ `mike-fuller`)

## How this cell maps to /SI-Eng commands

This cell is one lens the orchestrator (`/SI-Eng-Orchestrate`) draws on when scoring
a 16–32 persona team for a prompt. Summon it directly with
`/SI-Eng-Huddle finops-cost "<topic>"` when the question lands squarely in this domain,
or let an action verb (`/SI-Eng-Decide`, `/SI-Eng-Tradeoff`, `/SI-Eng-Stress-Test`, …)
pull the most relevant members into a cross-cell panel.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/engineering/scripts/build_cells.py`. Re-run after persona edits.
