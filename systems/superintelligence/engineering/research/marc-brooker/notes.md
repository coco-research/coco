# Marc Brooker — Research Notes

**Researched:** 2026-05-30
**Slug:** marc-brooker
**Cell:** cloud-architecture (cell_role: specialist)
**Team:** engineering (home_team: engineering)

---

## Identity & current role (VERIFIED + CORRECTION)

- **Correction to task brief.** The brief specified Marc Brooker as "AWS Senior Principal Engineer." As of early 2026 he has been promoted to **VP and Distinguished Engineer at AWS**, focusing on spec-driven AI-assisted development. His own blog "About" text (slow to update) still reads "engineer at Amazon Web Services... working on databases, serverless, and serverless databases," but two independent 2026 sources confirm the VP/Distinguished Engineer title:
  - SE Radio episode 710 (2026-03-04) explicitly introduces him as "VP and Distinguished Engineer at AWS." https://se-radio.net/2026/03/se-radio-710-marc-brooker-on-spec-driven-ai-dev/
  - Conference/speaker listing corroborates the seniority arc (Sr Principal → DE/VP). https://www.conferencecast.tv/speaker-42423-marc-brooker
  - Persona frontmatter uses `affiliations_2026: ['Amazon Web Services (VP and Distinguished Engineer)']` and notes the prior Sr Principal title under past context. Logged the title change here per instruction to "correct wrong assumptions."

- At AWS since 2008 (~17–18 years). Worked on EC2, EBS, IoT, then AWS Lambda (scaling, virtualization, Firecracker), Aurora Serverless, and distributed databases (DynamoDB-adjacent correctness work). South African; PhD University of Cape Town (multistatic radar simulation, 2008).
- Personal blog: **brooker.co.za/blog** ("Marc's Blog"). Very active — multiple posts per month through 2026. All opinions "my own."
- LinkedIn: https://www.linkedin.com/in/marc-brooker-b431772b

---

## Recent signals (post-2025-05-30, for recent_signal_12mo) — VERIFIED >= 3 ✅

All dates confirmed from the blog index page (brooker.co.za/blog/). Found 11 distinct 2026 posts plus late-2025 posts; selected the strongest:

1. **2026-05-20 — "Agentic software development hypothesis"**
   - https://brooker.co.za/blog/2026/05/20/hypothesis.html
   - Thesis in three escalating forms: any coding task with (weak) a complete spec / (strong) a deterministic oracle / (strongest) a non-adversarial oracle "will become trivial." Acknowledges most real tasks lack complete specs and most oracles aren't deterministic. Frames where agentic coding actually bites.

2. **2026-05-18 — "What's Easy Now? What's Hard Now?"**
   - https://brooker.co.za/blog/2026/05/18/whats-easy-whats-hard.html
   - Maps which engineering work agents collapsed vs. what remains hard (specs, judgment, verification, taste).

3. **2026-04-30 — "It's time to be right."**
   - https://brooker.co.za/blog/2026/04/30/be-right.html
   - Four-quadrant frame: defect *frequency* x defect *seriousness*. Argues agentic-AI adoption is gated by **defect rate**, not peak capability. "Defect rate is going to be one of the main inputs into how many people can use an agent." Focus on the **left tail** (failures), not best-case demos.

4. **2026-04-09 — "Spec Driven Development isn't Waterfall"**
   - https://brooker.co.za/blog/2026/04/09/waterfall-vs-spec.html
   - Defends spec-driven dev against the "this is just waterfall" objection; specs are living, iterative artifacts that drive both code generation and property-based tests.

5. **2026-01-21 — "Pass@k is Mostly Bunk"**
   - https://brooker.co.za/blog/2026/01/21/pass-k.html
   - pass@k is "exponentially forgiving"; "There's a value of k, a fairly low one generally, that can make anything look good." Humans aren't that forgiving: "I tried 10 times and it only worked once, what a piece of junk." Keep metrics honest.

Other recent posts confirmed (available as supporting material, not all used as signals):
- 2026-03-25 "What about juniors?" https://brooker.co.za/blog/2026/03/25/ic-junior.html
- 2026-03-20 "My heuristics are wrong. What now?" https://brooker.co.za/blog/2026/03/20/ic-leadership.html
- 2026-03-18 "Music To Build Agents By" https://brooker.co.za/blog/2026/03/18/apprentice.html
- 2026-02-25 "SFQ: Simple, Stateless, Stochastic Fairness" https://brooker.co.za/blog/2026/02/25/sfq.html (stochastic fairness queuing — the noisy-neighbor algorithm used in Lambda)
- 2026-02-07 "You Are Here" https://brooker.co.za/blog/2026/02/07/you-are-here.html
- 2026-01-12 "Agent Safety is a Box" https://brooker.co.za/blog/2026/01/12/agent-box.html
- 2025-12-16 "On the success of 'natural language programming'" https://brooker.co.za/blog/2025/12/16/natural-language.html
- 2025-12-15 "What Does a Database for SSDs Look Like?" https://brooker.co.za/blog/2025/12/15/database-for-ssd.html — distributed-log durability, 30s working-set RAM sizing, 32kB transfer sizing, cross-AZ replication. "The modern database commits transactions to a distributed log, which provides multi-machine multi-AZ durability."
- 2025-11-20 "What Now? Handling Errors in Large Systems" https://brooker.co.za/blog/2025/11/20/what-now.html

> Note: The "Scaling Correctness" Antithesis BugBash podcast (2025-08-06) and the "Fifteen years of TLA+ at AWS" keynote (2024) are strong but fall OUTSIDE the post-2025-05-30 recency window, so they are filed under canonical_works / key_publications rather than recent_signal_12mo. Recency bar of >=3 is comfortably met by the 2026 blog posts above.

---

## Canonical works & publications (VERIFIED)

### Amazon Builders' Library (author page: https://aws.amazon.com/builders-library/authors/marc-brooker/)
- **"Timeouts, retries, and backoff with jitter"** — the canonical operational-resilience reference.
  - https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
  - Core heuristics: set timeouts on ALL remote calls (pick acceptable false-timeout rate, e.g. 0.1% → use p99.9 of downstream latency, pad for network); retries only safe for transient/random failures, never load-based; retry at a SINGLE stack layer (avoid multiplicative retry storms); side-effecting APIs need idempotency; exponential backoff WITH a cap; cap total retry attempts (token bucket, in AWS SDKs since 2016) rather than relying on backoff alone; ADD JITTER to break synchronized retries; for scheduled work use *deterministic per-host* jitter (consistent, debuggable). Famous framing: "retries are selfish."

### Formal methods writing (blog)
- **"Formal Methods: Just Good Engineering Practice?"** (2024-04-17) https://brooker.co.za/blog/2024/04/17/formal/
  - Formal methods reduce TOTAL engineering cost by catching design flaws before construction; software lets design+construction happen simultaneously, which is a trap. Spectrum of rigor: whiteboard decision tables → state machines → TLA+ → deterministic simulation. Quotes Wellington ("Engineering is... the art of not constructing... doing with one dollar what any bungler can do with two") and Hyrum's Law ("With sufficient users of an API, all observable behaviors will be depended on by somebody"). TLA+ enables "verified aggressive optimizations" — explore correctness/performance tradeoffs early.
- **"Formal Methods Only Solve Half My Problems"** (2022-06-02) https://brooker.co.za/blog/2022/06/02/formal.html
- **"Getting into formal specification, and getting my team into it too"** (2022-07-29) https://brooker.co.za/blog/2022/07/29/getting-into-tla.html
- Keynote: **"Fifteen years of TLA+ at AWS"** (TLA+ Conf, 2024) https://www.youtube.com/watch?v=HxP4wi4DhA0

### Time / clocks
- **"It's About Time!"** (2023-11-27) https://brooker.co.za/blog/2023/11/27/about-time.html — five escalating levels of dependence on physical time; ties to AWS microsecond clock sync (Nov 2023). "If you can come up with a good explanation for what will happen when time is wrong, and you're OK with that happening with some probability, then you should feel OK using physical time."

### Lambda
- **"Ten Years of AWS Lambda"** (2024-11-14) https://brooker.co.za/blog/2024/11/14/lambda-ten-years.html — Node.js launch choice (npm), underestimated language-flexibility demand, median-latency focus (not just tail) for microservice compounding, stochastic fairness queuing for noisy neighbors, multi-AZ persistent worker manager.

### Peer-reviewed publications (publications.html — https://brooker.co.za/blog/publications.html)
- **Systems Correctness Practices at AWS: Leveraging Formal and Semi-formal Methods** — Brooker & Ankush Desai, ACM Queue Vol 22 No 6 / CACM, 2025. https://queue.acm.org/detail.cfm?id=3712057 (DOI https://dl.acm.org/doi/10.1145/3712057). NOTE: queue.acm.org returned 403 to WebFetch but the title/authors/venue are confirmed via search result snippets and the publications page. Advocates a spectrum: formal methods (TLA+, P), deterministic simulation testing, fault injection, property-based testing.
- **Resource Management in Aurora Serverless** — VLDB 2024, **Best Paper**. (Brooker et al., incl. Tim Kraska, Doug Terry.)
- **On-demand Container Loading in AWS Lambda** — USENIX ATC 2023, **Best Paper**. (Brooker, Danilov, Greenwood, Piwonka.)
- **Firecracker: Lightweight Virtualization for Serverless Applications** — NSDI 2020. (Agache, Brooker, et al.)
- **Millions of Tiny Databases** — NSDI 2020. (Brooker, Tao Chen, Fan Ping) — Physalia; covers leases/consensus/cell-based isolation.
- **Restoring Uniqueness in MicroVM Snapshots** — arXiv 2021 (Brooker, ..., Colm MacCárthaigh).
- **How Amazon Web Services Uses Formal Methods** — CACM 2015 (Newcombe, Rath, Zhang, Munteanu, Brooker, Deardeuff). The paper that put TLA+ at AWS on the map. https://cacm.acm.org/research/how-amazon-web-services-uses-formal-methods/
- Earlier: radar-simulation papers (IEEE TAES, etc.) 2006–2011 from his Cape Town PhD.

---

## Public stances (each with evidence URL) — VERIFIED

1. Retries are "selfish"; timeouts + capped exponential backoff + jitter are mandatory, retry at one layer only, side-effecting APIs need idempotency. → builders-library timeouts-retries-and-backoff-with-jitter.
2. Formal methods (esp. TLA+) are just good engineering practice — they reduce total cost and INCREASE velocity by catching design bugs before construction. → 2024/04/17/formal.
3. Use deterministic, per-host jitter for scheduled work (debuggable), random jitter for retry timing. → builders-library.
4. Agentic-AI adoption is gated by DEFECT RATE, not peak capability; obsess over the left tail. → 2026/04/30/be-right.
5. pass@k is "mostly bunk" — exponentially forgiving; keep eval metrics honest. → 2026/01/21/pass-k.
6. Specs are the central artifact in AI-assisted dev; "vibe coding" doesn't scale to complex codebases (forgets earlier requirements, regresses). → SE Radio 710 + 2026/04/09 waterfall-vs-spec.
7. Improving clock accuracy lets you safely depend on physical time — IF you can state what happens when the clock is wrong and accept that probability. → 2023/11/27/about-time.
8. Modern databases should commit to a distributed log for multi-AZ durability rather than local-disk durability. → 2025/12/15 database-for-ssd.

---

## Pairs / conflicts (using REAL ROSTER.md slugs) — VERIFIED against ROSTER.md

ROSTER cloud-architecture cell: james-hamilton, werner-vogels, adrian-cockcroft, marc-brooker, brendan-burns, eric-brewer, colm-maccarthaigh, radia-perlman.
data-and-storage: leslie-lamport (TLA+/Paxos), pat-helland, martin-kleppmann, etc.
architecture-testing-craft: dhh (anti-serverless/anti-cloud "majestic monolith"), kent-beck, martin-fowler.

- **pairs_well_with:**
  - `leslie-lamport` — TLA+ creator; Brooker is AWS's most public TLA+ practitioner. Direct lineage.
  - `colm-maccarthaigh` — AWS DE, co-author on the MicroVM snapshots paper; formal verification + networking; same cell.
  - `james-hamilton` — AWS DE, datacenter/Nitro economics; build-vs-managed + serverless infra economics; same cell.
  - `werner-vogels` — "everything fails all the time" — Brooker's resilience canon operationalizes Vogels' worldview; same cell.
  - `kent-beck` — property-based testing + tests-as-spec overlaps Brooker's spec-driven-dev verification stance.
- **productive_conflict_with:**
  - `dhh` — DHH's "majestic monolith" / anti-serverless / cloud-repatriation stance is the cleanest opposite of Brooker's serverless-native worldview.
  - `john-carmack` — "AGI now," capability-maximalist; Brooker counters with defect-rate-gated adoption and "pass@k is bunk."

---

## Blind spots (analysis)

- Deep AWS-insider lens; reasons from hyperscaler-scale primitives (distributed logs, microsecond clocks, cell isolation) that small teams can't replicate — can under-weight the on-prem / small-shop reality DHH champions.
- Correctness-first instinct can read as over-engineering to teams that ship fine with looser guarantees.
- His formal-methods enthusiasm assumes teams have the discipline/time to invest up front; under-weights org adoption friction (he himself wrote "getting my team into it").

---

## Voice notes

Calm, precise, quantitative South-African engineer voice. Reaches for concrete numbers (p99.9, 0.1% false-timeout, 30-second working set, 32kB transfers, $100). Loves a crisp aphorism ("retries are selfish"; "be right"; "pass@k is mostly bunk"). Cites Wellington and Hyrum's Law. Frames problems as distributions and tails. Honest about limits ("only solves half my problems"). Pedagogical, not preachy.

---

## Quality-bar self-check

- [x] >= 8 real source URLs (have ~14 unique).
- [x] >= 3 recent signals post-2025-05-30 (have 5 dated 2026 blog posts).
- [x] Every public_stance has a working evidence_url.
- [x] Corrected the title assumption (Sr Principal → VP & Distinguished Engineer) and logged it.
- [x] affiliations_2026 single-quoted (contains a colon-free value but parenthesized title; single-quoted to be safe).
- [x] pairs/conflicts all map to real ROSTER.md slugs.
