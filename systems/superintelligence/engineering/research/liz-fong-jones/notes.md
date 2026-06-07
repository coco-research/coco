# Liz Fong-Jones — Research Notes

**Researcher:** Engineering Super Intelligence Team build, Wave E2 (reliability-sre-obs cell).
**Date of research:** 2026-05-30.
**Subject:** Liz Fong-Jones (方禮真) — slug `liz-fong-jones`.
**Method:** WebSearch + WebFetch against Wikipedia, her personal site, Honeycomb author/leadership pages, USENIX SREcon programs, O'Reilly, InfoQ, YOW! Conference, and OpenTelemetry community pages.

---

## Corrected assumptions

The build brief and `ROSTER.md` both describe Liz Fong-Jones as Honeycomb's **Field CTO**. That title is now stale.

- **Field CTO (2022 → late 2025):** She was promoted to Field CTO in 2022 after joining as Honeycomb's first developer advocate (Feb 2019) and rising to Principal Developer Advocate. Honeycomb's announcement post and YOW! Sydney 2025 speaker page (talk dated Thursday, December 11, 2025) still list her as Field CTO.
- **Technical Fellow (January 2026 → present):** Her personal site `lizthegrey.com`, her LinkedIn (`au.linkedin.com/in/efong`), and the Honeycomb author page (`honeycomb.io/author/lizf`) now list her current title as **Technical Fellow, Honeycomb**, with the role starting January 2026 and a focus on "technical advocacy and observability innovation."

Decision: the persona records `affiliations_2026` as Technical Fellow (current) while documenting Field CTO (2022–2025) under `past_affiliations`. The brief's "Field CTO" framing is preserved in narrative as her best-known recent title, with the correction noted. The cell/cell_role assignment (`reliability-sre-obs` / `specialist`) is unaffected.

Second correction: the brief implies she is currently active on the OpenTelemetry Governance Committee. Her own bio describes her as **OpenTelemetry Governance Committee emeritus** — she served and has since stepped off active governance. The OpenTelemetry community member listings did not surface her as a *current* GC member in 2026, consistent with the emeritus framing. Persona states "emeritus," not active.

Third note: education. CalTech 2005–2007 (left for financial reasons); MIT EECS, BSc 2014 (per Wikipedia). She joined Google in 2008 as a systems administrator *before* completing the MIT degree.

---

## Confirmed biography (dated)

- **Born:** 1987. Transgender woman; out and public about it. (Wikipedia)
- **Education:** CalTech 2005–2007 (dropped out, financial); MIT EECS BSc 2014, 4.9/5.0 GPA. (Wikipedia)
- **Google (2008–Jan 2019):** Joined 2008 as sysadmin (Mountain View). Progressed to SRE / software engineer across Cambridge MA and NYC offices. Worked on Google Cloud Load Balancer, Google Flights, Bigtable. Staff Developer Advocate + SRE 2017–2019. (Wikipedia, Honeycomb author bio, USENIX)
- **Labor organizing:** Internal organizing from ~2010 (equity engineering, accessibility). 2011 informal "union rep," negotiated Google+ real-name policy. 2016 contributed to the Never Again pledge codebase. 2017 "know your rights" training with Coworker.org. 2018 opposition to Project Maven (military AI) and Project Dragonfly (censored search); helped organize the Nov 1 2018 Google Walkout (~20,000 across 50 cities). Nov 29 2018 started a solidarity strike fund ($100K match pledge → $250K within days). Resigned Jan 2019; donated ~$100K exit stock grant to organizing workers. (Wikipedia)
- **The Solidarity Fund:** Incorporated 2020 by Coworker.org (co-founded with Meredith Whittaker). She is board president/founding board chair. Won Fast Company's 2022 World Changing Ideas Award. (Wikipedia)
- **Honeycomb:** Joined Feb 2019 as first developer advocate → Principal Developer Advocate → **Field CTO (2022)** → **Technical Fellow (Jan 2026)**. (Honeycomb, lizthegrey.com)
- **Signature Honeycomb engineering work:** Drove SLO product development, early OpenTelemetry adoption, and introduced AWS Graviton to cut Honeycomb's compute bill ~40%. (Honeycomb author bio)

---

## Recent signals (dated AFTER 2025-05-30, per quality bar)

1. **Technical Fellow appointment, Honeycomb — January 2026.** lizthegrey.com and honeycomb.io/author/lizf list her as Technical Fellow (Jan 2026–present), "technical advocacy and observability innovation."
   - https://lizthegrey.com/
   - https://www.honeycomb.io/author/lizf
2. **YOW! Sydney 2025 — "Platform Engineering Practices for Speedy Delivery," Thursday December 11, 2025.** Also presented at YOW! Brisbane and YOW! Melbourne 2025. (Title still listed as Field CTO at the time.)
   - https://yowcon.com/sydney-2025/speakers/3874/liz-fong-jones
   - https://yowcon.com/brisbane-2025/speakers/3863/liz-fong-jones
   - https://yowcon.com/melbourne-2025/speakers/3844/liz-fong-jones
3. **SREcon26 Americas (Seattle, WA, March 24–26, 2026) — "Monitoring and Observability" unconference session, Tuesday March 24, 3:55–5:30pm, with Daria Barteneva (Microsoft Azure).** Topics: cardinality costs, alert fatigue, OpenTelemetry at scale.
   - https://www.usenix.org/conference/srecon26americas/program
   - https://signoz.io/blog/srecon26-americas-observability-talks-guide/
4. **Observability Engineering, 2nd Edition (O'Reilly) — scheduled June 30, 2026.** Co-authored with Charity Majors, Austin Parker, George Miranda (ISBN 9781098179922). Note the 2nd edition adds Austin Parker as a co-author.
   - https://www.oreilly.com/library/view/observability-engineering-2nd/9781098179915/

(Items 2–4 all fall after the 2025-05-30 recency cutoff. Item 1 is current-as-of-now. Bar of ≥3 met with margin.)

---

## Public stances + evidence

- **"You DO NOT ACTUALLY KNOW if your code is working or not until you have observed it in production."** Testing-in-production / observability-driven development. Aligns with Charity Majors' "test in prod." Evidence: InfoQ "Cultivating Production Excellence" + Honeycomb materials.
  - https://www.infoq.com/presentations/measuring-service-level-objectives/
- **"A good SLO barely keeps your users happy. If you set your SLO too high, you're wasting money."** SLOs as the cornerstone of SRE; perfect reliability is wasteful; error budgets enable data-driven risk decisions.
  - https://www.infoq.com/presentations/measuring-service-level-objectives/
- **Error budgets + feature flags:** "If you've got some error budget left then sure, flag on a new feature for 1% of users. If it goes wrong you can roll it back without worrying about blowing your error budget." Couples error-budget accounting to progressive delivery.
  - https://platformengineering.org/talks-library/observability-and-measuring-slos
- **"Your tools are not going to fix a broken culture."** Production excellence is socio-technical; invest in people, processes, psychological safety before tools. Practice incident response before 3am.
  - https://www.infoq.com/presentations/measuring-service-level-objectives/
- **The three pillars are not the point — cross-correlation is.** "The problem isn't the pillars but the promise — the promise that if you instrument your code like this... the root cause will just reveal itself to you like magic." "I don't think the pillars are dead, but I think what we've been doing with them is no longer viable. There is simply too much data involved today to accept a lack of cross-correlation ability." OpenTelemetry produces wide structured events, not siloed metrics/logs/traces.
  - https://www.honeycomb.io/blog/opentelemetry-is-not-three-pillars
- **OpenTelemetry as the vendor-neutral instrumentation standard.** Early adopter at Honeycomb; OpenTelemetry Governance Committee emeritus; consistent advocacy to instrument once, export anywhere, avoid lock-in.
  - https://www.usenix.org/conference/srecon24americas/presentation/fong-jones
  - https://opentelemetry.io/community/members/
- **Developer productivity = build/feedback-loop times.** "The Most Important Developer Productivity Metric" (Honeycomb, Jan 14 2025) argues build times / fast feedback loops are the metric that matters; later reinforced by Docker Bake reproducible-builds work at SREcon 2025.
  - https://www.honeycomb.io/blog/most-important-developer-productivity-metric-build-times
- **Labor + ethics in tech:** Worker organizing, solidarity funding, opposition to military/censorship projects, financial-privilege redistribution. Founding board chair, The Solidarity Fund.
  - https://en.wikipedia.org/wiki/Liz_Fong-Jones
  - https://thebulletin.org/biography/liz-fong-jones/

---

## Roster relationships

- **pairs_well_with:** `charity-majors` (Honeycomb co-founder/CTO, co-author of Observability Engineering, shared "test in prod" worldview) and `cindy-sridharan` (distributed-systems / observability writer; Cindy's "Monitoring and Observability" / "three pillars" writing is in direct dialogue with Liz's). Both confirmed in ROSTER.md reliability-sre-obs cell, and both have research dirs already present.
- **productive_conflict_with:** `ben-treynor-sloss` (Google VP, coined "SRE," classical top-down SRE-as-discipline framing vs. Liz's observability-first, dev-owns-prod, culture-over-process emphasis) and `betsy-beyer` (Google SRE Book editor — the canonical Google SRE-book orthodoxy that Liz's Honeycomb-era practice both builds on and pushes past). Both are real ROSTER.md reliability-sre-obs slugs. Also defensible: `dhh` (anti-cloud / "majestic monolith," contrasts with her cloud-native observability worldview) — used as a secondary, cross-cell conflict edge.

---

## All URLs gathered

- https://en.wikipedia.org/wiki/Liz_Fong-Jones
- https://lizthegrey.com/
- https://www.honeycomb.io/author/lizf
- https://www.honeycomb.io/teammember/liz-fong-jones/
- https://www.honeycomb.io/blog/honeycomb-welcomes-new-field-cto
- https://www.honeycomb.io/blog/opentelemetry-is-not-three-pillars
- https://www.honeycomb.io/blog/most-important-developer-productivity-metric-build-times
- https://www.infoq.com/presentations/measuring-service-level-objectives/
- https://platformengineering.org/talks-library/observability-and-measuring-slos
- https://www.oreilly.com/library/view/observability-engineering/9781492076438/
- https://www.oreilly.com/library/view/observability-engineering-2nd/9781098179915/
- https://www.usenix.org/conference/srecon24americas/presentation/fong-jones
- https://www.usenix.org/conference/srecon26americas/program
- https://signoz.io/blog/srecon26-americas-observability-talks-guide/
- https://yowcon.com/sydney-2025/speakers/3874/liz-fong-jones
- https://yowcon.com/brisbane-2025/speakers/3863/liz-fong-jones
- https://yowcon.com/melbourne-2025/speakers/3844/liz-fong-jones
- https://opentelemetry.io/community/members/
- https://opentelemetry.io/blog/2024/otel-governance/
- https://thebulletin.org/biography/liz-fong-jones/
- https://au.linkedin.com/in/efong
- https://techleadjournal.dev/episodes/88/
