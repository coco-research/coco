# Jonathan Blow — Research Notes

**Slug:** `jonathan-blow`
**Cell:** systems-programming
**Cell role:** specialist
**Home team:** engineering
**Researched:** 2026-05-30
**Researcher:** Claude (engineering SI build, wave E6)

These are the raw, dated findings behind `superintelligence/engineering/personas/jonathan-blow.md`. Saved so future re-syntheses do not re-crawl.

---

## Identity confirmation

- **Full name:** Jonathan David Blow. Born November 3, 1971, Southern California.
- **Education:** UC Berkeley, double major in computer science and English; dropped out with less than one semester remaining.
- **Studio:** Thekla, Inc. (the studio name used for *The Witness* onward; earlier games released under Number None).
- **Games:** *Braid* (2008), *The Witness* (2016), *Order of the Sinking Star* (announced Dec 11, 2025, releasing 2026).
- **Language:** Jai — proprietary systems language he and Thekla have been building since 2014, codename "Jai," sometimes styled JAI. Targeted as a modern C++ replacement for game/systems work.

Identification is unambiguous — single well-known public figure, matching all task descriptors (Braid, The Witness, Jai, "Preventing the Collapse of Civilization," anti-bloat polemic). Confidence in identity: very high.

Source: https://en.wikipedia.org/wiki/Jonathan_Blow (fetched 2026-05-30)

---

## Correcting / verifying task assumptions

- **"Indie game designer (Braid, The Witness)"** — Correct. But note Blow himself is uncomfortable with the "indie developer" label and believes the indie scene has stagnated in design progress. Worth capturing as nuance, not contradiction. (Wikipedia)
- **"Creator of the Jai programming language"** — Correct. Began designing in 2014; full-time after *The Witness* (2016). As of early 2026 still in **closed beta** ("a few hundred users"), invite-only, no public download. NOT yet publicly released — important correction to any assumption that Jai is generally available. (Mr. Phil Games "Jai in 2026"; Wikipedia Jai page)
- **"Jai beta release [as a recent 12-month signal]"** — Partial correction. There is NOT a public general-availability beta release in the last 12 months. The accurate framing is: Jai remained in private/closed beta through 2025–2026, and Thekla announced (Dec 2025) it will open-source the engine and language *after* Order of the Sinking Star ships. Active beta development continues (CHANGELOG iterating, e.g. beta 0.0.045), and the public dev streams continue. I used the Order of the Sinking Star announcement, the podcasts, and the Jai-in-2026 status report as the actual datable recent signals rather than a non-existent public beta launch.
- **"Preventing the Collapse of Civilization" talk** — Correct. Delivered at DevGAMM (Moscow), published to YouTube July 2019. Core thesis: software quality is declining; civilizational knowledge of how to build robust low-level systems is being lost generation-to-generation as abstraction insulates programmers from fundamentals. (Multiple sources below.)

---

## Canonical talks (dated)

- **"How to Program Independent Games"** — April 1, 2011, UC Berkeley CSUA invited talk. ~38 min + Q&A. Source: http://the-witness.net/news/2011/06/how-to-program-independent-games/
- **"The Truth in Game Design"** — GDC Europe 2011. Uses Conway's Game of Life, *Braid*, *The Witness* to argue for discovering rather than inventing game-design truths. Source: https://www.gamedeveloper.com/design/video-jon-blow-on-the-truth-in-game-design-
- **"Preventing the Collapse of Civilization"** — DevGAMM, published July 2019. YouTube: https://www.youtube.com/watch?v=ZSRHeXYDLko
  - Knowledge-loss-across-generations thesis (Roman concrete / Apollo program analogies).
  - "The quality of software today has decreased compared to software of the past"; users tolerate astonishing numbers of bugs vs. older software.
  - Abstraction insulates engineers from memory management / CPU fundamentals, accelerating loss of deep knowledge; "deep knowledge replaced by trivia."
  - Hardware limitations of the past forced efficient, creative solutions; computational abundance removes that discipline.
  - Sources: https://lukaspowers.substack.com/p/preventing-the-collapse-of-civilization ; https://datagubbe.se/endofciv/ ; https://news.ycombinator.com/item?id=25788317

---

## Jai — technical specifics (for signature_moves / mental_models)

- Statically typed, compiled, high-level systems language; "modern alternative to C++." (Wikipedia Jai page; Grokipedia)
- **Arbitrary compile-time code execution** via `#run` — any function can run at compile time with full read-write access to the program's AST. Blow: *"If I got rid of full arbitrary compile time execution, it wouldn't be the same programming language"* and *"Let's do everything at compile time. And by everything, I mean everything."* Source: https://grokipedia.com/page/jai-programming-language
- **Compile speed as a first-class design goal** — target of compiling ~1,000,000 lines/second; official figure ~250,000 lines/sec on x64 backend (CHANGELOG beta 0.0.045, benchmarked on Sokoban / Order of the Sinking Star codebase). Public demos showed the ~80,000-line game codebase compiling in under a second. Goal: cut typical dev time by ≥20%. Sources: Grokipedia; https://www.mrphilgames.com/blog/jai-in-2026
- No public package manager / no hidden allocations philosophy; explicit control, data-oriented design, integrated build system written in Jai itself.
- C++ frustration is the origin story: *"C++ is a powerful language in some ways ... but it makes [software development] a lot harder than it should be."* (Wikipedia)
- General software-quality lament: *"everybody in the world is flooded with low quality software, and everybody wishes that they had higher quality software."* (Wikipedia)

---

## Recent signals (all dated AFTER 2025-05-30) — verified

1. **Order of the Sinking Star announced at The Game Awards** — **2025-12-11**. Third Blow-directed game after Braid/Braid and The Witness; Sokoban-style grid puzzle; 1,400+ puzzles; 250h normal / 500h+ completionist; built entirely in Jai. Publisher Arc Games. ~10 years in development. Sources: https://en.wikipedia.org/wiki/Order_of_the_Sinking_Star ; https://www.engadget.com/gaming/ten-years-after-the-witness-jonathan-blows-next-massive-puzzle-game-is-almost-ready-for-primetime-015727378.html
   - Engadget quote: *"Once I was working on the game, it was a good way to show people what the programming language was about and also how game programming works."*
   - Engadget quote: *"We don't add puzzles to the game unless they show something cool about how the objects interact."*
   - Thekla press release (Dec 2025): *"Not too long after the game releases, we will give out the engine for free as an open-source project."*
2. **Software Unscripted podcast — "Jonathan Blow on Programming Language Design"** — **2025-11-15**. Covered compile-time execution, language feature interop, cross-compiling, memory safety vs. performance, dependency management. Sources: https://shows.acast.com/software-unscripted/episodes/jonathan-blow-on-programming-language-design ; https://lobste.rs/s/m7jvhl/jonathan_blow_on_programming_language (Lobsters discussion 2025-11-16)
3. **"Jai in 2026" status report (Mr. Phil Games)** — **January 2026**. Confirms closed beta, a few hundred users, open-source after game ships, professional adopters (Smari McCarthy since early 2020; Forrest Smith completed all 25 Advent of Code days in Jai, 4,821 lines). Source: https://www.mrphilgames.com/blog/jai-in-2026
4. **Wookash Podcast — Jonathan Blow on Jai and upcoming games** — **2026-01-24**. Topics: game, dev team structure, tooling decisions, materials/visual systems, state of Jai, metaprogramming, release date. Source: https://creators.spotify.com/pod/profile/lukasz-sciga/episodes/Jonathan-Blow-on-his-programming-language-jai-and-upcoming-games-e2tk405
5. **Order of the Sinking Star coming to Nintendo Switch 2** — **2026-05-14** (Nintendo Life). Arc Games' inaugural Switch 2 release; simultaneous with PC; later in 2026. Blow quote: *"Switch 2's portability is really nice here; you can just pick it up and play it in short bursts or really dive in for a long time."* Source: https://www.nintendolife.com/news/2026/05/order-of-the-sinking-star-from-braid-creator-jonathan-blow-is-coming-to-switch-2

6. **LambdaConf 2025 keynote "Visualizing Programs" / "Jai Demo and Design Explanation" posted** — **2025-07-11** (announced by Blow on X). Demonstrates Jai tooling for visualizing program structure (each square = a procedure sized by expression count), compile-time generic-instantiation impact on binary size, memory-allocation patterns, module dependencies, and a live visual memory debugger. Sources: https://x.com/Jonathan_Blow/status/1943438983935201435 ; https://www.youtube.com/watch?v=IdpD5QIVOKQ ; https://ziggit.dev/t/visualizing-programs/10920 ; https://www.lambdaconf.us/speakers/jonathan-blow (all confirmed 2026-05-30)

(Six recent signals; bar is ≥3. Re-verification pass 2026-05-30 confirmed all dates and added the LambdaConf signal.)

---

## Public stances (each with an evidence URL)

- **Software quality is in measurable decline; users tolerate far more bugs than they used to.** — https://www.youtube.com/watch?v=ZSRHeXYDLko (Preventing the Collapse of Civilization) ; https://en.wikipedia.org/wiki/Jonathan_Blow
- **Layered abstraction is the primary mechanism by which engineering knowledge is lost between generations.** — https://lukaspowers.substack.com/p/preventing-the-collapse-of-civilization
- **C++ is needlessly complex; a leaner, performance-first, data-oriented language (Jai) is the corrective.** — https://en.wikipedia.org/wiki/Jai_(programming_language)
- **Compile speed is a moral / productivity issue — slow builds are an unacceptable tax; aim for ~1M lines/sec.** — https://www.mrphilgames.com/blog/jai-in-2026 ; https://grokipedia.com/page/jai-programming-language
- **Full arbitrary compile-time execution is non-negotiable; "do everything at compile time."** — https://grokipedia.com/page/jai-programming-language
- **The indie game movement stagnated in design ambition; he resists the "indie" label.** — https://en.wikipedia.org/wiki/Jonathan_Blow
- **Craft / "truth in game design": you discover design truths, not invent them; only ship a puzzle that reveals something genuinely new about the system.** — https://www.gamedeveloper.com/design/video-jon-blow-on-the-truth-in-game-design- ; Engadget Dec 2025 quote above.

---

## Productive-conflict mapping (against real ROSTER.md slugs)

ROSTER cells reviewed for genuine, substantive disagreement axes:

- **web-and-frontend** — `rich-harris` (Svelte), `dan-abramov` (React), `guillermo-rauch` (Vercel/Next.js). Blow's anti-abstraction / native-performance / "the web stack is the canonical example of bloat" position is in direct tension with the JS-framework, build-tooling, layered-platform worldview. Strong productive conflict.
- **architecture-testing-craft** — `martin-fowler` (patterns/microservices), `gregor-hohpe` (enterprise integration / abstraction layers), `kent-beck` (TDD). Blow distrusts heavy pattern/abstraction culture and is skeptical of test-first dogma over direct, readable, fast code. Good conflict with abstraction-heavy architects.
- **languages-runtimes** — `bjarne-stroustrup` (C++, the literal thing Jai was built to escape). Sharp, well-documented disagreement.
- **devops-platform** — `kelsey-hightower` / `solomon-hykes` (containers, platform layers) — Blow would view the container/cloud-platform stack as bloat. Secondary conflict.

Chosen for frontmatter: `rich-harris`, `dan-abramov`, `martin-fowler`, `gregor-hohpe`, `bjarne-stroustrup`. All confirmed present in ROSTER.md.

## Pairs-well-with

- `john-carmack` (systems-programming, same cell) — performance-first, low-level mastery, skepticism of bloat, both legendary game programmers. Task-specified pairing; confirmed in ROSTER.md.
- `bryan-cantrill` (systems-programming) — hardware/software craftsmanship, anti-bloat, blunt cultural critic. Natural ally.
- `mitchell-hashimoto` (systems-programming) — Ghostty, native-performance terminal, craftsmanship ethos.
- `linus-torvalds` (systems-programming) — blunt, performance/correctness-first, distrust of fashionable abstraction.

---

## Blind spots (for the persona)

- Blunt cultural critic whose off-technical public positions (anti-vaccine rhetoric, support for Trump, opposition to DEI) have alienated collaborators — in Dec 2025, designers Alan Hazelden, Sean Barrett, and Jonah Ostroff (whose Sokoban-genre work influenced Order of the Sinking Star) publicly objected to his political views. Relevant as a *collaboration / team-dynamics* blind spot, not a technical one. Source: https://en.wikipedia.org/wiki/Order_of_the_Sinking_Star ; https://en.wikipedia.org/wiki/Jonathan_Blow
- Tends to treat "ship a perfect, hand-crafted artifact over a decade" as the default; under-weights time-to-market, team scaling, and the business case for "good enough" software.
- Skeptical-to-dismissive of memory-safety-by-language-design (Rust's borrow checker) and of managed runtimes; favors programmer discipline + performance over guardrails — a blind spot when the cost of a memory bug is catastrophic.
- Under-weights the value of broad abstraction layers for *team* productivity at scale; his frame is optimized for small, elite teams (Thekla), not 500-engineer orgs.
- Largely dismissive of AI-assisted / "vibe" coding as a serious engineering practice — risks missing genuine productivity shifts. (Software Unscripted Nov 2025; YouTube "Jonathan Blow said THIS about Vibe Coding".)

---

## Full source list (>=8 real URLs; >=3 recent)

1. https://en.wikipedia.org/wiki/Jonathan_Blow
2. https://en.wikipedia.org/wiki/Jai_(programming_language)
3. https://en.wikipedia.org/wiki/Order_of_the_Sinking_Star  (recent — Dec 2025 event)
4. https://www.engadget.com/gaming/ten-years-after-the-witness-jonathan-blows-next-massive-puzzle-game-is-almost-ready-for-primetime-015727378.html  (2025-12-11)
5. https://www.mrphilgames.com/blog/jai-in-2026  (Jan 2026)
6. https://www.nintendolife.com/news/2026/05/order-of-the-sinking-star-from-braid-creator-jonathan-blow-is-coming-to-switch-2  (2026-05-14)
7. https://shows.acast.com/software-unscripted/episodes/jonathan-blow-on-programming-language-design  (2025-11-15)
8. https://creators.spotify.com/pod/profile/lukasz-sciga/episodes/Jonathan-Blow-on-his-programming-language-jai-and-upcoming-games-e2tk405  (2026-01-24)
9. https://www.youtube.com/watch?v=ZSRHeXYDLko  (Preventing the Collapse of Civilization)
10. https://grokipedia.com/page/jai-programming-language
11. https://www.gamedeveloper.com/design/video-jon-blow-on-the-truth-in-game-design-
12. http://the-witness.net/news/2011/06/how-to-program-independent-games/
13. https://lukaspowers.substack.com/p/preventing-the-collapse-of-civilization
14. https://datagubbe.se/endofciv/
