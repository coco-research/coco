# Alex Stamos — Research Notes

**Researched:** 2026-05-30
**Slug:** alex-stamos
**Cell:** security (engineering team) — cell_role: lead-driver
**Status:** active

---

## Corrected assumptions (logged per instruction)

The build brief described the subject as "SentinelOne Chief Trust/Security Officer." This is **stale as of 2026-05-30** and was corrected during research:

1. **Current primary role is NOT SentinelOne CISO/CTO.** Stamos joined **Corridor** — an AI code-security startup co-founded by ex-CISA staffers Jack Cable and Ashwin Ramaswami — as **Chief Security Officer in August 2025** after the company's $5.4M seed round (led by Conviction). He **remains at SentinelOne only as a strategic adviser**, not as CISO. (Axios, 2025-08-05; Wikipedia.)
2. **SentinelOne title history:** joined late 2023 as **Chief Trust Officer** via the SentinelOne acquisition of Krebs Stamos Group; **promoted to Chief Information Security Officer (CISO) on 2024-08-01**; transitioned to strategic-adviser status when he joined Corridor in Aug 2025. So the correct SentinelOne title was CISO (not "Chief Trust/Security Officer"), and it is now a past/advisory role.
3. **Stanford Internet Observatory (SIO) was largely wound down in 2024.** Stamos founded SIO in **August 2019** and stepped back as director in **November 2023** citing the toll of political/legal pressure. Reporting in June 2024 described SIO as being dismantled; Stanford disputed the "shut down due to pressure" framing but acknowledged funding exhaustion. Stamos **continues as a Stanford lecturer/adjunct** (CS and International Policy programs) but is no longer running SIO day-to-day.
4. **Pair slugs verified in ROSTER.md security cell:** `window-snyder`, `katie-moussouris` both present. Conflict slugs `matthew-green`, `bruce-schneier` both present. All four are real ROSTER entries.

**Net:** `affiliations_2026` should lead with **Corridor (CSO)**, then **SentinelOne (strategic adviser)**, then **Stanford (lecturer / adjunct professor)**. SIO founding/direction is a past affiliation.

---

## Confirmed biography

- **Education:** EECS (Computer Science & Engineering), UC Berkeley, 2001. Grew up in Fair Oaks, CA; Bella Vista High School 1997.
- **Early career:** security consultant at @stake; systems engineer at Loudcloud (2001–2004).
- **iSEC Partners (2004–2010):** co-founded with Joel Wallenstrom, Himanshu Dwivedi, Jesse Burns, Scott Stender. Acquired by NCC Group, Oct 2010.
- **Artemis Internet / NCC Group (2010–2014):** CTO; five patents on secure-domain standards (.trust gTLD).
- **Yahoo! CSO (2014 – June 2015):** resigned after leadership complied with classified government demand to scan customer email for intelligence agencies.
- **Facebook / Meta CSO (2015 – August 2018):** led the team that surfaced ~$100K of Russian-linked ad spend (Sept 6, 2017, covering June 2015–May 2017). Departed amid internal disagreement over how aggressively to disclose Russian disinformation around the 2016 election.
- **Stanford (Aug 2019 – present):** founded the **Stanford Internet Observatory**; adjunct professor at CISAC; visiting scholar at the Hoover Institution; **lecturer** in CS and the MA International Policy program (continuing).
- **Krebs Stamos Group (2021):** co-founded with former CISA director Chris Krebs; first client SolarWinds. Acquired by SentinelOne, late 2023.
- **SentinelOne:** Chief Trust Officer (2023) → CISO (2024-08-01) → strategic adviser (2025).
- **Corridor (Aug 2025 – present):** Chief Security Officer. Corridor uses AI to discover software vulnerabilities and triage bug-bounty reports, including context-heavy authorization flaws. Customers include Cursor, Mercury, GreyNoise. Co-founders Jack Cable (CEO) and Ashwin Ramaswami; both ex-CISA Secure-by-Design.

---

## Canonical works / institutional builds

- **Stanford Internet Observatory (SIO)** — founded Aug 2019. Cross-disciplinary program to study online abuse in real time. https://cyber.fsi.stanford.edu/io/people/alex-stamos (redirects to tip.fsi.stanford.edu)
- **Trust & Safety Engineering course** — first taught Stanford CS, Fall 2019 quarter. First academic course of its kind on consumer-internet abuse and engineering/product responses.
- **Journal of Online Trust and Safety** — inaugural issue Oct 28, 2021; launched out of SIO. Stamos a founding force.
- **Stanford Trust and Safety Research Conference** — organizer.
- **Election Integrity Partnership (EIP)** — formed July 2020; SIO + UW Center for an Informed Public + Graphika + Atlantic Council DFRLab. Stamos led a 100+ researcher real-time effort documenting 2020 US election mis/disinformation. Final report March 2021.
- **Facebook "Information Operations and Facebook" white paper** (2017) — co-authored with Jen Weedon and Will Nuland on social-media election attacks.
- **"Can AI Write Persuasive Propaganda?"** — co-authored SIO research on generative-AI propaganda.
- **Aspen Commission on Information Disorder** — member.
- **Aspen Digital US Cybersecurity Group** — member.

---

## Recent signals (all dated AFTER 2025-05-30)

1. **2025-08-05 — Joins Corridor as CSO.** Axios. "AI is driving a wave of transformation unlike anything he's seen in his 25 years in the field — and creating an enormous gap between how code is written and how it's secured." On vibe-coders: "These people have no idea how the software works. And so it is completely impossible for them to understand then how it can be broken." https://www.axios.com/2025/08/05/corridor-ai-startup-alex-stamos
2. **2025-12-11 — Persuasion interview "Alex Stamos on the Real Threat Posed by AI."** Argues near-term AI computer-security threats are "much more dangerous and urgent" than the "existential" risks many fear. https://www.persuasion.community/p/alex-stamos-on-the-real-threat-posed
3. **2026-03-27 — RSAC 2026 panel (with Kevin Mandia, Morgan Adamski), reported by CyberScoop.** "The exploit discovery has gone exponential." "It's quite possible that all this development we've done in memory-unsafe languages, without formal methods, that none of that is actually secure in the presence of superintelligent bug-finding machines." "You're going to have every 19-year-old in St. Petersburg with the same capability." "Patch Tuesday, exploit Wednesday." "Two years if we're good… the minimum if we actually start really fixing code and refactoring stuff into type-safe languages using formal methods." Defenders can't patch their way out; prioritize defense-in-depth, block lateral movement / persistence. https://cyberscoop.com/ai-cyberattacks-two-years-insane-vulnerabilities-kevin-mandia-alex-stamos-morgan-adamski-rsac-2026/
4. **2026-04-17 — Coalition "Defending Against Superhuman Intelligence with Alex Stamos" (Activate 2026).** "Anyone that says they know exactly what the future of security looks like is trying to sell you something." "AI is completely revolutionizing the practice of cybersecurity, both defense and offense." "This is a bug in the Linux kernel that is older than a bunch of my coworkers." "You can take out all the safety parameters with a technique called obliteration, which is like brain surgery on an open-weight model." "We're automating all the entry-level jobs that bring people into security in the first place." "You have to assume that your system can be breached and that you can survive it." "You can't lose what you don't have." https://www.coalitioninc.com/blog/cyber-insurance/alex-stamos-activate-2026
5. **2026-04-11 — NPR "How AI is getting better at finding security holes."** Context piece on AI vulnerability discovery (Anthropic Project Glasswing / Mythos) quoting Stamos as CSO of Corridor: "LLMs have now bypassed human capability for bug finding." https://www.npr.org/2026/04/11/nx-s1-5778508/anthropic-project-glasswing-ai-cybersecurity-mythos-preview

---

## Public stances (each with evidence URL)

- **Strong encryption; no backdoors.** Feb 2015, New America conference, publicly challenged NSA Director Mike Rogers. Likened a government backdoor to "drilling a hole in the windshield" — a narrow entry undermines the whole shield. Asked whether, once forced to build backdoors, the US would then have to grant Russia and China the same access. https://www.theregister.com/2015/02/25/nsa_boss_encryption_backdoors/ ; https://slate.com/technology/2015/02/yahoo-s-alex-stamos-and-nsa-s-mike-rogers-fight-about-encryption.html
- **Calibrated, evidence-based trust & safety — NOT remove-at-any-cost.** "Since 2016 there's been a belief that any disinformation activity is immediately impactful and should be stopped at almost any cost… that's not how to handle abuse. We need to really understand how these abuses work and their impact so we can calibrate our responses." (FSI / SIO.) https://fsi.stanford.edu/news/stanford-internet-observatory-seeks-detect-internet-abuse-real-time
- **Near-term AI security threats outrank existential risk.** Persuasion, Dec 2025. https://www.persuasion.community/p/alex-stamos-on-the-real-threat-posed
- **AI gives attackers an asymmetric advantage in bug finding; defenders must shift to resilience.** Coalition Activate 2026. https://www.coalitioninc.com/blog/cyber-insurance/alex-stamos-activate-2026
- **Memory-unsafe code at scale may be indefensible against superhuman bug finders; refactor to type-safe languages + formal methods.** RSAC 2026. https://cyberscoop.com/ai-cyberattacks-two-years-insane-vulnerabilities-kevin-mandia-alex-stamos-morgan-adamski-rsac-2026/
- **Trust & safety is an engineering discipline, not just policy** — founded the first university Trust & Safety Engineering course and the Journal of Online Trust and Safety. https://www.aspendigital.org/person/alex-stamos/

---

## Pairing / conflict rationale

- **pairs_well_with:**
  - `window-snyder` — both are operator-CSOs who treat security as product engineering (firmware/IoT for Snyder; platform trust & safety for Stamos). Shared "secure-by-design / shift-left" worldview.
  - `katie-moussouris` — disclosure-policy and bug-bounty/VDP design overlaps directly with Corridor's bug-triage mission and Stamos's responsible-disclosure operator instincts.
- **productive_conflict_with:**
  - `matthew-green` — both pro-strong-encryption, but Stamos lived the operator's tension: as a platform CSO he had to weigh E2E encryption against trust & safety / CSAM detection and content moderation at scale. Green is closer to an encryption near-absolutist / skeptic of client-side scanning. The friction is *encryption-vs-platform-safety* — where the line sits when a platform must both protect privacy and police abuse. (Stamos NSA-backdoor stance: theregister.com link above.)
  - `bruce-schneier` — Schneier frames security largely through policy, economics, and structural power; Stamos is the in-the-arena operator who has run security at hyperscale and now ships an AI product. They sharpen each other on whether the fix is governance/regulation (Schneier) or operational engineering and resilience (Stamos).

---

## Sources (>=8, real URLs)

1. https://en.wikipedia.org/wiki/Alex_Stamos
2. https://www.axios.com/2025/08/05/corridor-ai-startup-alex-stamos
3. https://www.sentinelone.com/press/sentinelone-names-alex-stamos-chief-information-security-officer/
4. https://cyberscoop.com/ai-cyberattacks-two-years-insane-vulnerabilities-kevin-mandia-alex-stamos-morgan-adamski-rsac-2026/
5. https://www.coalitioninc.com/blog/cyber-insurance/alex-stamos-activate-2026
6. https://www.npr.org/2026/04/11/nx-s1-5778508/anthropic-project-glasswing-ai-cybersecurity-mythos-preview
7. https://www.persuasion.community/p/alex-stamos-on-the-real-threat-posed
8. https://www.theregister.com/2015/02/25/nsa_boss_encryption_backdoors/
9. https://www.platformer.news/stanford-internet-observatory-shutdown-stamos-diresta-sio/
10. https://en.wikipedia.org/wiki/Stanford_Internet_Observatory
11. https://fsi.stanford.edu/news/stanford-internet-observatory-seeks-detect-internet-abuse-real-time
12. https://www.aspendigital.org/person/alex-stamos/
13. https://slate.com/technology/2015/02/yahoo-s-alex-stamos-and-nsa-s-mike-rogers-fight-about-encryption.html
14. https://www.npr.org/2024/06/14/g-s1-4570/a-major-disinformation-research-teams-future-is-uncertain-after-political-attacks
