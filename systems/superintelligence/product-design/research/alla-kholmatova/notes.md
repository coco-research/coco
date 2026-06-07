# Research Notes — Alla Kholmatova

**Slug:** `alla-kholmatova`
**Cell:** design-systems-interaction · **Cell role:** specialist
**Home team:** product-design-super-intelligence
**Researched:** 2026-06-01
**Researcher:** Claude (Opus 4.8, 1M context) — Product & Design Super Intelligence Team build
**Status decision:** `archetype` (see "Status determination" below — this overrides the task brief's implied `active`)

---

## Summary verdict

Alla Kholmatova is the author of *Design Systems: A Practical Guide to Creating Design Languages for Digital Products* (Smashing Magazine, 2017), the canonical text that introduced the **functional patterns vs. perceptual patterns** distinction and reframed design systems as a problem of **shared language and culture** rather than tooling. Her influence on the field is durable and still actively cited in 2025. However, her own public output has effectively gone quiet: her most recent self-published writing dates to **2019** (Tilio Blog), and no verifiable talk, article, podcast, or interview dated **after 2025-06-01** could be found. Because the persona schema requires at least three recent signals dated within the last 12 months for `status: active`, and that bar cannot be met honestly, this profile is written as **`status: archetype`** with a `persistent_signals` block, exactly as the template prescribes for personas who are "no longer publishing" publicly.

---

## Status determination (why archetype, not active)

The task brief implied an active persona and asked to "verify current role." Verification produced the following:

1. **No recent signal (post-2025-06-01) exists.** Exhaustive search across web, conference archives, Medium, A List Apart, X/Twitter (`@craftui`), Smashing Magazine author page, and Goodreads turned up zero first-party output dated in the trailing 12 months. The only 2025-dated material is *third parties re-reviewing her 2017 book* (e.g., a 2025 reader noting the examples "feel a little dated" eight years on), which does not count as her own recent signal.
2. **Her last self-reported affiliation is her own bio**, "Designer, working on tilio.app" (Medium `@craftui`, profile bio; the Tilio Blog posts date to September 2019).
3. Per `superintelligence/templates/persona.md` lines 79–99: when recency "cannot apply (deceased, long-retired, or no longer publicly active)," set `recent_signal_12mo: []` and use `persistent_signals` (>=5 entries) instead. That is the correct, honest classification here. She is alive, but not publicly active in a way that produces datable recent signals.

**Confidence in identity:** very high (single, unambiguous public figure; consistent handle `@craftui` across X, Dribbble, Medium, A List Apart). **Confidence in current employer:** low (see below).

---

## Corrected assumption — the "Meta" claim is UNVERIFIED

The task brief stated: *"design at Snook/FutureLearn/Meta — verify current role."* Verification result:

- **Meta: NOT VERIFIED.** No source connects Alla Kholmatova to Meta or Facebook. Multiple targeted searches ("Alla Kholmatova Meta design systems designer," "Alla Kholmatova Meta product designer Facebook") returned only her 2017 book and FutureLearn-era bio. **Do not assert Meta as her employer.** It is logged here as an unconfirmed claim from the brief, not a finding.
- **Snook: NOT VERIFIED.** No source connects her to Snook (the London/Glasgow service-design studio, now NEC Digital Studio). The "Snook" search hits were the studio's own hiring pages, unrelated to her. **Do not assert Snook.**
- **FutureLearn: VERIFIED.** Multiple first-party and Smashing sources confirm she was a **senior product designer (also described as interaction designer / lead designer) at FutureLearn**, the open online education platform. This is where the 18 months of *Design Systems* research originated.

**Additional verified affiliations the brief omitted:**
- **Cezanne HR** — listed on her SlideShare profile as "Interaction designer at Cezanne hr" (early-career role).
- **Bulb** (UK energy company, now defunct) — she led/shaped Bulb's design system; authored "Introducing Bulb's design system" (Aug 7, 2018) and "The principles behind Bulb's design" (Sep 4, 2018) on the *Making Bulb* Medium publication.
- **tilio.app** — her own project; bio reads "Designer, working on tilio.app"; "Four writing strategies" published in the Tilio Blog (Sep 2, 2019). This is her most recent self-reported affiliation. (Note: a generic web search for "tilio.app" today surfaces unrelated apps named Tilio/Telio/Tylio — the original tilio.app appears dormant. Do not over-index on it as a live employer; flag as "last known.")

**Net affiliations_2026 stance:** since no current employer is verifiable, `affiliations_2026` is recorded as `[]` (consistent with the archetype convention used for personas no longer publicly active), and the known employment history is captured in `past_affiliations`.

---

## The book — core framework (verified, primary topic)

*Design Systems: A Practical Guide to Creating Design Languages for Digital Products* — Smashing Magazine, 2017. ISBN 9783945749586. Based on **18 months of research** including case-study interviews with **Airbnb, Atlassian, Eurostar, TED, and Sipgate**.

Core conceptual contribution:

- **Functional patterns** — concrete, tangible modules of the interface: a button, a header, a form field, a menu. They embody discrete actions/functions. (Smashing: "represented as concrete modules of the interface, such as a button, a header, a form element, a menu.")
- **Perceptual patterns** — the diffuse stylistic and sensory cues that together shape how a product is *perceived* and felt: tone of voice, typography, color choices, iconography style, spacing and layout, shapes, interactions, animations, even sound. (Smashing: "The ethos of a product forms patterns which together shape how a product is perceived… perceptual patterns.")
- **Shared language** — the central thesis: a design system is fundamentally a *shared language* among a team. Patterns only cohere when the team has a common vocabulary for them. Quote (Smashing launch page): the book "isn't about tooling; it's about how to set up a *shared* language that would help teams produce visual output that consistently renders designer's intent."
- **Design principles** — the agreed guidelines that govern how patterns are created, captured, and shared; the system's "constitution."
- **Pattern libraries** — the documented repository that keeps patterns honest and lets them evolve; the artifact, but downstream of the language and principles.

Book structure (two parts):
- Part 1: Design Systems · Design Principles · Functional Patterns · Perceptual Patterns · Shared Language
- Part 2: Parameters of Your System · Planning and Practicalities · Systemizing Functional Patterns · Systemizing Perceptual Patterns · Pattern Libraries

**Why it endures:** the functional/perceptual split gave the field language for the thing teams kept fumbling — that a "design system" is not just a component library (functional) but also the harder-to-pin-down house style and feel (perceptual), and that both need to be *named and shared* to be governed. It pairs naturally with Brad Frost's Atomic Design (structural decomposition) and Nathan Curtis's tokens/governance work (operational scaling).

---

## Earlier canonical writing (A List Apart — verified, with dates)

- **"Integrating Animation into a Design System"** — A List Apart, **Aug 17, 2017**. Animation as an expression of product personality, systematized.
  URL: https://alistapart.com/article/integrating-animation-into-a-design-system/ (author page: https://alistapart.com/author/craftui/)
- **"The Language of Modular Design"** — A List Apart, **Aug 11, 2015**. The seed of the book's thesis: break design into atomic units, but make a *shared vocabulary* the jumping-off point. ("a shared vocabulary should be the jumping-off point for teams" adopting modular design.)
  URL: https://alistapart.com/article/language-of-modular-design/
- **"Collaborative User Testing: Less Bias, Better Research"** — A List Apart, **Oct 7, 2014**. Reducing bias by making research planning/analysis collaborative.
  URL: https://alistapart.com/article/collaborative-user-testing-less-bias-better-research/

A List Apart bio (verified): "interaction designer at FutureLearn… fascinated by interfaces… reducing the gap between [designers and users]."

---

## Bulb / Tilio writing (Medium @craftui — verified, with dates)

- "Introducing Bulb's design system" — *Making Bulb*, **Aug 7, 2018**.
- "The principles behind Bulb's design" — *Making Bulb*, **Sep 4, 2018**.
- "Four writing strategies" — *Tilio Blog*, **Sep 2, 2019**. (Most recent self-published piece located.)
- Medium profile: https://medium.com/@craftui — bio "Designer, working on tilio.app," 1.4K followers.

---

## Speaking history (verified — all pre-2020, supports archetype framing)

- Smashing Conference Freiburg 2017 — speaker. https://archive.smashingconf.com/freiburg-2017/speakers/alla-kholmatova
- beyond tellerrand Berlin 2017 — speaker. https://beyondtellerrand.com/events/berlin-2017/speakers/alla-kholmatova
- From the Front 2016 — speaker. https://2016.fromthefront.it/speaker/2016/04/16/alla-kholmatova.html

No conference appearances dated after ~2019 were located. This reinforces the `archetype` (no-longer-publicly-active) classification.

---

## Voice & stance evidence (for narrative + public_stances)

- **"Not about tooling — about shared language."** Direct from the Smashing launch page (primary). This is the load-bearing stance: design systems are sociolinguistic/cultural artifacts first, technical artifacts second. Evidence: https://www.smashingmagazine.com/design-systems-book/
- **Functional vs. perceptual patterns** as the organizing taxonomy. Evidence: https://www.smashingmagazine.com/design-systems-book/ and the book itself.
- **Design principles before components.** Part 1 sequences Principles → Functional → Perceptual → Shared Language, i.e., principles govern patterns. Evidence: book structure on the same launch page.
- **Modular design needs a shared vocabulary first.** "The Language of Modular Design" (2015). Evidence: https://alistapart.com/article/language-of-modular-design/
- **Animation/motion is a pattern, not decoration** — belongs *in* the system. "Integrating Animation into a Design System" (2017). Evidence: https://alistapart.com/article/integrating-animation-into-a-design-system/
- **Research/testing should be collaborative to reduce bias.** "Collaborative User Testing" (2014). Evidence: https://alistapart.com/article/collaborative-user-testing-less-bias-better-research/

Voice style (inferred from her writing): calm, observational, language-obsessed, allergic to tool-worship and premature systematization. She reasons from how teams actually talk and behave, not from the component inventory. Favors the words "language," "vocabulary," "ethos," "perception," "shared." Anthropological more than engineering.

---

## Pairs / conflicts (against ROSTER.md slugs — verified slugs)

Same cell (`design-systems-interaction`): `brad-frost`, `nathan-curtis`, `josh-clark`, `dan-mall`, `adam-wathan` (cross-listed).

- **Pairs well with:** `brad-frost` (Atomic Design — structural taxonomy complements her functional/perceptual taxonomy), `nathan-curtis` (tokens + governance operationalize her "shared language" at scale), `dan-mall` (design-system pragmatics, "Design That Scales").
- **Productive conflict with:** `adam-wathan` (Tailwind utility-first treats the design system as utility classes in markup — a tooling/implementation-first stance that directly tensions her "not about tooling, it's about shared language" thesis); `brad-frost` is also a *mild* productive tension (his atoms→molecules→organisms is a structural hierarchy; she would argue the perceptual layer resists that clean nesting) — but the primary, sharper conflict is with the tooling-first camp, so `adam-wathan` is the cleaner conflict pick. Second conflict slug: `dieter-rams` (his "less but better" reductionist absolutism vs. her view that perceptual richness/ethos is itself systematizable and worth preserving, not stripping).

All slugs above confirmed present in `superintelligence/product-design/ROSTER.md`.

---

## All URLs gathered (for sources block)

1. https://www.smashingmagazine.com/design-systems-book/ — book launch page; functional/perceptual/shared-language framing, case studies, author bio. (PRIMARY)
2. https://www.smashingmagazine.com/printed-books/design-systems/ — printed book page.
3. https://www.smashingmagazine.com/author/alla-kholmatova/ — Smashing author page + bio.
4. https://alistapart.com/author/craftui/ — A List Apart author page + article list + bio.
5. https://alistapart.com/article/language-of-modular-design/ — "The Language of Modular Design" (2015).
6. https://alistapart.com/article/integrating-animation-into-a-design-system/ — animation in design systems (2017).
7. https://medium.com/@craftui — Medium profile; "working on tilio.app"; Bulb + Tilio posts.
8. https://www.goodreads.com/book/show/35857970-design-systems — book record (Goodreads).
9. https://archive.smashingconf.com/freiburg-2017/speakers/alla-kholmatova — Smashing Conf 2017 speaker.
10. https://beyondtellerrand.com/events/berlin-2017/speakers/alla-kholmatova — beyond tellerrand 2017 speaker.
11. https://designsystemsbook.com/ — the book's own site (companion site; intermittently reachable).
12. https://x.com/craftui — her X/Twitter handle (bio/handle confirmation; full content gated).
13. https://www.slideshare.net/AllaKholmatova — SlideShare; "Interaction designer at Cezanne hr."
14. https://2016.fromthefront.it/speaker/2016/04/16/alla-kholmatova.html — From the Front 2016 speaker.

---

## Open questions / caveats for future re-sync

- **Is she at Meta?** Unconfirmed as of 2026-06-01. If a future LinkedIn fetch (blocked today, HTTP 999) or a verifiable source confirms a Meta role, flip `status` to `active`, populate `affiliations_2026`, and move the relevant `persistent_signals` into `recent_signal_12mo`.
- LinkedIn (`uk.linkedin.com/in/allakholmatova`) returned HTTP 999 (anti-scrape) and X returned HTTP 402; neither could be read first-party. Re-attempt with an authenticated browser tool next sync to settle the current-employer question.
- A second edition of the book was searched for and NOT found; the 2017 edition remains canonical.
