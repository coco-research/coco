# Research Notes — Colm MacCárthaigh

**Slug:** `colm-maccarthaigh`
**Cell:** cloud-architecture (engineering team)
**Researched:** 2026-05-30
**Researcher:** registry-builder agent (Wave E1)

---

## Identity — CONFIRMED

Colm MacCárthaigh (Irish spelling; pronounced roughly "Colm Mc-Carthy") is a **Vice President and Distinguished Engineer at Amazon Web Services**, working on **EC2 Networking and cryptography**. Confirmed across LinkedIn, AWS Builders' Library author page, AWS Security Blog, and the AWS Podcast. Title progression visible across sources: he was "Senior Principal Engineer" in the 2019/2020 AWS Security Profiles interview and re:Invent listings, and is "VP / Distinguished Engineer" by 2024–2026 (LinkedIn, re:Invent 2025 session listings). No ambiguity — single, well-documented individual. Confidence in identity: very high.

- LinkedIn: https://www.linkedin.com/in/colmmacc/ (also https://www.linkedin.com/in/colmm1/)
- AWS Builders' Library author page: https://aws.amazon.com/builders-library/authors/colm-maccarthaigh/
- X handle: https://twitter.com/colmmacc — active, but X feeds are not directly crawlable by WebSearch/WebFetch in this environment. Individual tweet permalinks are citable where found.

## Career arc — CONFIRMED

- **Pre-AWS:** Early Internet / open-source work in Ireland. Member of the **Apache Software Foundation**; core contributor to **Apache httpd and APR (Apache Portable Runtime)**. (AWS Builders' Library bio; AWS Security Profiles interview.)
- **Joined AWS 2008** to help build **Amazon CloudFront**, then **Amazon Route 53**. (AWS Podcast #685; Builders' Library bio.)
- Worked across the largest AWS services: **EC2, S3, ELB, CloudFront, Route 53**.
- **Lead designer / Principal Engineer for AWS HyperPlane** — the engine powering Network Load Balancer, VPC NAT Gateway, VPC PrivateLink, EFS. (QCon NY 2019 speaker bio; LinkedIn.)
- **Main author of Amazon s2n / s2n-tls** — AWS's open-source C99 implementation of TLS/SSL, created in direct response to the **Heartbleed** vulnerability in OpenSSL (development started "literally the day after Heartbleed"). (Security Cryptography Whatever podcast; Builders' Library bio.) s2n handles TLS for, e.g., all of S3.
- Now **VP/DE — EC2 Networking + cryptography**; works on AWS **Nitro Enclaves** and network encryption; central technical figure on the **AWS European Sovereign Cloud**.
- Outside engineering: **Irish folk musician and singer** — tours, records albums, teaches workshops. First computer was a Commodore 64. (Builders' Library bio; Folk Stories podcast ep. 3.)

## Formal verification record — CONFIRMED via dblp

dblp PID 223/4997 (https://dblp.org/pid/223/4997.html):

1. **"Continuous Formal Verification of Amazon s2n"** — CAV 2018, pp. 430–446. Co-authors: Andrey Chudnov, Nathan Collins, Byron Cook, Joey Dodds, Brian Huffman, Stephen Magill, Eric Mertens, Eric Mullen, Serdar Tasiran, Aaron Tomb, Eddy Westbrook. Proves s2n implements a subset of TLS 1.2 (RFCs 5246, 5077, 6066) and that the socket-corking API is used correctly. Specs in **Cryptol**, code-spec proofs via **SAW (Software Analysis Workbench)**, wired into CI so properties stay proven over the software's lifetime.
   - https://link.springer.com/chapter/10.1007/978-3-319-96142-2_26
   - PDF: https://d1.awsstatic.com/Security/pdfs/Continuous_Formal_Verification_Of_Amazon_s2n.pdf
2. **"SideTrail: Verifying Time-Balancing of Cryptosystems"** — VSTTE 2018, pp. 215–228. Co-authors: Konstantinos Athanasiou, Byron Cook, Michael Emmi, Daniel Schwartz-Narbonne, Serdar Tasiran. (Verifying constant-time / timing-side-channel balancing — relevant to Lucky 13 mitigation in s2n.)
3. **"Restoring Uniqueness in MicroVM Snapshots"** — CoRR/arXiv 2021. Co-authors: Marc Brooker, Adrian Costin Catangiu, Mike Danilov, Alexander Graf, Andrei Sandu. (Firecracker/microVM snapshot RNG-uniqueness problem.)

Earlier AWS Security Blog posts:
- "Automated Reasoning and Amazon s2n" (2016-09-08)
- "s2n and Lucky 13" (2015-11-24)

## Canonical works (AWS Builders' Library) — CONFIRMED authorship

All four confirmed on the author page https://aws.amazon.com/builders-library/authors/colm-maccarthaigh/:

1. **"Workload isolation using shuffle-sharding"** — https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/ — shuffle sharding as a core multi-tenant blast-radius reduction technique. Companion site: https://shufflesharding.com/ . Architecture-blog companion: "Shuffle Sharding: Massive and Magical Fault Isolation."
2. **"Reliability, constant work, and a good cup of coffee"** — https://aws.amazon.com/builders-library/reliability-and-constant-work/ — the **constant-work** anti-fragility pattern (coffee-urn analogy; do the same amount of work regardless of load; avoid scaling/changing behaviour under stress). Used in Route 53 + NLB. Werner Vogels endorsed it: https://www.allthingsdistributed.com/2023/11/standing-on-the-shoulders-of-giants-colm-on-constant-work.html
3. **"Beyond five 9s: Lessons from our highest available data planes"** — lessons from Route 53 + AWS auth systems designed to survive cataclysmic failure, load spikes.
4. **"Amazon's approach to security during development"** — how AWS minimizes security risk in products and responds to issues.

**CORRECTION / wrong-assumption logged:** The famous Builders' Library article **"Timeouts, retries and backoff with jitter"** is authored by **Marc Brooker, NOT Colm MacCárthaigh** (verified by fetching the article page). Do NOT attribute it to Colm. (The shuffle-sharding / constant-work / exponential-backoff body of work is often conflated; Brooker owns timeouts-retries-jitter, MacCárthaigh owns shuffle-sharding + constant work. Both are in cloud-architecture cell.)

## Recent signals (post-2025-05-30) — 3 CONFIRMED, dates VERIFIED

1. **AWS European Sovereign Cloud launch** — 2026-01-15, Potsdam, Germany. Physically/logically separate, operated exclusively by EU residents in the EU; dedicated German legal entities; EU-citizen advisory board. MacCárthaigh is VP/DE — EC2 Networking and a central technical author on the sovereign-cloud trust/crypto story.
   - https://aws.amazon.com/blogs/aws/opening-the-aws-european-sovereign-cloud/
   - https://press.aboutamazon.com/aws/2026/1/aws-launches-aws-european-sovereign-cloud-and-announces-expansion-across-europe
2. **ALB Target Optimizer launch + re:Invent 2025 talk (NET336 "Load balancing evolved: ALB Target Optimizer")** — 2025-11-20. New ALB feature enforcing max concurrent requests per target via an AWS-provided agent + control channel; built for compute-/inference-heavy targets (as low as 1 request at a time); automatic load shedding. MacCárthaigh presented.
   - https://aws.amazon.com/about-aws/whats-new/2025/11/aws-application-load-balancer-target-optimizer/
   - https://www.youtube.com/watch?v=v--Pa6gNVQ0
3. **"Establishing a European trust service provider for the AWS European Sovereign Cloud"** — AWS Security Blog, 2025-07-10 (updated 2025-08-04 to add EU-resident citizenship requirements). Authored by Colm MacCárthaigh.
   - https://aws.amazon.com/blogs/security/author/colmmacc/

>=3 recent signals satisfied. All dates verified post-2025-05-30.

NOTE on X / AI-policy activity: The brief flagged he "is active on X about AI policy & infra." His X account (@colmmacc) is confirmed active and he is known for long technical threads (e.g. his 56-point mTLS critique to Istio/SPIFFE referenced on the SCW podcast), but specific dated 2025–2026 AI-policy tweets could not be individually crawled in this environment (X feeds not indexable by the available tools). I did NOT fabricate dated tweet citations. The three signals above are all blog/launch/talk artifacts with hard, verified dates, which clears the >=3 recent-signal bar without needing a tweet. If a future re-sync can crawl X, add 1–2 dated tweet permalinks on AI infra/policy.

## Stances + voice material — direct quotes (sources cited inline)

From **AWS Security Profiles interview** (https://aws.amazon.com/blogs/security/aws-security-profiles-colm-maccarthaigh-senior-principal-engineer/):
- "Be fully committed or get out of the way, but don't do anything in between."
- On simplicity: "I'm going to cover what simplicity means for us, and also talk about things we do that most customers would never need to do themselves."
- Favourite Leadership Principle: Ownership — "I love that we're empowered (and expected) to be owners at Amazon."
- Nitro Enclaves: "going to make it cheaper and easier for customers to isolate sensitive data. That's a big deal."

From **X** (https://x.com/colmmacc/status/986286693572493312):
- **"Security, durability, availability, speed. That's the priority order I think about for design trade-offs and it's never let me down. Simplicity and Cost are huge too but more like guiding principles."** — This is his single most-cited design heuristic. THE priority-order stance.

From **Security Cryptography Whatever** mTLS episode (https://securitycryptographywhatever.com/2021/12/29/the-feeling-s-mutual-mtls-with-colm-maccarthaigh/):
- s2n: "Development on S2N started literally the day after heartbleed."
- Crypto core function: "to turn meaningful signals into useless noise... to hide information in plain sight."
- mTLS skepticism: sent a "56 point detailed critique" to Istio/SPIFFE; "revocation has always been the stickiest problem in mTLS on both sides."
- State machines: **"Don't mix input parsing and changing state... separate those really clearly"** — his single most important bug-prevention rule.
- Memory safety in C: wrote "our own dialect of C, a pretty restricted dialect" using functional-programming techniques + extensive testing rather than declaring C unsafe.
- DNSSEC: "probably best described as a zombie right now. And it is the living dead." / 1024-bit keys took 10+ years to deploy; modern curves "would take over 20 years."
- X.509 parsing danger: found auth based on unanchored regex on cert string patterns (a CTO's assistant got admin because her title contained "admin").
- CBC vs GCM length-hiding: CBC "has a lot of positive properties... it's really defensive" against GCM nonce-reuse catastrophe; length hiding defends against real traffic-analysis attacks ("they can see what map you're looking at... what video you're watching").

From **"Reliability, constant work, and a good cup of coffee"** (https://aws.amazon.com/builders-library/reliability-and-constant-work/):
- The coffee-urn analogy: a system should do a constant amount of work no matter how many people want coffee.
- "Apply a full configuration each time in a loop" — constant-work config push.
- Robust AND cheap: "Storing a file in S3 and fetching it over and over in a loop, even from hundreds of machines, costs far less than the engineering time... building something more complex."

## Pairs / conflicts — against real ROSTER.md slugs

cloud-architecture cell: james-hamilton, werner-vogels, adrian-cockcroft, marc-brooker, brendan-burns, eric-brewer, colm-maccarthaigh, radia-perlman.

- **pairs_well_with:**
  - `marc-brooker` — same cell, co-author on the MicroVM-snapshots paper, both formal-methods-in-production advocates (Brooker = TLA+/lightweight formal methods, retries/timeouts; MacCárthaigh = SAW/Cryptol on s2n). Natural formal-methods pairing.
  - `bruce-schneier` (security cell) — applied crypto + security economics; both argue security is about economics and humility, not algorithms alone.
  - `werner-vogels` — Vogels publicly endorsed the constant-work pattern ("Standing on the shoulders of giants: Colm on constant work"); "everything fails all the time" is the same worldview as "design data planes to survive cataclysm."
  - `radia-perlman` — network-protocol design / robustness-by-construction kinship.
- **productive_conflict_with:**
  - `dhh` — DHH's "majestic monolith"/anti-cloud stance vs MacCárthaigh's deep multi-tenant managed-service worldview. Sharp, productive.
  - `matthew-green` — Green's academic-crypto-purist disclosure-and-correctness lens vs MacCárthaigh's ship-an-imperfect-but-survivable-MVP pragmatism (he openly calls TLS/TCP "imperfect MVPs that got locked in"). Genuine tension on "good enough" crypto engineering.

## Confidence

0.93 — identity certain, career/publication record fully corroborated, abundant first-person quotes for voice, four canonical works with confirmed authorship, three hard-dated recent signals. Slightly below 0.95 only because the X/AI-policy dimension (flagged in brief) could not be backed with dated tweet permalinks in this environment, and one wrong-assumption (timeouts-retries-jitter) had to be corrected out.

## Source URL inventory (>=8 real, >=3 recent)

1. https://aws.amazon.com/builders-library/authors/colm-maccarthaigh/
2. https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/
3. https://aws.amazon.com/builders-library/reliability-and-constant-work/
4. https://aws.amazon.com/blogs/security/aws-security-profiles-colm-maccarthaigh-senior-principal-engineer/
5. https://securitycryptographywhatever.com/2021/12/29/the-feeling-s-mutual-mtls-with-colm-maccarthaigh/
6. https://link.springer.com/chapter/10.1007/978-3-319-96142-2_26 (CAV 2018, Continuous Formal Verification of Amazon s2n)
7. https://dblp.org/pid/223/4997.html
8. https://x.com/colmmacc/status/986286693572493312 (priority-order stance)
9. https://aws.amazon.com/about-aws/whats-new/2025/11/aws-application-load-balancer-target-optimizer/ (RECENT, 2025-11-20)
10. https://www.youtube.com/watch?v=v--Pa6gNVQ0 (RECENT, re:Invent 2025 NET336)
11. https://aws.amazon.com/blogs/aws/opening-the-aws-european-sovereign-cloud/ (RECENT, 2026-01)
12. https://aws.amazon.com/blogs/security/author/colmmacc/ (RECENT post: trust service provider, 2025-07-10)
13. https://www.allthingsdistributed.com/2023/11/standing-on-the-shoulders-of-giants-colm-on-constant-work.html (Vogels endorsement)
14. https://github.com/aws/s2n-tls (s2n-tls repo)
