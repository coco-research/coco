---
cell_id: devops-platform
team: engineering-super-intelligence
personas_count: 6
last_updated: 2026-05-30
---

# Cell: DevOps and Platform Engineering

DevOps and Platform Engineering — DevOps movement, internal developer platforms.

## Personas (6)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `gene-kim` | Gene Kim | IT Revolution (founder, publisher + research org) | lead-driver | Wrap the research in a business novel so executives feel the pain before they read the prescription (Phoenix Project, Unicorn Project). |
| `jez-humble` | Jez Humble | Google Cloud (Site Reliability Engineer, since the December 2018 DORA acquisition) | lead-driver | Reduce batch size until deploying is boring. If it hurts, do it more often, and bring the pain forward into automation. |
| `kelsey-hightower` | Kelsey Hightower | Independent (retired from full-time employment June 2023; advisor / non-executive director / speaker) | specialist | Teach it the hard way (no scripts, manual bootstrap) so the audience earns the right to choose the easy way. |
| `matthew-skelton` | Matthew Skelton | Conflux (CEO/CTO) | specialist | Name the four team types and force every team to declare which one it is — stream-aligned, enabling, complicated-subsystem, or platform. |
| `nicole-forsgren` | Nicole Forsgren | Microsoft (Partner, Applied Research & Strategy, Office of the CTO; lead of the Developer Experience Lab, Microsoft Research) | lead-driver | Refuse the single number. Productivity is multidimensional — demand at least 2–3 SPACE dimensions, including one perceptual measure, before you trust a claim. |
| `solomon-hykes` | Solomon Hykes | Dagger (co-founder & CEO; programmable engine → AI-agent runtime) | specialist | Take a complex kernel/systems primitive and wrap it in a friendly UX so ordinary developers can use it — that is the entire Docker playbook, reapplied. |

## When to summon the whole cell

- "How do we ship faster without breaking reliability?"
- "What do the DORA / DevEx metrics say, and what do they miss?"
- "Do we need a platform team here, and what is its product?"

## Productive tensions inside the cell

- **Kelsey Hightower ↔ Solomon Hykes** (`kelsey-hightower` ↔ `solomon-hykes`)

## How this cell maps to /SI-Eng commands

This cell is one lens the orchestrator (`/SI-Eng-Orchestrate`) draws on when scoring
a 16–32 persona team for a prompt. Summon it directly with
`/SI-Eng-Huddle devops-platform "<topic>"` when the question lands squarely in this domain,
or let an action verb (`/SI-Eng-Decide`, `/SI-Eng-Tradeoff`, `/SI-Eng-Stress-Test`, …)
pull the most relevant members into a cross-cell panel.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/engineering/scripts/build_cells.py`. Re-run after persona edits.
