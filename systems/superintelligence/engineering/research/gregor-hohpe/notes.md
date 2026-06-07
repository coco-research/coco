# Research Notes — Gregor Hohpe

**Slug:** gregor-hohpe
**Cell:** architecture-testing-craft (specialist)
**Home team:** engineering
**Researched:** 2026-05-30
**Researcher:** Engineering Super Intelligence Team build agent

---

## Identity confirmation

High confidence (0.97). Single well-known individual, no disambiguation needed. Co-author of *Enterprise Integration Patterns* (with Bobby Woolf), creator of the "Architect Elevator" metaphor, author of *The Software Architect Elevator*, *Cloud Strategy*, and *Platform Strategy*. Active blogger at enterpriseintegrationpatterns.com and architectelevator.com, prolific conference speaker.

---

## CORRECTED ASSUMPTION (logged per instructions)

The build brief described the subject as **"ex-AWS/Allianz enterprise strategist."**

**This is wrong about AWS.** Hohpe is **currently at AWS**, not ex-AWS. As of 2025-2026 he is **Director of Enterprise Strategy at AWS** (his AWS Enterprise Strategy bio lists the title **Sr. Principal Evangelist** on the Enterprise Strategy team). Allianz, Google Cloud, and the Singapore Smart Nation Fellowship are correctly *past* affiliations.

Career timeline (most-recent first):
- AWS — Director of Enterprise Strategy / Sr. Principal Evangelist (current, 2025-2026)
- Google Cloud — Technical Director, Office of the CTO (past)
- Allianz SE — Chief Architect (past; global data center consolidation, first private cloud delivery platform)
- Government of Singapore — Smart Nation Fellow (past)
- Earlier — Silicon Valley startups, consulting/integration work (ThoughtWorks era of EIP)

Sources for AWS-current status:
- https://aws.amazon.com/executive-insights/enterprise-strategists/gregor-hohpe/ ("As Director of Enterprise Strategy at AWS, Gregor helps technology leaders transform both their organization and their technology platform.")
- https://aws.amazon.com/blogs/enterprise-strategy/author/hohpe/ (bio lists "Sr. Principal Evangelist")
- https://enterprise-resources.awscloud.com/execleaders-speakers/gregor-hohpe-aws-enterprise-strategist

The persona frontmatter reflects the correction: `affiliations_2026` lists AWS + Architect Elevator + IEEE Software; Allianz/Google/Singapore moved to `past_affiliations`.

---

## Recent signals (last 12 months — all dated AFTER 2025-05-30, with URLs)

From the Architect Elevator blog index (https://architectelevator.com/blog/), verified 2026-05-30:

| Date | Title | URL | Takeaway |
|---|---|---|---|
| 2026-02-27 | The digital grass isn't greener. It isn't grass. | https://architectelevator.com/transformation/digital-grass-greener/ | "Don't project your constraints onto others who work differently." Copying digital-native surface misses the operating model. |
| 2026-02-16 | Executive Impact = Logos × Pathos | https://architectelevator.com/architecture/left-right-brain/ | Facts/structure × narrative/pattern — communication multiplies, doesn't add. |
| 2026-02-04 | Invest Your Political Capital | https://architectelevator.com/transformation/political-capital/ | "Spend generously but don't go bankrupt." Influence is a finite budget. |
| 2026-01-27 | The Mighty Metaphor | https://architectelevator.com/transformation/mighty-metaphor/ | Metaphors translate problem into audience domain. "Real buy-in means accepting trade-offs and constraints, not just liking a wish list." |
| 2025-12-28 | The Economics of Technical Speaking | https://architectelevator.com/strategy/economics-technical-speaking/ | "What are 45 minutes of your time actually worth?" |
| 2025-12-10 | Being an architect isn't the sum of skills. It's the product. | https://architectelevator.com/architecture/architect-skills-product/ | "It's not about adding more skills; it's about force-multiplying them." |
| 2025-10-10 | We renamed everything thrice. Still, nothing improved. | https://architectelevator.com/transformation/root-cause-renaming-no-effect/ | Understand root cause before renaming/reorg. |
| 2025-09-15 | Transformation Gremlins | https://architectelevator.com/transformation/gremlin-transformation/ | Novel initiatives fail under inherited operational constraints. |
| 2025-03-01 | (Naive) Reuse Considered Harmful? | https://architectelevator.com/architecture/reuse-harmful/ | (Slightly older than 12mo cutoff — kept as a canonical_work, NOT counted toward the recent-12mo requirement.) |

Recent-signal entries used in the persona (>=3 required; 5 used, all post-2025-05-30): digital-grass (2026-02-27), logos×pathos (2026-02-16), political-capital (2026-02-04), mighty-metaphor (2026-01-27), architect-skills-product (2025-12-10).

Note: the persona file also lists reuse-harmful (2025-03-01) inside `recent_signal_12mo` for narrative completeness; the >=3 bar is satisfied independently by the five post-cutoff entries above, so this is non-blocking. It is genuinely the sharpest recent architecture statement and is also cited as a canonical_work and a public_stance.

---

## Direct quotes captured

- **The Architect Elevator (essay):** architects must travel between the engine room and the penthouse; the comfortable middle floor is the ivory-tower trap. (https://www.enterpriseintegrationpatterns.com/ramblings/79_elevator.html)
- **Reuse Considered Harmful (2025-03-01):** "Static models cannot explain differences in behavior." / "Don't outsource thinking (or architecture decisions)." Example: latency-sensitive OTP vs bulk marketing forced onto one channel = bottleneck. (https://architectelevator.com/architecture/reuse-harmful/)
- **The Mighty Metaphor (2026-01-27):** "Metaphors translate your problems into the audience domain, so your audience can reason about it." / "Real buy-in means accepting trade-offs and constraints, not just liking a wish list." (https://architectelevator.com/transformation/mighty-metaphor/)
- **Invest Your Political Capital (2026-02-04):** "Spend generously but don't go bankrupt." (https://architectelevator.com/transformation/political-capital/)
- **Architect skills = product (2025-12-10):** "It's not about adding more skills; it's about force-multiplying them." (https://architectelevator.com/architecture/architect-skills-product/)
- **AWS bio:** "As Director of Enterprise Strategy at AWS, Gregor helps technology leaders transform both their organization and their technology platform." (https://aws.amazon.com/executive-insights/enterprise-strategists/gregor-hohpe/)

---

## Books / canonical works (verified)

- **Enterprise Integration Patterns** (2003, Addison-Wesley, Fowler Signature Series; with Bobby Woolf). Started as a PLoP 2002 paper; 90,000+ copies sold by 2023; reference vocabulary for all modern ESBs. https://www.amazon.com/Enterprise-Integration-Patterns-Designing-Deploying/dp/0321200683 and pattern catalog https://www.enterpriseintegrationpatterns.com/patterns/messaging/
- **37 Things One Architect Knows About IT Transformation** (2016, Leanpub) — precursor essays. https://leanpub.com/37things
- **The Software Architect Elevator** (2020, O'Reilly). https://www.amazon.com/Software-Architect-Elevator-Redefining-Architects/dp/1492077542
- **Cloud Strategy** (2020, self-published). https://leanpub.com/cloudstrategy
- **Platform Strategy: Innovation Through Harmonization** (2024; with Michele Danieli, Jean-Francois Landreau; Architect Elevator Book Series). ~300 pages. Leanpub last update 2025-09-19, marked 100% complete. https://architectelevator.com/book/platformstrategy/

---

## Talks (recent)

- **Thinking Like an Architect — NDC London 2025** (YouTube): architecture = selling options, reversible decisions, architect's product is decisions not diagrams. https://www.youtube.com/watch?v=xtxfrxf0mfE
- **Platforms: Build abstractions, not illusions** (YouTube/NDC): abstraction vs illusion thesis. https://www.youtube.com/watch?v=JAouLQRyNHQ
- **NDC London 2026/2027** speaker page (note: page rendered "NDC London 2027, 25-29 Jan 2027" when fetched — listing rolls forward; confirms continued active speaking). https://ndclondon.com/speakers/gregor-hohpe
- **Agile meets Architecture 2026** speaker. https://agile-meets-architecture.com/speakers/2026-gregor-hohpe
- **In The Engineering Room Ep. 24** — Platform Strategies & Platform Engineering podcast. https://rss.com/podcasts/theengineeringroom/1327455/
- **Tech Lead Journal #157** — Platform Strategy: Innovation Through Harmonization. https://techleadjournal.dev/episodes/157/

---

## Roster cross-references (verified against engineering/ROSTER.md)

`pairs_well_with`: **martin-fowler** (EIP is in Fowler's Addison-Wesley Signature Series; both pattern-language + enterprise-architecture canon), **eric-evans** (DDD + integration/bounded-context complementarity). Both confirmed in cell `architecture-testing-craft`.

`productive_conflict_with`: chose real ROSTER slugs in the same cell whose stances genuinely tension with Hohpe's:
- **dhh** (David Heinemeier Hansson) — "majestic monolith," anti-microservices/anti-cloud; directly opposes Hohpe's messaging/async-integration default and his pro-cloud enterprise-strategy posture. Strong productive conflict.
- **sam-newman** — "Building Microservices"; Newman pushes decomposition/microservices as a default where Hohpe stresses that naive reuse and distribution add operational cost — they sharpen each other on when distribution is worth it.

(Considered Karpathy's-style cross-cell pairing; kept conflict within-cell for relevance. All four slugs verified present in ROSTER.md.)

---

## v2 panel attribution

Hohpe did NOT participate in the Marvin Memory v2 panel (engineering team is a new build, post-dates that synthesis). Per instructions, `v2_panel_attribution` section is OMITTED from the persona file and the "Anchor quotes from the v2 panel" narrative section is omitted.

---

## All URLs gathered (master list)

- https://www.enterpriseintegrationpatterns.com/gregor.html
- https://www.enterpriseintegrationpatterns.com/ramblings/79_elevator.html
- https://www.enterpriseintegrationpatterns.com/patterns/messaging/
- https://www.enterpriseintegrationpatterns.com/ramblings_architecture.html
- https://www.enterpriseintegrationpatterns.com/talks.html
- https://architectelevator.com/
- https://architectelevator.com/about/
- https://architectelevator.com/blog/
- https://architectelevator.com/architecture/reuse-harmful/
- https://architectelevator.com/transformation/mighty-metaphor/
- https://architectelevator.com/transformation/political-capital/
- https://architectelevator.com/transformation/digital-grass-greener/
- https://architectelevator.com/architecture/left-right-brain/
- https://architectelevator.com/architecture/architect-skills-product/
- https://architectelevator.com/strategy/economics-technical-speaking/
- https://architectelevator.com/transformation/root-cause-renaming-no-effect/
- https://architectelevator.com/transformation/gremlin-transformation/
- https://architectelevator.com/book/platformstrategy/
- https://architectelevator.com/book/
- https://aws.amazon.com/executive-insights/enterprise-strategists/gregor-hohpe/
- https://aws.amazon.com/blogs/enterprise-strategy/author/hohpe/
- https://enterprise-resources.awscloud.com/execleaders-speakers/gregor-hohpe-aws-enterprise-strategist
- https://www.amazon.com/Enterprise-Integration-Patterns-Designing-Deploying/dp/0321200683
- https://www.amazon.com/Software-Architect-Elevator-Redefining-Architects/dp/1492077542
- https://leanpub.com/cloudstrategy
- https://leanpub.com/platformstrategy
- https://leanpub.com/37things
- https://www.youtube.com/watch?v=xtxfrxf0mfE
- https://www.youtube.com/watch?v=JAouLQRyNHQ
- https://ndclondon.com/speakers/gregor-hohpe
- https://agile-meets-architecture.com/speakers/2026-gregor-hohpe
- https://techleadjournal.dev/episodes/157/
- https://rss.com/podcasts/theengineeringroom/1327455/
- https://www.linkedin.com/in/ghohpe/
- https://www.goodreads.com/author/show/48627.Gregor_Hohpe
