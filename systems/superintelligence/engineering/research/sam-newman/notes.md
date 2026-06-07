# Sam Newman — Research Notes

**Researched:** 2026-05-30
**Slug:** sam-newman
**Cell:** architecture-testing-craft (engineering team), cell_role: specialist
**Status determination:** active (multiple dated signals after 2025-05-30, see below)

---

## Identity confirmation

Sam Newman is an independent technology consultant, speaker, and author. Over 20 years
as a developer. Spent ~12 years at ThoughtWorks before going independent. Author of the
O'Reilly books *Building Microservices* (1st ed. 2015, 2nd ed. August 2021), *Monolith to
Microservices* (2019), and the forthcoming *Building Resilient Distributed Systems* (early
access since 2024; planned publication August 2026). Best known for the pragmatic,
anti-hype position that microservices are an "architecture of last resort" and that teams
should "default to a monolith." No organizational affiliation as of 2026 — he runs his own
consultancy. Identity is unambiguous; confidence high.

Source: https://samnewman.io/ ; https://www.oreilly.com/pub/au/6132 ;
GOTO Copenhagen 2026 bio (https://gotocph.com/2026/speakers/4243/sam-newman).

---

## Correction to brief's framing assumptions

The brief framed Sam Newman around "default to a monolith / don't start with microservices,
decomposition patterns, distributed-systems pragmatism." All three hold up and are well
cited. One refinement worth logging: as of 2025-2026 his **primary public center of gravity
has shifted from "microservices vs monolith" to resilience in distributed systems** —
timeouts/retries/idempotency, progressive collapse / cascading failure, and sociotechnical
resilience. His forthcoming book and his 2025/2026 conference talks are overwhelmingly about
*resilience*, not decomposition. The persona reflects this: he remains the microservices-
skeptic canon author, but his recent_signal_12mo is dominated by resilience work. This is an
expansion of the brief's framing, not a contradiction of it.

Also: he advocates the **modular monolith with multiple databases** as the default, not a
single-database monolith — an important nuance often dropped. The hardest part of any
eventual decomposition, in his telling, is separating the data tier.

---

## Key dated findings & quotes (with URLs)

### QCon London 2020 — "Monolith Decomposition" (date: 2020-05-13)
URL: https://www.infoq.com/news/2020/05/monolith-decomposition-newman/
- "The monolith is not the enemy."
- "Microservices should not be the default choice. You've got to think really carefully
  about if they're right for you."
- "microservices are not a good choice for most startups."
- "You are not going to fully appreciate the sheer terror, horror, pain, suffering, anguish,
  and expense of running microservices until they're actually in production."
- "the goal is independent deployability."
- Advocates modular monolith with multiple databases; separating the data tier is the
  hardest part of decomposition.

### InfoQ podcast — "Sam Newman on Information Hiding, Ubiquitous Language, UI Decomposition" (date: 2021-09-27)
URL: https://www.infoq.com/podcasts/sam-newman-ddd-microservices/
- "things that are hidden can change easily and things that are shared are part of your
  contract."
- Microservices are fundamentally modular architecture leaning on David Parnas's 1970s
  information-hiding work.
- Ubiquitous language is "the keystone of domain-driven design" and is widely neglected.
- UI decomposition: ask "could it be a webpage?" before defaulting to a single-page-app
  framework. Favors page-based decomposition over dedicated frontend teams / SPAs.
- Bounded contexts implement information hiding at the domain level.

### Building Microservices, 2nd Edition (date: 2021-08)
URL: https://samnewman.io/books/building_microservices_2nd_edition/
- Complete rewrite of 1st edition. Strongest chapter brings together microservices, DDD,
  coupling, cohesion, and information hiding.

### QCon London 2025 — "Timeouts, Retries and Idempotency" (article date: 2025-04-09)
URL: https://www.infoq.com/news/2025/04/resilient-distributed-systems/
- "Timeouts are about prioritising system health over the success of a single request."
- Excessive retries are "similar to a self-inflicted DoS attack." Rate-limit both client and
  server; add random jitter between retries.
- Idempotency: safe to apply multiple times; hard to retrofit; use request IDs or
  fingerprints; fingerprints must avoid timestamps and be time-bound.
- Reframes the "definition of insanity" cliché: repetition (retry) is sensible in distributed
  systems when it is safe.

### InfoQ podcast — "Do Microservices' Benefits Supersede Their Caveats?" (date: 2025-06-16)
URL: https://www.infoq.com/podcasts/microservices-benefits-supersede-caveats/
- Microservices are "an architecture of last resort because they introduce a significant
  amount of complexity when building a more distributed system."
- "If I were starting a project today, it would be a monolith. If I were starting a startup
  today, it would be a monolith."
- Three fundamental distributed-systems pain points: "It takes time for stuff to go from A to
  B... Sometimes the thing you want to talk to isn't there... resource pools are not infinite."
- "What is the outcome you're reaching for? Do you know why you're doing this?"
- "Architecture is always a journey... constantly changing... should always be some sense of
  flux."

### Building Resilient Distributed Systems (O'Reilly early access; planned pub 2026-08)
URL: https://samnewman.io/books/building-resilient-distributed-systems/
URL: https://www.oreilly.com/library/view/building-resilient-distributed/9781098163532/
- Three parts: Foundation (technical: timeouts, retries, idempotency, rate limiting,
  queueing, scaling, SLOs); People/Process/Culture (sociotechnical systems, incident
  management, postmortems); Implementation.
- "Resiliency can mean different things to different people, so it's important to start with
  a shared understanding."
- "the concept of the sociotechnical system has been around for decades, but it has only
  been somewhat recently that this school of thinking has come to the fore in digital system
  resiliency."
- Combines human factors / system safety with proven stability patterns.

### Early-access announcement on X (date: 2024-07-16)
URL: https://x.com/samnewman/status/1813159287637647532
- "My new book, Building Resilient Distributed Systems, is now available in early access form
  @OReillyMedia. A few chapters are available at this stage, ahead of the planned
  publication..."

---

## Recent signals (post-2025-05-30 cutoff) — for recent_signal_12mo

1. **QCon London 2026 talk — "Understanding Progressive Collapse: How To Avoid A Cascading
   Failure"** — Wednesday, March 18, 2026, 13:35 GMT, Architecting for Resilience track.
   URL: https://qconlondon.com/speakers/samnewman
   (date used: 2026-03-18)

2. **GOTO Copenhagen 2026 — "Understanding Progressive Collapse (or How To Avoid A Cascading
   Failure)"** — conference 28 Sep – 2 Oct 2026.
   URL: https://gotocph.com/2026/speakers/4243/sam-newman
   (date used: 2026-09-28 is future; for recency I anchor to the speaker-listing publication,
   which is live as of research date. NOTE: this is a *future* event. To stay strictly within
   "dated AFTER 2025-05-30," I keep QCon London 2026 (2026-03-18) as the primary; GOTO 2026
   listing is supplementary.)

3. **InfoQ podcast — "Do Microservices' Benefits Supersede Their Caveats?"** — 2025-06-16.
   URL: https://www.infoq.com/podcasts/microservices-benefits-supersede-caveats/
   (date: 2025-06-16 — AFTER 2025-05-30. Valid.)

4. **Building Resilient Distributed Systems — ongoing early access, new chapters every ~2
   months, planned publication August 2026.** As of 2026 this is his active in-progress work.
   URL: https://www.oreilly.com/library/view/building-resilient-distributed/9781098163532/
   (Active/ongoing through 2025-2026. Valid as a current signal.)

Recent-signal bar (>=3 dated after 2025-05-30): MET.
- 2025-06-16 InfoQ podcast ✓
- 2026-03-18 QCon London 2026 talk ✓
- 2026 (ongoing) Building Resilient Distributed Systems early access + Aug 2026 pub ✓
- 2026-09-28 GOTO Copenhagen 2026 (future event, supplementary) ✓

---

## Pairs / conflicts (validated against ROSTER.md)

Pairs well with (brief-specified, all valid roster slugs):
- martin-fowler (cell architecture-testing-craft) — Fowler's "MonolithFirst" bliki post is the
  canonical companion to Newman's "default to a monolith." Both ex-ThoughtWorks.
- adrian-cockcroft (cell cloud-architecture, file EXISTS) — Netflix microservices canon; the
  two represent the pro-adoption-with-discipline and the skeptic-pragmatist poles that agree
  on "don't start there."
- eric-evans (cell architecture-testing-craft) — DDD / bounded contexts are Newman's stated
  basis for finding microservice boundaries.

Productive conflict with (real roster slugs):
- dhh (David Heinemeier Hansson, cell architecture-testing-craft) — DHH's "majestic monolith"
  and anti-microservices/anti-cloud stance vs Newman's "microservices have their place, just
  not by default." They agree monolith-first but clash on whether microservices are ever the
  right call and on cloud repatriation. This is the brief's suggested conflict pairing and it
  is well-founded.
- adrian-cockcroft — also a productive-conflict axis: Cockcroft's Netflix-era "microservices
  at scale" enthusiasm vs Newman's "last resort." (Used as pairs_well_with here per brief;
  conflict is secondary.)

ROSTER note: martin-fowler, eric-evans, and dhh persona files are NOT yet written (cell 9 /
architecture-testing-craft is build wave E8, not yet built as of this research), but all three
slugs are valid entries in ROSTER.md cell 9 and are therefore correct references.

---

## All source URLs

1. https://samnewman.io/
2. https://samnewman.io/books/
3. https://samnewman.io/books/building_microservices_2nd_edition/
4. https://samnewman.io/books/monolith-to-microservices/
5. https://samnewman.io/books/building-resilient-distributed-systems/
6. https://samnewman.io/talks/
7. https://www.oreilly.com/pub/au/6132
8. https://www.oreilly.com/library/view/building-resilient-distributed/9781098163532/
9. https://qconlondon.com/speakers/samnewman
10. https://gotocph.com/2026/speakers/4243/sam-newman
11. https://www.infoq.com/news/2025/04/resilient-distributed-systems/
12. https://www.infoq.com/podcasts/microservices-benefits-supersede-caveats/
13. https://www.infoq.com/news/2020/05/monolith-decomposition-newman/
14. https://www.infoq.com/podcasts/sam-newman-ddd-microservices/
15. https://www.amazon.com/Building-Microservices-Designing-Fine-Grained-Systems/dp/1492034029
16. https://x.com/samnewman/status/1813159287637647532
17. https://martinfowler.com/bliki/MonolithFirst.html (companion stance, Fowler)
