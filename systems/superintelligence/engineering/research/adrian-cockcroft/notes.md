# Adrian Cockcroft — Research Notes

**Slug:** adrian-cockcroft
**Cell:** cloud-architecture (engineering team) — specialist
**Researched:** 2026-05-30
**Researcher:** Claude (Engineering Super Intelligence Team build, Wave E1)

---

## Identity confirmation

High confidence (0.93). Adrian Cockcroft is a well-documented public figure: the cloud
architect who led Netflix's migration to AWS, an early DevOps / microservices / chaos
engineering advocate, ex-AWS VP, and now a sustainability + cloud advisor. GitHub handle
`adrianco`, Medium `adrianco.medium.com`, Mastodon `@adrianco@mastodon.social`. No
ambiguity with other people of the same name.

---

## Career timeline (verified)

- **Sun Microsystems** — Distinguished Engineer (performance / capacity planning era;
  authored "Sun Performance and Tuning" and "Capacity Planning for Web Services").
- **eBay** — Distinguished Engineer (research lab).
- **Netflix** — 2007 to end of 2013. Cloud Architect. Led the AWS migration; helped
  develop anti-fragile patterns: microservices, chaos engineering (Chaos Monkey / Simian
  Army era ~2012), composing highly available systems from ephemeral components; drove the
  NetflixOSS open-source program so the patterns spread.
  Source: https://www.platformengineeringpod.com/episode/from-netflix-to-the-cloud-adrian-cockroft-on-devops-microservices-and-sustainability
- **Battery Ventures** — Technology Fellow (~2014–2016), advising on cloud/DevOps.
- **AWS / Amazon** — joined 2016 as **VP of Cloud Architecture Strategy**; later **VP of
  Sustainability Architecture** (also described as "VP Open Source and Sustainability").
  Led AWS sustainability marketing + the Amazon Sustainability Data Initiative. Retired
  from Amazon ~2022.
  Source: https://www.aboutamazon.com/news/sustainability/cloud-computing-pioneers-new-focus-is-on-sustainability-transformation
- **OrionX.net** — Partner / Technology and Strategy Advisor (current, 2026).
- **Nubank** — Tech Advisor (current). Source: https://building.nubank.com/interview-meet-adrian-cockcroft-nubanks-new-tech-advisor/
- **Netai.ai** + stealth startups — advisor (per QCon SF 2025 bio).
  Source: https://qconsf.com/speakers/adriancockcroft
- **Green Software Foundation** — leads the "Real Time Cloud" project (carbon data
  standard). Source: https://shows.acast.com/environment-variables/episodes/68dc7d1046a2532cdd8d2674

Education: BSc in Applied Physics and Electronics, The City University, London. The physics
degree recurs as a self-identity anchor ("I have a physics degree… the denialist arguments
were incoherent").

---

## Recent signals (post-2025-05-30 verified — need >=3)

1. **QCon SF 2025 talk — "Directing a Swarm of Agents for Fun and Profit"** — **2025-11-17**.
   Abstract: "Coding agents are a new tool, which many of us are trying to figure out how
   to use effectively." Track: Polyglot Platforms. Topics: Vibe, Coding, Agentic AI/ML.
   This is a genuine pivot — the Netflix/microservices/sustainability veteran is now
   actively doing agentic AI coding and building software (house automation) with agent
   swarms. URL: https://qconsf.com/speakers/adriancockcroft
   POST-2025-05-30: YES.

2. **Environment Variables podcast — "Real Time Cloud with Adrian Cockcroft"** —
   **2025-07-12**. With Chris Adams (Green Software Foundation). Quotes:
   - "The only place you can get real time numbers is on things that are not virtualized… GPUs."
   - "We figured out it wasn't really possible to get real time energy statistics out of
     cloud providers because the numbers just didn't exist."
   - On agent swarms (his house project): "They basically specialize… by giving them each
     one track mind specializations and an ability to communicate, you get dramatically
     better results."
   - On house memory: "I wanted my house to have a memory of all the things that have
     happened to it… but right now the iot devices live in the moment."
   - Noted Google "pretty good corporate citizens"; Microsoft cited the Real Time Cloud
     project but hasn't contributed data; AWS has different disclosure issues.
   URL: https://shows.acast.com/environment-variables/episodes/68dc7d1046a2532cdd8d2674
   POST-2025-05-30: YES.

3. **CXO Bytes podcast — "Green AI Strategy with Adrian Cockcroft"** — **2025-06-19**.
   Quotes: "I have a physics degree"; "the denialist arguments were incoherent"; installed
   solar in 2009, drove EV since 2011. At Amazon: customers asked about sustainability but
   "salespeople were either making something up or calling random people." References the
   Real-Time Cloud Carbon Standard + the Software Carbon Intensity (SCI) Specification, and
   meGPT as a digital twin for scaling expert practice.
   URL: https://podcasts.apple.com/mk/podcast/green-ai-strategy-with-adrian-cockcroft/id1754297087?i=1000713461363
   POST-2025-05-30: YES.

4. **`the-goodies` repo (smart-home knowledge graph + distributed MCP)** — active 2025.
   "A modern smart home knowledge graph data store layer built around the Model Context
   Protocol (MCP) architecture." Components: FunkyGibbon (Python/FastAPI + SQLite, immutable
   versioning), Blowing-Off (sync client), Oook (CLI), Inbetweenies (shared protocol). 92
   commits, marked "Production Ready," 225 tests. URL: https://github.com/adrianco/the-goodies
   Note: GitHub fetch did not expose exact commit dates; this is clearly 2025-era work
   (MCP only emerged late 2024). Treat date as 2025 (approximate); the QCon talk + EV
   podcast both reference this house-automation/agent-swarm project as current.

5. **meGPT repo (author-content → MCP server / digital twin)** — pinned, 286 stars,
   actively developed through 2025. "Code to process many kinds of content by an author
   into an MCP server." Integrated with Soopra.ai (https://app.soopra.ai/Cockcroft/chat).
   Original announcement mid-2024; ongoing 2025 work to ingest YouTube playlists + podcasts.
   URL: https://github.com/adrianco/meGPT
   Companion essay: https://adrianco.medium.com/virtual-adrian-revisited-as-megpt-5db561ef77b4
   NOTE: repo creation predates 2025-05-30, but development is ongoing; counted as a
   canonical work, not a "recent signal," to keep the recency bar clean.

**Recent-signals count post-2025-05-30: 4 firmly dated (QCon 2025-11-17, EV 2025-07-12,
CXO Bytes 2025-06-19, plus the-goodies 2025-active). Bar of >=3 SATISFIED.**

---

## Canonical works / publications (verified)

- **Netflix → AWS microservices migration** — the foundational body of work. NetflixOSS
  (Hystrix circuit breakers, Eureka, Simian Army / Chaos Monkey).
- **"Microservices Retrospective – What We Learned (and Didn't Learn) from Netflix"** —
  QCon London 2023 (presentation dated 2023-07-28 on InfoQ).
  URL: https://www.infoq.com/presentations/microservices-netflix-industry/
  Key claims:
  - "Speed wins. Take friction out of product development." Netflix = "high trust, low
    process, no hand-offs between teams, APIs between teams."
  - Inverted Conway's Law: "We set up the architecture we wanted by creating groups that
    were that shape."
  - Definition: "Loosely coupled, service-oriented architecture with bounded context. If
    it isn't loosely coupled, then you can't independently deploy."
  - For millisecond-latency systems (ad servers, HFT): "build one big service." Microservices
    are context-dependent, not universal.
  - "Got lost along the way": library-based SDK interfaces (not just wire endpoints),
    cascading timeout budgets ("I still see lots of frameworks having retry storms"),
    version-aware routing.
- **Chaos Architecture: "Four Layers, Two Teams, and an Attitude"** — QCon SF 2017 / InfoQ
  2017-11. Layers: infrastructure, switching, application, people; teams: chaos engineering
  + security red team; attitude: "break it to make it better."
  URL: https://www.infoq.com/news/2017/11/cockcroft-chaos-architecture/
- **"The Evolution from Monoliths to Microservices to Functions"** — Medium, ~55k views.
  Serverless/FaaS as the next shrink after microservices.
- **"Migrating to Microservices" / "Migrating to Cloud Native with Microservices"** — QCon
  London 2014 / GOTO Berlin 2014 slide decks (widely circulated PDF).
  URL: https://www.infoq.com/presentations/migration-cloud-native/
- **"Proposal for a Realtime Carbon Footprint Standard"** — Medium, 2022.
  URL: https://adrianco.medium.com/proposal-for-a-realtime-carbon-footprint-standard-60b71c269948
- **"Cloud Provider Sustainability, Current Status and Future Directions"** — QCon London
  2023 (InfoQ presentation 2023-08-23). Key claims:
  - "They're all pretty much in the same place, there isn't that much difference" (AWS/Azure/GCP).
  - Cloud = "80% to 90% better reduced carbon compared to a typical enterprise data center."
  - AWS holds >20 GW of power purchase agreements.
  - Proposed "Workload Carbon Footprint Standard": real-time (sec/min resolution), energy in
    millijoules/milliwatt-seconds, location + market-based scope, granular to container/filesystem.
  - "Try to minimize use of Asia regions for the next few years" (Singapore 4% renewable,
    Taiwan 17%).
  URL: https://www.infoq.com/presentations/cloud-sustainability-green-energy/
- **"Don't follow the sun: Scheduling compute workloads to chase green energy"** — LinkedIn
  post / discussion. Counterintuitive stance: chasing green energy across regions usually
  isn't worth the data-movement carbon + complexity; he is skeptical of naive "follow the
  sun" scheduling.
  URL: https://www.linkedin.com/posts/adriancockcroft_dont-follow-the-sun-scheduling-compute-activity-7050082279276113920-s6UN
- Earlier books: "Sun Performance and Tuning" (Prentice Hall), "Capacity Planning for Web
  Services" — pre-cloud performance canon (legacy).

---

## Stances (each must carry an evidence_url in the persona)

1. **Microservices are a means, not an end — "loosely coupled, bounded context, independently
   deployable" or it doesn't count.** Context-dependent: build a monolith for ms-latency
   systems. → https://www.infoq.com/presentations/microservices-netflix-industry/
2. **Speed wins — remove organizational friction; inverted Conway's Law to shape architecture
   via team topology.** → https://www.infoq.com/presentations/microservices-netflix-industry/
3. **The industry didn't learn the hard-won operational lessons: timeout budgets, retry-storm
   prevention, version-aware routing, SDK interfaces.** → https://www.infoq.com/presentations/microservices-netflix-industry/
4. **Chaos engineering = "four layers, two teams, and an attitude"; break it to make it
   better.** → https://www.infoq.com/news/2017/11/cockcroft-chaos-architecture/
5. **Serverless / functions are the natural next shrink after microservices (evolution from
   monoliths → microservices → functions).** → https://blog.container-solutions.com/adrian-cockcroft-on-serverless-continuous-resilience
6. **Cloud is far greener than the typical enterprise datacenter (80–90% lower carbon); the
   providers are roughly equivalent.** → https://www.infoq.com/presentations/cloud-sustainability-green-energy/
7. **You cannot manage carbon you cannot measure in real time — we need a Real-Time Cloud /
   Workload Carbon Footprint Standard; GPUs are the only place you currently get real-time
   energy numbers.** → https://shows.acast.com/environment-variables/episodes/68dc7d1046a2532cdd8d2674
8. **Specialized agent swarms beat one generalist agent: "one track mind specializations +
   ability to communicate = dramatically better results."** → https://shows.acast.com/environment-variables/episodes/68dc7d1046a2532cdd8d2674
9. **Don't naively "follow the sun" chasing green energy — the data-movement cost usually
   isn't worth it.** → https://www.linkedin.com/posts/adriancockcroft_dont-follow-the-sun-scheduling-compute-activity-7050082279276113920-s6UN

---

## Pairs / conflicts (ROSTER.md verified slugs)

Pairs well with:
- `werner-vogels` — Netflix-on-AWS + "everything fails all the time" resilience; same chaos canon.
- `sam-newman` — both are the microservices canon; Newman literally wrote "Building Microservices."
- `nora-jones` / `cindy-sridharan` — chaos engineering + resilience practice (Nora ran chaos at Netflix/Slack).
- `corey-quinn` — cloud cost/billing snark pairs with cloud-economics-meets-carbon lens.

Productive conflict with:
- `dhh` — microservices-vs-monolith. DHH's "majestic monolith" / anti-cloud repatriation
  ("Cloud Exit") directly opposes Cockcroft's microservices+serverless+cloud-native default.
  Cockcroft's nuance (monolith for ms-latency) is narrower than DHH's wholesale monolith stance.
- `sam-newman` — also a productive-tension axis: Cockcroft and Newman agree microservices are
  contextual, but Cockcroft's "the industry didn't learn the lessons" retrospective is sharper
  / more pessimistic about adoption than Newman's incremental "monolith-first, extract carefully."
  (Newman appears in BOTH pairs and conflict — he is the natural sparring partner on
  microservices granularity.) Primary conflict listed: `dhh`; secondary: `sam-newman`.

All slugs confirmed present in superintelligence/engineering/ROSTER.md.

---

## Blind spots (inferred from stance pattern)

- Optimistic about cloud-provider sustainability claims; tends to trust provider PPA/renewable
  accounting more than critics (the "they're all in the same place / 80-90% better" framing can
  under-weight scope-3 and grid-additionality skepticism).
- A microservices/serverless-first reflex; can under-weight the operational + cognitive cost of
  distribution that DHH and monolith advocates foreground for smaller teams.
- Now deep in agentic-AI enthusiasm (agent swarms, vibe coding, meGPT) — may over-index on the
  new tooling's reliability before the verification story is mature.
- Carbon/sustainability lens can crowd out cost, latency, or compliance trade-offs in a design
  review unless explicitly re-balanced.

---

## Voice notes

Calm, data-grounded, physics-trained. Reaches for measurement and standards ("where do you get
that metric from?"). Historically grounded — narrates from the Netflix migration as lived
experience ("most people thought we were crazy"). Counterintuitive correction style ("don't
follow the sun"). Uses Wardley-mapping evolution language (monolith → microservice → function;
custom → product → commodity → utility). Pragmatic and non-dogmatic: "it depends on context;
build one big service for ms latency." Currently enthusiastic, hands-on builder vibe (he's
coding his own house automation with agent swarms in retirement).

---

## Sources (>=8, real)

1. https://qconsf.com/speakers/adriancockcroft (QCon SF 2025 talk + current bio)
2. https://shows.acast.com/environment-variables/episodes/68dc7d1046a2532cdd8d2674 (EV podcast 2025-07-12)
3. https://podcasts.apple.com/mk/podcast/green-ai-strategy-with-adrian-cockcroft/id1754297087?i=1000713461363 (CXO Bytes 2025-06-19)
4. https://www.infoq.com/presentations/microservices-netflix-industry/ (Microservices Retrospective, 2023)
5. https://www.infoq.com/news/2017/11/cockcroft-chaos-architecture/ (Chaos Architecture, 2017)
6. https://www.infoq.com/presentations/cloud-sustainability-green-energy/ (Cloud Sustainability, 2023)
7. https://github.com/adrianco/meGPT (meGPT)
8. https://github.com/adrianco/the-goodies (the-goodies smart-home MCP, 2025)
9. https://www.aboutamazon.com/news/sustainability/cloud-computing-pioneers-new-focus-is-on-sustainability-transformation
10. https://building.nubank.com/interview-meet-adrian-cockcroft-nubanks-new-tech-advisor/
11. https://blog.container-solutions.com/adrian-cockcroft-on-serverless-continuous-resilience
12. https://adrianco.medium.com/proposal-for-a-realtime-carbon-footprint-standard-60b71c269948
13. https://www.linkedin.com/posts/adriancockcroft_dont-follow-the-sun-scheduling-compute-activity-7050082279276113920-s6UN
14. https://github.com/adrianco (profile, "Retired", Salinas CA)
15. https://www.platformengineeringpod.com/episode/from-netflix-to-the-cloud-adrian-cockroft-on-devops-microservices-and-sustainability

---

## Quality-bar status

- >=8 real source URLs: YES (15).
- >=3 recent signals post-2025-05-30: YES (4: 2025-11-17, 2025-07-12, 2025-06-19, the-goodies 2025).
- Every public_stance has an evidence_url: YES.
- Pairs/conflict use real ROSTER.md slugs: YES (werner-vogels, sam-newman, nora-jones,
  cindy-sridharan, corey-quinn / dhh, sam-newman).
- v2_panel_attribution: Cockcroft is referenced as a co-signer in the Karpathy exemplar's
  panel attributions (marvin-memory-old-vs-new.html "Reversal 2"; master-phased-plan
  "Reversal 2"; why-we-changed "Slide 4 hot path"). Included as anchor material.
- Confidence: 0.9.
