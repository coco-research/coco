# Ronny Kohavi — research notes

**Subject:** Ronny (Ron) Kohavi — author of *Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing* (Cambridge University Press, 2020).
**Slug:** `ronny-kohavi` · **Cell:** growth-metrics · **Cell role:** lead-driver · **Home team:** product-design-super-intelligence.
**Research date:** 2026-06-01 · **Researcher:** Claude (Opus 4.8).
**Status:** active (still teaching, posting, publishing as of 2026).

---

## Identity confirmation

High confidence (0.95). The subject is unambiguous: there is one prominent Ronny / Ron Kohavi in the experimentation field. His own sites (`exp-platform.com`, `experimentguide.com`, Stanford AI Lab page `ai.stanford.edu/~ronnyk/`), LinkedIn (`linkedin.com/in/ronnyk/`), and the Maven course pages all cross-confirm the same person and biography. Name appears as both "Ronny Kohavi" (informal, LinkedIn, course branding) and "Ron Kohavi" (book byline, academic publications). The task specifies slug `ronny-kohavi`; `real_name` recorded as "Ron Kohavi" to match the book byline, with "Ronny" noted as the common form.

### Correction to task framing
The task brief lists his career as "ex-Microsoft (Analysis & Experimentation), ex-Amazon, ex-Airbnb." This is accurate but **chronologically out of order**. Verified sequence (earliest → latest):
1. **Silicon Graphics** — managed the MineSet data-mining/visualization project (1990s).
2. **Blue Martini Software** — VP of Business Intelligence (company IPO'd 2000; later acquired by RedPrairie).
3. **Amazon** — Director of Data Mining and Personalization (early 2000s).
4. **Microsoft** — joined 2005; founded the Experimentation Platform (ExP) team in 2006; rose to Technical Fellow and Corporate VP of **Analysis & Experimentation**; led ~110 data scientists/engineers; departed November 2019 (some sources say "until 2021," but the cleaner reading is he left for Airbnb in late 2019 / early 2020).
5. **Airbnb** — VP and Technical Fellow leading Relevance & Experimentation; until March 2021.
6. **Independent (2021–present)** — consultant, teacher (Maven), author. Runs `experimentguide.com`. Not, as of research date, attached to a single employer.

So "ex-Microsoft / ex-Amazon / ex-Airbnb" is correct, but Amazon preceded Microsoft, which preceded Airbnb. Affiliations_2026 should reflect **independent practice** (Maven instructor + consultant), not a current corporate seat.

---

## Career facts (verified)

- **Education:** PhD in Machine Learning, Stanford University (his classic 1995 thesis work on wrappers for feature selection and the bias-variance decomposition of zero-one loss is heavily cited). BA from the Technion, Israel.
  - Source: https://ai.stanford.edu/~ronnyk/
- **Citations:** >55,000 citations; H-index ~60 (Google Scholar); three papers among the top ~1,000 most-cited in Computer Science; 15 patents granted.
  - Source: https://ai.stanford.edu/~ronnyk/
- **Award:** Individual Lifetime Achievement Award for Experimentation Culture, September 2020.
  - Source: https://ai.stanford.edu/~ronnyk/ and https://www.abtasty.com/blog/1000-experiments-club-ronny-kohavi/
- **Airbnb impact:** led relevance/experimentation delivering 6%+ booking-conversion improvement, "worth hundreds of millions of dollars of annual incremental revenue."
  - Source: https://ai.stanford.edu/~ronnyk/

---

## Canonical works

- **Book:** *Trustworthy Online Controlled Experiments: A Practical Guide to A/B Testing*, Ron Kohavi, Diane Tang, Ya Xu. Cambridge University Press, 2020. Often nicknamed "the HiPPO book." Translated into Chinese and Japanese.
  - https://www.cambridge.org/core/books/trustworthy-online-controlled-experiments/D97B26382EB0EB2DC2019A7A7B518F59 (frontmatter PDF: https://assets.cambridge.org/97811087/24265/frontmatter/9781108724265_frontmatter.pdf)
  - Companion site: https://experimentguide.com/ — tagline "Accelerate innovation using trustworthy online controlled experiments."
  - Chapter 1 PDF (free): https://experimentguide.com/wp-content/uploads/TrustworthyOnlineControlledExperiments_PracticalGuideToABTesting_Chapter1.pdf
- **HBR article:** "The Surprising Power of Online Experiments: Getting the Most Out of A/B and Other Controlled Tests," Ron Kohavi & Stefan Thomke, *Harvard Business Review*, Sept–Oct 2017, pp. 74–82.
  - https://hbr.org/2017/09/the-surprising-power-of-online-experiments
  - Contains the famous Bing example: an employee's low-priority headline change, shelved for months, was finally A/B tested by one engineer and increased revenue ~12% — "worth $100 million" — Bing's best revenue-generating idea ever.
- **Academic:** "Online Controlled Experiments at Large Scale" (KDD 2013); "Trustworthy Online Controlled Experiments: Five Puzzling Outcomes Explained" (KDD 2012); "Pitfalls in Online Controlled Experiments." His "Wrappers for Feature Subset Selection" (1997, with George John) and "A Study of Cross-Validation and Bootstrap..." (IJCAI 1995) are the top-1,000-cited CS papers from his earlier ML career.
  - Publications list: http://robotics.stanford.edu/users/ronnyk/ronnyk-bib.html
- **Practitioner platform:** `exp-platform.com` — "Accelerating Innovation through Trustworthy Experimentation." Hosts decades of his papers and slide decks.

---

## Recent signals (post-2025-06-01, for `recent_signal_12mo`)

1. **"Ronny Kohavi on teaching A/B testing at scale"** — interview/profile, Kevin Anderson's *Experimental Mind* Substack, **2026-01-21**.
   - https://kevinanderson.substack.com/p/ronny-kohavi-on-teaching-ab-testing
   - Quotes: "Smart people are confidently wrong about outcomes." "The audience is not much better than random" (re: predicting which variant wins). "I prefer to give people examples and develop their intuition." "We are now facing a revolution with the use of AI and LLMs, and new opportunities to generate and evaluate new ideas are opening up" — and using "the gold standard of randomized controlled experiments... to evaluate these ideas is critical." Emphasis on statistical power, winner's curse (exaggeration), false positives. Notes many orgs have limited users → low statistical power.
2. **Maven flagship cohort "Accelerating Innovation with A/B Testing," June 1–11, 2026** (sessions June 1, 2, 4, 8, 11). 4.8/5 over ~150 reviews. Course tagline internalizes "the humbling reality: we are poor at assessing the value of ideas" and "Getting numbers is easy; getting numbers you can trust is hard."
   - https://maven.com/kohavi/abtesting
   - Course start date itself (2026-06-01) is the freshest dated signal — he is actively teaching as of the research date.
3. **"A/B Testing: The Science of Not Fooling Yourself,"** New Economies Substack, **2025-11-11** — extended treatment built on Kohavi's framing.
   - https://www.neweconomies.co/p/ab-testing-the-science-of-not-fooling
   - "A/B tests, or online randomized controlled experiments, are the gold standard in science for establishing causality." Median success rate ~10% (range 8–33%). With ~10% prior, the probability a statistically significant result is a true positive is only ~78% (p<0.05 is NOT 95% probability B beats A). A 5%-converting site wanting to detect a 5% improvement needs >240,000 users. Twyman's Law: "Any figure that looks interesting or different is usually wrong."
4. **Advanced course LinkedIn post** — "Advanced A/B Testing Course by Ronny Kohavi," LinkedIn, activity id 7365985929041244160 (2025; #abtesting #experimentguide). Advanced cohort opened December 2024; 6 advanced cohorts taught.
   - https://www.linkedin.com/posts/ronnyk_abtesting-experimentguide-activity-7365985929041244160-CnuP

Teaching tally: 15 Maven cohorts of the flagship June 2023 → December 2025; advanced class opened Dec 2024 (6 cohorts). Combined with earlier private/corporate teaching, "30+ cohorts since 2021 / 1,000+ practitioners" per Maven/Lenny copy.

---

## Key stances + quotes (with evidence URLs for `public_stances`)

1. **Most ideas fail.** "Over two-thirds of ideas actually fail to move the metrics that they were designed to improve." At Microsoft, ~1/3 of well-designed experiments were positive, ~1/3 flat, ~1/3 negative. At highly optimized Bing, only ~10–20% of ideas win; "only 15% of launched experiments succeeded." At Airbnb, 250 ML ideas tested, ~20 succeeded (~90% failure) — but those 20 drove the 6% conversion lift.
   - https://www.abtasty.com/blog/1000-experiments-club-ronny-kohavi/
   - https://www.lennysnewsletter.com/p/the-ultimate-guide-to-ab-testing
2. **We are poor at assessing the value of ideas — the intuition-data gap.** "Smart people are confidently wrong about outcomes"; in his live polling, "the audience is not much better than random" at predicting winners.
   - https://kevinanderson.substack.com/p/ronny-kohavi-on-teaching-ab-testing
3. **Getting trustworthy numbers is the hard part.** "Getting numbers is easy; getting numbers you can trust is hard." Trust > volume of experiments.
   - https://experimentguide.com/
4. **Twyman's Law.** "Any figure that looks interesting or different is usually wrong." Breakthrough positive results deserve more scrutiny, not celebration; re-run and run validity (A/A) tests.
   - https://www.neweconomies.co/p/ab-testing-the-science-of-not-fooling
5. **Sample Ratio Mismatch (SRM) is the seatbelt.** Not checking SRM is "like a car without seatbelts." An SRM is to data quality what a fever is to illness — a symptom of many underlying problems; if present, the result is untrustworthy.
   - https://www.linkedin.com/posts/ronnyk_abtesting-experimentguide-srm-activity-7035674277836177408-s1im
6. **HiPPO — the Highest Paid Person's Opinion — should yield to data.** The book's mascot. In his own LinkedIn survey, "HiPPO" was only ~5% of stated reasons not to A/B test (i.e., people know they should test; other frictions dominate).
   - https://hbr.org/2017/09/the-surprising-power-of-online-experiments
7. **The OEC (Overall Evaluation Criterion) must encode long-term value, not a vanity short-term proxy.** Define success up front; combine into a single criterion aligned with long-term company goals; pair with guardrail metrics so you don't win the metric and lose the business.
   - https://experimentguide.com/wp-content/uploads/TrustworthyOnlineControlledExperiments_PracticalGuideToABTesting_Chapter1.pdf
8. **A/B testing is the gold standard for causality; observational studies are the bottom of the evidence hierarchy.** Don't substitute correlational/observational analysis (or, newly, LLM-simulated users) for randomized controlled experiments.
   - https://www.neweconomies.co/p/ab-testing-the-science-of-not-fooling
9. **LLMs do not give you causal evidence.** Replacing real users with LLM-generated "users" returns the model's baked-in assumptions, not causal truth; RCTs remain the gold standard for evaluating AI-generated ideas.
   - https://kevinanderson.substack.com/p/ronny-kohavi-on-teaching-ab-testing
10. **Statistical power and the winner's curse.** Low-power experiments inflate measured effect sizes (winner's curse / exaggeration); most orgs have far less power than they think; a 5%-converting site detecting a 5% lift needs 240,000+ users.
    - https://www.neweconomies.co/p/ab-testing-the-science-of-not-fooling
    - https://kevinanderson.substack.com/p/ronny-kohavi-on-teaching-ab-testing

---

## ROSTER cross-references (verified against superintelligence/product-design/ROSTER.md)

- **Cell:** growth-metrics (cell 3). Peers: lenny-rachitsky, elena-verna, andrew-chen, casey-winters, brian-balfour, **sean-ellis**, crystal-widjaja.
- **pairs_well_with:** `sean-ellis` (per task; North Star metric + PMF survey ↔ OEC + guardrail metrics — both insist on a single defining success metric). Also `crystal-widjaja` (instrumentation/data quality is the precondition for trustworthy experiments) and `brian-balfour` (growth models need experiment-validated assumptions).
- **productive_conflict_with (real ROSTER slugs):**
  - `jakob-nielsen` (design-foundations-usability) — qualitative discount usability ("test with 5 users") vs Kohavi's quantitative position that 5 users tell you nothing about a metric and you need hundreds of thousands. The canonical qual-usability-vs-quant-A/B tension. Conflict tag: `qualitative-usability-vs-quantitative-ab`.
  - `don-norman` (design-foundations-usability) — human-centered, intuition-and-principle-led design vs "your intuition is no better than random; let the experiment decide." Conflict tag: `intuition-led-design-vs-data-led-decisions`.
  - `nir-eyal` (sprints-behavior-bridge) — Kohavi would insist the OEC must include long-term/guardrail metrics so engagement optimization doesn't silently harm users; Eyal's habit-formation can over-index on a short-term engagement metric the way a badly chosen OEC does. Conflict tag: `short-term-engagement-metric-vs-long-term-oec`.

All five slugs (sean-ellis, jakob-nielsen, don-norman, nir-eyal, crystal-widjaja, brian-balfour) confirmed present in ROSTER.md.

---

## Sources (deduped, ≥8)

1. https://ai.stanford.edu/~ronnyk/ — official bio, career, awards, citations.
2. https://experimentguide.com/ — book companion site, tagline, philosophy quotes.
3. https://hbr.org/2017/09/the-surprising-power-of-online-experiments — HBR article, Bing $100M example, HiPPO.
4. https://www.lennysnewsletter.com/p/the-ultimate-guide-to-ab-testing — Lenny's Newsletter interview (career + pitfalls + SRM + redesigns).
5. https://www.abtasty.com/blog/1000-experiments-club-ronny-kohavi/ — AB Tasty interview; two-thirds-fail quote; Airbnb 250/20; failure-is-good.
6. https://maven.com/kohavi/abtesting — Maven flagship course, June 2026 cohort, ratings, "poor at assessing ideas" framing.
7. https://kevinanderson.substack.com/p/ronny-kohavi-on-teaching-ab-testing — Experimental Mind profile, 2026-01-21; teaching philosophy + AI/LLM stance.
8. https://www.neweconomies.co/p/ab-testing-the-science-of-not-fooling — 2025-11-11; gold-standard, median 10% success, 240K-user power, Twyman's Law.
9. https://www.linkedin.com/posts/ronnyk_abtesting-experimentguide-srm-activity-7035674277836177408-s1im — SRM "seatbelt" stance.
10. https://www.linkedin.com/in/ronnyk/ — LinkedIn profile.
11. https://www.cambridge.org/core/books/trustworthy-online-controlled-experiments/D97B26382EB0EB2DC2019A7A7B518F59 — publisher record.
12. http://robotics.stanford.edu/users/ronnyk/ronnyk-bib.html — full publication list.

---

## Bar-check

- ≥8 sources: yes (12).
- ≥3 recent signals post-2025-06-01 each with date + URL: yes (4: 2026-01-21, 2026-06-01 cohort, 2025-11-11, 2025 advanced-course post).
- every public_stance has evidence_url: yes (10 stances, all cited).
- productive_conflict_with uses real ROSTER slugs: yes (jakob-nielsen, don-norman, nir-eyal).
- pairs_well_with includes sean-ellis: yes.
- v2_panel_attribution: omit (Kohavi did not participate in the Marvin Memory v2 panel).
