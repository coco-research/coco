# Charity Majors — research notes

**Researched:** 2026-05-30
**Slug:** charity-majors
**Team / cell:** engineering / reliability-sre-obs, cell_role lead-driver
**Researcher:** SI-Eng build agent (Wave E2)

These are the raw, dated findings backing `superintelligence/engineering/personas/charity-majors.md`.
Saved so future re-syntheses do not re-crawl. All URLs verified reachable on 2026-05-30.

---

## Identity confirmation

Charity Majors (handle **@mipsytipsy**) is the co-founder and CTO of Honeycomb.io. Confirmed
via the Honeycomb leadership page and her personal blog **charity.wtf**. Identification is
unambiguous — single, distinctive public figure. Confidence high.

- Honeycomb leadership bio: https://www.honeycomb.io/teammember/charity-majors/
- Personal blog: https://charity.wtf/
- Mastodon: https://hachyderm.io/@mipsytipsy
- Bluesky: https://bsky.app/profile/charity.wtf
- X / Twitter: https://x.com/mipsytipsy

### Career timeline (verified)
- Grew up in rural Idaho; was a classical-piano performance major; dropped out of college.
- **Linden Lab** — worked on infrastructure and the databases powering Second Life.
- **Parse** — ~3.5 years (pre- and post-acquisition by Facebook).
- **Facebook** — production engineering manager (post-Parse acquisition).
- **Honeycomb** — co-founded 2016; CTO and co-founder.
- Recurring theme she states about herself: "always seems to end up responsible for the databases."
- Source: honeycomb.io author/leadership pages + Pragmatic Engineer interview.

NOTE / corrected assumption: the brief framed her primarily around "test in production" and
high-cardinality. Both are real and central, but her 2025-2026 center of gravity has shifted to
**Observability 2.0** (single source of truth = wide structured events) and the **ops-vs-dev /
"bring back ops pride"** debate, plus a notable **AI/agentic-development pivot**. The persona
weights those accordingly rather than over-indexing on the older "test in prod" framing.

---

## Foundational / canonical works

### "Yes, I Test in Production (And So Do You)" — Honeycomb blog (2021-09-10)
The signature "test in production" essay. Argues testing in prod "has gotten a bad rap"; you are
*already* testing in production whether you admit it or not, so build the tooling (canaries,
feature flags, instrumentation, observability) to do it safely and deliberately.
- https://www.honeycomb.io/blog/yes-i-test-in-production-and-so-do-you
- Talk version (QCon SF 2018, on InfoQ): https://www.infoq.com/presentations/testing-production-2018/

### "The Engineer/Manager Pendulum" — charity.wtf (2017-05-11)
Her most-cited management essay. Thesis: the best technical leaders oscillate between IC and
management every few years rather than picking a lane and climbing forever. Became an
industry-standard career frame; she gave a "goes mainstream" follow-up keynote at SREcon23 EMEA.
- https://charity.wtf/2017/05/11/the-engineer-manager-pendulum/
- SREcon23 EMEA: https://www.usenix.org/conference/srecon23emea/presentation/majors

### "There Is Only One Key Difference Between Observability 1.0 and 2.0" — charity.wtf (2024-11-19)
The canonical statement of the Observability 2.0 thesis. Quote (paraphrased from the piece):
> "Observability 2.0 has one source of truth: wide, structured log events, from which you can
> derive all the other data types. That's it. That's what defines each generation."
Argues you **cannot** simultaneously store data across multiple "pillars" AND keep a single source
of truth — they are mutually exclusive architectures.
- https://charity.wtf/2024/11/19/there-is-only-one-key-difference-between-observability-1-0-and-2-0/
- Honeycomb companion post: https://www.honeycomb.io/blog/one-key-difference-observability1dot0-2dot0
- Honeycomb "It's Time to Version Observability": https://www.honeycomb.io/blog/time-to-version-observability-signs-point-to-yes

### "Observability Engineering" (O'Reilly) — book, co-authored
1st edition (2022): Charity Majors, Liz Fong-Jones, George Miranda. ISBN 9781492076445.
- https://bookshop.org/p/books/observability-engineering-achieving-production-excellence-charity-majors/a245b98bfc15568f
2nd edition (2026, dead-tree June 2026): adds **Austin Parker** as a 4th co-author (OpenTelemetry
+ AI emphasis). 32 new chapters; ~90% new material; new chapters on cost, governance, AI;
contributor "rogues gallery" (Jeremy Morrell, Hanson Ho, Matt Klein, etc.).
- O'Reilly 2nd ed: https://www.oreilly.com/library/view/observability-engineering-2nd/9781098179915/

---

## Recent signal (last 12 months — all AFTER 2025-05-30)

### 2026-03-09 — "Your Data is Made Powerful By Context (so stop destroying it already)"
charity.wtf. Core thesis: data derives **exponential** power from relational context; adding a
field doesn't add linear value, it adds combinatorial value through new pairwise/multi-field
relationships. The "three pillars" model destroys this by fragmenting connections at write time.
Connects directly to AI: "AI-SRE" agents need rich, context-preserving wide events because humans
can paper over imprecise tools with intuition but agents cannot. Memorable line: "AI, much like
alcohol, is both the cause of and solution to all of life's problems."
- https://charity.wtf/2026/03/09/your-data-is-made-powerful-by-context-so-stop-destroying-it-already-xpost/

### 2026-03-03 — "My (hypothetical) SRECon26 keynote"
charity.wtf. Argues SREs must **"swim out to meet"** the AI wave rather than wait for disruption.
Documents her own shift from cautious skepticism (early 2025: AI as a "slop-happy toddler") to
treating generative AI as a genuine paradigm shift. SREs are uniquely positioned because they are
pragmatic, outcome-focused guardrail-builders. The durable skills are organizational navigation /
business translation / influence — not raw coding, which is being commodified.
- https://charity.wtf/2026/03/03/my-hypothetical-srecon26-keynote-xpost/

### 2026-02-18 / 2026-02-19 — Observability Engineering 2nd-edition posts
"Martin Fowler told me the second edition should be shorter (it's twice as long)" (2026-02-18) and
"First I wrote the wrong book, then I wrote the right book" (2026-02-19). Announces the 2nd ed:
90% new material, sharper mission aimed at software engineers (not just ops), contributor gallery.
- https://charity.wtf/2026/02/18/observability-engineering-a-book-so-nice-we-wrote-it-twice-xpost/
- https://charity.wtf/2026/02/19/first-i-wrote-the-wrong-book-then-i-wrote-the-right-book-xpost/

### 2026-01-19 — "Bring Back Ops Pride"
charity.wtf. The ops-vs-dev manifesto. Quotes:
> "'Operations' is not a dirty word, a synonym for toil, or a title for people who can't write code."
> "The difference between dev and ops is a separation of concerns... If your concern is protecting
> [services'] ability to serve customers in the face of any and all threats... you are, in fact, in ops."
> "The hardest technical challenges... have always been on the infrastructure side."
Argues euphemistic rebranding (DevOps, SRE, platform engineering) obscures a real business
function and discourages talent. Restore dignity by naming ops honestly and rewarding excellence.
- https://charity.wtf/2026/01/19/bring-back-ops-pride-xpost/

### 2025-12 — Blog platform move (WordPress → Substack)
She moved/crossposts her blog to Substack in December 2025, noting her first Substack post was
"almost exactly a decade earlier" (2015-12-27). Newer charity.wtf posts carry the "-xpost" suffix.
- https://charitydotwtf.substack.com/
- https://charity.spicytakes.org/ (alt index)

### 2025-01-22 — Pragmatic Engineer interview "Observability: the present and future"
Dense source for her observability-vs-monitoring stance (note: just outside the 12-mo window for
2026-05-30, so used as a *stance citation* not a "recent signal"). Key claims captured below.
- https://newsletter.pragmaticengineer.com/p/observability-the-present-and-future

---

## Public stances (each must be cited)

1. **Observability 2.0 = one source of truth (wide structured events), not three pillars.**
   You cannot have both a single source of truth and pillar-siloed storage. 2.0 stores each
   request once, in one format: arbitrarily-wide structured events.
   - https://charity.wtf/2024/11/19/there-is-only-one-key-difference-between-observability-1-0-and-2-0/

2. **You are already testing in production — so do it deliberately.** Build canaries, feature
   flags, instrumentation, fast deploys; "testing in prod has gotten a bad rap."
   - https://www.honeycomb.io/blog/yes-i-test-in-production-and-so-do-you

3. **High cardinality is the whole point.** You must be able to slice on unbounded dimensions
   (request_id, user_id, build_id, feature flags). Metrics tools designed for low cardinality
   can't do this economically; you need columnar storage over wide events.
   - https://newsletter.pragmaticengineer.com/p/observability-the-present-and-future

4. **Static dashboards are a poor view into software; observability is interactive.**
   "Unless your dashboard is dynamic and allows you to ask questions, I feel like it's a really
   poor view into your software." Dashboards only show what you pre-graphed — you miss the unknown
   unknowns. (This is the live nerve of the dashboards/monitoring-vs-observability debate.)
   - https://newsletter.pragmaticengineer.com/p/observability-the-present-and-future

5. **SLOs are the right starting point, not dashboards.** SLOs are "APIs for engineering teams" —
   meet the target and you earn autonomy; they protect against micromanagement.
   - https://newsletter.pragmaticengineer.com/p/observability-the-present-and-future

6. **Ops is a legitimate, hard discipline — bring back ops pride.** Stop using "operations" as a
   slur or euphemizing it away; the hardest problems are on the infra side.
   - https://charity.wtf/2026/01/19/bring-back-ops-pride-xpost/

7. **The engineer/manager pendulum — oscillate, don't pick a lane.** Best technical leaders swing
   between IC and management every few years.
   - https://charity.wtf/2017/05/11/the-engineer-manager-pendulum/

8. **AI raises the stakes for observability, it doesn't replace it.** Agents validate changes at
   speed/scale and need context-rich wide events; SREs must "swim out to meet" AI.
   - https://charity.wtf/2026/03/09/your-data-is-made-powerful-by-context-so-stop-destroying-it-already-xpost/
   - https://charity.wtf/2026/03/03/my-hypothetical-srecon26-keynote-xpost/

---

## Productive conflict (real ROSTER.md slugs)

- **ben-treynor-sloss** (coined "SRE", Google VP) — the classic axis. Treynor Sloss's SRE canon is
  built on monitoring discipline, error budgets, the "four golden signals," dashboards, and
  carefully designed alerting. Majors's o11y-2.0 thesis is partly a critique of that monitoring /
  three-pillars / dashboard-centric worldview ("dashboards are a poor view into your software").
  They agree on SLOs/error-budgets but diverge sharply on dashboards-vs-observability and on the
  three-pillars data model. Genuine, well-documented tension. (ROSTER cell 2 confirmed.)
- **betsy-beyer** (Google SRE Book editor) — same cell; productive friction on the Google-SRE-canon
  vs. Honeycomb-o11y-2.0 framing. Sharpening rather than hostile.
- **dhh** (architecture-testing-craft; "majestic monolith," anti-cloud) — Majors's whole world is
  distributed-systems observability and cloud-native operability; DHH's monolith-on-owned-metal
  stance is a productive opposite pole on "do you even need this much o11y machinery."

## Pairs well with (confirmed in ROSTER cell 2 reliability-sre-obs)
- **liz-fong-jones** — Honeycomb field CTO; co-author of Observability Engineering; SLOs +
  OpenTelemetry. Closest collaborator. Confirmed slug in ROSTER.
- **cindy-sridharan** — distributed-systems / observability writing; long-time o11y ally. Confirmed.
- (also natural: nora-jones, tammy-butow on the chaos-engineering/test-in-prod axis.)

---

## Signature moves / voice notes
- Blunt, profane, funny. Swears freely. Blog is literally titled "charity.wtf." Tagline:
  "about technology, databases, startups, engineering management, and whiskey."
- Picks fights deliberately (tags posts "picking fights").
- Grounds abstract architecture claims in operational reality ("you are already doing X").
- Reasons about cost relentlessly — three pillars = paying to store the same request 3x.
- Career self-description: "always end up responsible for the databases."
- Coined / popularized: "test in production," "observability 2.0," "the engineer/manager pendulum,"
  high-cardinality observability, "single source of truth = wide events."

## Blind spots (inferred, hedged)
- Strong commercial alignment with Honeycomb's product thesis — the o11y-2.0 framing is also a
  sales position; a skeptic would note she has a vendor's interest in declaring three-pillars dead.
- Can be combative / absolutist in framing ("you CANNOT have both") where a hybrid is sometimes
  pragmatic.
- Focus is operability/runtime; less on upstream concerns like formal correctness or compliance.

---

## Source URL inventory (>=8, >=3 recent)
1. https://www.honeycomb.io/teammember/charity-majors/
2. https://charity.wtf/
3. https://charity.wtf/2024/11/19/there-is-only-one-key-difference-between-observability-1-0-and-2-0/
4. https://www.honeycomb.io/blog/yes-i-test-in-production-and-so-do-you
5. https://charity.wtf/2017/05/11/the-engineer-manager-pendulum/
6. https://newsletter.pragmaticengineer.com/p/observability-the-present-and-future
7. https://charity.wtf/2026/03/09/your-data-is-made-powerful-by-context-so-stop-destroying-it-already-xpost/   (recent)
8. https://charity.wtf/2026/03/03/my-hypothetical-srecon26-keynote-xpost/                                       (recent)
9. https://charity.wtf/2026/01/19/bring-back-ops-pride-xpost/                                                    (recent)
10. https://charity.wtf/2026/02/18/observability-engineering-a-book-so-nice-we-wrote-it-twice-xpost/             (recent)
11. https://www.oreilly.com/library/view/observability-engineering-2nd/9781098179915/
12. https://www.honeycomb.io/blog/time-to-version-observability-signs-point-to-yes
