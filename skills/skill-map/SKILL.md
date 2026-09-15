---
name: skill-map
description: "Discover in-repo CoCo skills and slash commands from the skill-map. Use when the user asks which skill/command to use, how to find capabilities, marketplace/map lookup, or plain-language goals that should map to ranked skill/command ids."
domain: meta
---

# Skill Map

**Announce at start:** "Skill Map skill activated."

Local-first discovery over the generated map at `docs/skill-map.json` (built from `docs/asset-counts.json`, skill/command indexes, and SI verb list). **No new runtime** — rank in-process.

## When to use

- "What skill should I use for X?"
- Marketplace / skill-map / find in-repo capability
- Plain-language goal → ranked skill and command ids

## Hard rules

1. **Totals** must match `docs/asset-counts.json` (`skills.total`, `commands.customer_facing`). If the map is stale, run `python3 scripts/build-skill-map.py` and use the refreshed file.
2. **REQUIRED baseline first:** always include `karpathy-guidelines` and `maker-mdap` in the ranking when present in the map (boost to the top band).
3. **Maker MDAP** appears only when `skills/maker-mdap` exists and is listed — never invent ids.
4. **/SI-*** decision verbs come from the map's `si_verbs` list (visible even though generated at install).
5. Do not peer-mesh TLs into SI as second managers; discovery ≠ SI spawn.

## Ranking procedure

Given a plain-language goal:

1. Load `docs/skill-map.json`.
2. Tokenize the query (lowercase words, length ≥ 3).
3. Score each entry by overlap of tokens with `id`, `name`, `description`, and `tags` (Jaccard-like: `|q∩d|/|q∪d|`).
4. Apply boosts:
   - `required: true` → +0.5
   - `kind: si_verb` → +0.15 when query mentions decide/review/plan/design/debug/vote/tradeoff/analyse/analyze or "SI"
5. Return top 8: `kind`, `id`, `path` (if any), `score`, one-line why.
6. Always state asset-count totals from the map header.

## Success

Worker query → ranked in-repo ids including `karpathy-guidelines` (and `maker-mdap` when shipped), with `/SI-*` verbs visible and totals cited from asset-counts.
