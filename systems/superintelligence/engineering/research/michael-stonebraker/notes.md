# Michael Stonebraker — Research Notes

**Researched:** 2026-05-30
**Researcher:** Engineering Super Intelligence Team build (Wave E3, data-and-storage cell)
**Slug:** `michael-stonebraker`
**Confidence in identity:** 1.00 — single, unambiguous public figure; Turing laureate; deep public record.

These are dated raw findings, direct quotes, and every URL consulted, preserved so future
re-syntheses do not need to re-crawl.

---

## Identity & headline facts

- Born **October 11, 1943** (age 82 as of mid-2026). Source: Wikipedia.
- **Professor emeritus, UC Berkeley** (where he built Ingres and Postgres) and **adjunct
  professor emeritus, MIT CSAIL**. The subject brief said "MIT adjunct" — confirmed, with the
  refinement that as of the latest record he is *emeritus* at both Berkeley and MIT, while
  remaining active in research and as DBOS CTO/co-founder. Source: Wikipedia.
- **2014 ACM A.M. Turing Award** (announced March 2015). Official citation: *"for fundamental
  contributions to the concepts and practices underlying modern database systems."* Sources:
  ACM bulletin (Mar 2015), SD Times, Britannica.
- Other honors: IEEE John von Neumann Medal (2005), ACM Fellow (1994), National Academy of
  Engineering (1997, "for development and commercialization of relational and object-relational
  database systems"). Source: Wikipedia.

## Systems created (the canonical lineage)

1. **Ingres** — started 1973 at UC Berkeley; one of the first relational DBMS implementations.
   Commercialized as Ingres Corporation. (Wikipedia)
2. **Postgres** (POST-inGRES) — object-relational successor; became PostgreSQL, "the world's
   most popular database." (Wikipedia, BigDATAwire)
3. **C-Store** (2005) — column-oriented DBMS; commercialized as **Vertica**. (Wikipedia, KDnuggets)
4. **H-Store** (MIT) — main-memory OLTP engine; commercialized as **VoltDB**. (Wikipedia)
5. **Aurora / Borealis** — stream processing; commercialized as **StreamBase**. (Wikipedia)
6. **SciDB** (2008) — array DBMS for science / complex analytics; company Paradigm4. (Wikipedia)
7. **Mariposa** — distributed/federated DB research (post-Postgres). (Wikipedia)
8. **Tamr** — data unification / ML-driven data curation startup. (Wikipedia)
9. **DBOS** — current venture (see below).

Companies founded (per Wikipedia): Ingres Corporation, Illustra, Paradigm4, StreamBase Systems,
Tamr, Vertica, VoltDB, Hopara, and DBOS.

## DBOS — latest venture (verify-the-latest, per brief)

- **DBOS = "DataBase-oriented Operating System."** Thesis: run the OS state (scheduling, files,
  IPC, messaging) ON a distributed transactional database, so fault-tolerance, scaling, state
  management, observability, and security become database problems with ACID guarantees.
- **Founded / launched publicly:** March 12, 2024 press release announcing **$8.5M seed**, led by
  **Engine Ventures and Construct Capital**, with Sinewave and GutBrain Ventures. The research
  began ~2 years earlier as an MIT–Stanford project (VLDB 2022 progress report). Source: PRNewswire
  (2024-03-12); Crunchbase.
- **Co-founders** (PRNewswire 2024-03-12): Mike Stonebraker, Matei Zaharia (also Databricks),
  Christos Kozyrakis, Peter Kraft, Qian Li, Chuck Bear, Michael Coden. Andy Palmer joined the board.
- **ROLE DISCREPANCY — RESOLVED:** The March 2024 press release lists Stonebraker as
  **"Co-founder and CTO."** The current `dbos.dev/about` page describes him as **architect /
  co-founder** and lists **Qian Li as CEO**. (A separate generic web summary erroneously named
  "Andy Palmer" as CEO — Palmer is a board member, NOT CEO; that summary is wrong and is NOT used.)
  CORRECTION APPLIED IN PROFILE: Stonebraker is **co-founder and CTO** of DBOS; **Qian Li is CEO**.
  The brief's hint "serial DB founder" is correct; the brief did not assert he is CEO, so no
  conflict. We record him as CTO + co-founder, affiliations_2026 value single-quoted because it
  contains a colon.
- **Products:** DBOS Transact (open-source durable-execution library, Python + TypeScript) and
  DBOS Conductor (control plane for agents/workflows). Tagline: "Effortless Open Source Durable
  Workflow Orchestration"; "Durable AI, built effortlessly." Source: dbos.dev/about.

## Recent signals (must be dated AFTER 2025-05-30; collected for recency bar)

1. **2026-04-29 — DBOS blog: "Event-driven Programming is Usually a Poor Architecture"**
   (a.k.a. the "GOTO considered harmful (2026)" piece). Authored by Mike Stonebraker.
   URL: https://www.dbos.dev/blog/goto-considered-harmful-2026
   Argument: event-driven architectures are the modern equivalent of GOTO spaghetti — control
   flow is obscured, errors are scattered across independent handlers. Workflow architectures with
   durable execution win for multi-step, stateful, failure-prone applications — exactly the shape
   of AI agents. Quotes captured:
   - "In an event driven architecture, this is difficult to code, because each event handler is
     independent of the others, and it is difficult to perform global operations."
   - "If every handler is writing a log, one must trek through multiple logs looking for the error."
   - Concludes "the vast majority of applications" benefit from workflow over event-driven models.
   Invokes Dijkstra's "GOTO considered harmful" as the framing analogy.

2. **2026-01 — CIDR 2026 paper: "Consistency and Correctness in Data-Oriented Workflow Systems"**
   (Stonebraker et al.). URL: https://www.vldb.org/cidrdb/papers/2026/p9-stonebraker.pdf
   (PDF binary did not parse cleanly via WebFetch; title/author/venue confirmed by the URL path
   `cidrdb/papers/2026/p9-stonebraker.pdf` and the CIDR 2026 program. CIDR 2026 held January 2026,
   Chaminade CA per series convention.) Continues the DBOS durable-workflow correctness thesis.

3. **2025-12-10 — "Data 2025: Year in Review" webcast with Andy Pavlo (DBOS).**
   URL: https://www.dbos.dev/webcast-2025-in-review-with-mike-stonebraker-and-andy-pavlo
   Companion writeup (Vonng): https://blog.vonng.com/en/db/db-year-review-2025/
   Direct/near-direct Stonebraker quotes captured from the writeup:
   - On vector DBs: "A vector database is a bunch of blobs—relational style—with a graph-oriented
     index." Vector indexes are "just indexes"; Postgres added them within a year; they struggle
     with updates and only work well in memory. Vector DBs either stay narrow secondary indexes or
     add SQL+transactions and "then they're competing with Postgres."
   - On LLM text-to-SQL: tested 7 real databases incl. MIT's data warehouse — "I got accuracy of
     zero. Not low—zero." Skeptical of 60–90% public benchmark accuracy claims for enterprise.
   - On Postgres: "Betting the ranch on Postgres is absolutely the correct thing to do." All major
     clouds adopted the Postgres wire protocol; community governance avoided the trust erosion of
     Oracle's MySQL acquisition.
   - On CS careers: top-tier university CS grads thrive; bifurcation — elite designers + AI writes
     code; ordinary/vocational programmers squeezed out. "Understanding code is critical."
   - Recommended re-reading his & Pavlo's 2024 paper "What Goes Around Comes Around... and Around."

4. **2025 — "DBOS: three years later," The VLDB Journal, Vol. 34, No. 3 (2025).**
   URLs: https://link.springer.com/article/10.1007/s00778-024-00899-0 ;
   https://dspace.mit.edu/handle/1721.1/159216
   Update on DBOS: 2 more years as research, then ~18 months as a VC-backed startup; added a
   provenance system and a Python+TypeScript programming environment; performance evaluations.
   Builds on the VLDB 2022 progress report.

(>=3 recent signals satisfied — actually 4, two of them post-2026-01-01. Recency bar MET; no need
for status:archetype. status = active.)

## Key publications / canonical works (with URLs)

- **"One Size Fits All": An Idea Whose Time Has Come and Gone** — Stonebraker & Çetintemel,
  ICDE 2005. Won the IEEE ICDE 2015 Influential Paper Award. The thesis namesake of the brief.
  PDF: https://cs.brown.edu/people/ugur/fits_all.pdf ; dblp:
  https://dblp.org/rec/conf/icde/StonebrakerC05.html
  Core claim: the DBMS market will fracture into many specialized engines; the general-purpose
  "row-store does everything" architecture is obsolete for non-OLTP workloads.

- **The End of an Architectural Era (It's Time for a Complete Rewrite)** — Stonebraker, Madden,
  Abadi, Harizopoulos, Hachem, Helland; VLDB 2007, pp. 1150–1160. H-Store vs a popular RDBMS on
  TPC-C; specialized engines beat general RDBMS by 1–2 orders of magnitude.
  PDF: http://nms.csail.mit.edu/~stavros/pubs/hstore.pdf ; dblp:
  https://dblp.org/rec/conf/vldb/StonebrakerMAHHH07.html
  Note co-author **Pat Helland** (`pat-helland`, same data-and-storage cell).

- **MapReduce: A major step backwards** — DeWitt & Stonebraker, The Database Column blog,
  January 17, 2008. Called MapReduce a "giant step backward" in the programming paradigm for
  large-scale data, sub-optimal (brute force, no indexing), missing DBMS features and tooling.
  Drew heavy backlash. This is the direct basis for productive-conflict with **jeff-dean**
  (MapReduce co-author) and Sanjay Ghemawat.
  PDF: https://www.cs.utexas.edu/~rossbach/cs380p/papers/dewitt08blog-mapreduce-backwards.pdf
  Mirror: https://homes.cs.washington.edu/~billhowe/mapreduce_a_major_step_backwards.html
  (A revised version, "MapReduce and Parallel DBMSs: Friends or Foes?", appeared in CACM 2010.)

- **What Goes Around Comes Around... and Around** — Stonebraker & Pavlo, SIGMOD Record,
  Vol. 53, No. 2, June 2024, pp. 21–37. A 20-year retrospective on data models; concludes RM + SQL
  keep winning; document stores "on a collision course with RDBMSs"; vector DBs are document DBMSs
  with ANN indexes that RDBMSs will absorb.
  PDF: https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf ; dblp:
  https://dblp.org/rec/journals/sigmod/StonebrakerP24.html
  This is the natural **pairs_well_with: andy-pavlo** anchor.

- **Looking Back at Postgres** — Stonebraker / Joe Hellerstein retrospective, arXiv 2019.
  PDF: https://arxiv.org/pdf/1901.01973 — anchors **pairs_well_with: joe-hellerstein**
  (Hellerstein authored the Postgres retrospective and was a Berkeley colleague).

- **DBOS: A DBMS-oriented Operating System** — VLDB 2022 progress report (Skiadopoulos, Li, Kraft,
  Kaffes, Hong, Mathew, Bestor, Cafarella, Mao, Min, Zaharia, Kozyrakis, Stonebraker, Madden et al).
  PDF: https://people.eecs.berkeley.edu/~matei/papers/2022/cidr_dbos.pdf

- **NoSQL critique (2010–2011):** Stonebraker authored several CACM/blog pieces arguing NoSQL gives
  up SQL and ACID for scalability that the relational world would soon match. Referenced in Wikipedia.

## Pairs / conflicts mapping (verified against ROSTER.md slugs)

- **pairs_well_with:**
  - `andy-pavlo` — co-author of "What Goes Around... and Around" (2024) and the Dec 2025 year-in-
    review; CMU; DBOS collaborator. Confirmed in ROSTER data-and-storage cell.
  - `joe-hellerstein` — Berkeley colleague; "Looking Back at Postgres" co-retrospective; query
    optimization lineage. Confirmed in ROSTER data-and-storage cell.
- **productive_conflict_with:**
  - `jeff-dean` — MapReduce co-creator; Stonebraker's "MapReduce: A major step backwards" (2008)
    is a direct, named critique of the MapReduce paradigm Dean & Ghemawat introduced. Confirmed
    `jeff-dean` is in ROSTER data-and-storage cell.
  - `martin-kleppmann` — DDIA author, CRDT/local-first/eventual-consistency advocate. Stonebraker's
    "RM+SQL+ACID wins; specialized/eventually-consistent stores are niche" stance is in direct
    productive tension with Kleppmann's pluralist, local-first, derived-data worldview. Confirmed
    `martin-kleppmann` is in ROSTER data-and-storage cell.
  - (Also natural tension with `dhh` on "majestic monolith" pragmatism vs Stonebraker's
    specialization thesis, but the two named in the brief — jeff-dean, martin-kleppmann — are the
    primary anchors and both verified.)

## Corrections to assumptions (logged per instructions)

1. Brief said DBOS may be "his latest venture" and hinted CEO — **he is co-founder + CTO, not CEO;
   Qian Li is CEO.** A web summary that named "Andy Palmer" as CEO is WRONG (Palmer is a board
   member). Profile uses CTO + co-founder.
2. Brief said "MIT adjunct" — accurate but refined: he is **adjunct professor *emeritus*** at MIT
   CSAIL and professor emeritus at UC Berkeley. Both recorded.
3. "Sharp critic of MapReduce and NoSQL hype" — fully confirmed (2008 MapReduce blog; 2010–2011
   NoSQL critiques; 2024 "What Goes Around" and Dec 2025 vector-DB commentary continue the line).

## All URLs consulted (sources list, >=8)

1. https://en.wikipedia.org/wiki/Michael_Stonebraker
2. https://www.acm.org/articles/bulletins/2015/march/turing-award-2014
3. https://amturing.acm.org/award_winners/stonebraker_1172121.cfm  (HTTP 403 on fetch; cited for citation)
4. https://www.dbos.dev/about
5. https://www.dbos.dev/blog/goto-considered-harmful-2026
6. https://www.vldb.org/cidrdb/papers/2026/p9-stonebraker.pdf
7. https://www.dbos.dev/webcast-2025-in-review-with-mike-stonebraker-and-andy-pavlo
8. https://blog.vonng.com/en/db/db-year-review-2025/
9. https://link.springer.com/article/10.1007/s00778-024-00899-0  (DBOS: three years later, VLDB J 2025)
10. https://dspace.mit.edu/handle/1721.1/159216
11. https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf  (What Goes Around... 2024)
12. https://cs.brown.edu/people/ugur/fits_all.pdf  (One Size Fits All, ICDE 2005)
13. http://nms.csail.mit.edu/~stavros/pubs/hstore.pdf  (End of an Architectural Era, VLDB 2007)
14. https://www.cs.utexas.edu/~rossbach/cs380p/papers/dewitt08blog-mapreduce-backwards.pdf
15. https://homes.cs.washington.edu/~billhowe/mapreduce_a_major_step_backwards.html
16. https://arxiv.org/pdf/1901.01973  (Looking Back at Postgres, 2019)
17. https://people.eecs.berkeley.edu/~matei/papers/2022/cidr_dbos.pdf  (DBOS VLDB 2022)
18. https://www.prnewswire.com/news-releases/technology-pioneer-mike-stonebraker-raises-8-5m-to-launch-dbos-and-radically-transform-cloud-computing-302086000.html
19. https://www.crunchbase.com/organization/dbos-inc
20. https://www.kdnuggets.com/2012/05/interview-mike-stonebraker-one-size-does-not-fit-all.html
21. https://hpcwire.com/bigdatawire/2024/07/08/dont-believe-the-big-database-hype-stonebraker-warns/
22. https://dblp.org/pid/s/MichaelStonebraker.html
23. https://www.britannica.com/biography/Michael-Stonebraker
24. https://sdtimes.com/acm/2014-turing-award-goes-to-mits-michael-stonebraker/
25. https://dblp.org/rec/journals/sigmod/StonebrakerP24.html
26. https://dblp.org/rec/conf/icde/StonebrakerC05.html
27. https://dblp.org/rec/conf/vldb/StonebrakerMAHHH07.html
