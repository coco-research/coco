# Jez Humble — Research Notes

**Researched:** 2026-05-30
**Researcher:** Engineering Super Intelligence Team build (Wave E9, devops-platform cell)
**Slug:** `jez-humble` | **Cell:** `devops-platform` | **Cell role:** `lead-driver`
**Status decision:** `active` (see "Recency assessment" below for the nuance)

---

## Identity confirmation (high confidence)

Jez Humble is unambiguously identified. He is the co-author of *Continuous Delivery* (2010, with David Farley), *Lean Enterprise* (2015, with Joanne Molesky and Barry O'Reilly), *The DevOps Handbook* (with Gene Kim, Patrick Debois, John Willis), and *Accelerate* (2018, with Nicole Forsgren and Gene Kim). He co-founded DevOps Research and Assessment (DORA) with Forsgren and Kim. There is exactly one person with this public profile; no disambiguation required. Confidence 0.95.

His own GitHub bio (verbatim, fetched 2026-05-30) reads:
> "Co-author of some books on software. SRE @GoogleCloudPlatform, lecturer UC Berkeley. PGP: http://keybase.io/jezhumble . He/him."
Source: https://github.com/jezhumble — Location listed: SF Bay Area.

---

## Current role (2026) — verified

- **Google Cloud — Site Reliability Engineer.** His Google Research people page states he "works for Google Cloud as a site reliability engineer."
  Source: https://research.google/people/106958/
- **UC Berkeley School of Information — Lecturer.** His GitHub bio (current) says "lecturer UC Berkeley." Berkeley's own people page labels him "Former Continuing Lecturer" and lists the courses he taught: **Info 290T (Agile Engineering Practices)** and **Info 290M (Lean/Agile Product Management)**.
  Source: https://www.ischool.berkeley.edu/people/jez-humble

**Correction / reconciliation logged:** The Berkeley page says "Former Continuing Lecturer," but his own current GitHub bio still claims "lecturer UC Berkeley." I have rendered the affiliation as the Google Cloud SRE role (unambiguously current per Google's own page) plus the Berkeley lectureship qualified as ongoing-but-intermittent. The user's brief described him as "UC Berkeley lecturer" — this is supported by his self-description, with the caveat that Berkeley's site uses "former." His Info 290M course materials are CC-licensed and public at https://leanagile.pm/ and https://github.com/jezhumble/lapm.

**One unverifiable secondary claim:** A search snippet claimed he is "tech lead of the SRE team that manages Cloud Run, App Engine, Cloud Functions." This appears in third-party search summaries but is NOT on Google's own research page (which only says "site reliability engineer"). I have NOT asserted the Cloud Run tech-lead specificity in the persona frontmatter; I describe him as a Google Cloud SRE, which is verified. Flagged as lower-confidence.

**Brief assumption corrected — "ex-Google":** The user brief listed "ex-Google/18F." This is wrong about Google. Jez Humble is CURRENTLY at Google (since the December 2018 DORA acquisition; DORA LLC was acquired and he joined Google Cloud). He is ex-18F (the US federal digital services team, during the Obama "Tech Surge"). The "ex-Google" framing has been corrected to "Google Cloud (current)" in the persona. 18F is correctly past.

---

## DORA and the Four Key Metrics — verified

- DORA (DevOps Research and Assessment) was founded by **Nicole Forsgren, Jez Humble, and Gene Kim**.
- **Acquired by Google Cloud in December 2018.**
- The DORA / Accelerate **Four Key Metrics** (codified in *Accelerate*, 2018):
  1. **Deployment Frequency** — how often the org deploys to production (velocity / throughput).
  2. **Lead Time for Changes** — time from commit to running in production (velocity / throughput).
  3. **Change Failure Rate** — % of deployments causing a production failure (stability).
  4. **Mean Time to Recovery (MTTR)** — time to restore service after a production incident (stability).
  (First two = throughput; last two = stability. A later DORA addition is "reliability/operational performance" as a fifth measure, but the canonical four are the above.)
- Sources:
  - https://en.wikipedia.org/wiki/DevOps_Research_and_Assessment
  - https://waydev.co/accelerate-metrics/
  - https://dora.dev/research/team/ (Humble listed in the "DORA Collective" of current and former contributors)

---

## Canonical works — verified bibliography

| Work | Year | Co-authors | Note |
|---|---|---|---|
| *Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation* | 2010 | David Farley | Addison-Wesley Signature Series (Fowler). Won the **2011 Jolt Excellence Award**. Introduced the **deployment pipeline**. |
| *Lean Enterprise: How High Performance Organizations Innovate at Scale* | 2015 | Joanne Molesky, Barry O'Reilly | O'Reilly. Improvement Kata, innovation accounting, Westrum typology, HP LaserJet case study (cycle time months → one day). |
| *The DevOps Handbook* | 2016 | Gene Kim, Patrick Debois, John Willis | IT Revolution. |
| *Accelerate: The Science of Lean Software and DevOps* | 2018 | Nicole Forsgren, Gene Kim | IT Revolution. Won the **Shingo Publication Award**. Codified the Four Key Metrics + Westrum culture. |

- Continuous Delivery on Martin Fowler's site: https://martinfowler.com/books/continuousDelivery.html
- Continuous Delivery (Amazon): https://www.amazon.com/Continuous-Delivery-Deployment-Automation-Addison-Wesley/dp/0321601912
- Lean Enterprise (O'Reilly): https://www.oreilly.com/library/view/lean-enterprise/9781491946527/
- Accelerate (IT Revolution): https://itrevolution.com/product/accelerate/
- continuousdelivery.com (his canonical site): https://continuousdelivery.com/about/talks/

---

## Public stances — each with citable evidence

1. **Deployment pipeline + automate everything.** *Continuous Delivery* (2010) introduced the deployment pipeline as the automated path from check-in to release; releasing should be a routine, non-event "push-button" operation rather than a stressful crunch. Evidence: https://martinfowler.com/books/continuousDelivery.html

2. **"If it hurts, do it more often" / reduce batch size.** The CD philosophy: painful activities (integration, deployment, testing) should be done more frequently, not deferred, so the pain is forced into automation and small batches. Evidence: https://continuousdelivery.com/ (and the principles section of the book). Captured in the deployment-pipeline thesis on Fowler's book page.

3. **Trunk-based development; long-lived feature branches are antithetical to CI.** Humble argues that a branch is "by-design intended to hide change," which is the opposite of *continuous* integration; trunk-based development "puts the needs of the team above the needs of the individual" and challenges "the mythos of the developer-as-hero." Research (State of DevOps / Accelerate) shows teams on trunk or sub-day branches have significantly higher performance. Evidence: https://dora.dev/capabilities/trunk-based-development/

4. **Measure the Four Key Metrics — throughput AND stability move together.** *Accelerate*'s central empirical claim: high performers are faster AND more stable; the two are not a trade-off. Evidence: https://en.wikipedia.org/wiki/DevOps_Research_and_Assessment and https://waydev.co/accelerate-metrics/

5. **Culture is causal, and it is measurable.** Drawing on Westrum's typology, *Accelerate* shows that a **generative** (performance-oriented) culture predicts software-delivery and organizational performance; culture is not a soft afterthought but a measurable lever. Evidence: https://itrevolution.com/articles/westrums-organizational-model-in-tech-orgs/

6. **AI amplifies the existing system — it does not fix a broken one.** The 2025 DORA report (the program Humble co-founded) frames AI as an amplifier: "AI doesn't fix a team; it amplifies what's already there," and AI adoption has a *negative* relationship with delivery stability absent strong testing, version control, and fast feedback loops — exactly the CD capabilities Humble has advocated for 15 years. Evidence: https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report

7. **Continuous delivery "won't work here" is almost always an excuse, not a constraint.** His Agile 2017 / repeated keynote "Continuous Delivery Sounds Great But It Won't Work Here" systematically refutes the common excuses (regulation, legacy, scale). Evidence: https://www.infoq.com/presentations/continuous-delivery-highlights/

---

## Recency assessment — THE KEY FINDING / unmet-bar nuance

**Jez Humble has gone substantially quiet as a public first-person voice.** Findings:

- His personal talks page (continuousdelivery.com/about/talks/) lists **no talks dated 2024, 2025, or 2026.** Most recent first-person conference appearances I could find: **YOW! Sydney/Brisbane 2023 and GOTO Aarhus 2023.**
  - https://yowcon.com/sydney-2023/speakers/2908/jez-humble
  - https://gotoaarhus.com/2023/speakers/2679/jez-humble
- The most recent LinkedIn post surfaced ("Explore DORA's research program") links to an **8-year-old** white paper (Nava + DORA, federal cloud), not new 2025 content.
- His Medium ("DORA's Journey") is dated **February 2019.**
- His AAE speaker-bureau profile was "last updated September 24, 2024" — i.e., he remains *available* but there is no recent recorded engagement.
- **The 2025 DORA "State of AI-Assisted Software Development" report (published 2025-09-23) is led by Nathen Harvey, NOT Jez Humble.** Humble is now in the "DORA Collective" as a founding/historical contributor. The 2026 follow-up ("ROI of AI-Assisted Software Development," covered by InfoQ 2026-05-11) likewise does NOT mention Humble; lead is again Nathen Harvey.
  - https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report
  - https://www.infoq.com/news/2026/05/dora-roi-ai-assisted-dev-report/
- No findable Mastodon/Hachyderm/X first-person posts dated after 2025-05-30. (Mastodon is poorly indexed, so absence is not conclusive, but nothing surfaced.)

**Why status remains `active` (not `archetype`):** The schema defines `archetype` as "deceased or no longer publishing; profile is drawn from canonical published work." Humble is **alive and professionally active** — he is a current Google Cloud SRE and (per his own bio) a UC Berkeley lecturer. He is "no longer prolifically *publishing thought-leadership*," but he is not retired or deceased, and he is operationally active inside Google. Treating him as `archetype` would mis-state his employment status. The honest framing, therefore:

- Keep `status: active`.
- Populate `recent_signal_12mo` with the genuinely datable post-2025-05-30 items that legitimately reflect his living influence: (a) the DORA program he co-founded continuing to publish on AI (Sept 2025 + 2026 reports), and (b) his canon being actively applied/operationalized in the AI-coding-stability discourse. Each `takeaway` is framed HONESTLY as canon-continuation / institutional signal, NOT as a fabricated first-person quote. No invented quotes anywhere.
- **This is the one soft spot against the quality bar:** the ≥3 recent signals are *institutional/canonical-continuation* signals dated correctly, rather than three fresh first-person Humble statements (which do not appear to exist in the window). Documented here transparently per the template's instruction ("if <3, document").

---

## Pairs / conflicts (validated against ROSTER.md devops-platform + architecture-craft cells)

**Pairs well with:**
- `gene-kim` — co-author of *The DevOps Handbook* and *Accelerate*; co-founder of DORA. Same cell (devops-platform). Natural amplifier.
- `nicole-forsgren` — co-author of *Accelerate*; the research/statistics rigor behind the Four Key Metrics. Same cell. Humble brings the practitioner CD canon; Forsgren brings the predictive-validity science.

**Productive conflict with (real ROSTER.md slugs):**
- `dhh` (David Heinemeier Hansson, architecture-testing-craft) — DHH's "majestic monolith" / anti-cloud / anti-microservices, deploy-when-ready stance productively clashes with Humble's pipeline-discipline + measure-everything framing. Both value simplicity but disagree on instrumentation and process formality.
- `charity-majors` (reliability-sre-obs) — Majors' "test in prod" / observability-first and skepticism of staging environments sharpens against Humble's pre-production deployment-pipeline / automated-test-gate orthodoxy. Productive: both want fast safe deploys, disagree on where the safety comes from.
- `kelsey-hightower` (devops-platform) — Hightower's pragmatic "you might not need [the heavy platform]" minimalism vs. Humble's structured CD/measurement program is a useful tension within the same cell.

(Selected `dhh` and `charity-majors` as the two primary `productive_conflict_with` entries — both are confirmed slugs in ROSTER.md and represent the sharpest real disagreements.)

---

## All source URLs (master list)

1. https://research.google/people/106958/
2. https://www.ischool.berkeley.edu/people/jez-humble
3. https://github.com/jezhumble
4. https://en.wikipedia.org/wiki/DevOps_Research_and_Assessment
5. https://martinfowler.com/books/continuousDelivery.html
6. https://www.amazon.com/Continuous-Delivery-Deployment-Automation-Addison-Wesley/dp/0321601912
7. https://www.oreilly.com/library/view/lean-enterprise/9781491946527/
8. https://itrevolution.com/product/accelerate/
9. https://dora.dev/capabilities/trunk-based-development/
10. https://dora.dev/research/team/
11. https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report
12. https://www.infoq.com/news/2026/05/dora-roi-ai-assisted-dev-report/
13. https://www.infoq.com/presentations/continuous-delivery-highlights/
14. https://waydev.co/accelerate-metrics/
15. https://itrevolution.com/articles/westrums-organizational-model-in-tech-orgs/
16. https://continuousdelivery.com/about/talks/
17. https://medium.com/@jezhumble/doras-journey-an-exploration-4c6bfc41e667
18. https://leanagile.pm/
