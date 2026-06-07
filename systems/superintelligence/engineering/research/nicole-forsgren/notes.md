# Nicole Forsgren — Research Notes

**Slug:** `nicole-forsgren`
**Researched:** 2026-05-30
**Researcher:** Claude (engineering Super Intelligence Team build, Wave E9 devops-platform)
**Status:** active
**Confidence:** 0.95

---

## Identity confirmation

Dr. Nicole Forsgren (publishes as "Nicole Forsgren, PhD"; personal site `nicolefv.com`; LinkedIn handle `nicolefv`). Lead author of *Accelerate*, co-creator of the DORA research program and the SPACE framework. Single, unambiguous identity — no disambiguation needed.

---

## Correction to the briefing assumption (logged per instruction)

The task brief described her as **"Microsoft Research / GitHub (ex-Google) Partner."** This is *directionally correct but imprecise* and one search result actively contradicted it. Findings:

1. **Current employer (2026) is Microsoft, NOT Google.** Her own site (`nicolefv.com`), Wikipedia, the QCon SF 2025 speaker bio, and Microsoft Build all confirm she is a **Partner at Microsoft**, leading the **Developer Experience Lab** and working in the **Office of the CTO (OCTO)**. The QCon SF 2025 bio gives the precise title: **"Partner, Applied Research & Strategy, OCTO @Microsoft."**
   - Source: https://qconsf.com/speakers/nicoleforsgren
   - Source: https://nicolefv.com/ — *"She's currently a Partner at Microsoft, where she leads the Developer Experience Lab and works with the Office of the CTO, using AI to revolutionize how developers work."*

2. **An ACM ByteCast search snippet claimed she is "Senior Director of Developer Intelligence at Google."** This is STALE / out of date — it describes a historical role, not her 2026 position. Google is a *past* affiliation (DORA was acquired by Google in 2018; she worked at Google Cloud ~2018–2020). She left Google for GitHub (VP Research & Strategy, 2020), and GitHub is a Microsoft subsidiary, so "GitHub → Microsoft Research" is the lineage. The brief's "ex-Google" is accurate; "Microsoft Research / GitHub" is accurate; but her **single current employer is Microsoft (OCTO + Developer Experience Lab)**, and the "Google" current-role claim is wrong. Resolved: affiliations_2026 = Microsoft only.
   - Source (the stale claim): https://learning.acm.org/bytecast/ep81-nicole-forsgren

3. **Lab name correction.** Older sources (and one 2026 search snippet) call her lab the **"Developer Velocity Lab."** It has been **renamed the "Developer Experience Lab"** at Microsoft Research. Current/2025 sources use "Developer Experience Lab."
   - Source: https://www.microsoft.com/en-us/research/group/developer-experience-lab/

4. **`getdx.com/news/nicole-forsgren` does NOT announce her joining DX.** The DX hire announced in that timeframe was **Brian Houck** (Distinguished Scientist, May 4 2026), a SPACE/DevEx co-author. Forsgren co-authored the *Frictionless* book (2025) with DX founder/CEO **Abi Noda**, but she is **not** a DX employee — she remains at Microsoft. Avoided this false attribution.
   - Source: https://getdx.com/news/frictionless/

**Net:** affiliations_2026 set to Microsoft (Partner, Applied Research & Strategy, OCTO; lead, Developer Experience Lab, Microsoft Research) + ACM Queue editorial board. cell:devops-platform, cell_role:lead-driver as specified.

---

## Biography (verified)

- **PhD in Management Information Systems**, University of Arizona (Eller College of Management). Also a **Master's in Accounting**, University of Arizona.
  - Source: https://itrevolution.com/faculty/nicole-forsgren/ ; https://nicolefv.com/about
- **Early career:** mainframe programmer (first job — medical and finance systems), **Software Engineer at IBM**, sysadmin, performance engineer, then professor. Self-described as "entrepreneur (with an exit to Google), professor, developer, sysadmin, and performance engineer."
  - Source: https://nicolefv.com/about ; https://itrevolution.com/faculty/nicole-forsgren/
- **Chef Software** (~2014–2015): Director of Organizational Performance and Analytics.
- **DORA (DevOps Research and Assessment LLC)** — co-founded late 2015 with Jez Humble and Gene Kim; served as **CEO**. **Acquired by Google in 2018.**
- **Google Cloud** (~2018–2020) after the DORA acquisition.
- **GitHub** (2020): **VP of Research & Strategy.** (GitHub is owned by Microsoft.)
- **Microsoft Research / Microsoft OCTO** (current): **Partner**, leads the **Developer Experience Lab** (formerly Developer Velocity Lab); title "Partner, Applied Research & Strategy, OCTO."
  - Sources: https://en.wikipedia.org/wiki/Nicole_Forsgren ; https://qconsf.com/speakers/nicoleforsgren

---

## Canonical works / publications (verified)

### Accelerate: The Science of Lean Software and DevOps (2018)
- Authors: Nicole Forsgren, Jez Humble, Gene Kim. IT Revolution Press.
- **Won the Shingo Research and Professional Publication Award (2019).**
- Synthesizes **~23,000 survey data points** across years of State of DevOps research.
- Established the **four key DORA metrics**: Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time to Restore (MTTR/Time to Restore Service).
- **24 capabilities** across 5 categories (Continuous Delivery 8, Architecture 2, Product & Process 4, Lean Management & Monitoring 5, Cultural 5) that statistically predict performance.
- Methodology: survey research + psychometrics + statistical analysis (cluster analysis to derive performance profiles; the book is notable for bringing rigorous quantitative method — latent constructs, structural equation modeling — to DevOps).
  - Sources: https://en.wikipedia.org/wiki/Accelerate_(book) ; https://www.amazon.com/Accelerate-Software-Performing-Technology-Organizations/dp/1942788339

### The SPACE of Developer Productivity: There's more to it than you think (ACM Queue, Feb 2021)
- Authors: Nicole Forsgren, Margaret-Anne Storey, Chandra Maddila, Thomas Zimmermann, Brian Houck, Jenna Butler.
- ACM Queue Vol 19, No 1; DOI 10.1145/3454122.3454124.
- **SPACE = Satisfaction & well-being; Performance; Activity; Communication & collaboration; Efficiency & flow.**
- Core argument (abstract, exact quote): *"Developer productivity is about more than an individual's activity levels or the efficiency of the engineering systems relied on to ship software, and it cannot be measured by a single metric or dimension."*
- Prescriptive guidance: capture **at least 2–3 SPACE dimensions** (including at least one perceptual/subjective measure); never rely on activity-only metrics (commits, lines of code, PRs merged).
  - Sources: https://queue.acm.org/detail.cfm?id=3454124 ; https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/ ; https://getdx.com/blog/space-metrics/

### DevEx: What Actually Drives Productivity? (ACM Queue, 2023)
- Authors: Abi Noda, Margaret-Anne D. Storey, Nicole Forsgren, Michaela Greiler.
- Introduces the **three core DevEx dimensions: feedback loops, flow state, cognitive load.**
  - Source: https://queue.acm.org/detail.cfm?id=3595878 (DevEx); dblp http://dblp.org/pers/f/Forsgren:Nicole

### DevEx in Action: A study of its tangible impacts (ACM Queue, Jan 2024)
- Authors: Nicole Forsgren, Eirini Kalliamvakou, Abi Noda, Michaela Greiler, Brian Houck, Margaret-Anne Storey.
- ACM Queue Vol 21, No 6; DOI 10.1145/3639443. Empirical follow-up showing DevEx correlates with business and individual outcomes.
  - Source: https://queue.acm.org/detail.cfm?id=3639443 ; https://www.microsoft.com/en-us/research/publication/devex-in-action-a-study-of-its-tangible-impacts/

### The DevOps Handbook, 2nd edition — co-author.
  - Source: https://nicolefv.com/writing

---

## Recent signals (last 12 months — all AFTER 2025-05-30)

1. **Frictionless: 7 Steps to Remove Barriers, Unlock Value, and Outpace Your Competition in the AI Era** — book by Nicole Forsgren & Abi Noda, **Shift Key Press, published 2025-12-11.** ISBN 9781662966378. "The first end-to-end system for understanding and improving developer experience at scale." >100 pages of workbooks. Back cover: *"AI can generate code in minutes — so why does shipping software still take forever? The answer is friction."*
   - Sources: https://www.amazon.com/Frictionless-Remove-Barriers-Outpace-Competition/dp/1662966377 ; https://getdx.com/news/frictionless/ ; https://newsletter.pragmaticengineer.com/p/frictionless-why-great-developer (2025-12-10)

2. **QCon SF 2025 opening keynote — "Reducing Friction in the AI Age"** — delivered **2025-11-18.** Key line: *"code can be written in minutes, but in large organizations, deployment can still take months."* Defined friction as *"non-productive administrative and coordination delays that interrupt a developer's work."* Cited research that developers lose **~31% of their time** to friction. Advocated optimizing DevEx across feedback loops, flow state, cognitive load instead of chasing raw productivity.
   - Source: https://www.infoq.com/news/2025/11/forsgren-reduce-ai-friction/

3. **Lenny's Podcast — "How to measure AI developer productivity in 2025"** — published **2025-10-19.** Themes: "why most productivity metrics are a lie"; "why AI accelerates coding but developers aren't speeding up as much as you think"; DevEx = flow state + cognitive load + feedback loops. Reiterates she created DORA and SPACE.
   - Source: https://www.lennysnewsletter.com/p/how-to-measure-ai-developer-productivity ; Apple Podcasts https://podcasts.apple.com/us/podcast/how-to-measure-ai-developer-productivity-in-2025-nicole/id1627920305?i=1000732511416

4. **DORA 2025 report restructure** — discussed widely Dec 2025. The State of DevOps Report was renamed **"State of AI-assisted Software Development"**; the old low/medium/high/elite performance tiers were replaced by **seven team archetypes**; **Rework Rate** added as a stability metric. Forsgren quoted on the need for *"new frameworks for measuring DevEx in the age of AI."* AI adoption correlated positively with throughput in 2025 (reversed from 2024) but still associated with *increasing instability.*
   - Source: https://redmonk.com/rstephens/2025/12/18/dora2025/ (2025-12-18)

---

## Public stances (each cited)

1. **"You cannot measure productivity with a single metric or dimension."** — SPACE paper abstract.
   - https://queue.acm.org/detail.cfm?id=3454124
2. **Activity metrics (lines of code, commits, PRs) alone are misleading; measure at least 2–3 SPACE dimensions including a perceptual one.**
   - https://getdx.com/blog/space-metrics/
3. **Developer Experience (feedback loops, flow state, cognitive load) is the lever; productivity is the outcome.** DevEx drives business results.
   - https://queue.acm.org/detail.cfm?id=3639443
4. **Friction — administrative/coordination delays — is the real tax; developers lose ~31% of their time to it, and AI amplifies bottlenecks rather than removing them.** (Frictionless / QCon keynote)
   - https://www.infoq.com/news/2025/11/forsgren-reduce-ai-friction/
5. **DevOps performance is empirically measurable: the four key DORA metrics (deploy frequency, lead time, change failure rate, time to restore) predict org performance — claims must be backed by data, not anecdote.** (Accelerate)
   - https://www.amazon.com/Accelerate-Software-Performing-Technology-Organizations/dp/1942788339
6. **In the AI era the old DORA tiers and assumptions break; we need new measurement frameworks for AI-assisted development.** (DORA 2025 / Lenny's)
   - https://redmonk.com/rstephens/2025/12/18/dora2025/

---

## Roster cross-references

- **pairs_well_with:** gene-kim (Accelerate / DORA co-author, same devops-platform cell), jez-humble (Accelerate / DORA co-author, same cell), matthew-skelton (Team Topologies, same cell — DevEx + team cognitive load are complementary).
- **productive_conflict_with (real ROSTER.md slugs):**
  - `dhh` (David Heinemeier Hansson, architecture-testing-craft) — DHH is skeptical of metrics-driven management and big-org process; Forsgren's empirical-measurement stance sharpens against his "majestic monolith / trust the craftsperson" instinct.
  - `charity-majors` (reliability-sre-obs) — both care about engineering effectiveness, but Majors champions observability/"test in prod" and is wary of surveys/metrics that can be weaponized against ICs; productive tension over what is actually measurable vs. felt.
  - (Considered: `corey-quinn` for cost-vs-DevEx framing; chose the two above as sharper, genuine disagreements grounded in the roster.)

---

## Sources (master list, >=8)

1. https://nicolefv.com/ — personal site, current role
2. https://nicolefv.com/about — bio, PhD, career
3. https://nicolefv.com/writing — books
4. https://en.wikipedia.org/wiki/Nicole_Forsgren — career history
5. https://en.wikipedia.org/wiki/Accelerate_(book) — Accelerate, DORA metrics, awards
6. https://queue.acm.org/detail.cfm?id=3454124 — SPACE paper
7. https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/ — SPACE (MSR)
8. https://queue.acm.org/detail.cfm?id=3639443 — DevEx in Action
9. https://www.infoq.com/news/2025/11/forsgren-reduce-ai-friction/ — QCon SF 2025 keynote (2025-11-18)
10. https://www.lennysnewsletter.com/p/how-to-measure-ai-developer-productivity — Lenny's podcast (2025-10-19)
11. https://getdx.com/news/frictionless/ — Frictionless book (2025)
12. https://newsletter.pragmaticengineer.com/p/frictionless-why-great-developer — Frictionless review (2025-12-10)
13. https://redmonk.com/rstephens/2025/12/18/dora2025/ — DORA 2025 analysis (2025-12-18)
14. https://qconsf.com/speakers/nicoleforsgren — current title "Partner, Applied Research & Strategy, OCTO @Microsoft"
15. https://getdx.com/blog/space-metrics/ — SPACE dimensions explainer
16. https://itrevolution.com/faculty/nicole-forsgren/ — faculty bio
