# Bjarne Stroustrup — Research Notes

**Slug:** bjarne-stroustrup
**Cell:** languages-runtimes (engineering team)
**Cell role:** lead-driver
**Researched:** 2026-05-30
**Researcher:** Claude (engineering persona build, wave E6)

These are the raw, dated findings behind `superintelligence/engineering/personas/bjarne-stroustrup.md`.
Do not re-crawl on re-synthesis; update in place with new dated signals.

---

## Identity confirmation (high confidence)

- **Real name:** Bjarne Stroustrup. Pronounced roughly "B-yar-neh Strov-strup."
- **Born:** 30 December 1950, Aarhus, Denmark. (Wikipedia)
- **Subject is correctly identified.** He is unambiguously the creator of C++. No disambiguation needed.

### Correction logged — nationality / "Danish vs American"
The task framing implies a US-anchored identity (Columbia / Morgan Stanley). Primary sources are more precise:
- Wikipedia classifies him as a **Danish computer scientist**, born in Aarhus.
- His own bio (stroustrup.com/bio.html) says he "lives in New York City" but does **not** explicitly assert US citizenship or naturalization.
- He has lived and worked in the US since 1979 (Bell Labs, New Jersey), so he is commonly described as **Danish-American** by long residence. I have written the profile as "Danish-American (Denmark-born, US-based since 1979)" rather than asserting naturalization, which I could not verify from a primary source. This is the safest factual framing.

---

## Biography & career timeline (Wikipedia, stroustrup.com/bio.html, Columbia Engineering, AU alumni interview)

- **Education:**
  - Aarhus University, 1969–1975 — Candidatus Scientiarum (cand. scient.) in mathematics with computer science.
  - University of Cambridge, **PhD 1979** — dissertation on distributed computing, supervised by **David Wheeler**.
- **Career:**
  - **1979–2002: Bell Labs** (Murray Hill, NJ). Member of technical staff → head of Large-scale Programming Research department. **Bell Labs Fellow (1993)**, **AT&T Fellow (1996)**. This is where C++ ("C with Classes," begun 1979) was created and standardized.
  - **2002–2014: Texas A&M University** — College of Engineering Chair Professor in CS; **University Distinguished Professor (in perpetuity) since 2011**.
  - **January 2014 – April 2, 2022: Morgan Stanley** (NYC) — Technical Fellow and Managing Director in the technology division; concurrently **visiting professor at Columbia**.
  - **July 2022 – present: Columbia University** — full Professor of Computer Science.
  - **Since 2021:** Technical Advisor to Metaspex (C++ business applications).
- **Major awards:**
  - Charles Stark Draper Prize (2018)
  - Computer Pioneer Award (IEEE, 2018)
  - Computer History Museum Fellow (2015)
  - Dahl–Nygaard Prize (2015)
  - Grace Murray Hopper Award (ACM, 1993)

Source URLs:
- https://en.wikipedia.org/wiki/Bjarne_Stroustrup
- https://www.stroustrup.com/bio.html
- https://www.engineering.columbia.edu/faculty-staff/directory/bjarne-stroustrup

---

## Canonical works / publications

- **The C++ Programming Language** (4 editions; the definitive reference).
- **The Design and Evolution of C++** ("D&E", 1994) — the rationale book; how and why C++ evolved.
- **A Tour of C++** (3 editions) — the concise modern primer.
- **Programming: Principles and Practice Using C++** (2 editions) — his teaching text.
- **C++ Core Guidelines** (with Herb Sutter) — https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines — the living, tool-enforceable rule set aimed at "statically type-safe and resource-safe C++."
- "A brief introduction to C++'s model for type- and resource-safety" — https://www.stroustrup.com/resource-model.pdf
- "21st Century C++" — CACM blog + paper P3650R0 (2025-03-06). PDF: https://www.stroustrup.com/21st-Century-C++.pdf

---

## Core technical doctrine (well-established, multiple sources)

- **Zero-overhead principle:** "What you don't use, you don't pay for" and "what you do use, you couldn't hand-code any better." This is the central design law of C++ and the line he refuses to cross for safety. (C++ Core Guidelines intro; widely attributed.)
- **RAII (Resource Acquisition Is Initialization):** tie every resource to an object's lifetime — acquire in the constructor, release in the destructor. Gives deterministic cleanup with zero runtime overhead and no garbage collector. He considers RAII the foundation of safe modern C++.
- **Design aim (from his bio):** "to give meaning to 'modern C++' as a completely type-safe and resource-safe language and help users to use it as such."
- **"Never use a raw pointer as a resource handle"** — direct advice from the May 2025 devclass interview.
- **"95 to 99 percent of your loops are: do everything over this container"** — argues for range-based for. (devclass, 2025-05-09)

---

## THE MEMORY-SAFETY / RUST / GOVERNMENT DEBATE (the live 2024–2026 story)

This is the spine of his "lead-driver" role in the languages-runtimes cell.

### Government pressure timeline
- ~2022: **NSA** publishes guidance flagging C and C++ as memory-unsafe; recommends memory-safe languages.
- **February 2024:** White House **ONCD** report calls for memory-safe languages.
- **October 2024:** **CISA** "Product Security Bad Practices" report. Sets a **January 1, 2026** deadline: manufacturers of memory-unsafe products should adopt memory-safe languages or publish a **memory-safety roadmap**.
- Note (from The Register, 2025-03-02): the new US administration "removed everything from the White House web site and fired most of the CISA people who worked on memory safety" — so the political pressure partly receded even as the technical debate continued.

### Stroustrup's rebuttal — verbatim quotes

**InfoWorld, 2024-03-18** (rebutting the White House warning):
> "I find it surprising that the writers of those government documents seem oblivious of the strengths of contemporary C++ and the efforts to provide strong safety guarantees."
> "Improving safety has been an aim of C++ from day one and throughout its evolution."
> "Much quality C++ is written using techniques based on RAII (Resource Acquisition Is Initialization), containers, and resource management pointers rather than conventional C-style pointer messes."
> "There are two problems related to safety. Of the billions of lines of C++, few completely follow modern guidelines, and peoples' notions of which aspects of safety are important differ."
- URL: https://www.infoworld.com/article/2336463/c-plus-plus-creator-rebuts-white-house-warning.html

**The Register, 2025-03-02** ("calls for action to address 'serious attacks'"):
- In a February 7, 2025 note supporting Profiles: *"This is a call to urgent action partly in response to unprecedented, serious attacks on C++."*
> "I feel strongly about this. Please don't be fooled by my relatively calm language."
- On the SG23 mailing list, **2025-02-13**, regarding CISA's 2026 deadline: *"I consider that a credible threat."*
- URL: https://www.theregister.com/2025/03/02/c_creator_calls_for_action/

### Profiles — his proposed solution (vs Rust)
- **Profiles** = sets of rules that, when followed, deliver specific, named safety guarantees enforced by the ISO standard via static analysis + minimal runtime checks. Initial profiles cluster around **type safety, bounds/range, and lifetime** (also stated as type_safety / range / arithmetic in some drafts).
- His framing: **"I want this set of guarantees and it will then be enforced."** (paraphrased core of Profiles; quoted ~May 2025)
- Key philosophical claim: **there is more than one kind of safety**; memory safety is one of "on the order of a dozen" safety concerns. He objects to C++ being lumped with C.
- The **"irreconcilable design disagreement" with Rust**: Rust's model uses **function coloring** (safe/unsafe annotations restricting what you can call); the C++ committee explicitly wants to **avoid requiring a safe/pure function annotation**. (The Register, 2025-09-16; the phrase "irreconcilable design disagreement" is attributed in the coverage to the Safe C++ side / committee dynamics, with Stroustrup on the Profiles side.)

### Safe C++ vs Profiles — the committee decision
- **Safe C++** (Sean Baxter, author of the Circle compiler) proposed a Rust-style borrow-checked subset with a safe `std2` library.
- The **C++ Safety and Security working group (SG23)** voted to **prioritize Profiles**. Reported vote tallies (InfoWorld 2025-09-30): **19 for Profiles, 9 for Safe C++, 11 for both, 6 neutral.** EWG straw poll (The Register 2025-09-16): **20/45 encouraged Baxter's paper, 30/45 encouraged Profiles, 6 neutral.**
- **Safe C++ work discontinued within ISO** — confirmed by C++ Alliance CEO Harry Bott to InfoWorld, **2025-09-29/30**: "Yes, work on Safe C++ within ISO has been discontinued."
- Baxter (2025-06): *"The Rust safety model is unpopular with the committee. Further work on my end won't change that. Profiles won the argument."*
- Baxter's skepticism about Profiles: *"I would have implemented profiles if profiles had a chance of working. But they will not ever work."* and "The whole Standard Library is unsafe. I proposed a rigorously safe std2, and that was rejected."
- **Stroustrup, 2025-09-24:** disputed that Safe C++ was a true C++ subset, claiming it eliminated "almost all good/safe C++ code."
- URLs:
  - https://www.theregister.com/2025/09/16/safe_c_proposal_ditched/
  - https://www.infoworld.com/article/4065702/safe-c-proposal-for-memory-safety-flames-out.html

### C++26 outcome
- Profiles **did not make C++26.** Stroustrup, ~May 2025: **"The sad thing is, the standards committee got confused and did not guarantee that this would be in C++ 26."** Work continues toward later standards (C++29 direction papers, Feb 2026).

---

## RECENT SIGNALS (dated AFTER 2025-05-30 — for recent_signal_12mo)

From his official WG21 papers list (https://www.stroustrup.com/WG21.html) and press:

1. **P3704R0 "What are profiles?"** — 2025-05-19. (Just BEFORE the 2025-05-30 window cutoff by 11 days — NOT eligible as a "recent" signal but useful context.)
2. **InfoWorld "Safe C++ proposal for memory safety flames out"** — 2025-09-30. Safe C++ discontinued in ISO; Profiles win. Stroustrup central advocate. URL: https://www.infoworld.com/article/4065702/safe-c-proposal-for-memory-safety-flames-out.html  ✅ post-2025-05-30
3. **The Register "Safe C++ proposal all but abandoned in favor of profiles"** — 2025-09-16. Vote tallies, "irreconcilable design disagreement," C++26 quote. URL: https://www.theregister.com/2025/09/16/safe_c_proposal_ditched/  ✅ post-2025-05-30
4. **P4023R0 "Strategic Direction for AI in C++: Governance, and Ecosystem"** — 2026-02-22. Co-authors: Wong, Garland, McKenney, Orr, Stroustrup, Vandevoorde. Stroustrup now co-steering C++'s official AI strategy. URL: https://www.stroustrup.com/WG21.html  ✅ post-2025-05-30
5. **D3984R0 "A type-safety profile"** — 2026-02-22. Concrete profiles work continuing toward C++29. URL: https://www.stroustrup.com/WG21.html  ✅ post-2025-05-30
6. **P2000R5 "Direction for ISO C++"** + **P5000R0 "Direction for ISO C++29"** — 2026-02-18/23. Long-range steering documents he co-authors. URL: https://www.stroustrup.com/WG21.html  ✅ post-2025-05-30

These give >=3 qualifying recent signals comfortably (items 2,3,4,5,6 all post-2025-05-30).

---

## AI stance (devclass, 2025-05-09 — note: just before window, used as context not a "recent signal")

> "Yes, I do have serious concerns. I'm not saying it won't help, but it does have a tendency of guiding people towards things which everybody used to do."
- Fears practitioners become "so used to having it done for them" that they can no longer "detect problems."
- On language fragmentation: "instead of getting one language that's too big, like C++, we will get 10 languages that are all insufficient."
- URL: https://devclass.com/2025/05/09/interview-bjarne-stroustrup-on-21st-century-c-ai-risks-and-why-the-language-is-hard-to-replace/

The Feb 2026 P4023R0 AI-governance paper shows this concern translating into formal committee steering — good throughline.

---

## ROSTER cross-references (verified against superintelligence/engineering/ROSTER.md)

- **pairs_well_with** — real engineering-team slugs in the same/adjacent cells:
  - `anders-hejlsberg` (languages-runtimes; pragmatic incrementalist on type systems / TS)
  - `chris-lattner` (languages-runtimes; LLVM/Clang — tooling that enforces guidelines)
  - `guido-van-rossum` (languages-runtimes; BDFL-style long-term language stewardship)
  - `colm-maccarthaigh` (cloud-architecture; formal verification of safety properties — sympathetic to "prove the guarantee" over "rewrite the language")
- **productive_conflict_with** — real slugs, genuine disagreement:
  - `graydon-hoare` (Rust creator) — the central Rust-vs-C++ / function-coloring-vs-profiles axis.
  - `rich-hickey` (Clojure; "Simple Made Easy") — Hickey would call C++ the archetype of incidental complexity; Stroustrup defends the necessity of multi-paradigm breadth. Direct philosophical clash.
  - `john-carmack` (systems-programming) — Carmack's pragmatism about rewriting for simplicity / his openness to other languages vs Stroustrup's "C++ is hard to replace because it works across diverse domains."

All slugs above confirmed present in ROSTER.md.

---

## All source URLs (>=8, several post-2025-05-30)

1. https://en.wikipedia.org/wiki/Bjarne_Stroustrup
2. https://www.stroustrup.com/bio.html
3. https://www.stroustrup.com/WG21.html  (Feb 2026 papers — recent)
4. https://www.engineering.columbia.edu/faculty-staff/directory/bjarne-stroustrup
5. https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
6. https://www.infoworld.com/article/2336463/c-plus-plus-creator-rebuts-white-house-warning.html  (2024-03-18)
7. https://www.theregister.com/2025/03/02/c_creator_calls_for_action/  (2025-03-02)
8. https://www.theregister.com/2025/09/16/safe_c_proposal_ditched/  (2025-09-16, recent)
9. https://www.infoworld.com/article/4065702/safe-c-proposal-for-memory-safety-flames-out.html  (2025-09-30, recent)
10. https://devclass.com/2025/05/09/interview-bjarne-stroustrup-on-21st-century-c-ai-risks-and-why-the-language-is-hard-to-replace/  (2025-05-09)
11. https://www.stroustrup.com/21st-Century-C++.pdf  (P3650R0, 2025-03-06)
12. https://thenewstack.io/can-c-be-saved-bjarne-stroustrup-on-ensuring-memory-safety/
13. https://www.stroustrup.com/resource-model.pdf
14. https://isocpp.org/files/papers/P3650R0.pdf

Confidence: 0.95 (identity certain; doctrine well-documented; recent signals abundant and primary-sourced). Only soft spot is exact citizenship wording, handled conservatively above.
