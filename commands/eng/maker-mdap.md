---
description: "Load the MAKER/MDAP knowledge base (arXiv:2511.09030) — Maximal Agentic Decomposition, first-to-ahead-by-k voting, red-flagging, cost scaling. Usage: /maker-mdap [topic | ch01–ch07]"
argument-hint: "[topic, framework name, or chapter number]"
allowed-tools: Read
---

# /maker-mdap — MAKER / MDAP

Load the `maker-mdap` skill and answer from it. Arguments: **$ARGUMENTS**

Read `skills/maker-mdap/SKILL.md` first. Then, based on `$ARGUMENTS`:

- **Empty** — summarize the core frameworks (MAD, first-to-ahead-by-k, red-flagging, the Θ(p^-m · c · s · ln s) cost law) and the chapter index. Stop. Do not dump chapters.
- **Chapter** (`ch01`…`ch07`, or `1`–`7`) — read that file under `skills/maker-mdap/chapters/` and answer from it.
- **Topic** (voting, red-flagging, cost scaling, decomposition, MAD, MAKER, MDAP, collisions, calibrate-then-scale, parsers, Hanoi, k_min, insight vs execution, …) — use the Topic Index in SKILL.md, read the matching chapter(s) plus `glossary.md` / `patterns.md` / `cheatsheet.md` as needed, then answer.
- **Browse** (`chapters`, `index`, `what do you have`) — print the chapter + topic index from SKILL.md.

## Rules

- This skill is the paper (arXiv:2511.09030) only. Do not invent results that are not in the files.
- Numeric thresholds in the paper (e.g. the ~700-token red-flag cutoff) are Hanoi-specific; say so if applying them elsewhere.
- Scope is *execution* of a given strategy, not *insight* (generating the strategy).
- Prefer the cheatsheet for decision rules; open a chapter only when the question needs it.
