# Martin Kleppmann — Research Notes

**Researched:** 2026-05-30
**Researcher:** Claude (engineering Super Intelligence Team build, Wave E3, cell `data-and-storage`)
**Subject slug:** `martin-kleppmann`
**Method:** WebSearch + WebFetch against primary sources (martin.kleppmann.com, Cambridge CST, O'Reilly, Ink & Switch, EuroSys, SE Radio, localfirst.fm).

---

## Correction to the briefing assumption (LOGGED)

The build brief described Kleppmann as a "(Cambridge → TU Munich professor)" and instructed me to "verify TU Munich move." **This is the wrong direction and the wrong title.** The verified career path is the reverse:

- **University of Cambridge** — Research Fellow, Systems Research Group / Department of Computer Science and Technology, **2015–2022**.
- **TU Munich (Technical University of Munich)** — Research Fellow, Systems Research Group (Chair of Distributed Systems & Operating Systems), **2022–2023** (a short ~1-year fellowship, not a professorship).
- **University of Cambridge** — **Associate Professor** of Computer Science and Technology, **since 2024 → present (2026)**. He returned to Cambridge. He is NOT a TU Munich professor.

He teaches "Concurrent and Distributed Systems" (Part IB) and "Cryptography and Protocol Engineering" (MPhil ACS / Part III) at Cambridge.

**Resolution:** `affiliations_2026` set to University of Cambridge (Associate Professor). TU Munich (2022–2023) recorded under `past_affiliations` as a research-fellow stint, not a chair. Verified via:
- https://www.cst.cam.ac.uk/people/mk428 — "Associate Professor … since 2024."
- https://martin.kleppmann.com/ — "Research fellow in the Systems Research Group (2022–2023)" [TU Munich]; "Cambridge: Research fellow (2015–2022)."
- https://www.cl.cam.ac.uk/teaching/2425/ConcDisSys/ — principal lecturer, Concurrent and Distributed Systems 2024–25.

Note: several secondary/podcast bios (e.g., the old localfirst.fm intro, some older talk pages) still describe him as "a research fellow at the Technical University of Munich" — these are stale (pre-2024). The primary Cambridge and personal-site sources are authoritative and current.

---

## Identity & biography (verified)

- **Real name:** Martin Kleppmann. Born in Germany. Top of the Cambridge Computer Science graduating class, 2006 (B.A.). Took a year at the Royal Scottish Academy of Music and Drama after his B.A.
  - Source: https://www.rescuecom.com/blog/index.php/rescuecom/one-of-the-young-stars-of-the-internet-martin-kleppmann/
- **Industry background (the "secret weapon" before academia):**
  - **Go Test It** — co-founder; automated cross-browser website testing. Acquired by **Red Gate Software in 2009**.
  - **Rapportive** — co-founder (with Rahul Vohra as CEO, Sam Stokes as CTO); Gmail browser extension showing social profiles of email senders. Acquired by **LinkedIn in 2012**.
  - **LinkedIn** — software engineer on large-scale data infrastructure (post-Rapportive acquisition). His DDIA material is grounded in this real production data-infra experience.
  - Sources: https://www.rescuecom.com/blog/index.php/rescuecom/one-of-the-young-stars-of-the-internet-martin-kleppmann/ ; https://martin.kleppmann.com/2011/08/16/founderly-interview.html ; https://www.oreilly.com/pub/au/6235
- **Current contact:** Room GE17, mk428@cst.cam.ac.uk. Active on Mastodon and Bluesky.
  - Source: https://www.cst.cam.ac.uk/people/mk428

---

## Canonical work — Designing Data-Intensive Applications (DDIA)

- **1st edition:** 2017, O'Reilly, sole author. Has **sold over 200,000+ copies, translated into eight languages** (Cambridge profile figure). Widely regarded as the canonical modern textbook on data systems architecture.
  - Source: https://www.cst.cam.ac.uk/people/mk428
- **2nd edition:** **February 2026**, O'Reilly, co-authored with **Chris Riccomini**. ISBN 9781098119065 (print) / 9781098119058 (online).
  - Verified publication month/year (February 2026) via O'Reilly: https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/
  - 14 chapters; "integrates new technologies and emerging trends."
  - Notable content change: **cut most MapReduce coverage** ("practically nobody uses it anymore"; Spark/Flink have replaced it). Source: search summary of O'Reilly + ScyllaDB landing page https://lp.scylladb.com/designing-data-intensive-apps-book-offer
  - Chris Riccomini: software engineer / investor, 15+ yrs at PayPal, LinkedIn, WePay; runs Materialized View Capital.
  - This is an ACTIVE recent signal (post-2025-05-30): the 2nd edition shipping Feb 2026 is the single biggest recent event.

---

## Recent signals (post-2025-05-30, dated + URL)

1. **DDIA 2nd Edition published** — Feb 2026, O'Reilly, w/ Chris Riccomini.
   - https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/
   - Takeaway: First major revision in 9 years; drops MapReduce, adds modern streaming/dataflow + emerging trends. Re-cements him as the field's reference author.

2. **Blog: "Prediction: AI will make formal verification go mainstream"** — 08 Dec 2025.
   - https://martin.kleppmann.com/2025/12/08/ai-formal-verification.html
   - Thesis: LLM coding assistants will push formal verification from a fringe pursuit into mainstream software engineering — cheaper proof generation, the necessity of verifying AI-generated code, and FM as an antidote to LLM unreliability.
   - Quotes:
     - "I believe that AI will bring formal verification, which for decades has been a bit of a fringe pursuit, into the software engineering mainstream."
     - "Rather than having humans review AI-generated code, I'd much rather have the AI prove to me that the code it has generated is correct."
     - "The limiting factor will not be the technology, but the culture change required for people to realise that formal methods have become viable in practice."

3. **SE Radio Episode 716: "Martin Kleppmann on Local-First Software"** — 15 Apr 2026.
   - https://se-radio.net/2026/04/se-radio-716-martin-kleppmann-local-first-software/
   - Key points: local-first combines "the best of two different worlds" (pre-internet local files + cloud-style real-time collaboration); simplifies dev architecture ("the application code is only ever interacting with this local database that's embedded on the client"); Automerge = embedded CRDT DB, ~14,000 weekly NPM downloads, growing production adoption; local-first UNSUITABLE for single-source-of-truth systems (banking, huge catalogs); emerging use case = human-AI collaboration via version-control-style review of AI-generated changes; geopolitical resilience argument for decentralization.

(Additional recent academic signals, slightly outside the strict 12-month window but adjacent / supporting:)
- **EuroSys 2025 (April 2025): "Collaborative Text Editing with Eg-walker: Better, Faster, Smaller"** w/ Joseph Gentle. Won the **Gilles Muller Best Artifact Award**. Eg-walker is a new collaboration algorithm avoiding both OT's slow-merge weakness and CRDTs' load/memory cost.
   - https://dl.acm.org/doi/10.1145/3689031.3696076 ; https://arxiv.org/abs/2409.14252 ; https://2025.eurosys.org/awards.html
- **Nov 2025: IEEE Transactions on Parallel and Distributed Systems** — article on minimizing interleaving anomalies (CRDT/collaborative editing correctness). (per martin.kleppmann.com publications list)

---

## Foundational / canonical works (for canonical_works + key_publications)

- **Designing Data-Intensive Applications** (book) — 2017 (1st) / Feb 2026 (2nd, w/ Riccomini). O'Reilly.
- **"Local-first software: You own your data, in spite of the cloud"** — Onward! 2019 essay, Ink & Switch. Co-authors: Martin Kleppmann, Adam Wiggins, Peter van Hardenberg, Mark McGranaghan. **Coined the term "local-first"**; defined the **seven ideals** (no spinners / fast; multi-device; offline; collaboration; longevity; security & privacy by default; you retain ultimate ownership & control). First 4 overlap offline-first; last 3 are what makes local-first distinct.
   - https://www.inkandswitch.com/essay/local-first/ ; https://martin.kleppmann.com/2019/10/23/local-first-at-onward.html
- **Automerge** — open-source CRDT library (JSON-like data structure that merges concurrent edits automatically). Kleppmann is a co-founder/maintainer. Repo + project.
   - https://automerge.org/
- **"A Critique of the CAP Theorem"** (2015 paper, arXiv) + blog **"Please stop calling databases CP or AP"** (11 May 2015). Argues CAP is too simplistic/misunderstood to characterize real systems; ACID "consistency" ≠ CAP "consistency"; proposes more careful framing.
   - https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html
   - This is the primary basis for PRODUCTIVE CONFLICT with `eric-brewer` (CAP author). It's a respectful technical disagreement about whether CAP is a useful framing, not a claim CAP is wrong.

---

## Mental models / signature moves (synthesized from sources)

- Reason from first principles about the *guarantees* a system actually provides, not the marketing label (CAP critique; ACID-vs-CAP-consistency distinction).
- "Show me the trade-off, precisely." He insists on naming exactly which property degrades under which failure mode.
- Local-first as the default critique of cloud-first: ownership, longevity, offline, no-spinner latency.
- CRDTs as the merge primitive; convergence by construction beats coordination.
- Pedagogy through synthesis: DDIA's whole method is mapping the landscape of real systems and extracting the durable principles.
- Formal verification will become mainstream because verification (not generation) is the bottleneck in an AI-coding world.

## Voice style
Measured, precise, academic-but-accessible. The DDIA register: define terms carefully, enumerate trade-offs, refuse hype, use concrete real-world systems as evidence. Politely insistent on rigor ("please stop calling databases CP or AP"). Distinguishes guarantees from labels.

---

## Roster cross-references (verified against ROSTER.md, cell data-and-storage / cloud-architecture)

- **pairs_well_with:**
  - `pat-helland` (data-and-storage) — immutability, "Life Beyond Distributed Transactions," log-centric data; deeply compatible with Kleppmann's replication/streams and event-sourcing chapters.
  - `leslie-lamport` (data-and-storage) — logical clocks, Paxos, TLA+. Kleppmann's Dec 2025 formal-verification prediction directly amplifies Lamport's life's work; DDIA leans on Lamport clocks for ordering.
- **productive_conflict_with:**
  - `eric-brewer` (cloud-architecture) — CAP theorem author; Kleppmann's "Please stop calling databases CP or AP" + "A Critique of the CAP Theorem" is the canonical pushback on CAP as a framing. EVIDENCED.
  - `michael-stonebraker` (data-and-storage) — Stonebraker is famously combative about NoSQL/"one size does not fit all"/MapReduce-as-major-step-backward and a strong RDBMS+specialized-engine proponent; Kleppmann is more ecumenical/landscape-surveying and treats NoSQL, streaming, and CRDT/local-first stores as legitimate design points. Productive friction over how much the relational model + purpose-built engines should dominate vs. a pluralistic data-systems view.

---

## Sources (master list, all real URLs)

1. https://martin.kleppmann.com/ — personal site (current affiliation, research areas)
2. https://www.cst.cam.ac.uk/people/mk428 — Cambridge faculty profile (Associate Professor since 2024)
3. https://www.cl.cam.ac.uk/teaching/2425/ConcDisSys/ — Concurrent & Distributed Systems course 2024–25
4. https://www.oreilly.com/library/view/designing-data-intensive-applications/9781098119058/ — DDIA 2nd ed, Feb 2026
5. https://martin.kleppmann.com/2025/12/08/ai-formal-verification.html — AI + formal verification prediction (Dec 2025)
6. https://se-radio.net/2026/04/se-radio-716-martin-kleppmann-local-first-software/ — SE Radio 716 (Apr 2026)
7. https://www.inkandswitch.com/essay/local-first/ — Local-first manifesto (2019)
8. https://martin.kleppmann.com/2019/10/23/local-first-at-onward.html — Local-first Onward! 2019 publication page
9. https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html — CAP critique blog (2015)
10. https://dl.acm.org/doi/10.1145/3689031.3696076 — Eg-walker EuroSys 2025
11. https://2025.eurosys.org/awards.html — EuroSys 2025 Best Artifact Award
12. https://automerge.org/ — Automerge CRDT library
13. https://www.rescuecom.com/blog/index.php/rescuecom/one-of-the-young-stars-of-the-internet-martin-kleppmann/ — biography (Go Test It, Rapportive)
14. https://www.oreilly.com/pub/au/6235 — O'Reilly author page
15. https://www.localfirst.fm/4/transcript — localfirst.fm ep 4 (CRDTs, Automerge, Bluesky)
16. https://arxiv.org/abs/2409.14252 — Eg-walker arXiv
