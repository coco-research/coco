# Eric Evans — Research Notes

**Subject:** Eric Evans — author of *Domain-Driven Design: Tackling Complexity in the Heart of Software* (2003); founder of Domain Language, Inc.
**Slug:** `eric-evans`
**Researched:** 2026-05-30
**Cell:** architecture-testing-craft (engineering team) · cell_role: specialist
**Status determination:** **active** — three-plus genuinely recent signals found (post-2025-05-30), so the `status: archetype` fallback in the brief is NOT triggered. Documented below.

---

## Status decision (active, not archetype)

The brief flagged Evans as "lower-profile (occasional DDD Europe keynotes)" and instructed: if fewer than three genuinely recent (post-2025-05-30) signals exist, set `status: archetype`. Research found **at least four** qualifying recent signals, so the persona is set to **active**:

1. **DDD Europe 2026 — Opening Keynote + interview with Martin Fowler** (speaker page live; the lineup announcement blog "Martin Fowler to keynote at DDD Europe 2026" is dated 2026-03-09). Conference: Antwerp, workshops June 8-10, conference June 10-12, 2026. https://2026.dddeurope.com/speakers/eric-evans/
2. **"Context Mapping with an AI-based Component"** — article, 2026-01-06. https://www.domainlanguage.com/articles/context-mapping-an-ai-based-component/
3. **"Interview: Strategic Design today (and AI)"** with Marco Heimsoeth (KanDDDinsky organizer) — 2025-09-24. https://www.domainlanguage.com/articles/interview-strategic-design-2025-and-ai/
4. **"AI Components for a Deterministic System (An Example)"** — article, 2025-08-24. https://www.domainlanguage.com/articles/ai-components-deterministic-system/

All four are dated after 2025-05-30. Evans is demonstrably still publishing and speaking, so `recent_signal_12mo` is populated and `persistent_signals` is omitted.

---

## Correction to brief assumptions

- **Book publication year.** The brief says *Domain-Driven Design* (2003). Wikipedia confirms the book was published **August 22, 2003** by Addison-Wesley. (It is frequently miscited as 2004 — the 2003 date in the brief is correct.) No correction needed; flagging because the 2004 date circulates widely.
- **"Occasional DDD Europe keynotes."** Accurate framing, but understates current activity. Beyond keynotes, Evans is actively writing (2025-2026 article series on AI + strategic design), running paid workshops (Berlin Oct 2025; Antwerp masterclass June 2025), and maintaining the DDD eLearn video course. He is lower-profile than (say) Martin Fowler but is not dormant.

---

## Biographical / foundational facts

- Founder and principal of **Domain Language, Inc.**, a small consultancy focused on Domain-Driven Design.
- Author of the foundational 2003 "Blue Book": *Domain-Driven Design: Tackling Complexity in the Heart of Software* (Addison-Wesley, ISBN 9780321125217). Published 2003-08-22.
- Coined / codified the canonical DDD vocabulary: **ubiquitous language, bounded context, context map, aggregate (with aggregate root), entity, value object, anti-corruption layer, published language, shared kernel, customer/supplier, conformist.**
- DDD eLearn: 5+ hours of edited video course, self-guided, targeted at architects and senior developers. Traditional in-person training currently routed through partners.
- Wikipedia notes there is no standalone biographical Wikipedia page for Evans himself; the DDD concepts page is the canonical reference.

Source: https://en.wikipedia.org/wiki/Domain-driven_design ; https://www.domainlanguage.com/

---

## Bounded contexts vs. microservices (the load-bearing recent-decade stance)

From InfoQ coverage of his **DDD Europe 2019** talk "Defining Bounded Contexts" (https://www.infoq.com/news/2019/06/bounded-context-eric-evans/) and his **GOTO 2015 / DDD Exchange 2015** talk "DDD & Microservices: At Last, Some Boundaries!" (https://www.infoq.com/news/2015/06/dddx-microservices-boundaries/ ; video https://www.youtube.com/watch?v=yPvef9R3k-M):

- **Key quote (paraphrased by InfoQ):** the belief that "a microservice is a bounded context" is "an oversimplification." A microservice *can* be a good bounded context, but a service is not *always* a bounded context.
- Evans enumerates multiple bounded-context types around microservices:
  1. **Service Internal** — how one autonomous service works, isolated, owned by one team.
  2. **API of Service** — how services communicate; teams design/adapt to differing APIs.
  3. **Cluster of co-designed services** — several services designed to work together form one bounded context; the cluster's internal model may differ from the API model.
  4. **Interchange Context** — the interaction layer itself is a bounded context, modeling "messages, schemas and protocols."
  5. (also discussed) **Exposed Legacy Asset** — a legacy system fronted by a microservice-looking interface.
- **Quote:** microservices are "the biggest opportunity, but also the biggest risk we have had for a long time." He cautions against adopting them for bandwagon reasons rather than genuine business need.
- He warns prescriptive guidance like "each microservice is a bounded context" diverges from the DDD "sweet spot."
- DDD summarized as: focus on the **core domain**, explore models **collaboratively**, maintain **ubiquitous language** within **bounded contexts**.

Related: "Eric Evans: DDD is Not for Perfectionists" (InfoQ 2017, https://www.infoq.com/news/2017/02/ddd-perfectionists/) and "Eric Evans Says Domain-Driven Design (DDD) Isn't Done" (InfoQ 2018, https://www.infoq.com/news/2018/09/ddd-not-done/) — Evans explicitly frames DDD as an evolving, non-dogmatic discipline.

---

## AI / LLM strategic-design stances (2025-2026 — the freshest material)

### "My AI Learning Journey" — DDD Europe 2025 talk
https://2025.dddeurope.com/program/my-ai-learning-journey/ ; video https://www.youtube.com/watch?v=cR7joaBOXhc

- Two-year self-directed deep dive into AI/LLMs: prompt-engineering experiments, fine-tuning small models, textbooks and papers.
- Explored "without preconceptions, avoiding imposing existing frameworks prematurely" — samples multi-head attention ("transformers") and latent-space dynamics.
- Includes "a little" mathematics deliberately "to avoid relying on metaphors rather than substance."
- "[I] will discuss a few connections with DDD that occur to me, still tentatively." Believes the tech "aligns well with domain-driven practitioners tackling complex problems through abstractions and language."
- NOTE: the program page does NOT mention Anthropic by vendor name — earlier search summary's "companies like Anthropic" framing was third-party blog color, not Evans's own words. Logged so the persona does not over-claim a vendor stance.

### "AI Components for a Deterministic System (An Example)" — 2025-08-24
https://www.domainlanguage.com/articles/ai-components-deterministic-system/

Direct quotes:
- "How do we wrangle behavior that is intrinsically non-deterministic so that it can be used in structured, deterministic systems?"
- "Assigning categories is a classification task, which LLMs are good at. Creating the categorization scheme is a modeling task, which is fundamentally different."
- On NAICS codes: "These classification schemes have been used widely and shown to be broadly applicable. This fits the 'Published Language' pattern from DDD."
- "Using a standard classification also takes away our flexibility to choose our own model. Depending on the application, that may be an unacceptable tradeoff, but watch out for our bias toward believing we need a custom model!"
- "I'd suggest having humans drive the modeling in an exploratory, iterative process." (when classification is a core differentiator)

### "Context Mapping with an AI-based Component" — 2026-01-06
https://www.domainlanguage.com/articles/context-mapping-an-ai-based-component/

Key arguments + quotes:
- **"LLMs are bounded contexts too"** — each with its own language (natural-language prompts), consistency model (probabilistic), and interface contract.
- **"Anticorruption layers are essential for AI integration."** The impedance mismatch between deterministic apps and probabilistic AI requires real translation: "This isn't just JSON parsing – it's bridging between fundamentally different computational paradigms."
- Context maps must document **actual** architecture, not aspirational designs — explicit warning against drawing maps showing preferred refactorings not yet implemented. ("Context maps evolve with understanding. The initial simple map was useful for getting started, but iterative refinement captured more insight into the subtle complexity.")
- Re-uses Published Language pattern (NAICS) for clarity over custom taxonomies.

### Domain Language current focus (homepage)
https://www.domainlanguage.com/
- "helping organizations thoughtfully integrate AI technologies like LLMs into domain-rich systems while preserving the design integrity that delivers business value."

---

## Pairs / conflicts (from ROSTER.md, architecture-testing-craft cell)

- **pairs_well_with (per brief):** martin-fowler (DDD Europe 2026 joint interview; Fowler wrote the foreword-adjacent endorsement and popularized DDD via bliki), sam-newman ("Building Microservices" — bounded contexts → service boundaries lineage), gregor-hohpe (enterprise integration patterns / interchange context / architect elevator).
- **productive_conflict_with (real ROSTER slugs):**
  - `dhh` — David Heinemeier Hansson, "majestic monolith," explicitly anti-microservices; sharpens Evans on whether bounded contexts justify distribution.
  - `sam-newman` — productive *and* conflicting: Newman is a natural pair but pushes harder/faster on decomposition than Evans, who counsels caution ("biggest risk we've had"). Listed as a pair per brief; the sharper distribution-pace tension goes to dhh + michael-truell.
  - `michael-truell` — Cursor CEO; represents AI-codegen-first development that can erode the deliberate, human-driven modeling Evans insists on ("have humans drive the modeling"). Genuine tension over where AI belongs in the design loop.
  - Considered but not used: andrej-karpathy (AI team cross-list) — adjacent on "LLMs as bounded contexts" but more amplifying than conflicting.

---

## All source URLs collected

1. https://www.domainlanguage.com/
2. https://www.domainlanguage.com/author/eric/
3. https://www.domainlanguage.com/articles/context-mapping-an-ai-based-component/ (2026-01-06)
4. https://www.domainlanguage.com/articles/interview-strategic-design-2025-and-ai/ (2025-09-24)
5. https://www.domainlanguage.com/articles/ai-components-deterministic-system/ (2025-08-24)
6. https://2026.dddeurope.com/speakers/eric-evans/
7. https://2026.dddeurope.com/blog/martin-fowler-to-keynote-at-ddd-europe-2026/ (2026-03-09; index 404'd on direct fetch but listed on blog index)
8. https://2025.dddeurope.com/program/my-ai-learning-journey/
9. https://www.youtube.com/watch?v=cR7joaBOXhc (My AI Learning Journey, DDD Europe 2025)
10. https://www.infoq.com/news/2019/06/bounded-context-eric-evans/
11. https://www.infoq.com/news/2015/06/dddx-microservices-boundaries/
12. https://www.youtube.com/watch?v=yPvef9R3k-M (DDD & Microservices: At Last, Some Boundaries! — GOTO 2015)
13. https://www.infoq.com/news/2018/09/ddd-not-done/
14. https://www.infoq.com/news/2017/02/ddd-perfectionists/
15. https://en.wikipedia.org/wiki/Domain-driven_design
16. https://www.amazon.com/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215
