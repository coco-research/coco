# Andy Pavlo — Research Notes

**Subject:** Andrew (Andy) Pavlo — Carnegie Mellon University database-systems professor.
**Slug:** `andy-pavlo` · **Cell:** data-and-storage · **Cell role:** specialist · **Home team:** engineering.
**Researched:** 2026-05-30. **Last verified:** 2026-05-30.

All findings below are dated and carry source URLs. Quotes are verbatim from the cited source unless marked as paraphrase.

---

## Identity confirmation (high confidence)

- Full name: **Andrew Pavlo**, goes by **Andy Pavlo**. Born May 20, 1981, Baltimore.
  Source: https://en.everybodywiki.com/Andy_Pavlo
- **Associate Professor with Indefinite Tenure of Databaseology** in the Computer Science Department at CMU. Member of the Database Group (CMU-DB) and the Parallel Data Laboratory.
  Source: https://www.cs.cmu.edu/~pavlo/
- Education: BS + MS, Rochester Institute of Technology (2005–2006); MS (2009) and **PhD (2013), Brown University**, dissertation *"Scalable Transaction Execution in Partitioned Main Memory Database Management Systems,"* **advised by Stanley Zdonik and Michael Stonebraker.**
  Source: https://en.everybodywiki.com/Andy_Pavlo
  - NOTE / corrected assumption: the prompt and some secondary sources hint at "UW-Madison." That is **wrong** — his PhD is from **Brown University**. The Stonebraker co-advisorship is what makes the `pairs_well_with: michael-stonebraker` link a real mentor/collaborator tie, not just a topical adjacency.

## Career timeline

- 2013 — Assistant Professor, CMU CS.  Source: https://en.everybodywiki.com/Andy_Pavlo
- 2019 — Promoted to Associate Professor.  Source: https://en.everybodywiki.com/Andy_Pavlo
- March 2020 — Co-founded **OtterTune** with PhD students **Dana Van Aken** and **Bohan Zhang** (CEO & co-founder). ML-based automatic cloud-DB configuration tuning.
  Source: https://www.csd.cs.cmu.edu/people/faculty/andrew-pavlo ; https://www.dbta.com/Authors/Andy-Pavlo-Co-Founder-and-CEO-OtterTune-9409.aspx
- May 2021 — OtterTune launched commercially; 2022 raised $12M Series A.  Source: https://en.everybodywiki.com/Andy_Pavlo
- **June 2024 — OtterTune announced shutdown / wound down operations.**  Source: WebSearch result (dbta + everybodywiki corroborated). This matches the prompt's "OtterTune founder (wound down)."
- 2025–2026 — back to full-time academic + commentator role; **announced a NEW startup** with his PhD students in the Jan 2026 retrospective ("I hope to say more on that soon"). The current-projects list on his homepage cheekily lists the startup as **"SO-YOU-DONT-HAVE-TO INCORPORATED'; DROP TABLE companies; --"** (a Bobby-Tables SQL-injection joke; the real name/details are not yet public as of 2026-05-30).
  Source: https://www.cs.cmu.edu/~pavlo/ ; https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html

## Awards & honors

- 2014 — **ACM SIGMOD Jim Gray Doctoral Dissertation Award.**  Source: https://www.csd.cs.cmu.edu/people/faculty/andrew-pavlo
- 2018 — **Sloan Research Fellowship.**  Source: https://www.csd.cs.cmu.edu/people/faculty/andrew-pavlo
- 2019 — **NSF CAREER Award** (for "Self-Driving Database Management Systems").  Source: https://en.everybodywiki.com/Andy_Pavlo
- **2026 — IEEE TCDE Ramez Elmasri Outstanding Database Education Award.** Ceremony **May 6, 2026** at ICDE 2026, Montréal. RECENT SIGNAL.
  Source: https://db.cs.cmu.edu/2026/05/prof-andy-pavlo-wins-2026-ieee-tcde-ramez-elmasri-outstanding-database-education-award/

## Research systems / canonical works

- **Peloton** — the first "self-driving DBMS" research prototype (white-box, clean-slate autonomous DB). The famous talk "Make Your Database Dream of Electric Sheep: Designing for Autonomous Operation."
  Source: https://www.datacouncil.ai/talks/peloton-the-self-driving-database-management-system ; https://cs.uchicago.edu/events/event/andy-pavlo-cmu-make-your-database-dream-of-electric-sheep-designing-for-autonomous-operation/
- **NoisePage** — successor self-driving DBMS research system (in-memory, Postgres-compatible).  Source: https://www.cs.cmu.edu/~pavlo/
- **OtterTune** — black-box ML tuning of existing DBMSs (MySQL/Postgres/Oracle). Two research tracks: black-box (tune existing) vs white-box (clean-slate autonomous). Source: WebSearch dbta.
- **BenchBase / OLTP-Bench (BenchBase)** — multi-DBMS benchmarking framework. Listed on homepage as **BenchBase**.  Source: https://www.cs.cmu.edu/~pavlo/
- **Database of Databases (dbdb.io)** — encyclopedia of DBMSs.  Source: https://www.cs.cmu.edu/~pavlo/
- **optd** — query-optimizer research project (current).  Source: https://www.cs.cmu.edu/~pavlo/
- **CMU 15-445/645 Intro to Database Systems** + **15-721 Advanced Database Systems** — the famous fully open-sourced YouTube lecture series; one of the most popular free DB courses online. The basis for the 2026 education award.
  Source: https://www.cs.cmu.edu/~pavlo/ ; https://www.youtube.com/watch?v=vdPALZ-GCfI ; https://db.cs.cmu.edu/2026/05/prof-andy-pavlo-wins-2026-ieee-tcde-ramez-elmasri-outstanding-database-education-award/

## Key publications

- **"What Goes Around Comes Around... And Around..."** — Michael Stonebraker & Andrew Pavlo, **SIGMOD Record 2024**. 60-year history of data-modeling research arguing RM/SQL remains the default winner; every attempt to replace the relational model/SQL (OODBMS in the 90s, NoSQL for "webscale," now vector DBs for AI/ML) has failed.
  Paper: https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf
  ACM: https://dl.acm.org/doi/10.1145/3685980.3685984
  Talk video: https://www.youtube.com/watch?v=8Woy5I511L8
  - Note: this is a deliberate echo/update of Stonebraker & Hellerstein's classic 2005 "What Goes Around Comes Around" — ties Pavlo to BOTH suggested pairs (Stonebraker as co-author, Hellerstein as the original framing's author).
- **"Self-Driving Database Management Systems"** — Pavlo et al., CIDR 2017 (the vision paper behind Peloton/NoisePage). Source: corroborated via Peloton talk + NSF CAREER title.
- Dissertation (2013): "Scalable Transaction Execution in Partitioned Main Memory Database Management Systems," Brown University (H-Store/VoltDB lineage).

## RECENT SIGNALS (all dated AFTER 2025-05-30) — bar requires >=3

1. **2026-05-06** — Wins **2026 IEEE TCDE Ramez Elmasri Outstanding Database Education Award**; ceremony at ICDE 2026 Montréal.
   https://db.cs.cmu.edu/2026/05/prof-andy-pavlo-wins-2026-ieee-tcde-ramez-elmasri-outstanding-database-education-award/
2. **2026-01-04** — Publishes **"Databases in 2025: A Year in Review"** (annual retrospective). Topics: PostgreSQL dominance, Databricks $1B for Neon + Snowflake $250M for CrunchyData + Microsoft HorizonDB, MCP-for-everyone (with security warnings), MongoDB v. FerretDB litigation, Parquet fragmentation, file-format wars (F3/Vortex/FastLanes/AnyBlox), vector-DB hype cooling, announces new startup.
   https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html
3. **Jan 2026** — Launches **"PostgreSQL vs. The World" Spring 2026 Seminar Series** (co-org with Jignesh Patel + Sam Arch). Thesis: PostgreSQL compatibility is now the de-facto baseline; alternatives must compete on PostgreSQL's terms.
   https://db.cs.cmu.edu/2026/01/postgresql-vs-the-world-seminar-series-spring-2026/ ; https://db.cs.cmu.edu/seminars/spring2026/
4. **2025-12-10** — DBOS webcast **"2025 in Review with Mike Stonebraker and Andy Pavlo."** Topics: whether AI is a bubble, AI agents replacing DBAs, graph DB relevance, Postgres M&A.
   https://www.dbos.dev/webcast-2025-in-review-with-mike-stonebraker-and-andy-pavlo
5. **Fall 2025** — Organizes **"Future Data Systems" Seminar Series** (lakehouse ecosystem, Apache Iceberg).
   https://db.cs.cmu.edu/seminars/fall2025/

## Public stances + evidence (every claim cited)

1. **The relational model / SQL keeps winning; every "SQL is dead" wave (OODBMS, NoSQL, now vector DBs) eventually reconverges on RM/SQL.**
   "What Goes Around Comes Around... And Around" (SIGMOD Record 2024): all efforts to completely replace the data model or query language have failed; vector-DB proponents are the latest to take up the "relational model is outdated" mantle.
   https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf
2. **Vector databases won't replace SQL — they'll be absorbed.** Vector indexes are "just indexes" Postgres added within a year; vector DBs either specialize into secondary-index tools (like Elasticsearch) or add SQL+transactions and become Postgres competitors. Quote: "SQL will evolve over time and add support for vector primitives or vector built-ins and vector functions."
   https://www.firebolt.io/blog/vector-databases-wont-replace-sql---andy-pavlo (2024-06-04)
3. **PostgreSQL has become the de-facto default for modern applications.** "Every major cloud vendor now offers an enhanced, opinionated PostgreSQL-compatible database management system... These moves make PostgreSQL the de facto database choice for modern applications."
   https://db.cs.cmu.edu/seminars/spring2026/ ; https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html
4. **MCP-to-database access is a security liability without least-privilege + proxy guardrails.** "nobody should trust an application with unfettered database access, whether it is via MCP or the system's regular API"; lazy security will "get wrecked when the LLM starts popping off."
   https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html
5. **Databases should be autonomous / self-driving — tuning, indexing, and physical design should be done by the DBMS, not a human DBA.** This is the Peloton/NoisePage/OtterTune research thesis ("Self-Driving Database Management Systems," CIDR 2017; NSF CAREER 2019).
   https://cs.uchicago.edu/events/event/andy-pavlo-cmu-make-your-database-dream-of-electric-sheep-designing-for-autonomous-operation/
6. **Benchmark claims must be reproducible and honest — vendors fudge.** In the 2025 retrospective he calls out SurrealDB benchmarks where they "weren't flushing writes to disk and lost data," and Parquet's "94% [of files] use only v1 features from 2013" implementation-fragmentation problem.
   https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html
7. **Open, free database education is a public good.** All CMU-DB course materials, lectures, and infra are open-sourced; basis of the 2026 TCDE education award.
   https://db.cs.cmu.edu/2026/05/prof-andy-pavlo-wins-2026-ieee-tcde-ramez-elmasri-outstanding-database-education-award/

## Memorable quotes / voice (verbatim from cited sources)

- On Redis re-licensing: "switched their license back one year after their rugpull (I called this shot last year)." — 2025 retrospective
- On FerretDB litigation: "It is going to be challenging to convince a jury that you were not trying to divert customers when you changed one letter" (FerretDB was originally "MangoDB"). — 2025 retrospective
- On file-format-war xkcd references: "You don't need to email it to me again." — 2025 retrospective
- On vector-DB hype cycle: "SQL slow, SQL stupid... five years later... SQL and relational model is actually a good idea." — Firebolt 2024
- "I don't know who will win the file format war. The next battle is likely to be over GPU support." — 2025 retrospective
- Voice: dry, sardonic, prolific, contrarian-but-empirical. Heavy use of pop-culture/profane analogies (the "55-year-old man who wakes up inexplicably pregnant" framing for non-Postgres DBs in the Spring 2026 seminar blurb). Cites a 60-year historical record to deflate hype. Discloses his own advising failures (Fauna, PostgresML) self-deprecatingly.

## Roster relationships

- **pairs_well_with: michael-stonebraker** — co-author of "What Goes Around Comes Around... And Around" (2024) and PhD co-advisor; co-host of the 2025-in-review webcast (2025-12-10). Direct, real collaboration. Both data-and-storage cell (ROSTER.md).
- **pairs_well_with: joe-hellerstein** — Hellerstein (with Stonebraker) authored the ORIGINAL 2005 "What Goes Around Comes Around" that Pavlo's 2024 paper updates; both are Berkeley/CMU systems-DB canon. Both data-and-storage cell.
- **productive_conflict_with** (real ROSTER.md slugs):
  - `martin-kleppmann` — Kleppmann's local-first / CRDT / "unbundling the database" worldview (DDIA) sits against Pavlo's "RM/SQL re-converges and a single autonomous Postgres-shaped DBMS wins" orthodoxy. Productive tension on whether the future is one big DB or many specialized stores.
  - `michael-truell` — Cursor/Anysphere CEO; Pavlo's MCP/agent-DB-access skepticism ("nobody should trust an application with unfettered database access") directly tensions the agentic-coding-tools-touch-the-DB optimism. Real ROSTER slug (ai-assisted-coding cell).
  - (Considered `dhh` — "majestic monolith" vs autonomous-DB — weaker tie; left out in favor of the two above.)

## Confidence

**0.95.** Identity is unambiguous (single famous public figure, consistent across CMU official pages, Wikipedia/everybodywiki, SIGMOD, IEEE TCDE). Recent signals are abundant and well-dated. Only soft spot: exact name/details of his 2026 new startup are not yet public (the homepage entry is a placeholder SQL-injection joke), so that fact is logged as "announced, undisclosed."

## All source URLs

1. https://www.cs.cmu.edu/~pavlo/
2. https://www.csd.cs.cmu.edu/people/faculty/andrew-pavlo
3. https://en.everybodywiki.com/Andy_Pavlo
4. https://www.cs.cmu.edu/~pavlo/blog/2026/01/2025-databases-retrospective.html
5. https://db.cs.cmu.edu/2026/05/prof-andy-pavlo-wins-2026-ieee-tcde-ramez-elmasri-outstanding-database-education-award/
6. https://db.cs.cmu.edu/seminars/spring2026/
7. https://db.cs.cmu.edu/2026/01/postgresql-vs-the-world-seminar-series-spring-2026/
8. https://db.cs.cmu.edu/seminars/fall2025/
9. https://www.dbos.dev/webcast-2025-in-review-with-mike-stonebraker-and-andy-pavlo
10. https://db.cs.cmu.edu/papers/2024/whatgoesaround-sigmodrec2024.pdf
11. https://dl.acm.org/doi/10.1145/3685980.3685984
12. https://www.firebolt.io/blog/vector-databases-wont-replace-sql---andy-pavlo
13. https://cs.uchicago.edu/events/event/andy-pavlo-cmu-make-your-database-dream-of-electric-sheep-designing-for-autonomous-operation/
14. https://www.datacouncil.ai/talks/peloton-the-self-driving-database-management-system
15. https://www.youtube.com/watch?v=8Woy5I511L8
16. https://www.youtube.com/watch?v=vdPALZ-GCfI
