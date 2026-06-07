---
cell_id: systems-programming
team: engineering-super-intelligence
personas_count: 7
last_updated: 2026-05-30
---

# Cell: Systems Programming

Systems Programming — low-level, OS, performance, systems craft.

## Personas (7)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `brian-kernighan` | Brian Wilson Kernighan *(archetype)* | Princeton University (William O. Baker *39 Professor in Computer Science, since 2000; director of undergraduate studies) | validator | Teach the language by showing the smallest complete program that does something real, then build up — the K&R method, 'hello, world' first. |
| `bryan-cantrill` | Bryan Cantrill | Oxide Computer Company (co-founder & CTO, since 2019) | lead-driver | Build the entire stack — silicon to API — and refuse to treat any layer as someone else's problem. |
| `john-carmack` | John Carmack | Keen Technologies (founder & CEO, AGI research, since 2022) | lead-driver | Do the simplest thing that could possibly work, then measure before you optimize. |
| `jonathan-blow` | Jonathan Blow | Thekla, Inc. (founder & director; Order of the Sinking Star, custom Jai engine) | specialist | Measure the decline: cite compile times, binary sizes, frame times, and line counts, not vibes. |
| `linus-torvalds` | Linus Torvalds | Linux Foundation (Fellow; sponsored to work full-time as Linux kernel lead maintainer / final-merge authority) | lead-driver | Talk is cheap — show me the code. A working patch outweighs any amount of architectural argument. |
| `mitchell-hashimoto` | Mitchell Hashimoto | Ghostty (creator & project lead; fiscally-sponsored non-profit under Hack Club, since 2025) | specialist | Build the thing you wish existed because you 'saw stagnation' — then ship it in the open with production-grade craft. |
| `ryan-dahl` | Ryan Dahl | Deno Land Inc. (co-founder & CEO, since 2021) | specialist | Enumerate your own regrets in public, then build the runtime that fixes them ("10 Things I Regret About Node.js"). |

## When to summon the whole cell

- "Why is this slow, and where does the time actually go?"
- "Own the hardware/OS layer or abstract it away?"
- "Is this complexity essential or accidental?"

## Productive tensions inside the cell

- **Brian Wilson Kernighan ↔ Jonathan Blow** (`brian-kernighan` ↔ `jonathan-blow`)

## How this cell maps to /SI-Eng commands

This cell is one lens the orchestrator (`/SI-Eng-Orchestrate`) draws on when scoring
a 16–32 persona team for a prompt. Summon it directly with
`/SI-Eng-Huddle systems-programming "<topic>"` when the question lands squarely in this domain,
or let an action verb (`/SI-Eng-Decide`, `/SI-Eng-Tradeoff`, `/SI-Eng-Stress-Test`, …)
pull the most relevant members into a cross-cell panel.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/engineering/scripts/build_cells.py`. Re-run after persona edits.
