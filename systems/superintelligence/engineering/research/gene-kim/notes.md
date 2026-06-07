# Gene Kim — Research Notes

**Subject:** Gene Kim — author, researcher, founder of IT Revolution + DevOps Enterprise Summit.
**Slug:** `gene-kim`  **Cell:** `devops-platform`  **Cell role:** `lead-driver`  **Home team:** `engineering`
**Researched:** 2026-05-30  **Researcher:** Claude (engineering Super Intelligence Team build, Wave E9)
**Confidence:** 0.97 (well-documented public figure; identity unambiguous; deep recent signal)

---

## Identity confirmation

- Full name: Gene Kim. American entrepreneur, researcher, author. Born January 11, 1971.
  Source: https://prabook.com/web/gene.kim/2458554 ; https://en.everybodywiki.com/Gene_Kim
- As a student of Gene Spafford at Purdue, co-authored the open-source tool **Tripwire** in 1992.
- Co-founded **Tripwire, Inc.** in 1997 with Wyatt Starnes; served as **CTO for 13 years**, leaving July 2010 to become a full-time author and researcher. Company reached 260+ employees and $74M revenue by 2009.
  Source: https://en.everybodywiki.com/Gene_Kim ; http://www.realgenekim.me/tripwire/
- Began studying high-performing IT organizations in 1999.
- Co-authored *The Visible Ops Handbook* (2004) and *Visible Ops Security* (2008) — predecessors to the DevOps canon.
- Since **2014** has organized the **DevOps Enterprise Summit**, now renamed **Enterprise Technology Leadership Summit (ETLS)** and **Enterprise AI Summit**.
  Source: https://itrevolution.com/author/gene-kim/ (official bio, accessed via search snippet — page itself returns 403 to WebFetch)
- Founder of **IT Revolution** (publisher + research org).
- Co-founded **DORA (DevOps Research and Assessment)** with Nicole Forsgren in 2015; acquired by Google in 2018.
  Source: https://waydev.co/accelerate-metrics/

Identity is unambiguous — single well-known public figure, no disambiguation needed.

---

## Canonical works / books (with co-authors)

- **The Phoenix Project: A Novel about IT, DevOps, and Helping Your Business Win** (2013) — with Kevin Behr and George Spafford. Business novel that popularized DevOps via the "Three Ways."
- **The DevOps Handbook** (2016; 2nd ed. 2021) — with Jez Humble, Patrick Debois, John Willis (2nd ed. adds Nicole Forsgren). Codifies the Three Ways: Flow, Feedback, Continual Learning & Experimentation.
  Source: https://www.amazon.com/DevOps-Handbook-World-Class-Reliability-Organizations/dp/1942788002
- **Accelerate: The Science of Lean Software and DevOps** (2018) — co-author with Dr. Nicole Forsgren (lead) and Jez Humble. Shingo Publication Award winner. Establishes the four key DORA metrics (deployment frequency, lead time for changes, time to restore service, change failure rate) from research across 23,000+ respondents / 2,000+ orgs.
  Source: https://waydev.co/accelerate-metrics/ ; https://getdx.com/blog/accelerate-metrics/
- **The Unicorn Project** (2019) — solo. WSJ bestseller. Sequel to Phoenix Project; introduces the "Five Ideal" (locality & simplicity; focus, flow & joy; improvement of daily work; psychological safety; customer focus).
- **Wiring the Winning Organization** (Nov 21, 2023) — with Dr. Steven J. Spear. Shingo Publication Award Winner, 2024 Eric Hoffer Book Award Finalist, shortlisted 2024 Business Book Award. Introduces the three mechanisms: **slowification, simplification, amplification** — systematically moving problem-solving from the "danger zone" to the "winning zone."
  Source: https://itrevolution.com/product/wiring-the-winning-organization/ ; https://www.goodreads.com/en/book/show/125164532-wiring-the-winning-organization
- **Vibe Coding: Building Production-Grade Software With GenAI, Chat, Agents, and Beyond** (Oct 21, 2025) — with Steve Yegge (foreword/contribution by Dario Amodei). IT Revolution Press. Won 2026 Axiom Book Awards Gold Medal.
  Source: https://www.simonandschuster.com/books/Vibe-Coding/Gene-Kim/9781966280026 ; https://itrevolution.com/product/vibe-coding-book/
- Books have sold **over 1 million copies** collectively.

---

## The frameworks (signature intellectual contributions)

### The Three Ways (DevOps Handbook / Phoenix Project)
Source: https://itrevolution.com/articles/the-three-ways-principles-underpinning-devops/ ; https://itrevolution.com/articles/three-ways-revisited-devops-handbook/
- **First Way — Flow:** fast left-to-right flow of work Dev → Ops → customer. Make work visible, reduce batch sizes, build in quality, optimize for global goals.
- **Second Way — Feedback:** right-to-left feedback loops; shorten and amplify them so corrections happen continually.
- **Third Way — Continual Learning & Experimentation:** culture of experimentation, risk-taking, learning from failure; repetition and practice as prerequisite to mastery.

### Slowification / Simplification / Amplification (Wiring the Winning Organization, with Spear)
Source: https://itrevolution.com/product/wiring-the-winning-organization/
- **Slowification:** solve problems in a calmer, less time-pressured setting (planning, practice, offline) before doing them in the heat of production.
- **Simplification:** make work easier through modularization, incrementalization, linearization — reduce the size and coupling of problems.
- **Amplification:** make problems and signals loud so they get attention and get solved, rather than being suppressed.
- Core thesis: high performers win by moving problem-solving from the **danger zone** (high-risk, high-pressure, coupled) to the **winning zone** (low-risk).

### FAAFO (Vibe Coding, with Yegge)
Source: https://www.audible.com/pd/Vibe-Coding-Audiobook/B0FPGKZZHL ; Tech Lead Journal #244 (https://open.spotify.com/episode/4xzPzhnTKGrJYcUyJWBRTU)
- **F**ast, **A**mbitious, **A**utonomous, **F**un, **O**ptionality — the real value proposition of AI-assisted ("vibe") coding.

### DORA four key metrics (Accelerate, with Forsgren & Humble)
Deployment frequency, lead time for changes, time to restore service, change failure rate.

---

## Recent signal (last 12 months — all dated AFTER 2025-05-30 except where noted)

1. **Platform Engineering Podcast Ep. 30 — "From DevOps to 'Vibe Coding'"** — **May 28, 2025**.
   NOTE: This is two days BEFORE the 2025-05-30 cutoff, so it does NOT qualify as a recent_signal_12mo entry. Used only for background quotes. Defines vibe coding as "anything besides writing code by hand"; says DevOps "turned into a set of tools"; advocates measuring "code deployment lead time."
   Source: https://www.platformengineeringpod.com/episode/from-devops-to-vibe-coding-gene-kim-on-ai-assisted-development-and-platform-engineering

2. **Checkmarx interview — "Gene Kim on Vibe Coding and Why DevSecOps Must Be Ready"** — **June 24, 2025**. ✅ QUALIFIES
   Quotes: committed 4,000 lines of functional code in four days; AI code became a "haunted codebase" so "opaque and brittle it required a full two-day stand-down to make it operable again"; "The same instincts that served us at 5 miles per hour now fail us at 50." Names "Shadow Code" and "Speed Without Validation" as emerging risks; DevSecOps as enabler.
   Source: https://checkmarx.com/blog/ai-llm-tools-in-application-security/gene-kim-on-vibe-coding-and-why-devsecops-must-be-ready-for-whats-coming/

3. **Vibe Coding (book) released** — **Oct 21, 2025**. ✅ QUALIFIES
   With Steve Yegge; Dario Amodei contribution. Argues developers should trust AI agents rather than manually reviewing every change. Honestly documents failures (AI silently deleted tests, generated 3,000-line functions, nearly deleted weeks of work). Won 2026 Axiom Book Awards Gold Medal.
   Source: https://itrevolution.com/product/vibe-coding-book/ ; https://www.theregister.com/2025/10/21/book_review_vibe_coding/

4. **AI Engineering Code Summit — "2026: The Year the IDE Died"** (with Steve Yegge) — **Nov 20, 2025**. ✅ QUALIFIES
   On how coding agents transform dev tools. Kim covered enterprise adoption patterns, the FAAFO framework, 10x improvement case studies; "trust in AI systems grows with experience"; leading orgs mandating AI-assisted development to build capability.
   Source: https://thefocus.ai/reports/aiecode-2025-11/speakers/gene-kim/ ; https://www.youtube.com/watch?v=7Dtu2bilcFs

5. **Tech Lead Journal #244 — "Gene Kim: How Vibe Coding Solved What I Couldn't in 13 Years"** — **Jan 19, 2026**. ✅ QUALIFIES
   1h04m. FAAFO framework defined. "Line cook to head chef" — shift from executing code to delegation, architecture, fast feedback. Orgs need "feedback loops 100x faster than before." Addresses deleted databases, corrupted repos.
   Source: https://open.spotify.com/episode/4xzPzhnTKGrJYcUyJWBRTU ; https://podcasts.apple.com/sn/podcast/gene-kim-how-vibe-coding-solved-what-i-couldnt-in-13-years/id1523421550?i=1000745740723

6. **Enterprise AI Summit announced — April 9-10, 2026** (forward signal). ✅ QUALIFIES (announcement dated late 2025/early 2026)
   New event under the IT Revolution umbrella focused on enterprise GenAI value creation.
   Source: https://www.linkedin.com/posts/realgenekim_enterprise-ai-summit-april-9-10-2026-activity-7439162723055300608-HEI9

7. **Enterprise Technology Leadership Summit (ETLS) Las Vegas** — **Sept 23-25, 2025**. ✅ QUALIFIES
   Kim + Yegge presented vibe coding; Tim O'Reilly on "Grappling with the bitter lesson." Theme: software outputs ceasing to be the constraint on value delivery; AI agents clearing backlogs faster than teams can plan.
   Source: https://itrevolution.com/articles/what-to-expect-at-the-2025-enterprise-technology-leadership-summit/ ; https://x.com/timoreilly/status/1970558795941368140

8. **"The genie is out of the bottle"** — Kim says "vibe coding is going to be the term that sticks" in response to attempts to rename the practice "agentic engineering."
   Source: https://thenewstack.io/vibe-coding-agentic-engineering/ (The New Stack)

---

## Public stances (each cited)

1. **The Three Ways underpin all of DevOps: Flow, Feedback, Continual Learning.**
   Evidence: https://itrevolution.com/articles/the-three-ways-principles-underpinning-devops/
2. **High performers win by slowification + simplification + amplification — moving problem-solving from the danger zone to the winning zone.**
   Evidence: https://itrevolution.com/product/wiring-the-winning-organization/
3. **Software delivery performance is measurable by exactly four metrics (DORA): deployment frequency, lead time for changes, time to restore service, change failure rate — and speed and stability rise together, not in tension.**
   Evidence: https://getdx.com/blog/accelerate-metrics/
4. **"Vibe coding" is anything besides writing code by hand, and the term will stick.**
   Evidence: https://thenewstack.io/vibe-coding-agentic-engineering/
5. **AI-assisted coding without strong testing, fast feedback, and architectural independence produces a "haunted codebase." DevSecOps must lead, not obstruct, GenAI adoption.**
   Evidence: https://checkmarx.com/blog/ai-llm-tools-in-application-security/gene-kim-on-vibe-coding-and-why-devsecops-must-be-ready-for-whats-coming/
6. **The developer role shifts from "line cook to head chef" — from writing code to delegating, architecting, and accelerating feedback loops; orgs need feedback loops 100x faster.**
   Evidence: https://podcasts.apple.com/sn/podcast/gene-kim-how-vibe-coding-solved-what-i-couldnt-in-13-years/id1523421550?i=1000745740723
7. **DevOps lost its meaning by being reduced to "a set of tools" — the real measure is code deployment lead time and team independence, not tool adoption.**
   Evidence: https://www.platformengineeringpod.com/episode/from-devops-to-vibe-coding-gene-kim-on-ai-assisted-development-and-platform-engineering

---

## Pairs / conflicts (ROSTER.md slugs verified)

- **pairs_well_with:** `jez-humble` (Continuous Delivery, DevOps Handbook, Accelerate co-author), `nicole-forsgren` (Accelerate lead author, DORA co-founder). Both in cell `devops-platform`. Also natural: `matthew-skelton` (Team Topologies), `kelsey-hightower`, `solomon-hykes`.
- **productive_conflict_with:**
  - `dhh` (David Heinemeier Hansson, cell architecture-testing-craft) — process-and-measurement-as-organizational-capability (Kim) vs. small-team simplicity and skepticism of process/measurement ceremony (DHH's "majestic monolith," anti-cargo-culting, "programmers susceptible to the siren song of complexity"). Source: https://x.com/dhh/status/1699910613777141895 ; https://corecursive.com/045-david-heinemeier-hansson-software-contrarian/
  - `charity-majors` (cell reliability-sre-obs) — productive tension on whether DORA's four metrics adequately capture reliability/operability vs. observability-first "test in prod" instrumentation. Friendly-adjacent, sharpening rather than opposing.

## Correction log

- The Register review (Oct 21, 2025) said it "doesn't mention a FAAFO framework" — but FAAFO IS in the book and is confirmed by the Tech Lead Journal episode and AI Engineering Code Summit coverage. The Register reviewer simply didn't surface that acronym. FAAFO = Fast, Ambitious, Autonomous, Fun, Optionality. Retained as confirmed.
- The Platform Engineering podcast (May 28, 2025) falls 2 days BEFORE the 2025-05-30 recency cutoff; therefore NOT counted as a recent_signal_12mo, used only for background. All recent_signal_12mo entries are dated June 2025 or later.
- Karpathy's "Accept All. Always." quote appears in the Vibe Coding book context but is Karpathy's, not Kim's — not attributed to Kim.

## Sources (master list)

- https://itrevolution.com/product/wiring-the-winning-organization/
- https://www.goodreads.com/en/book/show/125164532-wiring-the-winning-organization
- https://itrevolution.com/author/gene-kim/
- https://itrevolution.com/articles/the-three-ways-principles-underpinning-devops/
- https://itrevolution.com/articles/three-ways-revisited-devops-handbook/
- https://www.amazon.com/DevOps-Handbook-World-Class-Reliability-Organizations/dp/1942788002
- https://getdx.com/blog/accelerate-metrics/
- https://waydev.co/accelerate-metrics/
- https://www.simonandschuster.com/books/Vibe-Coding/Gene-Kim/9781966280026
- https://itrevolution.com/product/vibe-coding-book/
- https://www.theregister.com/2025/10/21/book_review_vibe_coding/
- https://checkmarx.com/blog/ai-llm-tools-in-application-security/gene-kim-on-vibe-coding-and-why-devsecops-must-be-ready-for-whats-coming/
- https://www.platformengineeringpod.com/episode/from-devops-to-vibe-coding-gene-kim-on-ai-assisted-development-and-platform-engineering
- https://thefocus.ai/reports/aiecode-2025-11/speakers/gene-kim/
- https://www.youtube.com/watch?v=7Dtu2bilcFs
- https://open.spotify.com/episode/4xzPzhnTKGrJYcUyJWBRTU
- https://podcasts.apple.com/sn/podcast/gene-kim-how-vibe-coding-solved-what-i-couldnt-in-13-years/id1523421550?i=1000745740723
- https://thenewstack.io/vibe-coding-agentic-engineering/
- https://itrevolution.com/articles/what-to-expect-at-the-2025-enterprise-technology-leadership-summit/
- https://en.everybodywiki.com/Gene_Kim
- https://prabook.com/web/gene.kim/2458554
- http://www.realgenekim.me/tripwire/
- https://x.com/dhh/status/1699910613777141895
