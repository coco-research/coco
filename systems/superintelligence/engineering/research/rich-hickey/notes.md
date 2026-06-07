# Rich Hickey — Research Notes

**Researched:** 2026-05-30
**Researcher:** Engineering Super Intelligence Team build (Wave E5, languages-runtimes)
**Slug:** rich-hickey
**Cell / role:** `languages-runtimes` / `lead-driver`
**Status decision:** `archetype` (see "Recency finding" below)

---

## Identity (very high confidence)

- **Real name:** Richard Hickey (publicly known as Rich Hickey).
- **Anchor:** Creator and original designer of the **Clojure** programming language (first public release 2007) and architect of **Datomic** (launched 2012). Author of the foundational software-design talks "Simple Made Easy," "The Value of Values," "Hammock Driven Development," "Are We There Yet?," "Spec-ulation," and "Maybe Not."
- **Career arc:** ~25+ years across scheduling systems, broadcast automation, audio analysis, database design, and machine listening before Clojure. Spent roughly 2.5 years (much of it unpaid, funded partly by a self-described two-year sabbatical) developing Clojure before its 2007 release.
- **Companies:** Founded **Cognitect** (incorporated 2012 alongside the Datomic launch; he served as CTO ~2013–2020). **Nubank** — the world's largest independent digital bank, which runs core infrastructure on Clojure and Datomic — **acquired Cognitect in 2020** to steward Clojure's ongoing development. Hickey was a **Distinguished Engineer at Nubank until August 2023.** Earlier he worked on **dotLisp** (a .NET-based Lisp) before Clojure. Earlier still, he ran **Metadata Partners**.
- **LinkedIn self-description:** "Author of Clojure and architect of Datomic."

Identification is **unambiguous** — single consistent public figure across Wikipedia, ACM Digital Library (HOPL IV author), InfoQ, clojure.org, LinkedIn, and the talk-transcript archives. Confidence on identity: very high.

---

## Recency finding — WHY status: archetype (IMPORTANT)

The task brief flagged that Hickey is "famously low-profile and rarely publishes lately" and instructed: search hard for any post-2025-05-30 signal; if 3 genuinely recent ones cannot be found, set `status: archetype` with `persistent_signals` and document it.

**Finding:** Hickey **retired from commercial software development in August 2023** (Wikipedia; corroborated across sources). He "maintains a relatively low public profile since retiring." He has not published a new technical thesis, essay, or design talk since roughly **2018** ("Maybe Not," Clojure/Conj 2018). His public theses — Simple vs Easy, the Value of Values, Hammock-Driven Development, complecting — date from 2009–2018 and are still industry-canonical references in 2026.

There **are** a handful of genuinely recent, datable signals after 2025-05-30, but they are **ceremonial / community appearances**, not new positions:

1. **Clojure/Conj 2025 opening remarks** — recorded **2025-11-13** in Charlotte, NC; video on the ClojureTV YouTube channel (`https://www.youtube.com/watch?v=MLDwbhuNvZo`). Conference-opening remarks, not a technical keynote.
2. **Clojure Documentary trailer** — clojure.org news item dated **2026-03-26** (`https://clojure.org/news/2026/03/26/documentary_trailer`), announcing an April 16, 2026 premiere.
3. **"Clojure: The Documentary"** — premiered **2026-04-16**; clojure.org documentary page published **2026-05-28** (`https://clojure.org/about/documentary`). Hickey is a primary subject alongside Alex Miller and Stuart Halloway. Funded by Nubank. The film is *about* his past work; it is not new output from him.
4. **Clojure 1.12.x maintenance releases through 2025** (1.12.1 June 2025, 1.12.2 Aug 2025, 1.12.3 Sept 2025, 1.12.4 Dec 2025) — these are stewarded by the Clojure Team (Alex Miller et al.) under Nubank; Hickey's direct involvement post-retirement is governance-level / light, not authorial.

**Decision:** Because the recent signals are ceremonial and Hickey is explicitly **retired and no longer publicly publishing new ideas**, the honest classification is `status: archetype` — exactly the case the schema describes ("no longer publishing; profile is drawn from canonical published work"). This mirrors the precedent set for `cindy-sridharan`, `brian-kernighan`, and `sanjay-ghemawat` in this same roster. We set `recent_signal_12mo: []` and populate `persistent_signals` (>=5) with his durable talks/positions, while explicitly logging the three recent ceremonial signals here in notes so future re-syntheses do not re-crawl.

**Assumption correction:** The brief's default framing leaned toward possibly `active`. The evidence (Aug 2023 retirement; last substantive talk 2018) does not support `active`. Corrected to `archetype`, documented here per the brief's instruction to "correct wrong assumptions; log in notes.md."

---

## Canonical works / talks (verified titles, years, URLs)

| Title | Kind | Year/Venue | URL |
|---|---|---|---|
| Simple Made Easy | talk | 2011, Strange Loop | https://www.infoq.com/presentations/Simple-Made-Easy/ |
| The Value of Values | talk | 2012, JaxConf | https://www.infoq.com/presentations/Value-Values/ |
| Are We There Yet? | talk | 2009, JVM Language Summit | https://www.infoq.com/presentations/Are-We-There-Yet-Rich-Hickey/ |
| Hammock Driven Development | talk | 2010, Clojure/Conj | https://www.youtube.com/watch?v=f84n5oFoZBc |
| Design, Composition and Performance | talk | 2013 | https://www.infoq.com/presentations/Design-Composition-Performance/ |
| The Language of the System | talk | 2012 | (ClojureTV / Clojure/Conj) |
| Spec-ulation Keynote | talk | 2016, Clojure/Conj | https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/Spec_ulation.md |
| Effective Programs — 10 Years of Clojure | talk | 2017, Clojure/Conj | https://2017.clojure-conj.org/rich-hickey/ |
| Maybe Not | talk | 2018, Clojure/Conj | https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/MaybeNot.md |
| A History of Clojure | paper | 2020, ACM PACMPL HOPL IV, Article 71, 46pp | https://dl.acm.org/doi/10.1145/3386321 |
| Clojure (the language) | repo | first release 2007 | https://clojure.org/ |
| Datomic (the database) | product | launched 2012 | https://www.infoq.com/presentations/The-Design-of-Datomic/ |

Talk transcripts archive (community): https://github.com/matthiasn/talk-transcripts/tree/master/Hickey_Rich

---

## Key theses, positions, and quotes (for voice + public_stances)

### Simple vs Easy (Simple Made Easy, 2011) — the central thesis
- **Simple** is objective: it is the opposite of *complex*. The Latin root is *sim-plex* = "one fold / one braid / one twist." A thing is simple if it is about one role, one task, one concept, one dimension — NOT interleaved with others.
- **Easy** is subjective and relative: it is the opposite of *hard*. "Easy" means *near* — near to hand (installed, available), near to our understanding/skill set, near our capabilities. Easy is about familiarity, not quality.
- **Complect** = to braid/interleave/intertwine. The opposite is **compose** — to place together without intertwining. "Composing simple components is the way we write robust software." Modularity alone does not make a system simple; modules can still be highly *complected*.
- Famous lines:
  - "Simplicity is a prerequisite for reliability."
  - "Programmers know the benefits of everything and the tradeoffs of nothing."
  - "We can only juggle so many balls. … We can only consider a few things at a time. Intertwined things must be considered together."
  - On guardrail-driven development: "Guard rail programming. … Just bouncing off the guard rails is no way to get anywhere." (his critique of relying on tests/type-checkers to "drive" rather than thinking first).
- Source: https://www.infoq.com/presentations/Simple-Made-Easy/ ; transcript: https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/SimpleMadeEasy.md

### The Value of Values (2012) — immutability and data-orientation
- **Values are immutable.** "A value is something that doesn't change." Place-oriented programming (PLOP) — mutable in-place updates — is a relic of memory scarcity. Immutable values can be freely shared, cached, sent across the wire, and reasoned about because they never change underneath you.
- **Information is simple — don't ruin it.** "We should just use data … the data is the data." Wrapping plain data (facts) in method-laden objects complects information with behavior and machinery, making it harder to program against. Prefer maps/vectors/sets — generic data structures — over bespoke classes.
- State complects **value** and **time**; objects/identity complect **state, identity, and value**. Separating identity from a succession of values (Clojure's atoms/refs; Datomic's immutable facts) is the path to sane concurrency.
- Source: https://www.infoq.com/presentations/Value-Values/

### Hammock Driven Development (2010) — think before you type
- The hard part of software is *problem-solving*, and problem-solving is done by the mind, not the keyboard. Deliberately schedule "hammock time" — undistracted thinking, plus sleep on hard problems to recruit the background/subconscious mind.
- Separate the **input phase** (gather facts, read, study related problems and prior art) from the **solution phase**. Write down the problem and what you know about it; feed your background mind a well-formed question, then sleep on it.
- "Don't just do something, stand there." Analysis and design are real work even when no code is being produced.
- Source: https://www.youtube.com/watch?v=f84n5oFoZBc ; transcript: https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/HammockDrivenDev.md

### Spec-ulation (2016) — semantic versioning critique / never break callers
- "Don't break callers." Changing a function/API in an incompatible way is not a "version" — it is a *different* thing, so **rename it** rather than bumping a major version. Semantic versioning's "major bump = breaking change is OK" is, in his framing, broken: breakage is breakage.
- A dependency relationship is a *commitment*; growth (adding) and accretion are fine; breakage and relaxing requirements / strengthening promises are the only safe changes.
- Source: https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/Spec_ulation.md

### Maybe Not (2018) — optionality and partial information
- Critiques `Maybe`/`Optional` as a per-field type. Optionality is about *what is or isn't in an aggregate*, not about wrapping individual values; representing "this key might be absent" by changing every value's type is the wrong cut. Clojure spec separates the schema of a value from whether a given context requires that key.
- Source: https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/MaybeNot.md

### Are We There Yet? (2009) — Whitehead, state, and time
- Borrowing from Whitehead's process philosophy: identity is not a thing but a *series of causally-related states over time*. OO conflates identity, state, and value; functional + immutable + epochal time models separate them.
- Source: https://www.infoq.com/presentations/Are-We-There-Yet-Rich-Hickey/

### Datomic — immutability as a database
- "Datomic is a true record-keeping system: nothing is ever overwritten." Facts (datoms) are immutable and accreted with time; the database is a value you can hold, query as-of any point in time, and reason about without coordination. Reads need no coordination with writes.
- Source: https://www.infoq.com/presentations/The-Design-of-Datomic/

### A History of Clojure (2020, HOPL IV) — the design retrospective
- Documents the rationale, process, and people behind Clojure: a Lisp on the JVM, immutable persistent data structures, a small set of generic data structures, separation of identity and state, and a deliberate, conservative, no-breakage stewardship ethic.
- Source: https://dl.acm.org/doi/10.1145/3386321

---

## Roster cross-references (verified against ROSTER.md, 2026-05-30)

- **Cell:** `languages-runtimes` (cell #6). Listed there: "Rich Hickey — Clojure; 'Simple Made Easy,' value of values." `cell_role: lead-driver` per brief.
- **pairs_well_with (real ROSTER slugs):**
  - `pat-helland` (data-and-storage) — "Life Beyond Distributed Transactions," **immutability** and append-only/accretion-of-facts worldview; near-identical to Hickey's "nothing is ever overwritten" Datomic stance.
  - `martin-kleppmann` (data-and-storage) — DDIA, CRDTs, **local-first**, immutable event logs and dataflow; deeply compatible with values-over-places.
  - `john-carmack` (systems-programming) — long-form, think-deeply-before-coding, functional-style/immutability advocacy and a famed dislike of incidental complexity; cultural twin of Hammock-Driven Development.
- **productive_conflict_with (real ROSTER slugs):**
  - `anders-hejlsberg` (languages-runtimes) — static, gradual, tooling-rich type systems (C#, TypeScript). Hickey is famously skeptical of static type systems as a *design driver* ("guard-rail programming") and favors dynamic typing + spec + data. Direct, productive type-systems clash.
  - `bjarne-stroustrup` (languages-runtimes) — C++ multiparadigm, zero-cost abstractions, type-rich, performance-via-machinery. Hickey's "information is simple, don't ruin it with classes" and "simplicity is a prerequisite for reliability" cut against heavy type/abstraction machinery.
  - `dhh` (architecture-testing-craft) — Rails ergonomics and developer happiness optimize for *easy* (familiar, near-to-hand, conventions). Hickey's Simple-vs-Easy thesis is, almost word-for-word, a critique of optimizing for easy over simple; a clean, productive friction.
  - (Considered `kent-beck`/TDD: Hickey's "guard-rail programming" remark is a sharpening disagreement with test-driven design as a thinking substitute — noted in narrative, but kept primary conflicts as the type-systems pair + dhh for the cleanest cross-cell friction.)

---

## Sources (all real, verified 2026-05-30)

1. https://en.wikipedia.org/wiki/Rich_Hickey  (bio, retirement Aug 2023, Cognitect/Nubank, low profile — recency basis for archetype)
2. https://www.infoq.com/presentations/Simple-Made-Easy/  (Simple Made Easy, 2011 Strange Loop)
3. https://www.infoq.com/presentations/Value-Values/  (The Value of Values, 2012)
4. https://www.infoq.com/presentations/Are-We-There-Yet-Rich-Hickey/  (Are We There Yet?, 2009)
5. https://www.youtube.com/watch?v=f84n5oFoZBc  (Hammock Driven Development, 2010)
6. https://www.infoq.com/presentations/The-Design-of-Datomic/  (Datomic design / immutability)
7. https://dl.acm.org/doi/10.1145/3386321  (A History of Clojure, HOPL IV, 2020)
8. https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/Spec_ulation.md  (Spec-ulation, 2016)
9. https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/MaybeNot.md  (Maybe Not, 2018)
10. https://clojure.org/news/2026/03/26/documentary_trailer  (RECENT — documentary trailer, 2026-03-26)
11. https://clojure.org/about/documentary  (RECENT — documentary page, premiere 2026-04-16, published 2026-05-28)
12. https://www.youtube.com/watch?v=MLDwbhuNvZo  (RECENT — Clojure/Conj 2025 opening remarks, 2025-11-13)
13. https://clojure.org/about/history  (Clojure history)
14. https://www.linkedin.com/in/richhickey  (self-description: author of Clojure, architect of Datomic)
15. https://github.com/matthiasn/talk-transcripts/tree/master/Hickey_Rich  (talk transcript archive)
16. https://2017.clojure-conj.org/rich-hickey/  (Effective Programs — 10 Years of Clojure, 2017)
