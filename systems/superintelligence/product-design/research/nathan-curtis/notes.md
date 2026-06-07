# Nathan Curtis — Research Notes

**Subject:** Nathan Curtis — design-systems operations writer; founder of Directed Edges (formerly co-led EightShapes).
**Slug:** `nathan-curtis`
**Cell:** `design-systems-interaction` (Product & Design Super Intelligence Team)
**Researched:** 2026-06-01
**Researcher:** Claude (research agent)
**Status decision:** `active` — abundant signal dated after 2025-06-01 (multiple articles Sep 2025 → late May 2026, plus a SmashingConf Amsterdam 2026 talk). No need for `archetype`.

---

## Corrected assumptions (logged per instruction)

1. **Affiliation correction — EightShapes is now PAST, not current.** The task brief and ROSTER.md anchor Nathan Curtis to "EightShapes." That was accurate 2006–2024 but is now stale. In 2024 he wound down active leadership of EightShapes and founded **Directed Edges LLC** (Fairfax, VA), his current independent design-systems consulting practice. His own Directed Edges site states: "Previously he led EightShapes with Dan Brown (2006–2024)." His LinkedIn headline reads "Directed Edges." SmashingConf Amsterdam 2026 bills him as "Founder and design systems consultant at Directed Edges."
   - **Resolution in persona:** `affiliations_2026: ['Directed Edges LLC']`; EightShapes moved to `past_affiliations` as `'EightShapes (co-founder with Dan Brown, 2006–2024)'`. Per schema, any value containing a colon is single-quoted (the EightShapes line has a colon-free form here, but Directed Edges and the EightShapes line are single-quoted defensively where punctuation warrants).
   - Frontmatter `archetype` one-liner still references EightShapes lineage because that is where the canonical corpus was published; the narrative makes the 2024 transition explicit.

2. **"Co-founder of EightShapes" is correct but incomplete.** He co-founded it *with Dan Brown* (the IA author, not the novelist) in 2006 near Washington, DC. Confirmed by eightshapes.com/nathan-curtis and directededges.com.

3. **Body of work is broader than "tokens + governance."** The 2025–2026 corpus is dominated by a new theme: **components-as-data / platform-agnostic component specifications** (intent recorded as structured YAML/JSON, Figma as output not input, schema design for AI consumption). This is his current frontier and must be the lead recent-signal, not the older token/governance canon.

---

## Biography (verified)

- Co-founded **EightShapes** with **Dan Brown** near Washington, DC, in **2006**. [eightshapes.com/nathan-curtis]
- Background: information architecture, user experience design, front-end development. [eightshapes.com/nathan-curtis]
- Founded **Directed Edges LLC** in **2024** as his independent consulting practice after EightShapes (2006–2024). Based in Fairfax, VA. [directededges.com/nathan-curtis; LinkedIn]
- Author of **_Modular Web Design_** (New Riders, 2009); editor/contributor to the **_Design Systems Handbook_** (2017, InVision/DesignBetter). [eightshapes.com/nathan-curtis]
- Has contributed to or consulted with **60–100+ design systems** over his career, including Google, Salesforce, Twitter, Dropbox, Vanguard, Morningstar, Verizon, Capital One, Target, Fidelity, Marriott. [eightshapes.com/nathan-curtis; smashingconf workshop page; directededges.com]
- Builds tools: **EightShapes Specs** (Figma spec automation plugin), **Contrast Grid**, **Visual Difference**, and **Anova** (variant-analysis / component-data extraction plugin, 2025). [eightshapes.com/nathan-curtis; "Analysis of Variants" Medium]
- ~31,000 Medium followers; the single most-cited independent writer on design-system operations. [medium.com/@nathanacurtis]
- Speaks globally: SmashingConf, Clarity Conference, Into Design Systems, Chicago Camps, UIE/UI conferences. [eightshapes.com/nathan-curtis; clarityconf.com; chicagocamps.org]

---

## Canonical works (dated, with one-liners)

- **"Tokens in Design Systems" (10 tips)** — Medium/EightShapes, **2016-06-24**. The article credited with bringing "design tokens" into mainstream DS vocabulary. URL: https://medium.com/eightshapes-llc/tokens-in-design-systems-25dd82d58421
  - Quote: *"We've spent so much effort trying to get design out of our variables… I felt instantaneously attracted to the idea of putting design back in."*
  - Tips include: options-then-decisions; expand beyond color/type; meaningful scales; the "used 3 times" curation criterion; graduate tokens out of components; JSON for portability, YAML for human management; automate documentation.

- **"Naming Tokens in Design Systems"** — Medium/EightShapes, **2020-10-15**. The four-level taxonomy: **Base** (category + concept + property), **Modifier** (variant/state/scale/mode), **Object** (component/element/group), **Namespace** (system/theme/domain). URL: https://medium.com/eightshapes-llc/naming-tokens-in-design-systems-9e86c7444676
  - Quotes: *"Avoid homonyms."* / *"Flexibility comes at the expense of specificity and — by extension — potentially precision of application."* / *"Start within, then promote across components"* / *"Include only the levels needed to sufficiently describe and distinguish purposeful intent."*

- **"Team Models for Scaling a Design System"** — Medium/EightShapes, **2015-09-17**. Introduced the **Solitary / Centralized / Federated** trio that became the field's default vocabulary for DS org structure. URL: https://medium.com/eightshapes-llc/team-models-for-scaling-a-design-system-2cf9d03be6a0

- **"Defining Design System Contributions"** — Medium/EightShapes, **2020-01-14**. Defines a contribution and sorts contributions by size: **fix → small enhancement → large enhancement → new feature**; large initiatives are *never* run as independent contributions. URL: https://medium.com/eightshapes-llc/defining-design-system-contributions-eb48e00e8898
  - Quote (definition): *"A design system contribution is…any proposal, design, code, documentation, or design asset of a new feature, enhancement, or fix completed by someone not on the system core team and released through the system for other people to reuse."*

- **"Component Specifications"** — Medium/EightShapes (the pre-data-era spec template article). The structural ancestor of the 2025 components-as-data work. URL: https://medium.com/eightshapes-llc/component-specifications-1492ca4c94c

- **"The Fallacy of Federated Design Systems"** — Medium, **2024-09-13**. Recants the binary framing of his own 2015 model. URL: https://medium.com/@nathanacurtis/the-fallacy-of-federated-design-systems-23b9a9a05542
  - Quotes: *"Positioning central versus federated as a mutually exclusive choice was a mistake."* / *"In my practice, successful design systems always have a central team and always seek the participation (and, if worth it, contribution) from a federated community."* / Federated "is not a choice, it's a facet."

- **_Modular Web Design_** (book, New Riders, 2009) and **_Design Systems Handbook_** (editor, 2017).

---

## Recent signals (all AFTER 2025-06-01 unless noted) — for `recent_signal_12mo`

1. **"Components as Data"** — Medium, **2025-09-23**. The thesis-setting article for his current frontier. URL: https://medium.com/@nathanacurtis/components-as-data-2be178777f21
   - *"A component definition in data is a structured description of a UI component expressed in a neutral format (like YAML or JSON)."*
   - *"My role is to architect how we record component decisions as structured data independent of any platform, including Figma."*
   - *"AI is everywhere, and it favors structured data. So express components that way."*
   - *"Data exposes errant design decisions, making components easier to audit."*
   - *"Starting with data and treating Figma assets as output rather than input."*
   - *"It's difficult to imagine returning to a time when I architected components only in a visual tool like Figma."*

2. **"Analysis of Variants"** — Medium, **2025-10-07**. Introduces the **Anova** plugin; argues for deterministic extraction over LLM guessing. URL: https://medium.com/@nathanacurtis/analysis-of-variants-9e440c30b93e
   - *"If we are to use components as data, how do we do it without losing or degrading it as data shifts back and forth across our tools?"*
   - On LLM unreliability: an LLM starting with an `Alert` component's `appearance` property "renamed options, added options, remove[d] options and renamed the property itself!"
   - *"The plugin extracts only the raw, intentional data directly from the asset. No guessing. No machine prediction."*

3. **SmashingConf Amsterdam 2026 — "Components as Data for Humans _and_ Machines"** — announced/listed on smashingconf.com, talk dated **Wednesday, June 15** (2026 program). URL: https://smashingconf.com/amsterdam-2026/speakers/nathan-curtis
   - Bio confirms current affiliation: "Founder and design systems consultant at Directed Edges."
   - Talk frames components as "intent recorded as data and managed through a lifecycle," and pushes a "component schema that machines love—one that is deterministic, complete, and succinct."
   - Also on the "Tokens, Tools, and Total Chaos" panel.

4. **Medium feed (2025-11 → 2026-05) — sustained shipping cadence.** From medium.com/@nathanacurtis, recent dated posts:
   - "Slots in Design Systems" — **2025-11-08**
   - "'Code Only' Props in Figma" — **2026-01-18**
   - "Figma Slots for Repeating Items" — **2026-01-23**
   - "Configuration Collapse" — **2026-02-27**
   - "Implementing Slots in a Figma Library" — **2026-03-02**
   - "Component Examples as Data" — ~**2026-05-27** ("5 days ago" relative to 2026-06-01 fetch)
   - URL: https://medium.com/@nathanacurtis

---

## Public stances (each with evidence URL)

1. **"Federated is not a choice, it's a facet."** Successful systems are always centralized AND federated; the 2015 either/or framing was a mistake. → https://medium.com/@nathanacurtis/the-fallacy-of-federated-design-systems-23b9a9a05542 (2024-09-13)
2. **Components should be defined as platform-agnostic structured data, with Figma as an output, not the source of truth.** → https://medium.com/@nathanacurtis/components-as-data-2be178777f21 (2025-09-23)
3. **Token names need a deliberate four-level taxonomy (namespace / object / base / modifier); include only the levels needed.** → https://medium.com/eightshapes-llc/naming-tokens-in-design-systems-9e86c7444676 (2020-10-15)
4. **Sort contributions by size; never run a catalog-wide initiative as a "contribution."** Small-and-quick contributions need automated, low-friction release; large ones need the full propose→design→code→doc→release workflow with core-team partnership. → https://medium.com/eightshapes-llc/defining-design-system-contributions-eb48e00e8898 (2020-01-14)
5. **Saying "no" is a core system-team skill — gate on shared need ("who else needs it?").** → https://www.knapsack.cloud/blog/nathan-curtis-co-founder-at-eightshapes-balancing-reuse-and-customization-in-ui-design (2023-12-13)
6. **Schemas for AI must be deterministic and complete; do not trust LLMs to author the canonical spec — extract it.** → https://medium.com/@nathanacurtis/analysis-of-variants-9e440c30b93e (2025-10-07)
7. **Put design back into the variables: tokens are named design decisions, not just CSS abstractions.** → https://medium.com/eightshapes-llc/tokens-in-design-systems-25dd82d58421 (2016-06-24)

---

## Pairs / conflict (ROSTER.md slugs, design-systems-interaction cell)

- **pairs_well_with:** `brad-frost` (Atomic Design — components/tokens vocabulary partner), `dan-mall` ("Design That Scales" — contribution & DS-ops pragmatics partner). Both per task brief; both real ROSTER slugs in the same cell.
- **productive_conflict_with:**
  - `adam-wathan` — utility-first (Tailwind) directly contests the semantic-token / named-component-API worldview Curtis advances. Real ROSTER slug (cross-listed from Engineering into this cell). Strong, documented tension: Wathan's "semantic class names are the wrong abstraction" vs. Curtis's "tokens are named design decisions."
  - `josh-clark` — "Designing for Touch" / AI-in-design-patterns; Clark leans into generative/AI-fluid interfaces, where Curtis insists on deterministic, extracted, human-curated structured data over machine prediction. Real ROSTER slug, same cell. Productive friction on how much to trust AI generation.

---

## Source URLs (all real, verified during this session)

1. https://eightshapes.com/nathan-curtis/
2. https://www.directededges.com/nathan-curtis
3. https://smashingconf.com/amsterdam-2026/speakers/nathan-curtis
4. https://medium.com/@nathanacurtis
5. https://medium.com/@nathanacurtis/components-as-data-2be178777f21
6. https://medium.com/@nathanacurtis/analysis-of-variants-9e440c30b93e
7. https://medium.com/@nathanacurtis/the-fallacy-of-federated-design-systems-23b9a9a05542
8. https://medium.com/eightshapes-llc/naming-tokens-in-design-systems-9e86c7444676
9. https://medium.com/eightshapes-llc/tokens-in-design-systems-25dd82d58421
10. https://medium.com/eightshapes-llc/defining-design-system-contributions-eb48e00e8898
11. https://medium.com/eightshapes-llc/team-models-for-scaling-a-design-system-2cf9d03be6a0
12. https://medium.com/eightshapes-llc/component-specifications-1492ca4c94c
13. https://www.knapsack.cloud/blog/nathan-curtis-co-founder-at-eightshapes-balancing-reuse-and-customization-in-ui-design
14. https://www.linkedin.com/in/nathanacurtis/

---

## Confidence

**0.95.** Identity is unambiguous (single well-known public figure, consistent first-party sources). Profile depth is high: 14 real sources, 4+ distinct recent signals dated after 2025-06-01, every stance individually cited. The one moving part is the very recent (2026) Anthropic-of-design-systems-equivalent: his AI/components-as-data direction is fresh and evolving, so 2026+ stances should be re-verified at next sync.
