# Brendan Eich — Research Notes

**Researched:** 2026-05-30
**Researcher:** Claude (engineering-super-intelligence build, Wave E6, languages-runtimes)
**Slug:** `brendan-eich`
**Cell:** `languages-runtimes` | **Role:** specialist | **Home team:** engineering

---

## Identity confirmation (high confidence, 1.00)

Brendan Eich is an unambiguous, well-documented public figure. Identification is certain — there is exactly one famous Brendan Eich: the creator of JavaScript, co-founder of Mozilla, and co-founder/CEO of Brave Software. No disambiguation needed.

- Born **July 4, 1961**, Pittsburgh, Pennsylvania.
- BS in mathematics and computer science, Santa Clara University.
- MS 1985, University of Illinois Urbana-Champaign.
- Started career at Silicon Graphics (~7 years, OS and network code), then MicroUnity, then Netscape.
- Source: https://en.wikipedia.org/wiki/Brendan_Eich

---

## Biographical timeline (verified)

| Date | Event |
|---|---|
| April 1995 | Joins Netscape, intending to embed Scheme in the browser. Management insists syntax resemble Java. |
| May 1995 | Writes the first JavaScript prototype in **10 days**. Initially named **Mocha**. |
| Sept 1995 | Renamed **LiveScript**, shipped with Navigator 2.0 beta. |
| Dec 1995 | Renamed **JavaScript** in a joint Netscape/Sun announcement. Eich also designs **SpiderMonkey**, the JS engine. |
| 1998 | Co-founds the Mozilla project (mozilla.org) with Jamie Zawinski and others; chief architect. |
| Aug 2005 | Becomes CTO of the newly created Mozilla Corporation. |
| 2011 | Hands off ownership of the SpiderMonkey module to Dave Mandelin. |
| Mar 24, 2014 | Appointed CEO of Mozilla. |
| Apr 3, 2014 | Resigns after **11 days** amid controversy over a 2008 $1,000 donation to California Proposition 8. "Under the present circumstances, I cannot be an effective leader." |
| 2015 | Co-founds **Brave Software** (with Brian Bondy). |
| Jan 2016 | Brave releases developer builds of its Chromium-based, ad/tracker-blocking browser. |
| May 31, 2017 | **Basic Attention Token (BAT)** ICO raises $35M in under 30 seconds. |

Sources:
- https://en.wikipedia.org/wiki/Brendan_Eich
- https://en.wikipedia.org/wiki/Brave_(web_browser)

---

## Technical legacy and stances

- **"Always bet on JS"** — his signature closing line in talks (Fluent, Finjs NYC 2016). Later pivoted to **"Always bet on JS — and WASM"** as WebAssembly matured. He framed browser JS engines as becoming "truly polyglot virtual machines," with JS enduring/absorbing APIs while WASM "carries some of the weight."
  - Source: https://www.slideshare.net/BrendanEich/always-bet-on-js-finjsio-nyc-2016
  - Source: https://medium.com/javascript-scene/why-we-need-webassembly-an-interview-with-brendan-eich-7fb2a60b0723
- Sponsor of **asm.js** (the typed-subset-of-JS precursor that proved native-speed compilation in the browser) and an early driver of **WebAssembly**.
- Long-standing member of **Ecma TC39**, the JavaScript standards committee. He has publicly worried that "tech giants could botch WebAssembly" — i.e., a standard captured by big vendors loses the open-web property.
  - Source: https://www.infoworld.com/article/2254271/brendan-eich-tech-giants-could-botch-webassembly-2.html
- The famous self-deprecation: JavaScript's flaws (type coercion, `==` vs `===`, hoisting) trace to the 10-day deadline and the management mandate to "make it look like Java." He has called this both JavaScript's "blessing and curse" — the flaws shipped, but worse-is-better shipping is also why JS won.
  - Source: https://www.infoworld.com/article/2256143/interview-brendan-eich-on-javascripts-blessing-and-curse.html
- His personal blog (brendaneich.com) is the canonical home of his language-design and web-platform essays.
  - Source: https://brendaneich.com/

---

## Brave / privacy / ads economics thesis

- **Privacy-by-default.** Brave blocks ads and trackers by default; the BAT model lets users opt in to privacy-preserving ads and earn 70% of ad spend in BAT. The thesis: the web needs ad funding, but not surveillance-based ad funding. "The Web requires ads for much of its funding, but not the poorly performing ads and trackers."
  - Source: https://brave.com/author/brendan-eich/ ("How Brave Works for You", Jan 27 2016)
- **Brave scale (Oct 2025):** ~100M monthly active users, ~42M daily active users.
  - Source: https://en.wikipedia.org/wiki/Brave_(web_browser)
- **"Metaphysical rebellion against big tech surveillance"** — his framing in a Blockworks interview. (Could not fetch full text — 403 Forbidden — but the framing is in the headline/summary and corroborated across sources.)
  - Source (headline + summary): https://blockworks.com/news/metaphysical-rebellion-big-tech-brave-ceo

---

## Recent signals (post-2025-05-30) — VERIFIED DATES

1. **"Verifiable Privacy and Transparency: A new frontier for Brave AI privacy"** — blog post, **Nov 20, 2025**. Announces Brave Leo deploying LLMs (DeepSeek V3.1 in Brave Nightly) inside NEAR.AI Nvidia-backed Trusted Execution Environments for cryptographically verifiable privacy. Moves from "trust me bro" to "trust but verify."
   - Source: https://brave.com/author/brendan-eich/

2. **Brave Leo adds Trusted Execution Environments** — The Register, **Nov 22, 2025**. Eich: "trust but verify" as privacy-by-design philosophy; TEEs (Intel TDX + Nvidia) let users verify the declared model is actually serving them and stop providers secretly swapping in cheaper models.
   - Source: https://www.theregister.com/software/2025/11/22/brave-ai-assistant-leo-adds-trusted-execution-environments/2176243

3. **"Unseeable prompt injections in screenshots: more vulnerabilities in Comet and other AI browsers"** — Brave security blog, public disclosure **Oct 21, 2025** (discovered Oct 1, 2025). Brave's security team (under Eich) demonstrates that agentic AI browsers are inherently insecure: indirect prompt injection via near-invisible text in screenshots executes as commands. Builds on the earlier Aug 2025 Comet disclosure.
   - Source: https://brave.com/blog/unseeable-prompt-injections/
   - Earlier (Aug 25, 2025): https://brave.com/blog/comet-prompt-injection/

4. **Brave Origin clarification** — X / PiunikaWeb, **Jan 2, 2026**. Eich did damage control after Reddit misinformation that Brave was paywalling features. "Brave stays as is, nothing paygated or changed due to Brave Origin." "Yes, we don't want subscription for this any more than you do." Brave Origin = an optional, separate build stripped of telemetry, rewards, wallet, VPN, and AI; free on Linux, one-time purchase elsewhere.
   - Source: https://piunikaweb.com/2026/01/02/brave-origin-misinformation-brendan-eich-clarifies/

5. **"Privacy is Fundamental: Verifiable Privacy and Transparency in the Age of AI"** — NEARCON talk, YouTube published **Feb 26, 2026**. Argues privacy succeeds when it enables adoption, verification, and real markets — privacy must be usable and verifiable, not just promised.
   - Source: https://www.youtube.com/watch?v=QJBSw9IOuLE

6. (Supporting) **Midnight Summit 2025 panel** — Dec 2025, with Illia Polosukhin, Mert Mumtaz, Zooko Wilcox. Argued for a private-by-default internet where AI is designed to protect user data.
   - Source: https://www.youtube.com/watch?v=SXWQzshQ4j4

---

## Corrected / clarified assumptions

- **Task brief said "founder & CEO of Brave."** More precise: **co-founder** (with Brian Bondy) and CEO. Brave Software, 2015. Logged for accuracy in the profile frontmatter via affiliations.
- **Task brief implied JavaScript was created "in 10 days, 1995."** Confirmed accurate — the prototype was written in 10 days in May 1995. The *naming* to "JavaScript" came in December 1995. The "10 days" refers to the prototype, not the full year of standardization.
- **The Mozilla CEO tenure was 11 days (Mar 24 – Apr 3, 2014), not a long tenure.** This is a defining, citable episode and is included because it shapes his "outspoken contrarian" archetype and his later stance on free expression / not bending to pressure.
- **Brave Origin is NOT a paywalling of Brave.** The Jan 2026 episode was misinformation; Eich's clarification is the signal, not a product pivot.

---

## Productive-conflict mapping (against real ROSTER.md slugs)

- **`ryan-dahl`** (systems-programming; Node.js, Deno) — Direct, real tension on JavaScript/runtime direction. Dahl built Node (server-side JS) and then Deno explicitly to *fix Node's regrets* (security-by-default, TypeScript-native, web-standard APIs). Eich is the language's creator and a TC39 institutionalist who bets on JS+WASM co-evolution inside the browser. They disagree on where the runtime's center of gravity should sit (browser standards vs. server runtime reinvention) and on how much to break with JS's legacy. **Strong, real conflict pair.**
- **`graydon-hoare`** (languages-runtimes; Rust creator) — Rust represents the "design carefully, prevent whole classes of bugs at compile time" philosophy; JavaScript represents "ship the worse-is-better thing in 10 days and let the ecosystem evolve it." Productive design-philosophy tension on type safety, memory safety, and whether a language should constrain the programmer.
- **`dhh`** (architecture-testing-craft; Rails) — Both are outspoken contrarians who clash with industry orthodoxy, but they would conflict on the build-system / front-end-complexity axis (DHH's anti-build, no-transpile "HTML over the wire" vs. Eich's JS-and-WASM-everywhere bet) and on ad/business models.

## Pairs-well-with (against real ROSTER.md slugs)

- **`anders-hejlsberg`** (languages-runtimes; C#, TypeScript) — TypeScript is the type system layered *on top of* Eich's JavaScript; they share the pragmatic, ship-and-evolve view of language design and both sit close to TC39's gradual-typing debates.
- **`bruce-schneier`** (security; security economics, policy) — Both reason about privacy as economics and incentives, not just technology. Eich's surveillance-advertising critique rhymes with Schneier's "surveillance capitalism" arguments.
- **`matthew-green`** (security; applied crypto, E2E encryption) — Eich's verifiable-privacy / TEE work and Brave's prompt-injection disclosures sit squarely in Green's applied-crypto and disclosure territory.
- **`evan-you`** (web-and-frontend; Vue, Vite) — Web-platform allies; both care about the health of the JS ecosystem and tooling/runtime evolution.

---

## Notes on sourcing gaps

- Could not fetch the full Blockworks "metaphysical rebellion" article (HTTP 403). Used the headline + search summary, which corroborate the framing. Cited as a supporting source, not the sole basis for any stance.
- The New Stack "10 days / what he'd do differently" article rendered only as a subscription shell via WebFetch; the title and existence are confirmed via search, and the substance ("blessing and curse," 10-day deadline) is independently corroborated by the InfoWorld interviews.
- X/Twitter (@BrendanEich) is an active, heavy-posting account; the Brave Origin clarification (Jan 2026) and NEARCON appearances confirm active 2026 posting. Direct tweet-permalink dating was done via the PiunikaWeb writeup rather than scraping X.

---

## Final source list (>=8 real URLs; >=3 within last 12 months)

1. https://en.wikipedia.org/wiki/Brendan_Eich
2. https://en.wikipedia.org/wiki/Brave_(web_browser)
3. https://brave.com/author/brendan-eich/  (Nov 20 2025 + 2016 posts)
4. https://www.theregister.com/software/2025/11/22/brave-ai-assistant-leo-adds-trusted-execution-environments/2176243  (Nov 22 2025)
5. https://brave.com/blog/unseeable-prompt-injections/  (Oct 21 2025)
6. https://brave.com/blog/comet-prompt-injection/  (Aug 25 2025)
7. https://piunikaweb.com/2026/01/02/brave-origin-misinformation-brendan-eich-clarifies/  (Jan 2 2026)
8. https://www.youtube.com/watch?v=QJBSw9IOuLE  (Feb 26 2026 NEARCON talk)
9. https://www.infoworld.com/article/2256143/interview-brendan-eich-on-javascripts-blessing-and-curse.html
10. https://www.infoworld.com/article/2254271/brendan-eich-tech-giants-could-botch-webassembly-2.html
11. https://brendaneich.com/
12. https://blockworks.com/news/metaphysical-rebellion-big-tech-brave-ceo
