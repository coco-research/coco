# Leslie Lamport — Research Notes

**Slug:** leslie-lamport
**Researched:** 2026-05-30
**Researcher:** SI-Eng research agent (Wave E3 — data-and-storage)
**Cell:** data-and-storage | **Cell role:** lead-driver | **Home team:** engineering
**Status decision:** `active` (see "Status determination" below)

---

## Status determination

The brief flagged that Lamport was born in 1941 (he is 85 as of May 2026) and asked
me to verify whether he is still giving talks / maintaining TLA+, and to fall back to
`status: archetype` with `persistent_signals` only if I could not find three genuine
signals dated after 2025-05-30.

**Verdict: `status: active`.** Lamport is alive, has retired from Microsoft Research
(effective 3 January 2025), but is verifiably still personally active in 2026 — he
continues to revise his book, gives Q&A talks, and sits for substantive interviews.
Three independent signals dated AFTER the 2025-05-30 cutoff:

1. **developing.dev video interview "Thinking Clearly, Paxos vs Raft, Working with
   Dijkstra"** — published **2026-02-23**. Substantive long-form interview; multiple
   fresh quotes (see Quotes below).
   URL: https://www.developing.dev/p/turing-award-winner-on-working-with
2. **The New Stack feature "TLA+ Creator Leslie Lamport: Programmers Need
   Abstractions"** by Darryl K. Taft — published **2026-03-14 09:00**. Covers his
   message on abstraction-before-code.
   URL: https://thenewstack.io/tla-creator-leslie-lamport-programmers-need-abstractions/
3. **"A Science of Concurrent Programs" book PDF — revised 2026-03-25.** Confirmed
   from the PDF's own metadata: `CreationDate (D:20260325190048Z)` /
   `ModDate (D:20260325190048Z)`. Google's index title for the file literally reads
   "A Science of Concurrent Programs Leslie Lamport 25 March 2026." He is still
   actively maintaining/revising this manuscript.
   URL: https://lamport.azurewebsites.net/tla/science.pdf

A fourth, near-cutoff signal — the **SCALE 22x closing keynote "Coding isn't
Programming"** — was delivered **2025-03-09** (BEFORE the cutoff), so it does NOT
count toward the post-cutoff requirement, but it is the talk the 2026-03-14 New
Stack article is built around and confirms his ongoing speaking activity.

**Nuance to preserve in the profile:** On his own home page / TLA+ news page
(14 May 2025) Lamport wrote, after retiring, "I do not know if I will now do anything
related to TLA+ or any other aspect of computer science." So `active` here means
"verifiably still personally producing/appearing in 2026," not "running a lab." TLA+
itself is now stewarded by the **TLA+ Foundation** (an independent Linux Foundation
non-profit, established 24 April 2023), not by Lamport directly.

---

## Corrected assumptions / fact-checks

- **CORRECTION to the brief's "still giving talks" framing:** The flagship recent
  talk ("Coding isn't Programming" / "Programmers Need Abstractions") was the SCALE
  22x closing keynote delivered **2025-03-09** (Pasadena Convention Center, Sunday
  3pm). It is frequently mis-cited as a "2026 talk" because the New Stack write-up
  appeared 2026-03-14. The TALK is March 2025; the COVERAGE is March 2026. Both are
  logged with correct dates.
- **CORRECTION:** Lamport did NOT simply "retire" into silence — he retired from
  Microsoft on 2025-01-03, but Microsoft "has graciously agreed to maintain his
  website," and he explicitly continues occasional Q&A talks and interviews.
- **CORRECTION on TLA+ ownership:** TLA+ is no longer Lamport's personal project — it
  belongs to the **TLA+ Foundation** since 2023. Language-change governance is now a
  documented process (Lamport + Stephan Merz + Chris Newcombe drafted the guidance,
  13 Aug 2024). So "maintaining TLA+" is institutionally the Foundation's job now.
- The famous quote *"A distributed system is one in which the failure of a computer
  you didn't even know existed can render your own computer unusable"* dates to a
  **June 1987 email**, NOT to any published paper. Cited correctly.
- Birth: **Leslie Barry Lamport, born 7 February 1941, New York City.**
- Turing Award: **2013** (announced March 2014), "for fundamental contributions to
  the theory and practice of distributed and concurrent systems, notably the
  invention of concepts such as causality and logical clocks, safety and liveness,
  replicated state machines, and sequential consistency."
- Dijkstra Prize: won **three times — 2000, 2005, 2014.**
- Other honors: IEEE John von Neumann Medal (2008); National Academy of Sciences
  (2011); ACM Fellow (2014). Solana blockchain named its smallest unit the
  "lamport" in his honor (2020).

---

## Career timeline (verified — Wikipedia)

- Massachusetts Computer Associates (Compass) — 1970–1977
- SRI International — 1977–1985
- Digital Equipment Corporation (DEC) → Compaq (DEC SRC / Systems Research Center) — 1985–2001
- Microsoft Research, Mountain View / Silicon Valley — 2001 – 3 January 2025
- Microsoft Research **emeritus / affiliate** — since 2025 (Microsoft maintains his site)

---

## Canonical works (verified)

- **"Time, Clocks, and the Ordering of Events in a Distributed System"** (1978, CACM)
  — logical clocks ("Lamport clocks"), the happened-before relation, state-machine
  replication. One of the most-cited papers in CS; won the 2000 PODC Influential
  Paper Award (later renamed the Dijkstra Prize) and an ACM SIGOPS Hall of Fame award.
- **"The Byzantine Generals Problem"** (Lamport, Shostak, Pease — 1982, TOPLAS) —
  foundational statement of Byzantine fault tolerance.
- **"The Part-Time Parliament"** (1998, TOCS) — the original (notoriously hard to
  read) Paxos paper, framed as the legend of the Greek island of Paxos.
- **"Paxos Made Simple"** (2001, ACM SIGACT News) — the readable re-explanation;
  opens with "The Paxos algorithm, when presented in plain English, is very simple."
- **LaTeX** (mid-1980s) — document preparation macros on top of Knuth's TeX; the
  "Lamport TeX." The standard for scientific/mathematical typesetting.
- **TLA+** (Temporal Logic of Actions; 1990s onward) — formal specification language
  for concurrent and distributed systems. Tooling: TLC model checker, TLAPS proof
  system, PlusCal algorithm language.
- **Bakery algorithm** (1974) — mutual exclusion without atomic lower-level
  primitives.
- **Sequential consistency** (1979) — the canonical memory-consistency model.
- **"Specifying Systems"** (Addison-Wesley, 2002) — the TLA+ book. Free PDF; last
  modified 16 Jan 2022.
- **"A Science of Concurrent Programs"** — new book; final draft posted 2 Jan 2025;
  revised 25 March 2026; freely downloadable, physical edition "in the works."

---

## Recent / dated findings

| Date | Item | URL |
|---|---|---|
| 2026-03-25 | "A Science of Concurrent Programs" PDF revised (from PDF metadata) | https://lamport.azurewebsites.net/tla/science.pdf |
| 2026-03-14 | The New Stack: "Programmers Need Abstractions" (Darryl K. Taft) | https://thenewstack.io/tla-creator-leslie-lamport-programmers-need-abstractions/ |
| 2026-02-23 | developing.dev interview: Thinking Clearly, Paxos vs Raft, Dijkstra | https://www.developing.dev/p/turing-award-winner-on-working-with |
| 2025-05-14 | lamport.org/TLA+ news: retirement note + "I do not know if I will now do anything related to TLA+" | https://lamport.azurewebsites.net/tla/news.html |
| 2025-05-04 | First TLA+ Community Event (McMaster U, co-located ETAPS 2025) | https://conf.tlapl.us/ |
| 2025-03-09 | SCALE 22x closing keynote "Coding isn't Programming" (Pasadena) | https://www.socallinuxexpo.org/scale/22x/presentations/closing-keynote-leslie-lamport/ |
| 2025-01-03 | Retired from Microsoft Research | https://lamport.azurewebsites.net/tla/news.html |
| 2025-01-02 | Final draft of "A Science of Concurrent Programs" posted | https://lamport.azurewebsites.net/tla/news.html |
| 2024-08-13 | TLA+ language-change governance doc (Lamport, Merz, Newcombe) | https://lamport.azurewebsites.net/tla/news.html |
| 2023-04-24 | TLA+ Foundation established (Linux Foundation non-profit) | https://foundation.tlapl.us/ |

---

## Quotes (dated, sourced)

From the **developing.dev interview (2026-02-23)**:
- "If you're thinking without writing, you only think you're thinking." (~00:54:45)
- "What does understanding mean? For me, understanding means you can write a proof of
  it. But what understanding means for most people is a warm fuzzy feeling." (~00:50:36)
- "The gift that I have is not in some sense raw intelligence. It's abstraction." (~01:08:48)
- On Raft: when the Raft authors sent him a draft, he told them to send it back when
  they had "an algorithm or a proof"; he was later told Raft is "basically the Paxos
  paper with some details filled in that the Paxos paper left unfinished," described
  very differently.
- "I shouldn't waste time trying to answer questions that I don't have to answer." (~01:09:24)

From the **SCALE 22x keynote / New Stack coverage (talk 2025-03-09; article 2026-03-14)**:
- "Coding isn't programming." (talk title; coding : programming :: typing : writing)
- "Writing stream-of-consciousness code doesn't produce a good program."
- "Thinking is always better than not thinking before coding."
- "You write an abstraction to help you think about the problem before you think
  about the code."
- Stripping a project to its essentials takes "extra thinking," but "it saves a lot
  of time in the end, because it can produce something simpler."

Historical / canonical:
- "A distributed system is one in which the failure of a computer you didn't even know
  existed can render your own computer unusable." (June 1987 email)
- "The Paxos algorithm, when presented in plain English, is very simple."
  ("Paxos Made Simple," 2001)
- "Coding is to programming what typing is to writing." (recurring)
- Earlier Quanta interview framing: programmers should learn more math / think before
  coding (Quanta, 2022-05-17).

---

## All URLs collected

- https://en.wikipedia.org/wiki/Leslie_Lamport
- https://lamport.org/
- https://lamport.azurewebsites.net/tla/news.html
- https://lamport.azurewebsites.net/tla/science.pdf
- https://lamport.azurewebsites.net/tla/book.html
- https://lamport.azurewebsites.net/pubs/pubs.html
- https://www.microsoft.com/en-us/research/people/lamport/
- https://amturing.acm.org/award_winners/lamport_1205376.cfm
- https://www.developing.dev/p/turing-award-winner-on-working-with
- https://thenewstack.io/tla-creator-leslie-lamport-programmers-need-abstractions/
- https://www.socallinuxexpo.org/scale/22x/presentations/closing-keynote-leslie-lamport/
- https://www.youtube.com/watch?v=tsSDvflzJbc  (SCALE 22x keynote video)
- https://foundation.tlapl.us/
- https://conf.tlapl.us/
- https://www.quantamagazine.org/computing-expert-says-programmers-need-more-math-20220517/
- https://www.microsoft.com/en-us/research/blog/tla-foundation-aims-to-bring-math-based-software-modeling-to-the-mainstream/
- https://spectrum.ieee.org/tla

---

## Roster cross-references (for pairs / conflicts)

Verified slugs present in `superintelligence/engineering/ROSTER.md`:
- `marc-brooker` — cloud-architecture; AWS formal methods (TLA+/P), "Formal Methods:
  Just Good Engineering Practice?" Natural pair on formal methods. (brief)
- `martin-kleppmann` — data-and-storage; DDIA, distributed-systems pedagogy. (brief)
- `pat-helland` — data-and-storage; "Life Beyond Distributed Transactions,"
  immutability, state-machine thinking. (brief)
- `eric-brewer` — cloud-architecture; CAP theorem. Productive conflict: Lamport's
  proof-first / "specify then build" formalism vs Brewer's pragmatic
  availability-vs-consistency-tradeoff framing. (brief)
- `jeff-dean` — data-and-storage; built the production systems (Chubby/Paxos in
  practice) Lamport theorized. Productive conflict on theory-first vs
  build-and-measure.
- `andy-pavlo` — data-and-storage; DB systems teaching, self-driving DBs.
- `john-carmack` — systems-programming; "ship it / measure it" pragmatist —
  productive conflict with proof-first specification.
- `dhh` — architecture-testing-craft; "just ship the monolith," anti-ceremony —
  productive conflict with up-front formal specification.
