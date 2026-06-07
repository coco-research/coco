# Steve Krug — Research Notes

**Researched:** 2026-06-01
**Researcher:** Claude (Product & Design Super Intelligence build, Wave PD2)
**Slug:** `steve-krug`
**Cell:** `design-foundations-usability` · **Role:** specialist · **Home team:** `product-design-super-intelligence`

---

## Status determination — CORRECTED from brief

The build brief specified `cell_role:specialist` and `status:active` by default. Research forced a correction.

Steve Krug (born 1950) is effectively **semi-retired**. The evidence:

- His personal blog at `sensible.com/blog/` has not had a new post since **March 22, 2022** ("You say 'potato,' I say 'focus group'").
- His "book about writing" has been "in development" since at least 2020 with no due date — he jokes he hopes "to get it done while I still have enough brain cells left to do it." (https://sensible.com/about/)
- He no longer teaches public workshops; he will occasionally be "talked into" remote in-house sessions for ~$15k/day. (https://sensible.com/category/faqs/)
- His most recent substantive public appearance is a single conference talk: **"Don't Make Me Think 3.0: What Endures and What Evolves in UX"** with Lou Rosenfeld at Advancing Research 2026, on **2026-03-11** (https://rosenverse.rosenfeldmedia.com/videos/dont-make-me-think-30-what-endures-and-what-evolves-in-ux).

The schema requires `status: active` to carry **≥3 signals dated after 2025-06-01**. Krug has exactly **one** (the March 2026 talk). The 2025-2026 web hits about him are overwhelmingly third-party commentary ("10 Usability Lessons from…", "Still the Bible of Web Usability?"), not signals *from* Krug.

**Decision:** Per the explicit fallback rule in the brief ("if you cannot find 3 post-2025-06-01 signals, set status:archetype with persistent_signals + document"), the persona is written as **`status: archetype`** with **`persistent_signals`** (≥5, historical permitted). The single fresh 2026 talk is included as the most recent persistent signal so future re-syntheses see it. `cell_role` remains `specialist` as instructed — archetype status concerns recency of public output, not cell function.

This is the only deviation from the brief's literal frontmatter values, and it is the deviation the brief itself sanctions.

---

## Biography (verified)

- **Born:** 1950. (https://en.wikipedia.org/wiki/Steve_Krug)
- **Based:** Chestnut Hill, Massachusetts.
- **Firm:** Advanced Common Sense — a one-man consultancy he describes as "just me and a few well-placed mirrors." (https://sensible.com/about/)
- **Education:** English Literature degree (switched out of Physics). Started as a proofreader at a typesetting shop, learned computers running typesetting equipment, then spent ~10 years as a technical writer before moving into usability. (search synthesis; https://en.wikipedia.org/wiki/Steve_Krug)
- **Career:** 25+ years as a usability consultant. Clients include **Apple, Bloomberg.com, Lexus.com, NPR, and the International Monetary Fund.** (https://sensible.com/about/)
- **X / Twitter:** @skrug (https://twitter.com/skrug)
- **Self-description of current life:** spends his time "either a) writing, or b) watching old movies on tv (when he really should be writing)." (https://sensible.com/about/)

---

## Books (canonical works)

1. **Don't Make Me Think: A Common Sense Approach to Web Usability** — 1st ed. 2000; 2nd ed. 2005; 3rd ed. **"Don't Make Me Think, Revisited"** 2014 (added mobile + touch). 700,000+ copies in print across 15+ languages. ISBN 9780321965516.
   - https://www.amazon.com/Dont-Make-Think-Revisited-Usability/dp/0321965515
   - https://sensible.com/dont-make-me-think/
2. **Rocket Surgery Made Easy: The Do-It-Yourself Guide to Finding and Fixing Usability Problems** — 2009. ~168 pages. Includes scripts, checklists, handouts for running your own tests. ISBN 9780321657299.
   - https://www.amazon.com/Rocket-Surgery-Made-Easy-Yourself/dp/0321657292
   - https://sensible.com/rocket-surgery-made-easy/

(Note: an earlier draft of one search erroneously said Rocket Surgery was "originally published in 2000, revised 2005 and 2013." That conflated it with Don't Make Me Think. Corrected: Rocket Surgery is a single 2009 edition; the multi-edition timeline belongs to Don't Make Me Think.)

---

## Canonical principles — verbatim quotes

### Krug's three laws of usability
1. **First Law:** "Don't make me think!"
2. **Second Law:** "It doesn't matter how many times I have to click, as long as each click is a mindless, unambiguous choice."
3. **Third Law:** "Get rid of half the words on each page, then get rid of half of what's left."
- Sources: https://blas.com/dont-make-me-think/ , https://quizlet.com/505860009/mgmt-445-dont-make-me-think-2-flash-cards/

### Definition of usability
"A person of average (or even below average) ability and experience can figure out how to use the thing to accomplish something without it being more trouble than it's worth."
- Source: https://howtoes.blog/2025/06/07/dont-make-me-think-a-book-summary/

### Refined meaning of the title
"'Don't Make Me Think' really means don't make me think *about things I don't need to think about*… You want them to think about *what's in it for them*."
- Source (Built In, 2020-04-07): https://builtin.com/articles/simplicity-ux-steve-krug-interview

### Scanning, satisficing, conventions
- Users don't read pages; they **scan** them, looking for keywords. They follow patterns like the F-pattern.
- Users **satisfice** — they choose the first reasonable option, not the optimal one.
- Design should exploit conventions rather than reinvent them.
- Sources: https://www.ronins.co.uk/hub/dont-make-me-think-by-steve-krug/ , https://en.wikipedia.org/wiki/Don't_Make_Me_Think

### The Trunk Test
Imagine being blindfolded, locked in a car trunk, driven around, then dropped on a random page of the site. You should still instantly identify: site ID, page name, sections, where you are, and how to search/navigate.
- Source: https://sydenhamgreen.wordpress.com/2014/04/22/the-trunk-test/

### The Reservoir of Goodwill
Users arrive with a "reservoir of goodwill" — a finite battery of patience. Friction (hidden info, forced registration, looking amateurish, asking for unneeded data) drains it; helpfulness and considerate design refill it. Keep it as full as possible.
- Sources: https://antonyjwhite.wordpress.com/2019/02/13/the-reservoir-of-goodwill/ , https://blog.bryanbibat.net/2009/05/07/usability-and-the-reservoir-of-goodwill/

---

## DIY / discount usability testing — verbatim quotes

### Core thesis
"The most valuable thing you can do to improve a website or app is to have the people who are building it, paying for it or marketing it watch some people trying to use it."

### A morning a month
"A morning a month, that's all we ask. Basically, it amounts to doing a round of testing once a month, with three users. On testing day, you do three tests in the morning and then debrief over lunch. By the time lunch is over, you're done with usability testing for the month, and you know what you're going to fix before the next round."
- Source: https://boagworld.com/usability/steve-krug/ , https://www.amazon.com/Rocket-Surgery-Made-Easy-Yourself/dp/0321657292

### Three users is enough
"If you watch three people try and use your site, you're going to discover a great many of the most serious problems that currently exist. It just works."

### The observer effect
"It's a transformative experience. People watch the tests and they suddenly get it — they understand what you've been trying to explain to them all this time."

### "The least you can do" (fixing philosophy)
"If you can come up with a tweak that makes it not be a serious problem, you've done just as well — and tweaks take much less work."

### Cost
"You can do your own usability tests and do them fairly well. It's going to cost a couple of hundred dollars as opposed to $5,000–$10,000."

### Timing mistake
"Most companies… test near the end of the development cycle, when the thing's almost finished… that's the worst possible time to do a test."
- Source (all five above): https://medium.com/the-lindberg-interviews/interview-with-steve-krug-how-to-get-diy-usability-testing-right-63dedddbd0ae

### Usability tests vs. focus groups
"Usability tests are about watching people actually try to use what we're building, so we can detect and fix the parts that confuse or frustrate them." (Distinguished from focus groups, which are people *talking about* things rather than *using* things.)
- Source: https://sensible.com/you-say-potato-i-say-focus-group/

---

## RECENT SIGNAL (post-2025-06-01) — verbatim quotes

### "Don't Make Me Think 3.0: What Endures and What Evolves in UX"
Talk with Lou Rosenfeld at **Advancing Research 2026**, **Wednesday, 2026-03-11, 1:35–2:05pm PT**. Hosted on Rosenverse. The session reflects on what endures in UX and what AI/tool-democratization is forcing to change.
- https://rosenverse.rosenfeldmedia.com/videos/dont-make-me-think-30-what-endures-and-what-evolves-in-ux
- https://rosenfeldmedia.com/advancing-research/people/steve-krug/

Direct quotes from the talk:
- On AI as augmentation, not autonomy: **"It's not self-driving cars, it's power steering."**
- On AI vs. social media: **"Unlike social media, which I think should not exist, AI should exist but with caution."**
- On AI quality trade-off: **"You can do stuff faster, but that doesn't mean it's gonna do the job as well."**
- On synthetic/simulated users: **"Simulated users is pure enshittification. It's not worth the paper it's printed on."**
- On the UX practitioner's identity: **"I feel like we are the user advocates. Our job is to be on the side of the angels and the users."**
- On the future job of UX: **"Most of our job is education — teaching people what AI is good for and what it's not."**
- On AGI: **"There's no reasonable prediction that AGI will exist in our lifetimes."**

This is the single strongest fresh signal and the basis for keeping the persona useful in 2026 conversations even under archetype status. It is notable that the "simulated users / enshittification" stance puts Krug in direct, citable conflict with anyone proposing AI-generated synthetic participants as a substitute for watching real humans — a live 2026 debate.

---

## Roster wiring (verified against ROSTER.md, 2026-06-01)

- **pairs_well_with:** `jakob-nielsen` (same cell, fellow discount-usability/heuristics pioneer; the brief named this pairing explicitly), `don-norman` (cell anchor, human-centered design / cognition), `jared-spool` (UX research education, shares the "just watch users" ethos).
- **productive_conflict_with:**
  - `nir-eyal` — Eyal's "Hooked" engagement-maximization model is precisely what Krug's "side of the angels / user advocate" stance pushes against.
  - `jony-ive` — expressive, aspirational industrial design vs. Krug's "self-evident, get-out-of-the-way, get rid of half the words" minimalism of *function*. Real ROSTER slug (design-leadership-craft).
  - `josh-clark` — Clark is the cell's "AI-in-design patterns" advocate; Krug's "simulated users is enshittification" and "AI is power steering not self-driving" stances generate a productive, citable tension over how far to push AI into the design/research loop.
  All three are real slugs in ROSTER.md.

---

## All source URLs collected

1. https://en.wikipedia.org/wiki/Steve_Krug
2. https://en.wikipedia.org/wiki/Don't_Make_Me_Think
3. https://sensible.com/about/
4. https://sensible.com/
5. https://sensible.com/dont-make-me-think/
6. https://sensible.com/rocket-surgery-made-easy/
7. https://sensible.com/you-say-potato-i-say-focus-group/
8. https://sensible.com/category/faqs/
9. https://sensible.com/blog/
10. https://rosenverse.rosenfeldmedia.com/videos/dont-make-me-think-30-what-endures-and-what-evolves-in-ux
11. https://rosenfeldmedia.com/advancing-research/people/steve-krug/
12. https://rosenverse.rosenfeldmedia.com/people/steve-krug
13. https://www.amazon.com/Dont-Make-Think-Revisited-Usability/dp/0321965515
14. https://www.amazon.com/Rocket-Surgery-Made-Easy-Yourself/dp/0321657292
15. https://builtin.com/articles/simplicity-ux-steve-krug-interview
16. https://medium.com/the-lindberg-interviews/interview-with-steve-krug-how-to-get-diy-usability-testing-right-63dedddbd0ae
17. https://boagworld.com/usability/steve-krug/
18. https://blas.com/dont-make-me-think/
19. https://antonyjwhite.wordpress.com/2019/02/13/the-reservoir-of-goodwill/
20. https://sydenhamgreen.wordpress.com/2014/04/22/the-trunk-test/
21. https://www.ronins.co.uk/hub/dont-make-me-think-by-steve-krug/
22. https://twitter.com/skrug

---

## Confidence

**0.93.** Identity is unambiguous (single famous person, no name collisions). Canonical principles and DIY-testing quotes are heavily corroborated across many sources. The one fresh 2026 signal (Advancing Research talk) is confirmed by two independent search hits plus the Rosenverse video and conference-people pages, and the AI/AGI/simulated-user quotes are consistent across those fetches. Minor uncertainty: the talk quotes are drawn from page summaries rather than a verbatim transcript, so phrasing may be lightly paraphrased by the source; the substance is reliable. Status set to `archetype` per the documented signal-recency rule.
