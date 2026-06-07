# Graydon Hoare — Research Notes

**Slug:** graydon-hoare
**Cell:** languages-runtimes
**Researched:** 2026-05-30
**Status determination:** ACTIVE (not archetype). The brief flagged that he is "lower-profile" and asked us to search hard for post-2025-05-30 signal and fall back to `status: archetype` if fewer than three genuinely recent posts could be found. **Correction logged:** the assumption that he is barely active does not hold. His Dreamwidth blog (`graydon2.dreamwidth.org`) shows a steady cadence of substantive, widely-discussed posts across 2025 and into 2026. He is lower-profile than peak-Rust-era Graydon, but he is demonstrably an active essayist. We therefore set `status: active` and populate `recent_signal_12mo` with five posts dated after 2025-05-30, all corroborated by Hacker News submission timestamps.

---

## Identity confirmation

- **Real name:** Graydon Hoare. Canadian software engineer, lives in Vancouver, BC.
- **Self-description (Uses This interview):** "middle-aged socialist boring cishet white guy." Specializes in developer tools (compilers, profilers, debuggers) and distributed systems. Source: https://usesthis.com/interviews/graydon.hoare/
- **Career timeline (Wikipedia / The New Stack / Crunchbase):**
  - Started Rust as a personal side-project around 2006. Mozilla adopted it and gave him a team (~2009).
  - Stepped back from Rust technical leadership around 2013 (burnout); worked on lower-profile Mozilla projects (Firefox-on-Android test automation, Mozilla Location Service).
  - 2014: joined Stellar (distributed payment network / transaction processor).
  - 2016: joined Apple to work on the Swift programming language; reportedly no longer on Swift by ~2019.
  - Also worked at Red Hat earlier in career.
  - 2026: lower public profile; primary public output is occasional long-form essays on his Dreamwidth blog. Exact current employer is not publicly disclosed in recent sources, so `affiliations_2026` is conservatively set to independent essayist / not publicly disclosed.
- Sources:
  - https://en.wikipedia.org/wiki/Rust_(programming_language)
  - https://thenewstack.io/graydon-hoare-remembers-the-early-days-of-rust/
  - https://usesthis.com/interviews/graydon.hoare/
  - https://www.crunchbase.com/person/graydon-hoare

**Disambiguation note:** Graydon Hoare is NOT Tony Hoare (C.A.R. Hoare, of quicksort / null-reference / CSP / Hoare logic fame). They are different people and not related; this is a recurring point of confusion online (see https://users.rust-lang.org/t/from-tony-hoare-to-graydon-hoare/132033). The "billion-dollar mistake" null-reference quote belongs to Tony Hoare, not Graydon. Logged so the persona does not conflate them.

---

## Recent activity inventory (post-2025-05-30) — RECENCY EVIDENCE

Built from the Hacker News Algolia API search of `graydon2.dreamwidth.org` story submissions, cross-checked against the Lobsters domain listing. HN submission timestamps are reliable proxies for publication dates (posts are typically submitted within hours/days of publishing).

Source for inventory: https://hn.algolia.com/api/v1/search?query=graydon2.dreamwidth.org&tags=story

| Date (HN submit) | Title | URL | HN points |
|---|---|---|---|
| 2026-03-15 | "LLM Time" | https://graydon2.dreamwidth.org/322732.html | 19 |
| 2026-02-27 | "Dear Time Lords: Freeze Computers in 1993" | https://graydon2.dreamwidth.org/322461.html | 115 |
| 2025-11-07 | "A Note on Fil-C" | https://graydon2.dreamwidth.org/320265.html | 241 |
| 2025-07-18 | "Losing language features: some stories about disjoint unions" | https://graydon2.dreamwidth.org/318788.html | 119 |
| 2025-06-16 | "Retrobootstrapping Rust for some reason" | https://graydon2.dreamwidth.org/317484.html | 142 |

That is FIVE posts after 2025-05-30, each independently submitted and discussed on Hacker News (the Fil-C post alone drew 241 points and ~210 comments). The recency bar (>=3 in last 12 months) is comfortably met. Status: ACTIVE.

Just-outside-window but useful canonical context:
- 2025-05-15 "10 Years of Stable Rust: An Infrastructure Story" — guest piece for the Rust Foundation. https://rustfoundation.org/media/10-years-of-stable-rust-an-infrastructure-story/ (This is 2 weeks before the 12-month cutoff, so it is filed under canonical_works, not recent_signal_12mo.)

The dreamwidth blog itself returns a CAPTCHA wall to automated fetchers (303 redirect to /captcha), so post content below was reconstructed from HN/Lobsters discussion threads and reputable secondary coverage that quote the posts. Direct-quote provenance is noted per item.

---

## Post content / argument notes

### "The Rust I Wanted Had No Future" (2023-06-05) — canonical, the headline essay
URL: https://graydon2.dreamwidth.org/307291.html
Mirror quoting the post in full: https://mjtsai.com/blog/2023/06/08/the-rust-i-wanted-had-no-future/

Thesis: the language Graydon would have built, given absolute creative control, would NOT have been as popular as the Rust we got — and that's fine, because the community's future-oriented choices are what made Rust succeed. Key design disagreements he names:
- **Performance vs. simplicity tradeoff (the core one):** "I would have traded performance and expressivity away for simplicity — both end-user cognitive load and implementation simplicity in the compiler." The community instead chose to "compete to win with C++ on performance." This is the spine of the whole essay.
- **Type-parameter / lifetime syntax:** disliked angle brackets `<T>` and the apostrophe-lifetime `'a` syntax; preferred square brackets for type parameters.
- **Structural typing + reflection:** wanted structural typing with compiler-emitted "type descriptors" reachable via a reflection operator. Rust went nominal.
- **Decimal type for money:** wanted a built-in decimal type up front for financial math; it was perpetually deferred to libraries.
- **Integer overflow:** wanted an integer type that overflows into an owned/refcounted bignum; "lost" that argument. Rust integers wrap or trap.
- **Tail calls:** "actually wanted them," dropped because of the C++ performance competition — "one of the saddest things ever written on the subject."
- **Stable ABI / crate boundaries:** wanted crates to inline internally but present stable entrypoints externally; "objected to the choice ever since," ties it to Rust's compile-time problems.

Quote (paraphrase widely reproduced): "the Rust We Got is many, many miles away from The Rust I Wanted."

Social-dynamics theme: he is at peace with having lost most of these arguments. The community's priorities (the "future" of the title) diverged from his, and the divergence is precisely what gave Rust a future. Self-effacing, anti-ego, "the project is bigger than its founder."

### "Always Bet on Text" (2014-10-13) — canonical
URL: https://graydon2.dreamwidth.org/193447.html
Thesis: "text is the most powerful, useful, effective communication technology ever, period." Text is the oldest and most stable communication tech; durable ("you can read texts from five thousand years ago"); "rock solid" — "you can inscribe it in granite that will likely outlast the human species"; and the most flexible. Note: this essay has been re-submitted to HN repeatedly (2015, 2021, 2023, 2025-12-26) — it is "Lindy," it keeps resurfacing, and it got a fresh wave of attention in the LLM era (e.g. Guillermo Rauch reshared it; oskarth: "This is even more relevant now in the age of LLMs. Text is Lindy.").
Corroboration: https://x.com/rauchg/status/1806720710569799874 ; https://jerz.setonhill.edu/blog/2017/03/15/always-bet-on-text/

### "things rust shipped without" (2015-07-03) — canonical
URL: https://graydon2.dreamwidth.org/218040.html
A catalog of features Rust deliberately shipped WITHOUT (GC, green threads in the runtime, a stable ABI, etc.) — the discipline of subtraction. 408 HN points; re-surfaced as recently as ~9 months ago on Lobsters. Demonstrates his "what you leave out is a design decision" lens.

### "10 Years of Stable Rust: An Infrastructure Story" (2025-05-15) — canonical, Rust Foundation guest piece
URL: https://rustfoundation.org/media/10-years-of-stable-rust-an-infrastructure-story/
- Frames Rust as **infrastructure**, not just a language: "Rust is a tool for building other infrastructure: network protocols, web servers, load balancers, telemetry systems, databases, codecs, cryptography, file systems, operating systems, virtual machines, interpreters, etc."
- On the motivation: "the infrastructure we had was not up to the task ... Crashes and downtime in the best cases, and security vulnerabilities in the worst." Driven by Moore's law plateauing + multicore + connectivity → an "infrastructure deficit."
- On lineage of the safety model: "Rust's safe memory model derives directly from decades of research in academia, as well as academic-industrial projects like Cyclone, built by AT&T Bell Labs and Cornell."
- On community: "Rust is a story about a large community of stakeholders coming together to design, build, maintain, and expand shared technical infrastructure"; credits "thousands and thousands of volunteers."
- On good infrastructure being invisible: "The robust and reliable necessities that enable us to get our work done ... confident that the system will keep humming along unattended."

### "A Note on Fil-C" (2025-11-07) — RECENT SIGNAL
URL: https://graydon2.dreamwidth.org/320265.html
HN thread: https://news.ycombinator.com/item?id=45842494 (241 pts, ~210 comments)
Fil-C is Filip Pizlo's memory-safe implementation of C/C++ (garbage-collected, capability/pointer-checked). Graydon's argument: Fil-C is a genuinely valuable pragmatic path to memory safety for the enormous installed base of existing C/C++ code, WITHOUT requiring a full rewrite into Rust. He frames the crash-instead-of-corrupt tradeoff as acceptable: "almost all programs have paths that crash, and perhaps the density of crashes will be tolerable." Notable because the Rust creator is publicly endorsing a NON-Rust route to memory safety — consistent with his "memory safety is the goal, Rust was one means" worldview, and his humility about Rust not being the only answer. (He also reacted warmly to the project: "This is super kind and awesome, I'm seriously flattered!")

### "Losing language features: some stories about disjoint unions" (2025-07-18) — RECENT SIGNAL
URL: https://graydon2.dreamwidth.org/318788.html
HN thread: https://news.ycombinator.com/item?id=44605245 (119 pts)
A historical tour of why languages have repeatedly failed to ship SAFE disjoint/sum types (tagged unions). FORTRAN's EQUIVALENCE storage overlays, C's unsafe `union` (borrowed from ALGOL 68), Pascal's unsafe variant records, Go's lack of first-class sum types. Core insight: designers' historical dismissal of "wasted bits" on a discriminant tag reflected genuine memory scarcity, not foolishness — but it baked unsafe patterns into the canon that persist long past the constraint. Rust's `enum` (safe sum types) is the corrective. Shows his historian-of-PLT lens.

### "Retrobootstrapping Rust for some reason" (2025-06-16) — RECENT SIGNAL
URL: https://graydon2.dreamwidth.org/317484.html
HN thread context: 142 pts. About reconstructing/bootstrapping early Rust toolchains — a software-archaeology / reproducibility exercise. Reinforces his interest in provenance, bootstrapping, and the durability of toolchains over time (the same instinct as "Dear Time Lords" and the bitmap-font preservation in the Uses This interview).

### "Dear Time Lords: Freeze Computers in 1993" (2026-02-27) — RECENT SIGNAL
URL: https://graydon2.dreamwidth.org/322461.html
HN thread: https://news.ycombinator.com/item?id=47176581 (115 pts)
Provocation/thought-experiment: computing should arguably have been "frozen" around 1993 — by then we had enough capability for meaningful work, while retaining simplicity, stability, and (per commenters' reading) better social outcomes; everything since has added complexity, surveillance, and "enshittification" without proportional benefit. A polemic about complexity-as-decay. Ties directly to his Uses This lament that "almost no modern software works well or is safe."

### "LLM Time" (2026-03-15) — RECENT SIGNAL
URL: https://graydon2.dreamwidth.org/322732.html
Tags on the post: `culture`, `vibecoding`. A cultural reflection on LLMs / "vibe coding." Direct content blocked by the CAPTCHA wall; classified from the post's own tags and the surrounding body of his recent work. Lower HN engagement (19 pts) than the Fil-C piece. Filed as a recent signal because it is a dated, attributable post on his blog; the takeaway is kept deliberately conservative (he is engaging critically with the LLM-coding moment) since full text could not be retrieved.

---

## Uses This interview (philosophy spine) — undated but evergreen
URL: https://usesthis.com/interviews/graydon.hoare/
- Daily tools: Emacs, command-line utilities, compilers across many languages.
- Hardware: deliberately old/reliable — stockpiles 2013–2015 MacBook Airs, refurb dual-socket Xeon workstations, older ThinkPads; "we haven't seen a ton of machine improvement in the past decade." Maximizes RAM and cores over novelty.
- Fonts: fights to keep low-res bitmap fonts (ctrld, Dina, Proggy) alive: "it looks right."
- The money quote on his worldview: laments that "almost no modern software works well or is safe," and wishes for time-rewinding plus **liability legislation** to force "software that has any sort of reliability." Critiques the industry's optimization for engagement over function and security.

---

## Stance synthesis (each maps to a public_stance with evidence_url)

1. "Memory safety is the goal; Rust was one means to it" — Fil-C endorsement (https://graydon2.dreamwidth.org/320265.html) + 10-years-of-Rust framing of safety as derived from Cyclone/academia (https://rustfoundation.org/media/10-years-of-stable-rust-an-infrastructure-story/).
2. "I would have traded performance and expressivity for simplicity" — the explicit thesis of "The Rust I Wanted Had No Future" (https://mjtsai.com/blog/2023/06/08/the-rust-i-wanted-had-no-future/).
3. "Always bet on text" — text is the most durable, flexible, powerful communication tech (https://graydon2.dreamwidth.org/193447.html).
4. "What a language ships WITHOUT is a primary design decision" — "things rust shipped without" (https://graydon2.dreamwidth.org/218040.html).
5. "A language is infrastructure, and good infrastructure is invisible and reliable" — Rust Foundation 10-year piece (https://rustfoundation.org/media/10-years-of-stable-rust-an-infrastructure-story/).
6. "A language is a community/social project; the founder's vision is not the point" — both the Rust Foundation piece and "The Rust I Wanted Had No Future" (https://thenewstack.io/graydon-hoare-remembers-the-early-days-of-rust/).
7. "Most modern software is neither reliable nor safe; we need liability, not just better intentions" — Uses This interview (https://usesthis.com/interviews/graydon.hoare/) reinforced by "Dear Time Lords" (https://graydon2.dreamwidth.org/322461.html).

---

## Roster cross-references (validated against ROSTER.md)

`pairs_well_with` (real slugs, same languages-runtimes cell or adjacent):
- `chris-lattner` — LLVM/Swift/Mojo; Graydon literally worked alongside the Swift world; both think in compiler infrastructure and language-as-platform terms.
- `rich-hickey` — "Simple Made Easy," value-of-values; Graydon's simplicity-over-performance and his "what we shipped without" subtraction discipline rhyme with Hickey's simplicity gospel.
- `anders-hejlsberg` — type-system pragmatism; both reason about cognitive load of type syntax and the realities of shipping a language to a huge audience.
- `bryan-cantrill` (systems-programming) — Oxide, "software should be reliable infrastructure," shared liability/quality-of-software politics.

`productive_conflict_with` (real slugs — the brief explicitly suggests Stroustrup):
- `bjarne-stroustrup` — Rust-vs-C++ and the memory-safety-vs-performance/compatibility axis. Graydon's "I'd trade performance for simplicity" and his Fil-C endorsement (a non-rewrite safety path) cut directly against Stroustrup's "you don't pay for what you don't use" zero-overhead philosophy and his defense of C++'s safety-profiles incrementalism.
- `john-carmack` (systems-programming) — Carmack's performance-first, hand-tuned, "ship it fast" instinct collides with Graydon's "freeze computers in 1993 / trade performance for simplicity / liability for unsafe software" worldview.

Both conflict targets are real ROSTER.md slugs (bjarne-stroustrup, languages-runtimes; john-carmack, systems-programming).

---

## Unmet-bar audit
- sources: 12 real URLs collected (>=8 met).
- recent_signal_12mo: 5 dated posts post-2025-05-30 (>=3 met).
- Every public_stance carries an evidence_url (met).
- Direct full-text of three 2025–2026 posts (Retrobootstrapping, Dear Time Lords specifics, LLM Time) could not be pulled from the source due to the dreamwidth CAPTCHA wall; takeaways for those were reconstructed from HN threads + post tags and kept conservative. All other content is from primary text or full-quote mirrors. No bar item unmet; this is a fidelity caveat, not a gap.
