# Pat Helland — Research Notes

**Subject:** Pat Helland — distributed-systems elder; Salesforce Principal Architect.
**Slug:** `pat-helland` | **Cell:** data-and-storage | **Cell role:** specialist | **Home team:** engineering
**Researched:** 2026-05-30 | **Last verified:** 2026-05-30
**Status decision:** `active` (justified below — passes the recency bar, though narrowly).

---

## 1. Identity and current role (verified)

- **Real name:** Pat Helland.
- **Current title/affiliation:** Principal Architect, Salesforce.com (San Francisco). Verified via ResearchGate profile ("Principal Architect | Salesforce.com, San Francisco | CRM Infrastructure") and his own Substack about-page bio.
  - Source: https://www.researchgate.net/profile/Pat-Helland
  - Source: https://pathelland.substack.com/about
- **At Salesforce since:** early 2012, per his CMU bio ("Pat has been working on database technology at Salesforce since 2012"). Verified on two CMU talk pages.
  - Source: https://pdl.cmu.edu/talk-series/2025/061225.shtml
  - Source: https://db.cs.cmu.edu/events/pat-helland-salesforce/ (bio: "Pat Helland has worked at Salesforce since early 2012, focusing on multi-tenanted database systems, scalable reliable infrastructure for storage, and software defined networking.")
- **Career arc (self-described):** "I've been building databases, transactions, distributed systems, fault tolerant systems, messaging systems, and application platforms since 1978 at various companies including Tandem, Microsoft, Amazon, and now Salesforce."
  - Source: https://pathelland.substack.com/about
- **Note on assumption correction:** The task brief listed him as "ex-Amazon/Microsoft/Salesforce." This is **partially inaccurate** — he is *currently* at Salesforce (not ex-Salesforce). Amazon and Microsoft are past affiliations; Salesforce is the present employer. The ROSTER.md anchor ("Salesforce; 'Life Beyond Distributed Transactions,' immutability") is correct. Corrected in the persona's `affiliations_2026` (Salesforce, present) vs `past_affiliations` (Tandem, Microsoft, Amazon). His Tandem tenure (1980s) is where he worked on TMF/NonStop transaction processing; he was the lead architect of Microsoft Transaction Server (MTS) / the original autonomous-computing and SOA work at Microsoft in the late 1990s–2000s; and he spent time at Amazon before joining Salesforce in 2012.

---

## 2. Canonical works (verified URLs + theses)

### "Life Beyond Distributed Transactions: An Apostate's Opinion"
- First as CIDR 2007 position paper; re-published ACM Queue 14(5): 69–98 (2016) and Communications of the ACM (2016).
- CIDR/UCI PDF: https://ics.uci.edu/~cs223/papers/cidr07p15
- ACM Queue (2016 reprint): https://dl.acm.org/doi/10.1145/3012426.3025012
- CACM: https://dl.acm.org/doi/10.1145/3009826
- Semantic Scholar: https://www.semanticscholar.org/paper/Life-beyond-Distributed-Transactions:-an-Apostate's-Helland/c20baa16cb57ff4979569871d15294fa720bbc23
- **Thesis:** Large mission-critical apps reject distributed transactions. Build on **entities** (collections of keyed data atomically updatable *within* one entity, living on a single machine at a time, never atomically across entities), **activities** (workflow patterns that coordinate across entities and reach agreement without atomicity), and **at-most-once messaging** with idempotence and compensation rather than 2PC. The "apostate" framing is self-aware: Helland spent his career advocating transactions and global serializability, then argued you must give them up at scale.

### "Immutability Changes Everything"
- CIDR 2015; ACM Queue 13(9) (2015/2016); CACM.
- CIDR PDF: https://www.cidrdb.org/cidr2015/Papers/CIDR15_Paper16.pdf
- ACM Queue: https://queue.acm.org/detail.cfm?id=2884038
- CACM: https://cacm.acm.org/practice/immutability-changes-everything/
- ACM DL full HTML: https://dl.acm.org/doi/fullHtml/10.1145/2857274.2884038
- **Thesis:** Falling storage cost + distributed scale make immutability the default. "Accountants don't use erasers; otherwise they may go to jail." Append-only is the model: observations recorded forever, derived results computed on demand, you can't rewrite history (small fixes are themselves append-only). Drives the design of log-structured storage, event sourcing, copy-on-write, LSM trees, distributed snapshots, and key-value stores. Immutable data needs no distributed coordination to share.

### "Data on the Outside versus Data on the Inside"
- CIDR 2005: 144–153; later ACM Queue (2020).
- CIDR PDF: https://www.cidrdb.org/cidr2005/papers/P12.pdf
- ACM Queue (2020): https://queue.acm.org/detail.cfm?id=3415014
- Morning Paper summary: https://blog.acolyer.org/2016/09/13/data-on-the-outside-versus-data-on-the-inside/
- **Thesis:** Data *inside* a service is classical transactional relational data in one database, living in a single point of time (transactions) and a single point of space (one DB). Data *outside* (messages, files, events, key-value pairs exchanged between services) is **immutable, versioned, and uniquely identified** (URI/key); "the same no matter when or where it is referenced." SOA composes coarse-grained autonomous services; reference data and immutability enable interoperation. The two worlds have opposite strengths and need different reasoning.

### Other notable canon
- "Standing on Distributed Shoulders of Giants" — ACM Queue: https://queue.acm.org/detail.cfm?id=2953944
- "Space Time Discontinuum" — ACM Queue: https://queue.acm.org/detail.cfm?id=3372732
- "I'm Probably Less Deterministic Than I Used to Be" — ACM Queue 20(3) (2022): https://queue.acm.org/detail.cfm?id=3546935
- "Fail-fast Is Failing… Fast!" — ACM Queue: https://queue.acm.org/detail.cfm?id=3458812
- "Autonomous Computing" — ACM Queue 20(1) (2022).
- "Scalable OLTP in the Cloud: What's the BIG DEAL?" — CIDR 2024 (solo-authored).
- ACM Queue column name: "Escaping the Singularity… It's Not Your Grandmother's Database Anymore" (recurring column).

---

## 3. Recent signals (post-2025-05-30 — the recency bar)

This is the bar's tightest constraint: ≥3 entries dated AFTER 2025-05-30, each with URL.

1. **CIDR 2026 — "A Multi-tenant Relational OLTP Database at Salesforce"** (Helland co-author).
   - Presented Mon 19 Jan 2026, 1:30–3:00 PM, session "Data Platform Benchmarking and Optimization Techniques," chaired by Jignesh Patel. Conference 18–21 Jan 2026, Chaminade, CA, USA.
   - Authors: Vaibhav Arora, Subho Chatterjee, Terry Chong, Thomas Fanghaenel, Pat Helland, Jamie Martin, Kaushal Mittal, Nat Wyatt.
   - Describes SalesforceDB: relational OLTP, LSM-based storage engine, multi-tenant. Three production read optimizations: location cache (key probes), range filters (short range scans), early tombstone pruning (queue-organized tables).
   - URL (landing): https://vldb.org/cidrdb/2026/a-multi-tenant-relational-oltp-database-at-salesforce.html
   - URL (PDF): https://vldb.org/cidrdb/papers/2026/p28-arora.pdf
   - URL (program): https://www.cidrdb.org/cidr2026//program.html
   - **DATE: 2026-01-19 — AFTER cutoff ✓**

2. **CMU Parallel Data Laboratory talk — "Yours, Mine, and Ours: Efficient Set Reconciliation in O(n log n) of the SET DIFFERENCE"** (with Daniel May, Salesforce).
   - 12 June 2025, 12:00–1:00 PM ET. Abstract: "Extremely large sets can be reconciled in O(n log n) of the SET DIFFERENCE, not the underlying size of the sets." Variant of erasure/fountain codes; applications to replica repair (faster than Merkle trees), gossip, genome analysis, cloud control-plane management. Builds on SIGCOMM 2024 "Practical Rateless Set Reconciliation" (Yang et al.).
   - URL (PDL): https://pdl.cmu.edu/talk-series/2025/061225.shtml
   - **DATE: 2025-06-12 — AFTER cutoff ✓**

3. **CMU CSD calendar listing of the same talk** (corroborating artifact, distinct URL).
   - URL: https://csd.cmu.edu/calendar/parallel-data-laboratory-talk-pat-helland-daniel-may
   - **DATE: 2025-06-12 — AFTER cutoff ✓**

**Honest caveat on recency (logged per bar instruction):** Items 2 and 3 are the *same event* surfaced through two CMU pages. So strictly there are **two distinct recent events** (CIDR 2026 paper; the June 2025 CMU talk), spanning **three dated citable artifacts** after 2025-05-30. His Substack ("Scattered Thoughts on Distributed Systems") archive's most recent visible posts were from Dec 2023 at crawl time, and no 2025 ACM Queue/CACM column or QCon/VLDB 2025 keynote surfaced in targeted searches. He is nonetheless clearly an *actively publishing* researcher (a CIDR 2026 paper a few months ago), so `status: active` is correct rather than `archetype`. The recency profile is genuinely thinner than a frontier-lab persona's, which is expected for a 47-year-career systems elder whose primary output is now occasional deep papers and talks rather than a high-frequency public feed. Flagged for the next re-sync to recrawl the Substack archive (pagination may have hidden newer posts) and check ACM Queue 2025–2026.

---

## 4. Public stances (each cited)

- **Distributed transactions don't scale; design around entities + at-most-once messaging instead.** Evidence: Life Beyond Distributed Transactions — https://ics.uci.edu/~cs223/papers/cidr07p15
- **Immutability is the default at scale; append-only beats update-in-place. "Accountants don't use erasers."** Evidence: https://queue.acm.org/detail.cfm?id=2884038
- **Data inside a service (transactional, mutable, one place/time) is a different universe from data outside (immutable, versioned, uniquely identified). Don't conflate them.** Evidence: https://www.cidrdb.org/cidr2005/papers/P12.pdf
- **Constraints improve design; greenfield is harder than brownfield because it lacks constraints** (urban-planning analogy). Evidence: InfoQ "Software Architecture and Urban Planning" — https://www.infoq.com/podcasts/urban-planning-software-architecture/
- **"It was great while it lasted" — single-database transactional simplicity does not survive scaling; SOA/microservices reintroduce coordination complexity that you must design for explicitly.** Evidence: "Mind Your State for Your State of Mind" — https://www.infoq.com/presentations/taxonomy-cluster-distributed-storage/
- **LSM storage is the right engine for cloud multi-tenant OLTP — but reads need explicit help (location cache, range filters, tombstone pruning).** Evidence: CIDR 2026 paper — https://vldb.org/cidrdb/papers/2026/p28-arora.pdf

---

## 5. Pairs / conflicts (validated against ROSTER.md)

- **pairs_well_with:** `martin-kleppmann` (DDIA, CRDTs, local-first — Helland's immutability/data-outside thesis is upstream of much of DDIA's reasoning) and `leslie-lamport` (logical clocks, Paxos, TLA+ — the formal substrate beneath Helland's pragmatic "no distributed transactions" stance). Both are real data-and-storage cell slugs. ✓
- **productive_conflict_with:** `michael-stonebraker` (one-size-does-NOT-fit-all but a fierce defender of full relational/ACID transactions and a skeptic of giving up serializability — directly clashes with Helland's "apostate" abandonment of distributed transactions); and `dhh` (David Heinemeier Hansson, architecture-testing-craft cell — "majestic monolith," anti-microservices — clashes with Helland's SOA/service-boundary worldview). Both are real ROSTER slugs. ✓
  - Considered `eric-evans` (DDD bounded contexts actually *agree* with Helland — rejected as conflict). Considered `leslie-lamport` for conflict (rejected — used as pair; their disagreement is more tonal than substantive).

---

## 6. Source list (all real, verified during research)

1. https://pathelland.substack.com/about
2. https://www.researchgate.net/profile/Pat-Helland
3. https://pdl.cmu.edu/talk-series/2025/061225.shtml
4. https://csd.cmu.edu/calendar/parallel-data-laboratory-talk-pat-helland-daniel-may
5. https://vldb.org/cidrdb/2026/a-multi-tenant-relational-oltp-database-at-salesforce.html
6. https://vldb.org/cidrdb/papers/2026/p28-arora.pdf
7. https://www.cidrdb.org/cidr2026//program.html
8. https://ics.uci.edu/~cs223/papers/cidr07p15
9. https://queue.acm.org/detail.cfm?id=2884038
10. https://www.cidrdb.org/cidr2005/papers/P12.pdf
11. https://dl.acm.org/doi/10.1145/3012426.3025012
12. https://db.cs.cmu.edu/events/pat-helland-salesforce/
13. https://www.infoq.com/podcasts/urban-planning-software-architecture/
14. https://www.infoq.com/presentations/taxonomy-cluster-distributed-storage/
15. https://dblp.org/pid/h/PatHelland.html
16. https://queue.acm.org/detail.cfm?id=3546935
