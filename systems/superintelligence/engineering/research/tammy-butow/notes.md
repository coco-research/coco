# Tammy Butow — Research Notes

**Researched:** 2026-05-30
**Researcher:** Claude (engineering super-intelligence roster build, wave E2, cell `reliability-sre-obs`)
**Slug:** `tammy-butow`
**Status decision:** `archetype` (see "Recency gap and status decision" below)

---

## Identity confirmation

- Full name: **Tammy Bryant Butow** (publishes as "Tammy Butow" and sometimes "Tammy Bütow" — the umlaut spelling appears in several podcast titles but her own properties use "Butow"/"Bryant Butow").
- Location: Cupertino, California (LinkedIn). Earlier carrd bio noted a relocation to the Miami–Fort Lauderdale area while at Statype.
- Australian by origin; degrees from QUT and RMIT (BSc/MSc Computer Science plus a Bachelor of Education).
- Co-founder of **Girl Geek Academy** (Australia); organized what is described as the world's first all-women hackathon in 2014.
- GitHub: https://github.com/tammybutow — bio currently reads "Working from home" with affiliation **Apple**. 48 repos; pinned repos include `chaosengineeringbootcamp` (~173 stars) and `Talks`.

Identification is **confirmed** (single unambiguous individual; consistent name, location, and career arc across LinkedIn, GitHub, O'Reilly, InfoQ, Gremlin, and multiple podcasts). Confidence in identity: high.

---

## Career arc (verified)

| Period | Role | Employer | Source |
|---|---|---|---|
| (early) | Security / Product / Infrastructure Engineering | National Australia Bank (NAB) | carrd, Gremlin author bio |
| (mid-2010s) | Engineering | DigitalOcean | carrd, Gremlin author bio |
| ~2016–2018 | SRE Manager, Databases team; IMOC (Incident Manager On-Call) | Dropbox (storage/DBs for 500M+ customers) | InfoQ "0 to 100 days - Running DRTs at Dropbox" (2016-09-24) |
| ~2018–2022 | Principal Site Reliability Engineer; Executive Team | **Gremlin** (chaos engineering vendor) | QCon/SREcon/Velocity speaker bios; Gremlin author page |
| ~2022–2023 | VP Product | **Statype** (stealth-mode seed-stage startup, founded 2021 by Moisey Uretsky; ex-DigitalOcean founder) | HashiCast Ep.36; LinkedIn post 2023; RocketReach |
| 2023–2024 | Student | **Stanford University Graduate School of Business** | LinkedIn education |
| ~2024–present | Affiliation listed as **Apple** (Cupertino); role not publicly disclosed | (likely SRE/reliability or product, non-public) | GitHub bio; LinkedIn location |

**Key correction to the build brief:** The brief described her as "Principal SRE; ex-Gremlin, ex-Dropbox/DigitalOcean." That is accurate for her *peak public era* (Gremlin, 2018–2022) but **outdated as her current role**. The correct, current picture as of 2026-05-30 is:
- She left Gremlin (~2022).
- She was **VP Product at Statype** (a product-leadership pivot away from pure SRE/IC).
- She completed **Stanford GSB (2023–2024)**.
- Her current public affiliation is **Apple** (GitHub bio + Cupertino location), role undisclosed.

The persona therefore carries `affiliations_2026: ['Apple (reliability / engineering; role not publicly disclosed)']` with the colon-bearing value single-quoted per schema. Her *signature thought-leadership* remains chaos engineering / SRE practice, so `cell: reliability-sre-obs` and `cell_role: specialist` are correct.

---

## Recency gap and status decision

The build brief asks for `>=3` `recent_signal_12mo` entries dated **after 2025-05-30**. **I could not verify any.** Findings:

- **Medium** (https://tammybutow.medium.com/): last article **Aug 30, 2021**. No 2022–2026 posts.
- **O'Reilly author page** (https://www.oreilly.com/people/tammy-butow/): single Radar piece, "Chaos Day: When reliability reigns," **Oct 3, 2018**. No recent reports.
- **Conference circuit:** Heavy 2016–2021 presence (QCon NY/London/SF, SREcon, Velocity, Chaos Conf, GDG). A "QCon London 2025 — Why the World Needs More Resilient Systems" reference surfaced in search summaries, but **the underlying InfoQ artifact (https://www.infoq.com/presentations/chaos-engineering-resilient-systems/ and /news/2018/03/...) is dated 2018**. I treat the 2025 attribution as an unverified search-summary artifact, **not** a confirmed recent signal. Did not cite it as a recent signal.
- **Podcasts:** Most appearances 2018–2021. HashiCast Ep.36 (Statype) is ~2022. No verified 2025–2026 episode.
- **GitHub:** Profile shows achievements but no clearly dated 2025–2026 public commits in the fetched content.

Per the persona schema (`templates/persona.md`, lines 79–98): if `recent_signal_12mo` cannot reach 3 entries within the last 12 months, document it and **consider `status: archetype`**, setting `recent_signal_12mo: []` and using `persistent_signals` instead. Archetype is defined as "deceased or no longer publishing; profile is drawn from canonical published work."

**Decision: `status: archetype`.** Tammy Butow is alive and professionally active, but she is **no longer publicly publishing** in the chaos-engineering / SRE thought-leadership channel that makes her a useful panel voice. Her move to product leadership (Statype), then Stanford GSB, then an undisclosed Apple role, has taken her out of public technical output since ~2022. The honest, schema-compliant choice is to anchor the persona to her **canonical 2016–2022 body of work** via `persistent_signals` rather than fabricate recent signals. This is documented here so a future re-synthesis knows the recency gap is real, not a crawl failure. If she resumes public output (a new talk, book, or Apple-attributed post-2025-05-30 signal), flip to `status: active` and populate `recent_signal_12mo`.

---

## Substantive findings (for persona body)

### Chaos engineering as a discipline
- Definition she uses repeatedly: chaos engineering is "the facilitation of controlled experiments to identify systemic weaknesses." (Gremlin author bio; SE-Radio Ep.325)
- She frames the goal as **building resilient systems** by improving the full incident lifecycle: **detection, mitigation, resolution, and prevention**. (InfoQ "Why the World Needs More Resilient Systems," QCon London 2018)
- Companies she cites as practitioners: Netflix, Gremlin, Dropbox, NAB, Under Armour, Twilio.

### GameDays
- At Gremlin she ran **GameDays** — "Gremlin on Gremlin," using the product against the company's own systems with the entire engineering team present. (Gremlin author page; multiple talks)
- GameDays are her preferred mechanism for converting chaos theory into team practice and for validating incident playbooks. (Chaos Conf talk with Robert Ross: "Incident Repro & Playbook Validation with Chaos Engineering")

### Disaster Recovery Testing (DRTs) at Dropbox
- Source: InfoQ "0 to 100 days - Running DRTs at Dropbox" (2016-09-24).
- As **SRE Manager of the Dropbox Databases team**, she rolled out new DRT techniques over a 100-day window, building on methodology from Dropbox's Infrastructure Reliability team (co-presenter Thomissa Comellas).
- DRTs = techniques for validating a system's ability to recover from failures and outages. This is her disaster-recovery-testing credential and a distinct thread from pure fault injection.

### SRE education and apprenticeships (distinctive view)
- Source: InfoQ "SRE Apprentices" podcast (2021-09-13).
- She advocates **formal, structured SRE apprenticeships** over traditional hiring: "you really can teach folks things, if you have a great curriculum" with clear success metrics.
- Method: **learning by doing** with progressively complex tasks (one-day → multi-week); **real-time code review on large screens** (not async GitHub) so apprentices can ask "why"; shadowing on-call; attending postmortems; building cross-team mentoring relationships.
- Six-month paid apprenticeship (competitive salary, long-term commitment, trained for production on-call) — distinct from internships. All participants passed final interviews; mentors grew leadership skills and got promoted; improved diversity outcomes.

### Business side of chaos
- She consistently connects chaos engineering to **business metrics — MTTD (mean time to detect) and MTTR (mean time to resolve)** — to justify the practice to leadership. (Co-authored O'Reilly content "Reducing MTTD" with engineers from LinkedIn, Amazon, Twitter, per carrd; New Stack interview "Gremlin's Tammy Butow on the Business Side of Chaos Engineering" — page later gated, cited from search summary.)

### Personal voice texture
- carrd bio: enjoys "riding bikes, skateboarding, snowboarding, and surfing" and "mosh pits, crowd surfing, metal, and hardcore punk." This informs her direct, energetic, hands-on, "break things on purpose" voice (cf. Software Misadventures interview title: "On failure injection, chaos engineering, extreme sports and being curious").

---

## Direct quotes / paraphrases captured

- "Chaos engineering is the facilitation of controlled experiments to identify systemic weaknesses." (Gremlin author bio — her standard definition)
- "You really can teach folks things, if you have a great curriculum." (SRE Apprentices, InfoQ, 2021-09-13)
- Apprentices should "see how senior members of the team interact to solve problems" by attending real meetings. (SRE Apprentices)
- Framing of resilience around the incident lifecycle: "detection, mitigation, resolution and prevention." (QCon London / InfoQ resilient-systems talk)

---

## Roster pairing / conflict reasoning (against `ROSTER.md`)

- **pairs_well_with: [nora-jones, adrian-cockcroft]** — both on the engineering roster.
  - `nora-jones`: Jeli founder; chaos engineering + incident analysis; co-author of O'Reilly *Chaos Engineering: System Resiliency in Practice*. Same cell (`reliability-sre-obs`), directly adjacent discipline — Butow runs the experiments, Jones analyzes the incidents. Strong amplifier.
  - `adrian-cockcroft`: ex-Netflix (the birthplace of Chaos Monkey / resilience engineering at scale) and ex-AWS. Cell `cloud-architecture`. Butow's chaos practice descends from the Netflix lineage Cockcroft helped establish; they reinforce each other on resilience-at-scale.
- **productive_conflict_with** — chosen from real ROSTER.md slugs:
  - `dhh` (David Heinemeier Hansson, `architecture-testing-craft`): "majestic monolith," anti-microservices, anti-cloud-complexity. Butow's chaos/SRE practice presumes distributed, failure-prone, multi-service systems worth instrumenting; DHH would argue much of that complexity is self-inflicted and a monolith removes the failure surface she's testing. Genuine, productive tension.
  - `charity-majors` (`reliability-sre-obs`): same cell, sharp disagreement of method — Majors champions **observability + "test in prod"** (high-cardinality instrumentation, debugging live) as the primary path to reliability, sometimes skeptical that pre-planned fault-injection GameDays catch the failures that matter versus instrumenting reality. Butow defends deliberate, controlled experiments and DRTs. Same goal (reliable systems), different primary lever — productive sharpening.

(Note: Nora Jones could also be framed as a conflict on the chaos-vs-incident-analysis axis, but the brief specifies her as a `pairs_well_with`, and she is genuinely a closer collaborator than an antagonist, so she stays in pairs.)

---

## All URLs consulted (sources)

1. https://www.gremlin.com/author/tammy-butow — Gremlin featured-author bio (Principal SRE; chaos definition; GameDays; Dropbox/DigitalOcean/NAB history)
2. https://archive.qconnewyork.com/speakers/tammy-butow — QCon NY speaker bio (Principal SRE @ Gremlin)
3. https://www.infoq.com/presentations/dropbox-drt/ — "0 to 100 days - Running DRTs at Dropbox" (2016-09-24); DRT methodology
4. https://www.infoq.com/podcasts/sre-apprentices/ — "Tammy Bryant Butow on SRE Apprentices" (2021-09-13); apprenticeship philosophy
5. https://www.infoq.com/presentations/chaos-engineering-resilient-systems/ — "Why the World Needs More Resilient Systems" (QCon London talk; incident-lifecycle framing)
6. https://www.usenix.org/conference/srecon18americas/presentation/butow — SREcon18 Americas "Chaos Engineering Bootcamp"
7. https://www.oreilly.com/people/tammy-butow/ — O'Reilly author page ("Chaos Day: When reliability reigns," 2018-10-03)
8. https://github.com/tammybutow — GitHub profile (Apple affiliation; chaosengineeringbootcamp, Talks repos)
9. https://www.linkedin.com/in/tammybutow/ — LinkedIn (Cupertino; Stanford GSB 2023–2024)
10. https://tambryantbutow.carrd.co — personal carrd (Statype VP Product; education; Girl Geek Academy; personal interests)
11. https://soundcloud.com/hashicast/episode-36-tammy-bryant-butow-statype — HashiCast Ep.36 (Statype VP Product role)
12. https://thenewstack.io/gremlins-tammy-butow-on-the-business-side-of-chaos-engineering/ — New Stack, business case for chaos (MTTD/MTTR) [page later gated]
13. https://open.spotify.com/episode/58lzoaAf2GAGHCAzDHCksp — SE-Radio Ep.325, Chaos Engineering
14. https://softwaremisadventures.com/p/tammy-bryant-butow-on-failure-injection — Software Misadventures interview (failure injection, extreme sports, curiosity)
15. https://www.crunchbase.com/person/tammy-butow — Crunchbase (Principal SRE @ Gremlin)
16. https://www.gremlin.com/blog/robert-ross-tammy-butow-incident-repro-playbook-validation-with-chaos-engineering-chaos-conf — Chaos Conf: incident repro + playbook validation

---

## Open items / caveats for future re-sync

- Apple role is **inferred from GitHub bio + Cupertino location**, not from a primary Apple-published source. Treat as best-available, not confirmed title.
- The "QCon London 2025" attribution needs primary confirmation before promoting to a `recent_signal_12mo`. If confirmed with a 2025 date, that alone is still pre-2025-05-30 and would not satisfy the "last 12 months from 2026-05-30" bar.
- If any post-2025-05-30 public signal appears (Apple talk, new book, podcast), flip `status: active`, move material into `recent_signal_12mo`, and raise confidence.
