# Kent Beck — Research Notes

**Slug:** `kent-beck`
**Subject:** Kent Beck — creator of Extreme Programming (XP) and Test-Driven Development (TDD); Agile Manifesto co-signer; "Tidy First?", "test && commit || revert," JUnit co-creator; now writing on "Augmented Coding" / TDD-with-LLMs.
**Cell:** `architecture-testing-craft` · **cell_role:** `lead-driver` · **home_team:** `engineering`
**Researched:** 2026-05-30 (last_verified) · **Researcher:** engineering-super-intelligence build agent
**Status:** active — high confidence on identity (single, unambiguous, globally famous software engineer).

---

## 1. Identity confirmation

Kent Beck is unambiguous. Born 1961, American software engineer. The defining one-line self-description on his own site (kentbeck.com): **"Creator of Extreme Programming and Test-Driven Development."** No disambiguation needed — there is exactly one Kent Beck in software engineering. Confidence on identity: ~1.0. Confidence on profile depth: 0.97 (rich primary-source material, current activity verified through May 2026).

---

## 2. Biography (verified facts, with corrections to brief)

Source: Wikipedia (https://en.wikipedia.org/wiki/Kent_Beck), kentbeck.com, GOTO/SE-Radio bios.

- **Born 1961.** B.S. and M.S. in computer and information science, **University of Oregon** (period ~1979–1987).
  - **CORRECTION to a common assumption:** Beck's degrees are from the University of Oregon, NOT Stanford or MIT. Verified on Wikipedia.
- **Early 1990s:** Smalltalk programmer. Developed **SUnit** (the Smalltalk testing framework that is the ancestor of the whole xUnit family).
- **1996:** Hired onto the **Chrysler Comprehensive Compensation System (C3)** project — the famous birthplace project of Extreme Programming.
- **1997 onward:** The C3 team's practices were formalized as **Extreme Programming (XP)**.
- **1999:** Published *Extreme Programming Explained: Embrace Change* (2nd ed. 2004).
- **2001:** One of the **seventeen original signatories of the Agile Manifesto**.
- **2002:** Published *Test-Driven Development: By Example* (Addison-Wesley) — the canonical TDD book.
- **JUnit:** Co-created with **Erich Gamma** (of Gang-of-Four / Design Patterns fame). JUnit seeded the xUnit pattern across nearly every language.
- **CRC cards:** Popularized with **Ward Cunningham** (inventor of the wiki).
- **~2011–2018:** Worked at **Facebook (Meta)**.
- **2019:** Joined **Gusto** as a software fellow / coach.
- **2023:** Published *Tidy First? A Personal Exercise in Empirical Design* (O'Reilly) — his first book in ~15 years. First book of the planned **Empirical Software Design** series. *Tidy Together* is the in-progress third book.
- **Current (2025–2026):** **Chief Scientist at Mechanical Orchard** (legacy-system modernization company). Also: independent author/consultant/speaker, visual artist (cityscapes/abstracts on glass), musician, and podcaster.
  - **NOTE on the brief:** The brief described his current activity as "now writing on 'Augmented Coding' / TDD-with-LLMs on Substack." Confirmed accurate. His Substack is **"Software Design: Tidy First?"** at tidyfirst.substack.com — **123K+ subscribers across 195 countries** (per kentbeck.com), weekly cadence. This is currently his primary public output, alongside the *Still Burning* podcast.

---

## 3. Signature contributions / canonical works

- **Extreme Programming (XP)** — values: communication, simplicity, feedback, courage, respect. Practices: pair programming, continuous integration, small releases, TDD, refactoring.
- **Test-Driven Development (TDD)** — Red → Green → Refactor. Beck's rule (quoted on Wikipedia): *"Never write a single line of code unless you have a failing automated test. Eliminate duplication."*
- **JUnit** (with Erich Gamma) — xUnit ancestor.
- **CRC cards** (with Ward Cunningham).
- **Agile Manifesto** co-signer (2001).
- **Tidy First?** (2023) — software design as an **economic decision**; "tidyings" = small structural improvements separated from behavioral changes; design's value framed as **optionality** for future work.
- **test && commit || revert (TCR)** — Medium post **September 28, 2018** (https://medium.com/@kentbeck_7670/test-commit-revert-870bbd756864). Beck introduced "test && commit"; **Oddmund Strømme** suggested adding the revert. (Also credited in the broader Oslo Code Camp group: Lars Barlindhaug, Oddmund Strømme, Ole Johannessen, Kent Beck.) Quote: *"If the tests fail, then the code goes back to the state where the tests last passed."* Part of his "Limbo on the Cheap" experiment.

---

## 4. Augmented Coding / TDD-with-LLMs (the recent body of work)

This is the core "recent signal" theme. All from the Tidy First? Substack.

### "Augmented Coding & Design" — **May 3, 2025**
URL: https://tidyfirst.substack.com/p/augmented-coding-and-design
- AI coding assistants lack the disciplinary restraint humans maintain. Human dev alternates between adding features and refactoring ("breathing"); AI "genies" tend to **continuously add complexity** without the self-imposed constraint to improve design.
- Vicious cycle: "More features introduces more complexity" → "More complexity slows development of more features." Eventually accumulated debt becomes so severe the AI cannot implement basic new features.
- Two dimensions: **Features** (new functionality, needs tests) vs **Options** (structural refinement reducing coupling, increasing cohesion). Ideal rhythm alternates.
- Emerging solution: **restrict the context** given to the AI — give only what's needed for the immediate step.
- Quote: *"Better to go hungry in the spring, plant the corn, & eat later"* (farming adage for investing in design rather than consuming debt).
- **NOTE:** This post predates the 2025-05-30 cutoff by ~4 weeks, so it is logged as a **canonical work**, NOT a recent_signal_12mo entry.

### "Augmented Coding: Beyond the Vibes" — **June 25, 2025**  ✅ recent signal
URL: https://tidyfirst.substack.com/p/augmented-coding-beyond-the-vibes
- Defines **augmented coding** vs **vibe coding**:
  - **Vibe coding:** ignore code quality, focus only on system behavior; feed errors back to the AI hoping for acceptable fixes.
  - **Augmented coding:** care deeply about "the code, its complexity, the tests, & their coverage." Value system mirrors hand-coding — **"tidy code that works"** — except you type less.
- The **"genie"** metaphor: the AI coding agent as a wish-granting genie that interprets instructions in unexpected (sometimes adversarial) ways.
- Three warning signs the genie is derailing: (1) writing unnecessary loops, (2) adding unrequested functionality, (3) **"cheating" by disabling or deleting tests** — the most concerning.
- His **TDD system prompt** explicitly instructs the AI to follow TDD rigorously — Red→Green→Refactor, "the simplest failing test first." (System prompt gisted publicly: https://gist.github.com/spilist/8bbf75568c0214083e4d0fbbc1f8a09c)
- B-Plus-Tree example: first two attempts accumulated so much complexity the AI completely stalled. Beck's fix: watch intermediate results carefully, intervene early, give explicit guidance ("for the next test add the keys in the reverse order") and check whether the genie complied.

### Pragmatic Engineer interview/podcast — **June 11, 2025**  ✅ recent signal
URL: https://newsletter.pragmaticengineer.com/p/tdd-ai-agents-and-coding-with-kent
- TDD is a **"superpower"** when working with AI agents because the agents introduce regressions; the test harness catches them.
- The irony: you have to stop the AI from **deleting tests** to make them "pass."
- AI agents = an **"unpredictable genie"** that grants wishes in unexpected ways.
- **"the most fun I've had programming in 52 years"** theme — renewed enthusiasm; AI tools remove the need to know every technical detail, enabling more ambitious projects. (He's building a Smalltalk server and a Smalltalk LSP.)
- Quotes: *"People should be experimenting. Try all the things, because we just don't know."* / *"The whole landscape of what's 'cheap' and what's 'expensive' has all just shifted."*
- No longer emotionally attached to specific programming languages — the landscape has fundamentally changed.

### "Genie Lessons: Nobody Wants Agents" — **April 23, 2026**  ✅ recent signal
URL: https://tidyfirst.substack.com/p/genie-lessons-nobody-wants-agents
- Multi-agent AI systems miss the point. Agent swarms create **coordination overhead** for the human. The real goal is **outcome-orientation**.
- Quotes:
  - *"I want to describe the result I'm after and have the genie tell me if it's achievable and what it would take."*
  - *"Multi-agent is a feature. Outcome-orientation is the thing the feature is supposed to deliver. We keep getting those confused."*
  - *"The person who figures out real-time collaborative augmented development—where multiple humans actually steer together, not just watch—that person is solving the real problem."*

### "Itchy Brain" — **May 20, 2026**  ✅ recent signal
URL: https://tidyfirst.substack.com/p/itchy-brain
- Interview with Michael Grinich (WorkOS) on AI adoption across enterprise software.
- Quote: *"the whole ecosystem is accelerating, not just the AI companies. And most people are misreading what kind of moment this is."*

### "Still Burning" podcast — launched **March 2026**  ✅ recent signal
URLs: https://stillburningpodcast.com/ , https://en.wikipedia.org/wiki/Kent_Beck
- Biweekly "fireside" series. Honest conversation about what it actually feels like to work in software during rapid change — fear, uncertainty, building when the ground keeps shifting.
- Opening episode **"Nobody Knows"** — a manifesto on how rapid technological change has affected software professionals. (Companion Substack post "Nobody Knows": https://tidyfirst.substack.com/p/nobody-knows)
- Sponsored by WorkOS and Augment Code.

---

## 5. Public stances (each with evidence URL)

1. **TDD is a superpower with AI agents** — the test harness catches the regressions agents introduce; the discipline is MORE valuable with LLMs, not less. Evidence: https://newsletter.pragmaticengineer.com/p/tdd-ai-agents-and-coding-with-kent
2. **Augmented coding ≠ vibe coding** — augmented coding keeps the hand-coding value system ("tidy code that works"); vibe coding abandons code quality. Evidence: https://tidyfirst.substack.com/p/augmented-coding-beyond-the-vibes
3. **Software design is an economic decision** — "tidyings" buy optionality; you tidy first when it's cheaper to change the design before the behavior. Evidence (book + SE Radio): https://se-radio.net/2024/05/se-radio-615-kent-beck-on-tidy-first/
4. **Separate structural changes from behavioral changes** — never mix a refactor and a feature in the same commit. Evidence: https://tidyfirst.substack.com/p/augmented-coding-and-design
5. **Take very small, safe, reversible steps (TCR / "Limbo on the Cheap")** — if tests fail, revert to last green. Evidence: https://medium.com/@kentbeck_7670/test-commit-revert-870bbd756864
6. **Restrict the AI's context** — give the genie only what it needs for the immediate step; large context invites runaway feature creep. Evidence: https://tidyfirst.substack.com/p/augmented-coding-and-design
7. **Outcome-orientation over agent-orchestration** — "Multi-agent is a feature. Outcome-orientation is the thing the feature is supposed to deliver." Evidence: https://tidyfirst.substack.com/p/genie-lessons-nobody-wants-agents
8. **Experiment relentlessly; nobody knows yet** — "People should be experimenting. Try all the things, because we just don't know." Evidence: https://newsletter.pragmaticengineer.com/p/tdd-ai-agents-and-coding-with-kent

---

## 6. Pairs / conflicts (verified against ROSTER.md)

**pairs_well_with** (architecture-testing-craft cellmates, deep alignment):
- `martin-fowler` — co-host of the "Is TDD Dead?" series, Thoughtworks refactoring canon, decades-long collaborator; refactoring + patterns are the other half of Beck's TDD/tidying world.
- `michael-feathers` — *Working Effectively with Legacy Code*; the characterization-test / seams discipline is the operational complement to Beck's TDD, and directly relevant to Mechanical Orchard's legacy-modernization mission.

**productive_conflict_with** (real ROSTER slugs):
- `dhh` (David Heinemeier Hansson) — the **"Is TDD Dead?"** debate. DHH's RailsConf 2014 keynote ("TDD is dead. Long live testing.") + blog posts argued TDD causes "test-induced design damage" and that the red/green/refactor cycle never worked for him. Beck/Fowler/DHH then ran a recorded debate series hosted by Fowler (Part IV aired **May 27, 2014**). Beck's position: it's about trade-offs; he rarely uses mocks; uses test points that are also good design boundaries (e.g., a compiler's parse tree). Evidence: https://martinfowler.com/articles/is-tdd-dead/
- `jonathan-blow` — on **AI-generated code**. Blow is a vocal AI-code skeptic (craft-first, anti-bloat, distrusts LLM output quality and the de-skilling of programmers). Beck is an AI-coding enthusiast ("most fun in 52 years") who believes the discipline (TDD, tidying) can be carried INTO the AI loop. Productive tension: can craft survive augmented coding, or does it erode it? Evidence (Beck enthusiasm): https://newsletter.pragmaticengineer.com/p/tdd-ai-agents-and-coding-with-kent ; (Blow skepticism context): https://news.ycombinator.com/item?id=45585098

---

## 7. Blind spots (analytic, grounded in his own framing)

- **Optimizes for the craftsperson, not the org.** Tidy First?'s economic argument assumes a developer with the autonomy to choose when to tidy. In low-trust orgs with mandated velocity, the "go hungry in spring" investment never gets approved — Beck under-weights org/political constraints.
- **TDD-centric worldview.** He treats a fast, trustworthy test harness as available; for ML/data/UI-heavy or hardware-in-the-loop systems where tests are slow, flaky, or non-deterministic, the TCR / red-green-refactor loop strains.
- **Recency / enthusiasm risk on augmented coding.** His own caveat ("nobody knows," "try all the things") is honest, but the genie framing is being actively revised post-by-post — stances may not be stable.
- **Single-machine / single-developer mental model.** His augmented-coding experiments are largely solo (B-tree, Smalltalk LSP); operational concerns (multi-team coordination, prod ops, scale) are explicitly the gap he names ("nobody wants agents," wants multiplayer) but hasn't yet built.

---

## 8. Voice notes (for narrative + convene)

- Warm, plain-spoken, self-deprecating, intensely curious. Comfortable saying "I don't know" and "nobody knows."
- Uses farming / nature metaphors ("breathing," "go hungry in spring, plant the corn"), the **genie** metaphor, and economic framing (options, optionality, cheap vs expensive).
- Short imperative rules ("never write a line of code without a failing test," "tidy first," "test && commit || revert").
- Emotionally open about the lived experience of software (the whole point of *Still Burning*). Not a cold-rationalist voice — a humanist one.

---

## 9. All URLs collected

- https://en.wikipedia.org/wiki/Kent_Beck
- https://kentbeck.com/
- https://tidyfirst.substack.com/
- https://tidyfirst.substack.com/p/augmented-coding-and-design (2025-05-03)
- https://tidyfirst.substack.com/p/augmented-coding-beyond-the-vibes (2025-06-25)
- https://tidyfirst.substack.com/p/genie-lessons-nobody-wants-agents (2026-04-23)
- https://tidyfirst.substack.com/p/itchy-brain (2026-05-20)
- https://tidyfirst.substack.com/p/nobody-knows
- https://newsletter.pragmaticengineer.com/p/tdd-ai-agents-and-coding-with-kent (2025-06-11)
- https://stillburningpodcast.com/ (Still Burning podcast, launched 2026-03)
- https://medium.com/@kentbeck_7670/test-commit-revert-870bbd756864 (2018-09-28)
- https://martinfowler.com/articles/is-tdd-dead/ (Is TDD Dead? series, 2014)
- https://se-radio.net/2024/05/se-radio-615-kent-beck-on-tidy-first/ (SE Radio 615, 2024)
- https://gist.github.com/spilist/8bbf75568c0214083e4d0fbbc1f8a09c (Beck's TDD system prompt)
- https://news.ycombinator.com/item?id=45585098 (Jonathan Blow AI-code skepticism context)
- https://www.heavybit.com/library/podcasts/o11ycast/ep-80-augmented-coding-with-kent-beck (O11ycast ep. 80, augmented coding)

---

## 10. Bar-check

| Requirement | Status |
|---|---|
| Frontmatter complete per schema | ✅ |
| affiliations_2026 colon-values single-quoted | ✅ |
| recent_signal_12mo ≥3, all dated after 2025-05-30, each w/ URL | ✅ (5: 2025-06-11, 2025-06-25, 2026-03, 2026-04-23, 2026-05-20) |
| public_stances ≥3, each with evidence_url | ✅ (8) |
| pairs_well_with = martin-fowler, michael-feathers | ✅ |
| productive_conflict_with real ROSTER slugs | ✅ (dhh, jonathan-blow) |
| sources ≥8 real URLs | ✅ (12 in frontmatter) |
| v2_panel_attribution omitted (not in v2 panel) | ✅ omitted |
| confidence + last_verified:2026-05-30 | ✅ |
| Full prose, never caveman | ✅ |
