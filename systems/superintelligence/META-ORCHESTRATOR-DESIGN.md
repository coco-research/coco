# Cross-Team Meta-Orchestrator — Design

**Status:** design (2026-06-01). Priority capability. Builds on the per-team orchestrators.

## Problem

Each Super Intelligence team has its own orchestrator (`/SI-AI-Orchestrate`, `/SI-Eng-Orchestrate`, …) that selects 16–32 personas **from that team only**. But the hardest real decisions are **cross-domain**:

- "Should we ship an AI compliance product?" → needs AI + Risk/Compliance + Product voices.
- "Price and package a fintech feature" → Finance + Product/Design + (Trading for market risk).
- "Re-architect on Kubernetes vs serverless for an AI workload" → Engineering + AI + Finance (cost).

No single team's roster covers these. The meta-orchestrator is a **top-level router** that assembles one panel **across teams**, while staying light (the original "CoCo loads everything" failure mode is explicitly avoided).

## Design principles (inherited + new)

1. **Light by construction.** Never load all persona records. Route at **team + cell granularity first** (compact descriptions), then drill into persona records for only the 1–4 selected teams.
2. **Hard 16–32 band**, cross-team total. Same as per-team.
3. **Approval gate**, confidence-tiered (high → 1-line summary + auto-proceed; low → AskUserQuestion). Grouped by team.
4. **Re-pick every invocation.** No caching.
5. **Reuse, don't fork.** Per-team registries are the source of truth; the meta layer federates them. Generated from the same `build_commands.py`.
6. **Delegate when single-domain.** If the prompt is clearly one team's turf, hand off to that team's normal orchestrator — zero meta overhead.

## Command surface

A new **top-level family** (no team segment), generated alongside the per-team commands:

| Command | Role |
|---|---|
| `/SI` | Meta-dispatcher. No args → list all built teams (from meta-registry) + the cross-team verb list + usage. With a **team** as first token (`/SI ai …`) → point to that team's `/SI-AI-*`. With a **verb** as first token → run the meta verb. |
| `/SI-Orchestrate "<prompt>"` | Cross-team selection + approval gate. Returns the approved cross-team roster. |
| `/SI-Decide`, `/SI-Tradeoff`, `/SI-Pre-Mortem`, `/SI-Analyse`, `/SI-Review`, `/SI-Stress-Test`, `/SI-Plan`, `/SI-Design`, `/SI-Vote`, `/SI-Debug`, `/SI-Defend`, `/SI-Roast`, `/SI-Post-Mortem`, `/SI-Re-Analyse`, `/SI-Full-Cycle` | All-teams action verbs. Each calls `/SI-Orchestrate` first, then runs the verb over the merged roster. |

No filename collision with per-team files: `SI-AI.md` (team dispatcher) vs `SI-Decide.md` (meta verb) vs `SI-AI-Decide.md` (per-team verb) are all distinct. Per-team `/SI-<team>-*` commands remain for scoped, single-domain use.

## Algorithm — two-stage selection

### Stage A — Team + cell routing (cheap; the "light" layer)

1. Read `superintelligence/registry.json` (meta) → list teams where `built: true`.
2. For each built team, read **only** its registry's `cells` section (cell id + description + persona_count) and team `description`. Do **not** read persona records yet.
3. Score each **team** against the prompt: keyword/domain overlap with team description + its cell descriptions → `team_relevance ∈ [0,1]`.
4. Select the top **1–4 teams** above a relevance floor. Within each selected team, mark the **candidate cells** (cells whose description matches the prompt).
   - If exactly one team clears the floor with a dominant margin → **delegate**: tell the user this is single-domain and invoke that team's `/SI-<team>-Orchestrate` instead. Stop.

### Stage B — Persona selection (scoped)

5. For the selected teams/cells only, load those personas' compact records from each team's `registry.json` (`personas` section: slug, cell, domains, voice_style_excerpt, productive_conflict_with).
6. Allocate the 16–32 budget across selected teams **strictly proportional to `team_relevance`** (LOCKED: pure proportional, no per-team floor) within the global 16–32 band. A low-relevance team may get only 1–2 seats — that is intended.
7. Within each team's allocation, run the standard greedy score: `0.40·domain-match + 0.30·cell-coverage + 0.30·productive-conflict-pairing`, re-scoring after each pick.
8. **Cross-team tension pass (new):** after per-team picks, ensure the panel spans opposing domain lenses — e.g., a "ship/scale/growth" voice **and** a "risk/cost/governance" voice. If the prompt is cross-cutting but the panel collapsed onto one stance, swap in an opposing-domain persona. Dedupe cross-listed personas by slug (Karpathy in AI+Eng, Wathan in Eng+P&D appear once).

### Stage C — Approval + execution

9. Present the proposed panel **grouped by team**, each persona with a one-line rationale + their team tag. Confidence-tiered gate (Approve / Drop / Add / Re-pick / Reject).
10. The calling action verb consumes the approved roster and produces its output. **Attribution names persona + team** (e.g., "*Aswath Damodaran (Finance)*: …"). Synthesis must explicitly surface **cross-team disagreement**, not just within-team.

## Implementation

Extend `build_commands.py` (single source of truth):

- Add a `META` pseudo-team config (no `data_dir`; instead reads the meta-registry + per-team registries live).
- Add `meta_dispatcher_body()` and `meta_orchestrate_body()` (the two-stage algorithm above), and reuse the existing action-verb bodies — they already "consume an approved roster," so only the orchestration step they call changes (`/SI-Orchestrate` instead of `/SI-<team>-Orchestrate`).
- Emit: `SI.md`, `SI-Orchestrate.md`, and `SI-<Verb>.md` for the 15 action verbs (no identity/roster/maintenance verbs at the meta level — those stay per-team). ~17 files.
- Paths: meta commands reference `{REPO}/superintelligence/registry.json` for routing and `{REPO}/superintelligence/<team>/registry.json` for the drill-down.

## Edge cases

- **Unbuilt teams** excluded (read `built: true`). Finance/Trading/GRC auto-join the moment their flag flips — no meta-command regen needed (it reads the registry live).
- **Single-domain prompt** → delegate to one team (Stage A step 4).
- **>4 relevant teams** → cap at the top 4 by relevance (log which were dropped, per the "no silent caps" rule).
- **Cross-listed personas** → dedupe by slug; attribute to `home_team`.
- **CoCo** → standalone; CoCo may invoke it but isn't load-bearing.

## Why this is light

Stage A touches ~6 small `cells` blocks (a few KB total). Stage B touches persona records for ≤4 teams, not all 6+. No verb ever loads every persona file. The expensive full-roster read only happens for the teams actually chosen.

## Decisions

- **LOCKED — Delegate-on-single-domain:** auto-hand-off to the one dominant team's orchestrator; no forced cross-team panel.
- **LOCKED — Budget:** pure proportional to team-relevance, no per-team floor.
- **LOCKED — Selection engine:** keep the **prompt-file shell** for now. A 2026-06-01 dry-run of Stage-A on 3 cross-domain prompts (real registries) routed sanely — the binding constraint is *team count*, not scoring quality. **Defer** the deterministic embedding selector (`meta_select.py`, local `nomic-embed`) until **≥5 teams are built** (after GRC + Finance + Trading), when cross-team value and the engine's payoff both materialize. `nomic-embed` is already loaded in LM Studio, so the upgrade is cheap when triggered.
- **LOCKED — Command surface:** **full `/SI` family** (`/SI` dispatcher + `/SI-Orchestrate` + 15 `/SI-<Verb>`) **AND CoCo-hosted** routing. Both surfaces: explicit slash commands for discoverability/tab-completion, and CoCo's natural-language router invokes `/SI-*` for cross-domain prompts. (Chosen for best capability, not least work.)

## Surface options (under discussion)

| # | Option | Files | Pros | Cons |
|---|---|---|---|---|
| A | **`/SI` + full `/SI-<Verb>` family (15)** | ~17 | Most explicit + tab-discoverable; mirrors per-team surface exactly | Most command files; `/SI-Decide` vs `/SI-AI-Decide` visual clutter |
| B | **Single smart `/SI` dispatcher** — `/SI <verb?> "<prompt>"`, infers verb+teams (confirms) | 1–2 | Leanest; most natural ("ask the whole brain trust"); one entrypoint | Less tab-discoverable; verb inference must be reliable |
| C | **CoCo-hosted** — `/coco` NL routes cross-team, invoking the *light* standalone meta-orchestrator under the hood | 0 new SI files | Matches the original "CoCo as orchestrator" vision; NL-first; one brain | Couples to CoCo being active; must keep Stage-A light to avoid the "loads everything" trap |
| D | **Hybrid (recommended)** — `/SI` smart dispatcher **+** explicit aliases for only the high-value cross-team verbs (`/SI-Decide`, `/SI-Tradeoff`, `/SI-Pre-Mortem`, `/SI-Review`, `/SI-Stress-Test`) **+** CoCo router can invoke `/SI` | ~7 | Leanest discoverable set; covers the verbs cross-team actually helps; honors CoCo vision without bloat; per-team verbs handle the rest | Slight asymmetry (not all 15 verbs aliased at meta level) |

**Reasoning for D:** cross-team panels add most value on **high-stakes synthesis verbs** (decide, tradeoff, pre-mortem, review, stress-test) — not on `roast`/`debug`/`vote`, which are usually single-domain. So alias only those five at the meta level, let `/SI "<prompt>"` infer for anything else, and let CoCo's natural-language router call `/SI` so the original "CoCo orchestrates" intent is realized — with the light Stage-A keeping it cheap.
