---
cell_id: security
team: engineering-super-intelligence
personas_count: 6
last_updated: 2026-05-30
---

# Cell: Security

Security — security architecture, cryptography, vuln research, disclosure policy.

## Personas (6)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `alex-stamos` | Alex Stamos | Corridor (Chief Security Officer, AI code-security startup, since August 2025) | lead-driver | Reframe a 'policy' problem as an engineering problem — trust & safety is a discipline with code, not a content-moderation opinion. |
| `bruce-schneier` | Bruce Schneier | Inrupt (Chief of Security Architecture) | lead-driver | Reframe the question from 'is it secure?' to 'who benefits, who pays, and what's the incentive?' — security is economics before it's math. |
| `katie-moussouris` | Katie Moussouris | Luta Security (founder & CEO, since April 2016) | specialist | Separate the two things everyone conflates: disclosure (the front door for reports) is not a bug bounty (a cash incentive). Fix the front door before you offer the cash. |
| `matthew-green` | Matthew Green | Johns Hopkins University (Associate Professor of Computer Science, Information Security Institute) | specialist | Ask of any new proposal: what does this break that the proposer never modeled? (model extraction, hash collisions, evasion, ghost-user auth weakening). |
| `tavis-ormandy` | Tavis Ormandy | Independent vulnerability researcher (since 2025-10-10) | specialist | Aim the fuzzer at the thing that is supposed to protect you — the antivirus, the proxy, the password manager — because it parses the most hostile input at the highest privilege. |
| `window-snyder` | Mwende Window Snyder | Thistle Technologies (founder & CEO, since 2020) | specialist | Make security a drop-in default — developers should never have to be security experts to ship a secure device. |

## When to summon the whole cell

- "What is the threat model, and what is the real attack surface?"
- "Is this cryptography / disclosure / policy choice sound?"
- "Are we adding security or just security theater?"

## Productive tensions inside the cell

- **Alex Stamos ↔ Matthew Green** (`alex-stamos` ↔ `matthew-green`)
- **Alex Stamos ↔ Bruce Schneier** (`alex-stamos` ↔ `bruce-schneier`)
- **Bruce Schneier ↔ Katie Moussouris** (`bruce-schneier` ↔ `katie-moussouris`)
- **Katie Moussouris ↔ Tavis Ormandy** (`katie-moussouris` ↔ `tavis-ormandy`)
- **Katie Moussouris ↔ Matthew Green** (`katie-moussouris` ↔ `matthew-green`)
- **Alex Stamos ↔ Tavis Ormandy** (`alex-stamos` ↔ `tavis-ormandy`)
- **Tavis Ormandy ↔ Mwende Window Snyder** (`tavis-ormandy` ↔ `window-snyder`)
- **Bruce Schneier ↔ Mwende Window Snyder** (`bruce-schneier` ↔ `window-snyder`)

## How this cell maps to /SI-Eng commands

This cell is one lens the orchestrator (`/SI-Eng-Orchestrate`) draws on when scoring
a 16–32 persona team for a prompt. Summon it directly with
`/SI-Eng-Huddle security "<topic>"` when the question lands squarely in this domain,
or let an action verb (`/SI-Eng-Decide`, `/SI-Eng-Tradeoff`, `/SI-Eng-Stress-Test`, …)
pull the most relevant members into a cross-cell panel.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/engineering/scripts/build_cells.py`. Re-run after persona edits.
