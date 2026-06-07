# John Carmack — Research Notes

**Subject:** John Carmack — co-founder of id Software (Doom/Quake), ex-CTO of Oculus, founder & CEO of Keen Technologies (AGI).
**Slug:** `john-carmack`
**Cell:** `systems-programming` (Engineering Super Intelligence Team)
**Cell role:** `lead-driver`
**Research date:** 2026-05-30
**Researcher:** Engineering SI Team build agent (Wave E6)

---

## Identity confirmation

High confidence. John D. Carmack is unambiguous in the public record: programmer behind Wolfenstein 3D, Doom, Quake; co-founder of id Software (1991); CTO of Oculus VR (2013–2019, "Consulting CTO" 2019–2022); founder of Keen Technologies (2022), an AGI research company. X handle `@ID_AA_Carmack`. No disambiguation issues. Confidence 0.97.

---

## Biographical / affiliation facts (2026)

- **Keen Technologies** — founder & CEO since 2022. AGI research company based in Dallas, TX. Raised an initial $20M round (Aug 2022) led by Nat Friedman and Daniel Gross, with Patrick Collison, Tobi Lütke, Sequoia, Capital Factory, and Jim Keller participating.
  - Source: https://x.com/ID_AA_Carmack/status/1560728042959507457 ; https://dallasinnovates.com/legendary-dallas-innovator-john-carmack-raises-20m-for-artificial-general-intelligence-startup-keen-technologies/
- **Richard Sutton partnership** — announced 2023-09-25 via Amii. Sutton ("principal founder of reinforcement learning," 2024 Turing Award context, author of "The Bitter Lesson" and the actor-critic / temporal-difference learning work) is Chief Scientific Advisor. Joint goal: "developing a genuine AI prototype by 2030, including establishing, advancing and documenting AGI signs of life."
  - Carmack quote: "The AI space is awash in capital, compute, and data, but it is still dominated by fashions that may yet hinder important breakthroughs."
  - Sutton quote: "John is a powerful intellect and one of the world's greatest system engineers."
  - Source: https://www.amii.ca/updates-insights/john-carmack-and-rich-sutton-agi
- **Past:** id Software (co-founder 1991, lead programmer through Rage/2013); Armadillo Aerospace (founder, 2000–2013, suborbital rocketry); Oculus VR / Facebook (CTO 2013–2019, Consulting CTO 2019–2022).

---

## Dated recent signals (post-2025-05-30 verified, plus near-boundary items)

1. **Upper Bound 2025 talk — "Keen Technologies Research Directions"**
   - Slides posted to X: **2025-05-22** (status 1925710474366034326). Notes posted same thread.
   - Full video posted: **2025-06-16** (status 1934720628306636986); also hosted by Amii.
   - Content: the "Physical Atari" project — a robot with a camera pointed at a real Atari/TV and a robotic joystick, learning to play games in real time. Argues researchers are "too comfortable in turn-based simulations" — "stop treating Atari like a turn-based board game where the environment waits patiently for actions; the real world keeps going regardless of whether the agent has finished processing its last observation." Trickiest implementation detail: score/life detection. Uses rectification with fixed cameras and AprilTags for moving cameras. Framed explicitly as **research, not a product**.
   - Sources: https://x.com/ID_AA_Carmack/status/1925710474366034326 ; https://x.com/ID_AA_Carmack/status/1934720628306636986 ; https://www.amii.ca/videos/keen-technologies-research-directions-john-carmack-upper-bound-2025 ; https://news.ycombinator.com/item?id=44070042
   - **Note on dating:** The video posting (2025-06-16) is unambiguously after 2025-05-30, so this qualifies as a recent signal. The slides (2025-05-22) fall just before the window; I cite the video date for the recent-signal entry.

2. **Venture Dallas 2025 — AGI fireside (with Ben Lamm)**
   - **2025-10-30**, George W. Bush Presidential Center, SMU.
   - Recounts being "late to recognize the importance of deep learning in 2012" when image classification and early RL (DeepMind Atari, in simulation) took off; positions Physical Atari as bringing reality into that simulation lineage.
   - Sources: https://dallasinnovates.com/agi-and-de-extinction-john-carmack-and-ben-lamm-join-venture-dallas-2025-lineup/ ; https://dallasinnovates.com/theres-so-much-energy-in-our-space-innovators-investors-invigorate-sold-out-2025-venture-dallas-conference/

3. **D CEO Magazine exclusive interview — "AI Won't Change the World as Much as People Think"**
   - Published **2025-11-19**.
   - Quotes:
     - "AI is going to change the world in some pretty significant ways, although not as much or as quickly as people believe."
     - "The inertia of the world's system is enormous, and it's not going to change as much as people think."
     - "Ten years from now, people will still be talking on Facebook."
     - "We're trying to learn fundamental things about architecture and learning that nobody knows right now."
     - On tangible vs abstract demos: "It was cooler when I could tell people to look at a virtual reality headset… now I'm like, 'Look at the numbers on this graph,' and it's just not as exciting."
   - Source: https://www.dmagazine.com/business-economy/2025/11/conversation-with-john-carmack-keen-technologies/

4. **"We are not on the brink of AGI" — X post**
   - **2026-03-14** (X status 2032460578669691171), reported by WebProNews same day.
   - Distinguishes "impressive pattern matching" from "genuine general intelligence"; argues current scaling approaches may be insufficient and fundamental architectural innovation beyond transformers is likely needed; Keen pursues efficiency/architecture over brute-force compute.
   - Source: https://www.webpronews.com/john-carmacks-blunt-verdict-on-ai-progress-we-are-not-on-the-brink-of-agi/

5. **Software-optimization / anti-bloat thought experiment — X post**
   - **2025-05-12** (X status 1922100771392520710). Reported by Slashdot 2025-05-13, TechSpot, etc.
   - "More of the world than many might imagine could run on outdated hardware if software optimization was truly a priority, and market price signals on scarce compute would make it happen. Rebuild all the interpreted microservice based products into monolithic native codebases!" — with the caveat: "Innovative new products would get much rarer without super cheap and scalable compute."
   - **Note on dating:** posted 2025-05-12, just before the 2025-05-30 window boundary. Treated as a near-boundary signal and used primarily as a *public_stance* anchor, not as one of the three required post-2025-05-30 recent signals. Items 1–4 satisfy the recent-signal requirement (video 2025-06-16, talk 2025-10-30, interview 2025-11-19, post 2026-03-14).
   - Sources: https://x.com/ID_AA_Carmack/status/1922100771392520710 ; https://tech.slashdot.org/story/25/05/13/1321259/carmack-world-could-run-on-older-hardware-if-software-optimization-was-priority

---

## Canonical engineering quotes / philosophy

- **On abstraction:** "Abstraction trades an increase in real complexity for a decrease in perceived complexity. That isn't always a win." / "It is not that uncommon for the cost of an abstraction to outweigh the benefit it delivers. Kill one today!"
- **On simplicity:** "Sometimes, the elegant implementation is just a function. Not a method. Not a class. Not a framework. Just a function."
- **On premature optimization (inverted):** "You can prematurely optimize maintainability, flexibility, security, and robustness just like you can performance."
- **On functional programming in C++ (2012 essay):** pragmatic — making state explicit and minimizing mutation/hidden parameters "makes it much easier to reason about"; but FP "really doesn't affect what you do in software engineering… only helpful when people are making certain classes of mistakes." Recommends returning new copies instead of self-mutating and "throwing const in front of practically every non-iterator variable."
  - Source: http://www.sevangelatos.com/john-carmack-on/
- **.plan files:** Carmack's legendary developer logs from the id era — terse, dated, technical. The original "do the simplest thing that could possibly work / measure before optimizing" engineering culture.
- **Lex Fridman #309 (2022-08-04, 5h23m):** the canonical long-form biography of his engineering method — adaptive tile refresh (Commander Keen), BSP (Doom), surface caching (Quake), z-fail stencil shadows ("Carmack's Reverse"). Source: https://lexfridman.com/john-carmack/

---

## Roster relationship reasoning

- **pairs_well_with (per task spec, all confirmed in ROSTER.md):**
  - `jonathan-blow` — systems-programming cell-mate; shares anti-bloat, "software is decaying," hand-rolled-over-framework worldview; Jai language.
  - `bryan-cantrill` — systems-programming cell-mate; Oxide hardware/software co-design, performance-first, contempt for unnecessary layers.
  - `chris-lattner` — languages-runtimes cell; LLVM/Mojo; performance-and-systems alignment, "make the fast thing accessible."
- **productive_conflict_with (real ROSTER.md slugs, abstraction/bloat axis):**
  - `martin-fowler` — architecture-testing-craft; patterns, refactoring, abstraction-as-design. Carmack: "kill an abstraction today." Direct philosophical tension.
  - `dhh` — architecture-testing-craft; though both are monolith-and-anti-microservice allies, DHH champions Ruby (interpreted, framework-heavy Rails) — exactly the "interpreted microservice" world Carmack jabs at. Productive friction on the interpreted-vs-native and framework-vs-bare-metal axis.
  - `andrej-karpathy` — ai-assisted-coding / AI team; both bet on RL and embodiment, but Karpathy is bullish on LLMs/transformers as the path while Carmack ("we are not on the brink of AGI," "dominated by fashions") is skeptical of the scaling-transformer consensus and bets on Sutton-style RL + embodiment. Sharp, productive disagreement on AGI trajectory.

  (All four slugs verified present in `superintelligence/engineering/ROSTER.md`: fowler & dhh in architecture-testing-craft; karpathy cross-listed in ai-assisted-coding.)

---

## Corrections / assumptions logged

- **Assumption in task brief:** conflict candidates "abstraction-heavy architects like martin-fowler." Confirmed valid — Fowler is in ROSTER (architecture-testing-craft) and is a clean abstraction-axis foil. Kept.
- **Added** `dhh` and `andrej-karpathy` as conflict slugs for sharper, real coverage (interpreted/framework axis and AGI-trajectory axis respectively); both are real ROSTER slugs.
- **Dating correction:** the famous "older hardware / monolithic native" tweet is **2025-05-12**, which is *before* the 2025-05-30 recency boundary — Slashdot's 25/05/13 story is a next-day write-up. I therefore did NOT count it as one of the three required post-2025-05-30 recent signals; it is used as a `public_stance` anchor instead. The three+ qualifying recent signals are the Upper Bound video (2025-06-16), Venture Dallas (2025-10-30), the D CEO interview (2025-11-19), and the "not on the brink of AGI" post (2026-03-14).
- **AGI timeline nuance:** Carmack's "2030 prototype / signs of life" goal (with Sutton) is a research milestone, NOT a claim that full AGI arrives in 2030. His 2026 posture ("we are not on the brink") is a deliberate recalibration against industry hype, not a reversal of the 2030 research target. Both framings are consistent.

---

## All URLs collected

- https://en.wikipedia.org/wiki/John_Carmack
- https://x.com/ID_AA_Carmack/status/1560728042959507457 (Keen $20M raise announcement)
- https://x.com/ID_AA_Carmack/status/1925710474366034326 (Upper Bound 2025 slides + notes)
- https://x.com/ID_AA_Carmack/status/1934720628306636986 (Upper Bound 2025 video)
- https://x.com/ID_AA_Carmack/status/1922100771392520710 (older-hardware / monolithic native tweet)
- https://www.amii.ca/videos/keen-technologies-research-directions-john-carmack-upper-bound-2025
- https://www.amii.ca/updates-insights/john-carmack-and-rich-sutton-agi
- https://www.dmagazine.com/business-economy/2025/11/conversation-with-john-carmack-keen-technologies/
- https://www.webpronews.com/john-carmacks-blunt-verdict-on-ai-progress-we-are-not-on-the-brink-of-agi/
- https://tech.slashdot.org/story/25/05/13/1321259/carmack-world-could-run-on-older-hardware-if-software-optimization-was-priority
- https://dallasinnovates.com/agi-and-de-extinction-john-carmack-and-ben-lamm-join-venture-dallas-2025-lineup/
- https://dallasinnovates.com/theres-so-much-energy-in-our-space-innovators-investors-invigorate-sold-out-2025-venture-dallas-conference/
- https://lexfridman.com/john-carmack/
- http://www.sevangelatos.com/john-carmack-on/
- https://news.ycombinator.com/item?id=44070042 (Upper Bound 2025 HN discussion)
- https://www.slideshare.net/slideshow/john-carmack-s-slides-from-his-upper-bound-2025-talk/279574649
