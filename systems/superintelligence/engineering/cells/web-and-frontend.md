---
cell_id: web-and-frontend
team: engineering-super-intelligence
personas_count: 6
last_updated: 2026-05-30
---

# Cell: Web and Frontend

Web and Frontend — frontend frameworks, web platform, UI engineering.

## Personas (6)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `adam-wathan` | Adam Wathan | Tailwind Labs (founder and CEO) | specialist | Reframe the dogma as a tradeoff: 'separation of concerns' is a straw man — the real question is whether CSS depends on HTML or HTML depends on CSS. |
| `dan-abramov` | Dan Abramov | Independent engineer (React core team member; between full-time roles, consulting + writing) | lead-driver | Turn an internal team intuition into a long-form blog post the whole ecosystem can reason about. |
| `evan-you` | Evan You | VoidZero Inc. (founder & CEO, since October 2024): Vite, Rolldown, Oxc, Vitest, Vite+ | lead-driver | Find the fragmentation seam — the place where five tools each re-parse the same AST — and collapse it into one shared pipeline. |
| `guillermo-rauch` | Guillermo Rauch | Vercel (Founder & CEO, since 2015 as ZEIT; rebranded Vercel 2020) | specialist | Collapse the gap between intent and a live URL — fewest commands, least config, instant deploy. |
| `rich-harris` | Rich Harris | Vercel (Svelte / SvelteKit core, since 2021) | lead-driver | Ask 'what if the framework were just a compiler?' — move the work to build time so the framework disappears from the shipped bundle. |
| `ryan-carniato` | Ryan Carniato | Netlify (Principal Engineer, Open Source) | specialist | Settle the argument with a benchmark — build the thing and let the numbers prove the model. |

## When to summon the whole cell

- "Which frontend framework / rendering model fits this product?"
- "Compiler, virtual DOM, or signals — what is the real tradeoff?"
- "How do we keep the web app fast and maintainable at scale?"

## Productive tensions inside the cell

- **Adam Wathan ↔ Rich Harris** (`adam-wathan` ↔ `rich-harris`)
- **Dan Abramov ↔ Rich Harris** (`dan-abramov` ↔ `rich-harris`)
- **Dan Abramov ↔ Ryan Carniato** (`dan-abramov` ↔ `ryan-carniato`)
- **Dan Abramov ↔ Evan You** (`dan-abramov` ↔ `evan-you`)
- **Evan You ↔ Rich Harris** (`evan-you` ↔ `rich-harris`)
- **Evan You ↔ Ryan Carniato** (`evan-you` ↔ `ryan-carniato`)

## How this cell maps to /SI-Eng commands

This cell is one lens the orchestrator (`/SI-Eng-Orchestrate`) draws on when scoring
a 16–32 persona team for a prompt. Summon it directly with
`/SI-Eng-Huddle web-and-frontend "<topic>"` when the question lands squarely in this domain,
or let an action verb (`/SI-Eng-Decide`, `/SI-Eng-Tradeoff`, `/SI-Eng-Stress-Test`, …)
pull the most relevant members into a cross-cell panel.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/engineering/scripts/build_cells.py`. Re-run after persona edits.
