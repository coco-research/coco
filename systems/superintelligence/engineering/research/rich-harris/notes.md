# Rich Harris — Research Notes

**Slug:** `rich-harris`
**Cell:** web-and-frontend (lead-driver)
**Researched:** 2026-05-30
**Researcher:** SI-Eng build agent (Wave E7)

These are the dated raw findings, quotes, and source URLs behind
`superintelligence/engineering/personas/rich-harris.md`. Future re-syntheses should
read this file first rather than re-crawling.

---

## Identity confirmation (HIGH confidence)

Rich Harris is a British web developer and award-winning interactive/data journalist,
creator of **Svelte**, **SvelteKit**, **Rollup**, and the earlier **Ractive.js**.
Employed by **Vercel** to work on Svelte full-time. The slug `rich-harris` is the
correct kebab-case of his real name. No identity ambiguity — single, well-documented
public figure with consistent self-presentation across GitHub (`@Rich-Harris`),
conference talks, and the Svelte blog.

- Wikipedia (Svelte) confirms career arc and project timeline.
  https://en.wikipedia.org/wiki/Svelte
- GitHub: https://github.com/Rich-Harris

---

## Career / affiliation timeline (with dates)

- **2013** — Created **Ractive.js** while at **The Guardian**, a tool for building
  interactive news stories. Svelte is the conceptual descendant of Ractive.
  Source: Wikipedia (Svelte), EverybodyWiki.
- **The Guardian** — front-end developer building interactive articles.
- **The New York Times** — graphics editor / "JavaScript Journalist," same
  interactive-storytelling role under tight newsroom deadlines. This newsroom
  constraint (ship fast, small payloads, works on bad connections) is the origin
  of Svelte's design philosophy.
  Source: Changelog Interviews #332 "A UI framework without the framework, featuring
  Rich Harris, JavaScript Journalist for The New York Times."
  https://changelog.com/podcast/332
- **November 11, 2021** — Joined **Vercel** to work on Svelte full-time; "the
  project's first dedicated contributor." Governance of Svelte explicitly stays
  independent. Joined alongside Simon Holthausen.
  Source: https://vercel.com/blog/vercel-welcomes-rich-harris-creator-of-svelte
  (publication date confirmed Nov 11, 2021 via WebFetch)
- **2026** — Still at Vercel (engineering / Svelte). `affiliations_2026: ['Vercel
  (Svelte core, since 2021)']`.

CORRECTION LOGGED: An early WebFetch summary of Wikipedia implied Harris joined Vercel
"when he and coworkers chose the name Svelte" — that conflates two events. The name
"Svelte" was chosen at The Guardian (~2016); he joined Vercel in Nov 2021. Persona
reflects the correct, separated timeline.

CORRECTION LOGGED: One search summary claimed "the team is working on Svelte 4 …
switching from TypeScript to JavaScript" as if current/future. That is stale 2022-era
copy. Svelte 4 shipped 2023-06-22; the current era is Svelte 5 (runes) + Async Svelte.
Persona uses the current state.

---

## Project timeline (Svelte / SvelteKit / Rollup)

- **Rollup** — JavaScript module bundler created by Harris; pioneered tree-shaking /
  ES-module bundling. Influenced Webpack and later Vite.
- **Svelte 1** — 2016-11-26 (written in JavaScript)
- **Svelte 2** — 2018-04-19
- **Svelte 3** — 2019-04-21 ("Rethinking reactivity" — reactivity moved into the
  language via compiler-instrumented assignments; rewritten in TypeScript)
  https://svelte.dev/blog/svelte-3-rethinking-reactivity
- **Svelte 4** — 2023-06-22 (internal rewrite from TypeScript back to JavaScript +
  JSDoc)
- **Svelte 5** — 2024-10-19, cut live at Svelte Summit Fall 2024. Ground-up rewrite.
  Introduced **runes** (`$state`, `$derived`, `$effect` — function-like compiler
  macros that compile to signals) and **Snippets** (reusable markup blocks). Adds
  fine-grained universal reactivity usable outside `.svelte` components.
  Source: Wikipedia (Svelte); Vercel "What's new in Svelte 5"
  https://vercel.com/blog/whats-new-in-svelte-5
- **SvelteKit** — announced Oct 2020, beta Mar 2021, **1.0 released Dec 2022**.
  The application/meta-framework on top of Svelte.

---

## Canonical essays / talks (the thesis material)

- **"Frameworks without the framework: why didn't we think of this sooner?"** (2016)
  The founding essay — "what if the framework was actually just a compiler?"
  https://svelte.dev/blog/frameworks-without-the-framework
- **"Virtual DOM is pure overhead"** — 2018-12-27. Argues the vdom-is-fast claim is a
  myth: diffing is fast but the vdom + component overhead is "pure overhead" you could
  skip with a compiler. Most-cited Harris polemic.
  https://svelte.dev/blog/virtual-dom-is-pure-overhead
- **"Rethinking Reactivity"** — talk at You Gotta Love Frontend (YGLF), Tel Aviv,
  April 2019. The talk that launched Svelte 3's reactivity model. "Frameworks are not
  tools for organising your code, they are tools for organising your mind."
  Video: https://www.youtube.com/watch?v=AdNJ3fydeao
  Slides mirror: https://conn.dev/talks/rethinking-reactivity.html
- **Svelte 3 blog post "Rethinking reactivity"**
  https://svelte.dev/blog/svelte-3-rethinking-reactivity

Recurring slogans, all attributable:
- "The framework is a compiler." / "frameworks without the framework"
- "Virtual DOM is pure overhead."
- "Write less code." (Svelte 5 positioning)
- "Success is not adoption — it's people building higher-quality, more resilient,
  more accessible apps." (Smashing, Jan 2025)

---

## RECENT SIGNALS (must be dated AFTER 2025-05-30 for recent_signal_12mo)

1. **"promise.then(...)" talk** — Svelte Society NYC; video posted **2025-07-19**.
   Harris on async reactivity / what's next for Svelte after async lands.
   https://www.youtube.com/watch?v=e-1pVKUWlOQ
   (After cutoff ✓)

2. **What's new in Svelte: August 2025** — published **2025-08-01**. Async Svelte
   (`await` in components, `experimental.async`, svelte@5.36.0) and **Remote
   Functions** (kit@2.27.0) officially shipped experimentally. Harris is the driver
   of both; the post links his videos ("promise.then(...)", "Asynchronous Svelte"
   Learn With Jason session).
   https://svelte.dev/blog/whats-new-in-svelte-august-2025
   (After cutoff ✓)

3. **What's new in Svelte: October 2025** — published **2025-10-01**. Continued
   remote-functions iteration (form schema/input/issues kit@2.42.0; query.batch
   kit@2.38.0; lazy discovery kit@2.39.0, PR #14293 by Rich-Harris).
   https://svelte.dev/blog/whats-new-in-svelte-october-2025
   PR: https://github.com/sveltejs/kit/pull/14293
   (After cutoff ✓)

4. **PR #14293 "feat: lazy discovery of remote functions"** authored by Rich-Harris on
   sveltejs/kit — direct evidence he is still hands-on in the codebase in 2025.
   https://github.com/sveltejs/kit/pull/14293
   (After cutoff ✓)

BORDERLINE (NOT used as recent_signal — dated on/just before cutoff, kept as canonical):
- **"What Svelte Promises"** — Svelte Summit Spring 2025 (event May 8-9, 2025 in
  Barcelona); YouTube upload **2025-05-25** (just before the 2025-05-30 window). Used
  as a canonical_work, not as recent_signal_12mo, to be safe on the date.
  https://www.youtube.com/watch?v=1dATE70wlHc
  Society page: https://sveltesociety.dev/video/what-svelte-promises-rich-harris-svelte-summit-spring-2025-a5cfbf80a458d5e6
- **Smashing Magazine "Svelte 5 and the Future of Frameworks: A Chat With Rich
  Harris"** — 2025-01. Too old for recent window; used for stances/quotes.
  https://www.smashingmagazine.com/2025/01/svelte-5-future-frameworks-chat-rich-harris/

---

## Public stances (each needs an evidence_url in the persona)

1. **"Virtual DOM is pure overhead."** The vdom-is-fast claim is a myth worth retiring.
   https://svelte.dev/blog/virtual-dom-is-pure-overhead
2. **"The framework should be a compiler."** Move work to build time; ship minimal
   imperative DOM code; the framework "magically disappears."
   https://svelte.dev/blog/frameworks-without-the-framework
3. **"Reactivity belongs in the language, not in a runtime API."** Svelte 3 compiles
   plain assignments into reactive updates; Svelte 5 runes make the signal contract
   explicit (`$state`/`$derived`/`$effect`).
   https://svelte.dev/blog/svelte-3-rethinking-reactivity
4. **"Write less code — boilerplate is a bug, not a feature."** Svelte 5 positioning.
   https://www.smashingmagazine.com/2025/01/svelte-5-future-frameworks-chat-rich-harris/
5. **"Success is quality of the web, not framework adoption."** Most software is bad;
   the goal is more resilient/accessible apps, not market share.
   https://www.smashingmagazine.com/2025/01/svelte-5-future-frameworks-chat-rich-harris/
6. **"Async should be a first-class primitive in the component model."** Async Svelte:
   `await` directly in components/markup, server-only Remote Functions callable from
   the client.
   https://svelte.dev/blog/whats-new-in-svelte-august-2025

---

## Pairs / conflicts (validated against ROSTER.md web-and-frontend cell)

ROSTER web-and-frontend slugs: `evan-you`, `dan-abramov`, `rich-harris`,
`guillermo-rauch`, `ryan-carniato`, `adam-wathan`.

- **pairs_well_with:**
  - `guillermo-rauch` — Vercel CEO; Harris's employer; aligned on the build-time /
    edge-rendering / "framework-defined infrastructure" thesis.
  - `ryan-carniato` — SolidJS; fine-grained reactivity / signals. Svelte 5 runes
    converged on the signals model Carniato championed; deep technical overlap.
  - `adam-wathan` — Tailwind; both compiler/build-time + author-ergonomics oriented,
    both ship in the SvelteKit/Vercel ecosystem.
- **productive_conflict_with:**
  - `dan-abramov` — React; the canonical vdom-vs-compiler debate. Harris's "Virtual
    DOM is pure overhead" is effectively a rebuttal of the React runtime model
    Abramov has long defended. (Note: Abramov ex-Meta per ROSTER.)
  - `evan-you` — Vue/Vite/VoidZero; friendly rival framework author. Differ on
    runtime-reactivity-plus-vdom (Vue) vs compiler-erases-the-framework (Svelte),
    and on framework scope/tooling strategy.

---

## Blind spots (reasoned, anchored)

- Strong author-experience bias from newsroom roots — optimizes for the person writing
  the component; can underweight very-large-team governance, migration cost, and
  ecosystem-size network effects where React/Vue win on people, not tech.
- Compiler-first worldview assumes a build step; weaker fit for no-build / CDN-script /
  runtime-only contexts.
- Svelte 5's ground-up rewrite + runes migration was disruptive for existing users;
  Harris has acknowledged reception friction (Svelte Radio "Svelte 5 reception").
  Tendency to pursue the technically-correct redesign over backward-compat comfort.
  https://www.svelteradio.com/episodes/rich-harris-on-the-svelte-5-reception/transcript

---

## Source URL inventory (>=8, >=3 recent)

1. https://en.wikipedia.org/wiki/Svelte
2. https://github.com/Rich-Harris
3. https://vercel.com/blog/vercel-welcomes-rich-harris-creator-of-svelte
4. https://svelte.dev/blog/virtual-dom-is-pure-overhead
5. https://svelte.dev/blog/frameworks-without-the-framework
6. https://svelte.dev/blog/svelte-3-rethinking-reactivity
7. https://www.youtube.com/watch?v=AdNJ3fydeao  (Rethinking Reactivity, YGLF 2019)
8. https://www.smashingmagazine.com/2025/01/svelte-5-future-frameworks-chat-rich-harris/
9. https://svelte.dev/blog/whats-new-in-svelte-august-2025  (RECENT, 2025-08-01)
10. https://svelte.dev/blog/whats-new-in-svelte-october-2025  (RECENT, 2025-10-01)
11. https://www.youtube.com/watch?v=e-1pVKUWlOQ  (RECENT, "promise.then(...)" 2025-07-19)
12. https://github.com/sveltejs/kit/pull/14293  (RECENT, Harris-authored PR 2025)
13. https://www.youtube.com/watch?v=1dATE70wlHc  (What Svelte Promises, Summit Spring 2025)
14. https://changelog.com/podcast/332  (NYT JavaScript Journalist framing)
15. https://vercel.com/blog/whats-new-in-svelte-5
16. https://www.svelteradio.com/episodes/rich-harris-on-the-svelte-5-reception/transcript
