# Michael Feathers — Research Notes

**Researched:** 2026-05-30
**Researcher:** Engineering Super Intelligence Team build (Wave E8, architecture-testing-craft cell)
**Subject confidence:** High. Single well-known public figure; no identity ambiguity. All facts cross-checked against primary sources (his own R7K site, Substack, LeanPub, conference speaker pages) plus secondary coverage (InfoQ, LeadDev, Tech Lead Journal).

---

## Identity and current role (verified)

- **Full name:** Michael C. Feathers.
- **Current role (2026):** Founder and Director of **R7K Research & Conveyance**, "a company specializing in software and organization design." Source: https://www.r7krecon.com/ and https://www.r7krecon.com/michael-feathers-bio
- **Career history:** Previously Chief Scientist at **Obtiva**; consultant with **Object Mentor International** (Robert C. Martin's firm). His bio states he has "consulted with hundreds of organizations" over 20+ years (some 2025 bios say "25 years") on "general software design issues, process change and code revitalization." Sources: r7krecon bio; YOW! Sydney/Melbourne 2025 speaker pages; LeanPub author page.
- **Most famous for:** Authoring *Working Effectively with Legacy Code* (Prentice Hall, 2004; Robert C. Martin Series). Source: https://www.amazon.com/Working-Effectively-Legacy-Michael-Feathers/dp/0131177052

## Canonical contributions (verified)

- **"Legacy code is code without tests."** His signature definition. Reaffirmed in the InfoQ 20-year retrospective (2021-03-15) and cited in the LeadDev Jan 2026 article. Sources: https://www.infoq.com/podcasts/working-effectively-legacy-code/ ; https://leaddev.com/ai/why-ai-both-problem-cure-legacy-code
- **Seams.** "A seam is a place in your code where you can separate things for testing without doing any extra work." Shirt-seam analogy. Source: InfoQ retrospective (2021-03-15).
- **Characterization tests.** "Tests that you write to understand the behavior of the system" — document actual behavior rather than validate correctness; can be disposable. Sources: InfoQ retrospective; Tech Lead Journal #195 (2024-10-14).
- **Dependency-breaking techniques.** In the InfoQ retrospective he says if rewriting the book he would cut the 24 dependency-breaking techniques down to "five or six most valuable ones"; his most-used remain **parameterized constructor** and **extract interface**. He'd also add more on org/communication structure (Conway), functional programming, and microservices separation. Source: InfoQ retrospective (2021-03-15).

## "Brutal Refactoring" — assumption check

- The user brief listed "Brutal Refactoring" as one of his works. **Status nuance:** *Brutal Refactoring: More Working Effectively with Legacy Code* (ISBN 9780321793201, Pearson/Addison-Wesley) has been a **long-announced / catalogued** title. Goodreads lists "First published February 19, 2016" (https://www.goodreads.com/book/show/25544117-brutal-refactoring) and it appears in many retailer catalogues (Amazon, Barnes & Noble, Booktopia). However, it is widely understood in the community to have been perpetually forthcoming rather than broadly released, and Feathers' own recent public output (the LeanPub *AI Assisted Programming* WIP, Substack, YOW talks) is where his active writing now lives. **Decision:** Include it in `canonical_works` as a listed/announced sequel, described accurately and without claiming it is a mainstream available bestseller. Not used as a recent signal.

## Error-handling / code-quality thinking (verified)

- **"Unconditional Code"** (GOTO Berlin 2017, GOTO Chicago 2018). Core thesis: error checks and conditional logic create "discontinuities that make reasoning difficult." Rather than *handle* errors, redesign so that "various error cases [become] impossible." Frames passing null / throwing as an **externality** — "you are forcing work on someone else." Discusses Null Object Pattern and domain extension. Sources: https://gotopia.tech/sessions/358/unconditional-code ; slides https://files.gotocon.com/uploads/slides/conference_9/358/original/goto_unconditional.pdf ; https://www.youtube.com/watch?v=AnZ0uTOerUI
- **"Toward a Galvanizing Definition of Technical Debt"** (2016-12-23): "Technical Debt is the refactoring effort needed to add a feature non-invasively." Ties to Open/Closed Principle. Source: https://michaelfeathers.silvrback.com/toward-a-galvanizing-definition-of-technical-debt

## AI + legacy code thinking (verified — this is his current frontier)

- **Forthcoming book:** *AI Assisted Programming*, published incrementally on LeanPub (https://leanpub.com/ai-assisted-programming). Release 2 (2024-08-20) went from 7 to 14 chapters, split into "Concepts" and "Techniques." Quote: "Writing a book incrementally and publicly puts you in a strange state of mind." Source: https://michaelfeathers.substack.com/p/ai-assisted-programming-release-2
- **Prompt-Hoisting** (2023-07-11): write executable tests that double as generation constraints AND verification — "When we use AI for code generation, quality assurance becomes much more important." Source: https://michaelfeathers.silvrback.com/prompt-hoisting-for-gpt-based-code-generation
- **"Prompting and the Probability Sandwich"** (2025-06-03): frames LLM codegen as a "probability sandwich" — deterministic input spec / probabilistic LLM middle / output code. Quotes: "English (or any other human language) is nowhere near as rigid or strict a language as a programming language." "LLMs are anything but deterministic. That's both a plus and a minus." Proposes standardizing on "a specification language with checkable syntax and defined semantics." Source: https://michaelfeathers.substack.com/p/prompting-and-the-probability-sandwich
- **Tech Lead Journal #195** (2024-10-14): AI is good for characterization tests (tests document current behavior, can be disposable); best for low-risk work (boilerplate, scripts, in-house tools); refactoring works better on smaller segments (large context windows degrade); hallucination means "you ask a question, you get an answer, and you just really don't know whether it's right or not"; "Take smaller steps." Developers remain irreplaceable — someone bears responsibility. Source: https://techleadjournal.dev/episodes/195/
- **LeadDev "Why AI is both the problem and the cure for legacy code"** (2026-01-08): uses Feathers' "code without tests" definition to argue vibe-coded untested code is *born* legacy; AI also enables modernization at scale with human oversight + validation loops. Source: https://leaddev.com/ai/why-ai-both-problem-cure-legacy-code

## Recent signals (post-2025-05-30 cutoff) — verified ≥3

1. **YOW! Melbourne 2025** (conference 2025-12-03 to 12-05). Talk "Conceptualisation"; masterclass "Forces in Software: Understanding the Physics of Software Evolution." Source: https://yowcon.com/melbourne-2025/speakers/3848/michael-feathers
2. **YOW! Sydney 2025** (2025-12-10 to 12-12). Same talk + masterclass. Source: https://yowcon.com/sydney-2025/speakers/3875/michael-feathers
3. **YOW! Brisbane 2025** — "Conceptualisation" session listed for 2025-12-09. Source: https://yowcon.com/brisbane-2025/sessions/3913/conceptualisation
4. **LeadDev article citing him** (2026-01-08). Source: https://leaddev.com/ai/why-ai-both-problem-cure-legacy-code
5. **"Prompting and the Probability Sandwich"** Substack (2025-06-03) — just past the cutoff. Source: https://michaelfeathers.substack.com/p/prompting-and-the-probability-sandwich

> Note: the brief said "currently writing on AI + legacy code." Confirmed — the LeanPub *AI Assisted Programming* WIP and the Substack run are exactly this. The book itself predates the 12-month window (releases in 2024) so it is logged in `canonical_works`, not `recent_signal_12mo`; the Substack continuation (2025-06) and conference appearances (Dec 2025) carry recency.

## "Forces in Software" masterclass — seven forces (verified, useful for mental_models)

Entropic forces; Conway's Law; Hyrum's Law; complexity attractors; resistance and flow; cohesive forces; evolutionary pressure. Framing question: "Why does software seem to drift toward complexity no matter how carefully we build it?" Source: https://yowcon.com/sydney-2025/masterclasses/554/forces-in-software-understanding-the-physics-of-software-evolution

## "Conceptualisation" talk (verified, Dec 2025)

Why naming is hard → how we form/identify/establish concepts. Draws on cognitive science. "A clearer operational grasp of what concepts are can make us better software designers." Source: https://yowcon.com/brisbane-2025/sessions/3913/conceptualisation

## Code Freeze 2025 keynote

Title "Working Effectively with Legacy Code"; abstract reexamines foundational design/DDD/architecture principles and "how AI and AR complement or challenge core engineering practices." Source: https://cse.umn.edu/umsec/code-freeze-2025-keynote-speaker-michael-feathers

## Roster fit (pairs / conflicts)

- **pairs_well_with:** `kent-beck` (TDD; both Object-Mentor-adjacent, both "take smaller steps") and `martin-fowler` (refactoring canon; Feathers' book is in the Fowler/Martin orbit). Both confirmed present in ROSTER.md cell 9 (architecture-testing-craft).
- **productive_conflict_with:** `dhh` (David Heinemeier Hansson) — same cell; DHH is famously anti-test-induced-design-damage and pro-majestic-monolith, against the rigorous test-seam discipline Feathers champions. Also `john-carmack` (systems-programming cell) — Carmack is bullish on AI for novel code and "AGI now," whereas Feathers is cautious about trusting AI on non-boilerplate and insists humans bear responsibility. Both slugs confirmed in ROSTER.md.

## All URLs used

- https://www.r7krecon.com/
- https://www.r7krecon.com/michael-feathers-bio
- https://www.r7krecon.com/articles
- https://www.r7krecon.com/legacy-code
- https://www.amazon.com/Working-Effectively-Legacy-Michael-Feathers/dp/0131177052
- https://www.amazon.com/Brutal-Refactoring-Working-Effectively-Legacy/dp/032179320X
- https://www.goodreads.com/book/show/25544117-brutal-refactoring
- https://www.infoq.com/podcasts/working-effectively-legacy-code/
- https://techleadjournal.dev/episodes/195/
- https://leaddev.com/ai/why-ai-both-problem-cure-legacy-code
- https://leanpub.com/ai-assisted-programming
- https://michaelfeathers.substack.com/p/prompting-and-the-probability-sandwich
- https://michaelfeathers.substack.com/p/ai-assisted-programming-release-2
- https://michaelfeathers.silvrback.com/prompt-hoisting-for-gpt-based-code-generation
- https://michaelfeathers.silvrback.com/toward-a-galvanizing-definition-of-technical-debt
- https://gotopia.tech/sessions/358/unconditional-code
- https://files.gotocon.com/uploads/slides/conference_9/358/original/goto_unconditional.pdf
- https://www.youtube.com/watch?v=AnZ0uTOerUI
- https://yowcon.com/melbourne-2025/speakers/3848/michael-feathers
- https://yowcon.com/sydney-2025/speakers/3875/michael-feathers
- https://yowcon.com/brisbane-2025/sessions/3913/conceptualisation
- https://yowcon.com/sydney-2025/masterclasses/554/forces-in-software-understanding-the-physics-of-software-evolution
- https://cse.umn.edu/umsec/code-freeze-2025-keynote-speaker-michael-feathers
- https://gotopia.tech/experts/173/michael-feathers
- https://newsletter.nerdnoir.com/p/engineering-conversations-with-michael
