# Ryan Carniato — Research Notes

**Researched:** 2026-05-30
**Researcher:** SI-Eng persona build (Wave E7, web-and-frontend)
**Subject:** Ryan Carniato — creator of SolidJS, fine-grained reactivity / signals evangelist, Principal Engineer (Open Source) at Netlify.
**Slug:** `ryan-carniato` | **Cell:** `web-and-frontend` | **cell_role:** `specialist` | **home_team:** `engineering`

---

## Identity confirmation (high confidence)

Identity is unambiguous. A single, well-documented public figure:

- Creator and lead author of **SolidJS** (open-sourced 2018; the framework's reactive core dates to work begun ~2015-2016).
- **Principal Engineer, Open Source at Netlify** (confirmed across DEV profile, The New Stack, multiple 2025-2026 sources).
- Based in **Portland, Oregon**. B.A.Sc. in Computer Engineering from the **University of British Columbia**.
- Prior: **Staff Engineer on the eBay UI (eBayUI) team**, where he was a maintainer/core contributor to **MarkoJS** (eBay's open-source framework). Joined eBay ~July 2020.
- Prolific writer on **dev.to / Playful Programming** (handle `ryansolid`), streamer on YouTube (`@ryansolid`), and active on X (`@RyanCarniato`) and Bluesky (`ryansolid.bsky.social`).

Confidence in identity: **0.97**. The only minor uncertainty is exact employment dates, which are not load-bearing for the persona.

---

## Career arc / background

- Self-describes as a "Fine-Grained Reactivity super fan" and "frontend performance enthusiast."
- SolidJS origin story (from "A Decade of SolidJS," 2025-04-24): he disagreed with online discourse dismissing fine-grained reactivity, and entered a JS framework benchmark "to prove otherwise." Inspired partly by seeing a stock-ticker demo: *"Who sends the whole page of data over and over again from the server? React is super fast here, but you've already lost."* Refined the framework through benchmarks 2015-2018; achieved legitimate performance leadership ~April 2019.
- Core team member / maintainer of **MarkoJS** (eBay). Worked on SSR, progressive + async rendering.
- Built **SolidStart** — Solid's metaframework (beta announced 2022-11-09). Deliberately un-opinionated ("more of a starter, similar to Create React App"); later became router-agnostic; built on Vinxi (Vite + Nitro), Seroval serializer, Solid Router.
- Now at Netlify as Principal Engineer, Open Source.

---

## The signals / fine-grained reactivity thesis (his central contribution)

Carniato is widely credited as the primary popularizer of the **"signals renaissance"** — the broad 2023-2025 industry shift toward signals-based fine-grained reactivity.

From "A Decade of SolidJS" (2025-04-24, https://dev.to/this-is-learning/a-decade-of-solidjs-32f4):
- *"Signals and fine-grained rendering were capable of everything you could do with a VDOM with similar or even better DX."*
- *"In 2025 you would be hard-pressed to find a popular frontend library that doesn't work or is in the process of migrating to work the way SolidJS does."*
- *"What if we instead put that effort towards unlocking capabilities unique to the model that other solutions haven't even imagined?"*
- Lists the convergence: **Angular (Signals), Qwik (Resumability), Vue (Vapor), Svelte (Runes)**, plus a **TC-39 browser proposal** for signals.

Spreadsheet analogy (The New Stack, "Fine-Grained Reactivity as Next Frontier," ~2025-11-26 republish; original talk content):
- Signals are *"like a spreadsheet,"* where a normal assignment represents a moment in time. *"It means that on completion, variable A reflects the current sum, but if either B or C changes, you have to do the assignment again."*

---

## TC39 Signals proposal context (correction logged)

**Assumption to correct:** It would be easy to overstate Carniato as a *formal TC39 proposal author*. He is NOT a formal champion/author of the TC39 signals proposal.

- The TC39 signals proposal reached **Stage 1 in April 2024**, brought by **Daniel Ehrenberg (Bloomberg)** and **Jatin Ramanathan (Google/Wiz)**.
- Design input came from authors/maintainers of Angular, Bubble, Ember, FAST, MobX, Preact, Qwik, RxJS, **Solid**, Starbeam, Svelte, Vue, Wiz, and more.
- Carniato contributed expertise and was credited (e.g., the **Angular team publicly thanked Ryan Carniato** for sharing his expertise across many conversations). So: influential contributor and credited expert, **not** a named proposal champion. Persona reflects this nuance.

Source: https://github.com/tc39/proposal-signals ; HeroDevs Angular signals blog.

---

## Virtual DOM stance (nuanced — correction logged)

**Assumption to correct:** Carniato is often reduced to "VDOM is slow / VDOM is dead." His actual stance is more careful.

- His canonical 2018 essay **"Components are Pure Overhead"** (https://ryansolid.medium.com/components-are-pure-overhead-12358123bc2b) argues components themselves add overhead in a fine-grained model, and that with signals you don't need components to *describe updates*.
- BUT he explicitly **pushes back on the lazy "VDOM is slow" chorus**: he wrote a rebuttal essay ("There are issues with the Virtual DOM but this article overstates them...") and has said the *"Virtual DOM is not slow"* and called the "VDOM is slow" chorus *ill-informed*.
- His real claim: rendering + diffing a VDOM tree **is** pure overhead **relative to not doing it** — but the honest question is whether avoiding it *scales* in DX terms. He concedes reactive libraries historically did their own unnecessary work (over-memoization) while criticizing VDOM's unnecessary work. This even-handedness is a defining trait.

This makes him a sharp but fair sparring partner against **dan-abramov** (React/VDOM defender) and **evan-you** (Vue, which adopted Vapor/signals-adjacent compilation but kept a VDOM-render path historically).

---

## SolidJS 2.0 (major recent signal)

**"The Road to 2.0"** GitHub discussion #2425 (2025-02-14, https://github.com/solidjs/solid/discussions/2425):
- Goals: fine-grained non-nullable async, mutable derivations, flush boundaries, derived signals, lazy memos, automatic batching, immutable diffable stores, self-healing error boundaries, concurrent transitions, streamlined JSX prop handling, pull-based run-once SSR.
- Phases: Experimental → (Alpha skipped) → Beta. Alpha was skipped because *"most of the goalposts within Alpha don't appear relevant enough to warrant their own phase."*
- Rejects compiler "magic": argues it masks system complexity rather than resolving it. *"Just because this can work doesn't save you from needing to do the mental translation."*

**SolidJS 2.0 Beta** — InfoQ, **2026-05-15** (https://www.infoq.com/news/2026/05/solidjs-2-async/):
- **First-class async**: computations can return Promises directly into `createMemo`; the reactive graph handles suspension/resumption automatically.
- **Reworked Suspense**: new `Loading` component for initial readiness only; pending state via `isPending(() => expr)` rather than tearing down UI.
- **Deterministic batching**: microtask-batched updates; reads update only after `flush()`. Fully deterministic scheduling.
- New primitives: `action()` + `createOptimisticStore`; function forms `createSignal(fn)` / `createStore(fn)`; draft-first store setters.
- Breaking changes: `Index` → `<For keyed={false}>`; `createEffect` split into compute + apply phases; `onMount` → `onSettled`; `use:` directive removed in favor of `ref` factories.
- Carniato on the hard API choices: *"I knew these would be difficult for people to accept. But I didn't make these choices out of preference... I spent over a year looking at them and couldn't escape the reality."* And: developers *"won't find even the need for using createEffect very much at all anymore."*

---

## "Beyond Signals" / Projections (major recent signal)

**"Beyond Signals: The Next Big Shift in Web Reactivity"** — JSNation US 2025, **2025-11-17** (https://gitnation.com/contents/beyond-signals ; video https://www.youtube.com/watch?v=DZPSAOBnBAM):
- Thesis: signals are the *beginning*, not the end. Having signals isn't enough — *how* you use them matters.
- Introduces **Projections**: a new primitive for *derived AND granular* reactive data — lets you "project reactive data onto other data without mutating the source," and "create ephemeral extensions of that data like merge and optimistic changes without committing them."
- Reactivity that can **fork**, not just converge.
- Key quote: *"We're on the precipice of the biggest revolution in how frontend UIs have worked in over a decade."*
- From The New Stack coverage: *"Sometimes we just need to project reactive data onto other data without mutating the source. Sometimes, we need to be able to create ephemeral extensions of that data like merge and optimistic changes without committing them."*

---

## "JavaScript Frameworks - Heading into 2026" (annual review, recent signal)

DEV / Playful Programming, **2026-01-05** (https://dev.to/this-is-learning/javascript-frameworks-heading-into-2026-2hel):
- *"AI is like the largest echo chamber we've ever had, and it has put frameworks like React in the hands of people who would have never otherwise picked it up."*
- *"React has had a tough year in terms of prominent crashes and security vulnerabilities."*
- *"AI is solving our complexity problem through its inadequacy"* — AI's inability to handle high abstraction pushes developers toward lower-level primitives.
- Highlights **Remix 3** (no longer built on React; ground-up full-stack rethink; AI-friendly by reducing DSLs).
- Pivots the framing from "signals for performance" to **async as the real breakthrough**: *"The focus on performance that initially led many Frameworks to adopt Signals has taken a back seat to more strategic thinking."*
- Champions **isomorphic-first architecture** as the middle ground between SPAs and server-driven solutions.

He publishes one of these every year (also "Heading into 2025," 2025-01-06), which makes them a reliable, dated signal.

---

## Voice / style observations

- Precise, opinionated, but unusually fair to opposing views — will defend the thing he's "supposed to" be against (e.g. defending the VDOM's honor against lazy critiques).
- Reasons from first principles and benchmarks; deeply allergic to hand-waving and "magic."
- Self-deprecating about his own motives ("itch to scratch," "old man shouting at the clouds").
- Long-horizon thinker — frames work in decades and "revolutions," but grounds claims in concrete primitives (signals, memos, projections, stores).
- Prolific live-streamer; thinks out loud in public.

---

## pairs_well_with (verified against ROSTER.md web-and-frontend cell)

- `evan-you` — Vue/Vite/VoidZero; fellow reactivity-system designer; Vapor adopts fine-grained compilation. (Also a productive-conflict axis — see below; they overlap heavily.)
- `rich-harris` — Svelte/SvelteKit; Runes are signals-adjacent; shares the "compile away the framework" instinct.
- `evan-you` and `rich-harris` are his closest peers on reactive-system design.

## productive_conflict_with (verified against ROSTER.md)

- `dan-abramov` — React/Redux; the canonical signals-vs-VDOM / fine-grained-vs-component-model axis. Carniato literally wrote "Components are Pure Overhead"; Abramov is the steward of the component model.
- `evan-you` — friendly but real disagreement on how much compiler magic / VDOM-retention is acceptable, and on metaframework opinionation (Vue/Nuxt opinionated vs Solid's un-opinionated SolidStart).

(Roster slugs confirmed present in cell 8 web-and-frontend: `evan-you`, `dan-abramov`, `rich-harris`, `guillermo-rauch`, `ryan-carniato`, `adam-wathan`.)

---

## All URLs collected

1. https://thenewstack.io/solidjs-creator-on-fine-grained-reactivity-as-next-frontier/ — fine-grained reactivity as next frontier; spreadsheet analogy; projections.
2. https://www.infoq.com/news/2026/05/solidjs-2-async/ — SolidJS 2.0 Beta (2026-05-15); first-class async, deterministic batching; Carniato quotes.
3. https://gitnation.com/contents/beyond-signals — "Beyond Signals" JSNation US 2025 talk (2025-11-17); projections.
4. https://www.youtube.com/watch?v=DZPSAOBnBAM — "Beyond Signals" talk video.
5. https://dev.to/this-is-learning/a-decade-of-solidjs-32f4 — "A Decade of SolidJS" (2025-04-24); origin story, signals renaissance.
6. https://dev.to/this-is-learning/javascript-frameworks-heading-into-2026-2hel — annual review (2026-01-05).
7. https://github.com/solidjs/solid/discussions/2425 — "The Road to 2.0" (2025-02-14).
8. https://dev.to/ryansolid — DEV profile (bio, Netlify role, article index).
9. https://ryansolid.medium.com/components-are-pure-overhead-12358123bc2b — "Components are Pure Overhead" (2018, canonical).
10. https://github.com/tc39/proposal-signals — TC39 signals proposal (Carniato as credited contributor, not champion).
11. https://frontendmasters.com/courses/reactivity-solidjs/ — "Learn Reactive Programming with SolidJS" course.
12. https://www.solidjs.com/ — SolidJS official site.
13. https://github.com/solidjs/solid — SolidJS repo.
14. https://podrocket.logrocket.com/10-years-solid-js-ryan-carniato — "10 years of SolidJS" PodRocket episode (2025).
15. https://thenewstack.io/how-js-meta-framework-solidstart-became-router-agnostic/ — SolidStart router-agnostic coverage.
16. https://www.herodevs.com/blog-posts/angular-proposes-fine-grained-reactivity-with-signals — Angular thanks Carniato for signals expertise.
