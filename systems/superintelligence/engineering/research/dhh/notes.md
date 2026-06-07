# DHH — Research Notes

**Subject:** David Heinemeier Hansson (DHH)
**Slug:** dhh
**Researched:** 2026-05-30
**Researcher:** engineering-super-intelligence build (Wave E8, architecture-testing-craft)
**Method:** WebSearch + WebFetch against primary sources (world.hey.com, dhh.dk, rubyonrails.org) and secondary coverage (Wikipedia, The Register, DataCenterDynamics, Lex Fridman transcript).

---

## Identity confirmation

High confidence (0.97). Single, unambiguous public figure. Creator of Ruby on Rails (2004), co-owner and CTO of 37signals (Basecamp, HEY), creator of Omarchy Linux, co-author of *Rework* / *Remote* / *It Doesn't Have to Be Crazy at Work* / *Getting Real* with Jason Fried. No identity disambiguation needed.

### Biographical anchors (Wikipedia, verified 2026-05-30)
- Born October 15, 1979, Copenhagen, Denmark. Danish national, long resident in the United States (Chicago / Marbella).
- Created Ruby on Rails in 2004, extracted from Basecamp; open-sourced separately in 2004.
- Partner and CTO at 37signals (formerly Basecamp).
- Books: *Agile Web Development with Rails* (2005, with Dave Thomas et al.), *Getting Real*, *Rework* (2010), *Remote: Office Not Required* (2013), *It Doesn't Have to Be Crazy at Work* (2018) — the last three with Jason Fried.
- Racing: 24 Hours of Le Mans competitor since 2012; ALMS Rookie of the Year 2012; FIA World Endurance Championship; class win at Le Mans (LMGTE Am, 2014, with Aston Martin). Roster brief says "Le Mans class-winning racing driver" — confirmed.
- Awards: Google/O'Reilly "Hacker of the Year" 2005; Jolt Award for Rails 1.0 (2006).
- Shopify board member (confirmed in dhh.dk self-description; Shopify connection reinforced by his Dec 1 2025 post "Six billion reasons to cheer for Shopify").
- URL: https://en.wikipedia.org/wiki/David_Heinemeier_Hansson

**Correction to brief's framing:** The task brief described several items as currently "very active." Verified actuals:
- "TDD is dead" is from **2014**, NOT recent. It remains a load-bearing *canonical* stance, but it is not a recent signal. Logged as canonical/public stance, not recent_signal.
- The TypeScript-removal-from-Turbo event is from **September 6, 2023**, NOT 2024. The brief said "anti-TypeScript ... 2024." Corrected to 2023. The exact phrase "TypeScript is rotting" does not appear in the primary post; the actual wording is "I've never been a fan" and "things that should be easy become hard, and things that are hard become `any`." Logged accurately.
- "We have left the cloud" is from **June 23, 2023**. The *cloud-exit cost-savings updates* (the ~$2M/yr and the S3/Pure Storage data-egress milestone) are from **2024–2025** and ARE recent enough; The Register coverage is May 9, 2025. So cloud-repatriation IS a live 12-month signal via the 2025 savings reporting, even though the original exit post is 2023.

---

## Cloud repatriation / "Leaving the Cloud"

- **"We have left the cloud"** — world.hey.com, **June 23, 2023**. Direct quotes:
  - "The last application was brought home to our own hardware on Wednesday. Hallelujah!"
  - "We'll save at least $1.5 million per year by owning our own hardware rather than renting it from Amazon."
  - "The benefits [of cloud] have been vastly overstated. The cloud is often just as complicated as running things yourself, and it's usually ridiculously more expensive."
  - URL: https://world.hey.com/dhh/we-have-left-the-cloud-251760fb
- **2024–2025 savings reporting** (The Register, May 9, 2025; DataCenterDynamics):
  - 37signals estimates it saved ~$2 million on its cloud bill in 2024 after repatriation, dropping its annual cloud bill from $3.2M to $1.3M.
  - Final phase = exiting S3 / data storage; expects a further ~$1.3M/yr saved, deleting the AWS account entirely once the ~$1.5M/yr S3 bill is gone.
  - Total projected savings well over $10M across five years. Spent ~$700K on Dell servers (compute) and ~$1.5M on Pure Storage (data).
  - URLs:
    - https://www.theregister.com/2025/05/09/37signals_cloud_repatriation_storage_savings/
    - https://www.datacenterdynamics.com/en/news/37signals-claims-it-saved-almost-2m-last-year-from-cloud-repatriation/
- Basecamp "Cloud Exit" landing page: https://basecamp.com/cloud-exit

**Conflict vectors:** This is the core node against **werner-vogels** (AWS CTO — "everything fails all the time," cloud-native gospel) and partially aligned-but-distinct from **corey-quinn** (Quinn agrees cloud billing is absurd and egress is a racket, but argues repatriation is right for very few companies and that DHH over-generalizes from 37signals' steady-state, predictable workload). The DHH-vs-Quinn relationship is "violent agreement on the disease, disagreement on the cure" — a productive_conflict, not a pure pairing.

---

## The Majestic Monolith / anti-microservices

- **"The Majestic Monolith"** — Signal v. Noise / Medium, **2016**.
  - "A majestic monolith ... collapses as many unnecessary conceptual models as possible and eliminates as much needless abstraction as you can swing a hammer at."
  - Core claim: for a small team (~12–20 engineers) on a focused product, the operational overhead of microservices is pure waste; the vast majority of systems are better served starting and staying a monolith.
  - URL: https://signalvnoise.com/svn3/the-majestic-monolith/ and https://medium.com/signal-v-noise/the-majestic-monolith-29166d022228
- **"The Majestic Monolith can become The Citadel"** — Signal v. Noise. The Citadel = monolith at the center + a small set of "Outposts" extracting narrow slices. URL: https://signalvnoise.com/svn3/the-majestic-monolith-can-become-the-citadel/
- **"How to recover from microservices"** — world.hey.com (more recent essay). URL: https://world.hey.com/dhh/how-to-recover-from-microservices-ce3803cc

**Conflict vectors:** Against **sam-newman** ("Building Microservices," the canonical pro-microservices text) and **martin-fowler** (microservices coined/popularized via martinfowler.com; though Fowler's "MonolithFirst" is closer to DHH than Newman's). Productive_conflict with both.

---

## TDD is dead

- **"TDD is dead. Long live testing."** — dhh.dk, **2014**. Followed his RailsConf 2014 opening keynote.
  - Argues TDD as commonly practiced produces "test-induced design damage" — excessive indirection (hexagonal Rails, heavy mocking) to make units fast/isolated.
  - Credits TDD with showing him "the tranquility of a well-tested code base" but calls test-first "training wheels" he has left behind. He is pro-*testing*, anti-*test-first-as-dogma*.
  - URL: https://dhh.dk/2014/tdd-is-dead-long-live-testing.html
- Triggered the **"Is TDD Dead?"** series of recorded conversations hosted by **martin-fowler** with **kent-beck** and DHH. Fowler noted DHH's critique assumed heavy mocking, which isn't intrinsic to TDD.
  - URL: https://martinfowler.com/articles/is-tdd-dead/

**Conflict vectors:** Direct, named, on-the-record debate against **kent-beck** (inventor of TDD). This is the single richest, most literal conflict node — they sat across a table for it. Productive_conflict_with kent-beck is mandatory and well-cited.

---

## Anti-TypeScript

- **"Turbo 8 is dropping TypeScript"** — world.hey.com, **September 6, 2023**.
  - "I've never been a fan. Not after giving it five minutes, not after giving it five years."
  - "TypeScript just gets in the way of that for me. Not just because it requires an explicit compile step, but because it pollutes the code with type gymnastics that add ever so little joy to my development experience, and quite frequently considerable grief."
  - "Things that should be easy become hard, and things that are hard become `any`. No thanks!"
  - URL: https://world.hey.com/dhh/turbo-8-is-dropping-typescript-70165c01
- Sparked major community backlash; the removal PR was unpopular with Turbo users/contributors. HN thread: https://news.ycombinator.com/item?id=37430401

**Conflict vectors:** Against **anders-hejlsberg** (creator of TypeScript) — strongest type-systems opponent. Also tension with **guillermo-rauch** (Vercel/Next.js ecosystem is TypeScript-first and serverless-first — double conflict: types AND serverless/cloud). Note: brief specifically requested guillermo-rauch on serverless; that holds — Rauch's Next.js + Vercel edge/serverless model is the antithesis of DHH's "own your hardware, no PaaS" stance.

---

## Omarchy (Linux)

- **"Omarchy is out"** — world.hey.com, around **June 26, 2025** (initial public release June 26, 2025; X announcement June 26 2025).
  - URLs: https://world.hey.com/dhh/omarchy-is-out-4666dd31 ; https://x.com/dhh/status/1938369883617861849
- Omarchy = opinionated Arch Linux + Hyprland tiling compositor, keyboard-first, preconfigured dev environment. Version 2.0 Aug 26 2025; 3.3.0 Jan 7 2026; 3.4.0 Feb 26 2026.
- **"All-in on Omarchy at 37signals"** — world.hey.com, **August 9, 2025**. 37signals migrating entire Ops + Ruby teams to Omarchy over ~3 years as hardware is replaced. Motivation: Docker runs natively on Linux (no macOS virtualization overhead); HEY test suite ~2x faster on a Framework Desktop (Linux) than on Apple M4 Max. Goal: new dev deploys to Basecamp/HEY in 15 minutes.
  - URL: https://world.hey.com/dhh/all-in-on-omarchy-at-37signals-68162450
- **"A petabyte worth of Omarchy in a month"** — world.hey.com, **October 16, 2025**. ~150,000 installs / a petabyte of ISOs served in 30 days; Discord >6,000 members.
- **"Panther Lake is the real deal"** — world.hey.com, **April 6, 2026**. Dell XPS 14 on Intel Panther Lake hitting ~1.4W idle on Omarchy.
- The New Stack coverage: https://thenewstack.io/what-is-omarchy-linux-and-why-is-37signals-moving-to-it/

---

## Rails 8 — "No PaaS Required"

- **Rails 8.0 final** — rubyonrails.org, **November 7, 2024** (beta1 Sept 27 2024).
  - Theme: "No PaaS Required." Ships the **Solid trifecta** (Solid Queue, Solid Cache, Solid Cable — database-backed adapters that remove Redis dependency for most users; Solid Queue runs 20M jobs/day for HEY), plus **Kamal 2** + **Thruster** for deploying to a bare Linux box in ~2 minutes, and **SQLite production-readiness**.
  - "Disks have gotten fast enough that RAM isn't needed for as many tasks."
  - URL: https://rubyonrails.org/2024/11/7/rails-8-no-paas-required
- This is the technical embodiment of the cloud-exit and anti-PaaS thesis: own your box, deploy with one command, no managed-service rent.

---

## AI / vibe coding

- **Lex Fridman Podcast #474** — released **July 2025** (~6 hours). "DHH: Future of Programming, AI, Ruby on Rails, Productivity & Parenting."
  - Embraces AI for drafting and API lookup but insists on hands-on coding to keep skill and joy.
  - On vibe coding: it is learning "in this superficial way that feels like learning but is completely empty calories."
  - "What it's made more fun to me is to be a beginner again." Says he could ship an iOS app "by the end of the week" with AI help despite years away from iOS.
  - URLs: https://lexfridman.com/dhh-david-heinemeier-hansson/ ; transcript https://lexfridman.com/dhh-david-heinemeier-hansson-transcript ; coverage https://thenewstack.io/dhh-on-ai-vibe-coding-and-the-future-of-programming/
- Blog posts 2025–2026 on AI: "Give me AI slop over human sludge any day" (Oct 7 2025); "Promoting AI agents" (Jan 7 2026); "Basecamp becomes agent accessible" (Mar 25 2026); "Clankers with claws" (Feb 5 2026); "Local LLMs are how nerds now justify a big computer they don't need" (Nov 25 2025).

---

## Controversies (2025) — material for blind_spots / voice, not technical stances

- Long-running political conflict. Roots in the **2022 Basecamp** internal-politics blowup ("no societal/political discussions at work" policy; ~1/3 of staff departed). DHH's framing: "You are the person you are complaining about."
- 2025: DHH posted increasingly political content (anti-DEI, anti-immigration, free-speech-absolutist). Sept 2025 posts include "Calling someone a 'nazi' is a permission slip for violence" (Sept 24), "Words are not violence" (Sept 11), expressed support for Tommy Robinson / anti-immigration protests.
- **Ruby community fallout:** Sidekiq (a major Ruby Central sponsor) pulled funding after DHH was invited to RailsConf 2025; calls for his removal from Rails governance; some RubyGems/Rails maintainers stepped away. Framework's sponsorship of Hyprland/Omarchy triggered a 1700+-comment backlash.
  - URLs: https://tekin.co.uk/2025/09/the-ruby-community-has-a-dhh-problem ; https://www.theregister.com/2025/10/14/framework_linux_controversy/ ; https://blogs.gnome.org/alatiera/2025/11/06/dhh-and-omarchy-midlife-crisis/

**Note for persona:** This is a *software-engineering* thought-leadership roster. The political controversies are logged here for completeness and feed the blind_spots field (his willingness to alienate the community his framework depends on, conflation of technical and political authority), but the persona's technical stances are kept distinct and are what the panel summons.

---

## Recent signals (post-2025-05-30) used in persona

| Title | Date | URL |
|---|---|---|
| Omarchy is out (initial public release) | 2025-06-26 | https://world.hey.com/dhh/omarchy-is-out-4666dd31 |
| Lex Fridman Podcast #474 (AI / vibe coding) | 2025-07 | https://lexfridman.com/dhh-david-heinemeier-hansson/ |
| All-in on Omarchy at 37signals | 2025-08-09 | https://world.hey.com/dhh/all-in-on-omarchy-at-37signals-68162450 |
| A petabyte worth of Omarchy in a month | 2025-10-16 | https://world.hey.com/dhh |
| Basecamp Five | 2026-05-26 | https://world.hey.com/dhh |
| Panther Lake is the real deal | 2026-04-06 | https://world.hey.com/dhh |

(Rails 8 "No PaaS Required" is Nov 7 2024 — just outside the strict 12-month window from 2026-05-30, so it is used as a canonical_work, not a recent_signal. The 2025 cloud-savings reporting (Register, May 9 2025) is also just inside/around the 12-month boundary and used as supporting evidence on the cloud stance rather than a headline recent_signal.)

---

## All URLs collected

- https://en.wikipedia.org/wiki/David_Heinemeier_Hansson
- https://dhh.dk/
- https://world.hey.com/dhh
- https://world.hey.com/dhh/we-have-left-the-cloud-251760fb
- https://world.hey.com/dhh/turbo-8-is-dropping-typescript-70165c01
- https://world.hey.com/dhh/all-in-on-omarchy-at-37signals-68162450
- https://world.hey.com/dhh/omarchy-is-out-4666dd31
- https://world.hey.com/dhh/how-to-recover-from-microservices-ce3803cc
- https://dhh.dk/2014/tdd-is-dead-long-live-testing.html
- https://martinfowler.com/articles/is-tdd-dead/
- https://signalvnoise.com/svn3/the-majestic-monolith/
- https://medium.com/signal-v-noise/the-majestic-monolith-29166d022228
- https://signalvnoise.com/svn3/the-majestic-monolith-can-become-the-citadel/
- https://rubyonrails.org/2024/11/7/rails-8-no-paas-required
- https://lexfridman.com/dhh-david-heinemeier-hansson/
- https://lexfridman.com/dhh-david-heinemeier-hansson-transcript
- https://thenewstack.io/dhh-on-ai-vibe-coding-and-the-future-of-programming/
- https://thenewstack.io/what-is-omarchy-linux-and-why-is-37signals-moving-to-it/
- https://www.theregister.com/2025/05/09/37signals_cloud_repatriation_storage_savings/
- https://www.datacenterdynamics.com/en/news/37signals-claims-it-saved-almost-2m-last-year-from-cloud-repatriation/
- https://basecamp.com/cloud-exit
- https://news.ycombinator.com/item?id=37430401
- https://tekin.co.uk/2025/09/the-ruby-community-has-a-dhh-problem
- https://www.theregister.com/2025/10/14/framework_linux_controversy/
- https://blogs.gnome.org/alatiera/2025/11/06/dhh-and-omarchy-midlife-crisis/
- https://x.com/dhh/status/1938369883617861849
</content>
</invoke>
