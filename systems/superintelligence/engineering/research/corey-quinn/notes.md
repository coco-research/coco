# Corey Quinn — Research Notes

**Researched:** 2026-05-30
**Slug:** corey-quinn
**Cell:** finops-cost (lead-driver)
**Team:** engineering-super-intelligence (home_team: engineering)

These are dated raw findings, direct quotes, and source URLs gathered for the
persona profile. Saved so future re-syntheses do not re-crawl.

---

## Identity confirmation (high confidence, 1.0)

Corey Quinn is unambiguously identified. He is the founder and Chief Cloud
Economist of Duckbill (formerly "The Duckbill Group"), an AWS-cost consultancy
he co-founded with Mike Julian in 2019. He authors the weekly *Last Week in AWS*
newsletter and hosts the *Screaming in the Cloud* and *AWS Morning Brief*
podcasts. He posts on X as @QuinnyPig. Lives in San Francisco with his spouse
and daughters. No identifier ambiguity.

- Duckbill author page: https://www.duckbillhq.com/blog/author/cquinn/
- LinkedIn: https://www.linkedin.com/in/coquinn/
- Last Week in AWS about page: https://www.lastweekinaws.com/about/

---

## CORRECTION to the brief — log per instruction

The brief supplied the quote **"the AWS bill is the soul of the org."** I could
NOT verify this exact phrasing in any source via web search (queried it directly;
no hit). It appears to be a paraphrase or misremembering. I have **not** used it
as a verbatim quote in the profile.

Quinn's **actual, verifiable** canonical framings of the same idea are:

1. **"When you talk about AWS billing, you're talking about AWS architecture.
   Most folks don't recognize that they're the same thing."**
   — *The Key to Unlock the AWS Billing Puzzle is Architecture*, Last Week in AWS,
   2021-06-09.
   https://www.lastweekinaws.com/blog/the-key-to-unlock-the-aws-billing-puzzle-is-architecture/

2. **"All architecture is fundamentally about cost, and all cloud cost is
   fundamentally about architecture."** (same thesis, restated form)

3. **"The bill is the only single source of truth. Unfortunately, AWS doesn't
   have an inventory service — other than the bill itself."**
   — *Reader Mailbag: AWS Billing*, Last Week in AWS.
   https://www.lastweekinaws.com/blog/reader-mailbag-billing/

The profile's archetype line and stances are built on these verified quotes, not
the unverified "soul of the org" line. The *spirit* of the brief — that the bill
is the truest map of what an org has actually built — is faithfully captured by
quote (3): the bill is the single source of truth about the architecture.

---

## Biography / career (verified)

From the AWS Security blog's tongue-in-cheek profile ("Definitely not an AWS
Security Profile: Corey Quinn, a 'Cloud Economist' who doesn't work here"):

- **"I have a background in SRE-style work and finance."** — this is the origin
  of the "Cloud Economist" hybrid. He was a systems/SRE engineer before, with a
  finance side.
- ~A decade of hands-on AWS use across many environments.
- **"Blending those together into a made-up thing called 'Cloud Economics' made
  sense and focused on a business problem that I can help solve."** — he coined
  the term "Cloud Economist."
- Role definition (his words): identifying cost-saving opportunities, building
  spend predictions, allocating expenditure, and establishing cloud governance
  that maintains engineering efficiency.
- **"Somewhere along the way, I became something of a go-to resource for the
  community."**
- Source: https://aws.amazon.com/blogs/security/definitely-not-an-aws-security-profile-corey-quinn-a-cloud-economist-who-doesnt-work-here/

Duckbill founding:
- Co-founded with **Mike Julian** in **2019**. Julian on LinkedIn: "When Corey
  Quinn and I started the Duckbill Group…" Note the consultancy is now branded
  **"Duckbill"** (duckbillhq.com), formerly "The Duckbill Group."
- Source: https://www.duckbillhq.com/about/

---

## Core thesis: billing IS architecture (verified, 2021-06-09)

From *The Key to Unlock the AWS Billing Puzzle is Architecture* (2021-06-09):

- **"When you talk about AWS billing, you're talking about AWS architecture.
  Most folks don't recognize that they're the same thing."**
- **"Cost is virtually never a driver behind an application rewrite."** — savings
  come as a side effect of capability improvements, not as the goal.
- He identifies two failure modes in cost tooling: tools that assume "whatever's
  in the environment is correct," or tools that assume "everything needs
  rebuilding to achieve modest savings." Both ignore business constraints.
- **"It's the rare AWS announcement that doesn't have architecture
  repercussions."**
- Conclusion: cost optimization needs engineers/architects who grasp
  architectural trade-offs in business context, not finance-only experts.
- Source: https://www.lastweekinaws.com/blog/the-key-to-unlock-the-aws-billing-puzzle-is-architecture/

---

## AWS data-transfer / egress criticism (verified, ongoing)

- Quinn calls AWS data-transfer pricing **"cloud's Achilles' heel"** and says
  customers are **"paying 1998 prices for data transfer."**
- Has repeatedly called out the **Managed NAT Gateway** as egregiously expensive
  and AWS egress-to-internet pricing as **"deeply obnoxious."**
- Podcast: *How AWS is Still Egregiously Egressing* (AWS Morning Brief).
  https://www.lastweekinaws.com/podcast/aws-morning-brief/how-aws-is-still-egregiously-egressing/
- Blog: *AWS Data Transfer Charges: Ingress Actually Is Free*.
  https://www.lastweekinaws.com/blog/aws-data-transfer-charges-ingress-actually-is-free/
- Context: data transfer is the third-largest line item on the average AWS bill;
  for distributed architectures it can hit 30–40% of total spend.

X post (surfaced with a future-dated timestamp from the test environment, 2044;
treated as a real Quinn post but NOT used as a dated recent_signal because the
timestamp is implausible):
- **"I have spent my career decoding AWS pricing and this is genuinely one of the
  most aggressively complex things I've ever seen them publish. It's like they
  took data transfer pricing and said 'what if we added a tier system nobody
  asked for and made it change based on topology?'"**
- https://x.com/QuinnyPig/status/2044220187441016850

---

## CloudFront flat-rate pricing analysis (verified, 2026-02-24) — RECENT SIGNAL

From *The Complete Guide to CloudFront's Flat-Rate Pricing (And Who It Actually
Helps)*, Duckbill, by Corey Quinn, 2026-02-24:

- **"That's a 99.6% price reduction for bandwidth-heavy workloads."**
- **"AWS can afford to offer 50TB for $15 because they know you're not
  leaving."** (lock-in thesis)
- **"This is AWS finally meeting them where they are."**
- **"AWS finally made CloudFront pricing predictable. They just made the decision
  about which pricing model to use more complicated."**
- Central argument: the $15/mo-for-50TB Pro plan is genuine savings for
  bandwidth-heavy users but functions primarily as ecosystem lock-in; flat-rate
  simplifies the decision but masks the underlying egress cost structure vs
  alternatives like Cloudflare.
- Source: https://www.duckbillhq.com/blog/the-complete-guide-to-cloudfronts-flat-rate-pricing/

---

## "AWS in 2026: The Year of Proving They Still Know How to Operate" (verified, 2026-01-08) — RECENT SIGNAL

From the Last Week in AWS blog, 2026-01-08:

- **"AWS's competitive moat was never just the services; it was the operational
  expertise that let them run those services at a scale nobody else could
  match."**
- **"Internal documents reportedly show 69-81% 'regretted attrition' — meaning
  the people leaving are the ones Amazon desperately wanted to keep."**
- **"The October us-east-1 outage took a disturbing length of time to identify
  DynamoDB as the culprit and communicate that to customers."** Baseline he will
  judge AWS against in 2026: the ~75-minute diagnostic time.
- On Trainium: **"Project Rainier deployed nearly 500,000 Trainium2 chips with
  Anthropic, with a million on the horizon."** He will track Trainium adoption
  beyond Anthropic ("a small number of very large customers") as the test of the
  custom-silicon strategy.
- Source: https://www.lastweekinaws.com/blog/aws-in-2026-the-year-of-proving-they-still-know-how-to-operate/

---

## re:Invent 2025 interview, Stack Overflow blog (verified, 2025-12-19) — RECENT SIGNAL

From *Last week in AWS re:Invent with Corey Quinn*, Stack Overflow blog,
2025-12-19:

- **"AWS is focused, almost to its own detriment, on large enterprises."**
- **"Everyone is talking about AI. Everyone is selling AI. It is not that everyone
  is buying AI."**
- **"You can assume… that it'll get it right 80% of the time. So, what use cases
  are there where that 20% 'wrong' factor is going to not be disastrous?"**
- **"It writes like a middle manager, and part of the problem is that we start to
  think that it's, 'oh, it's like a person.'"**
- Earlier remark (TechTarget) on AWS talking about AI less at re:Invent: **"The
  fact that they talk about [AI] less is a strong signal that they actually know
  what they're up to now."**
- Source: https://stackoverflow.blog/2025/12/19/last-week-in-aws-re-invent-with-corey-quinn/

---

## Screaming in the Cloud — Simon Willison episode (verified, 2026-03-14) — RECENT SIGNAL

- Quinn hosts Simon Willison (Datasette, LLM CLI) on AI's realities vs hype,
  Willison's "lethal trifecta" of AI security risks, and a prediction of a major
  breach within six months. Aired ~2026-03-14.
- The podcast is weekly and ongoing through 2026 (e.g., an episode with AWS
  Senior PE David Yanacek on AWS's DevOps Agent autonomously diagnosing
  incidents; an episode with Tailscale CEO Avery Pennarun on networking + zero-
  click auth).
- Show hub: https://www.lastweekinaws.com/podcast/screaming-in-the-cloud/

---

## AWS marketing / service-naming snark (verified)

- **"Proposal: all AWS service names get a 30 second review from me before they
  ship. 'Route53?' 'Love it.' 'Snowball Edge?' 'Urban Dictionary both of those
  words.' 'Systems Manager Session Mana—wow that sounds terrible now that I hear
  it spoken aloud.' I'm here to help."**
  — X, 2018. https://x.com/quinnypig/status/1070451608050315264
- *The Future of AWS Marketing is a Good Story* — argues AWS marketing should ask
  what the user is trying to do and surface relevant options, instead of "Service
  With A Dumb Name lets you provision print servers in specific suburbs of
  Milwaukee."
  https://www.lastweekinaws.com/blog/the-future-of-aws-marketing-is-a-good-story/

---

## Figma $300k/day AWS bill take (verified, 2025-07)

- LinkedIn: *Figma's $300k Daily AWS Bill Isn't the Scandal You Think It Is* —
  Quinn argues a large absolute bill is not inherently a scandal; the question is
  whether the spend maps to value and architecture, not whether the number is big.
- https://www.linkedin.com/posts/coquinn_figmas-300k-daily-aws-bill-isnt-the-scandal-activity-7349211523438759938-okkE

---

## Roster cross-references (verified against ROSTER.md)

- **pairs_well_with:** `jr-storment` (FinOps Foundation, "Cloud FinOps"),
  `erik-peterson` (CloudZero CTO, cost-per-feature) — both in finops-cost cell.
  Also `mike-fuller` is in-cell. (Neither jr-storment nor erik-peterson built yet
  — same E5 wave — but they are valid ROSTER slugs.)
- **productive_conflict_with:** `werner-vogels` (AWS CTO) and `james-hamilton`
  (AWS distinguished engineer) — both EXIST in
  superintelligence/engineering/personas/. These are the natural AWS-insider
  foils to Quinn's outside-critic stance on cost/pricing. Verified present:
  `grep -l "slug: werner-vogels" / "slug: james-hamilton"` both hit.
- Cell siblings: corey-quinn, jr-storment, mike-fuller, erik-peterson.

---

## Notes on directory naming

The persona schema doc refers to `superintelligenceTeam/...` but the actual repo
tree uses `superintelligence/` (e.g.
`superintelligence/engineering/personas/`). Files written under the real
`superintelligence/engineering/` tree to match the existing cloud-architecture
personas.

---

## All source URLs

1. https://www.lastweekinaws.com/about/
2. https://www.duckbillhq.com/blog/author/cquinn/
3. https://www.linkedin.com/in/coquinn/
4. https://aws.amazon.com/blogs/security/definitely-not-an-aws-security-profile-corey-quinn-a-cloud-economist-who-doesnt-work-here/
5. https://www.lastweekinaws.com/blog/the-key-to-unlock-the-aws-billing-puzzle-is-architecture/
6. https://www.lastweekinaws.com/blog/reader-mailbag-billing/
7. https://www.lastweekinaws.com/blog/aws-in-2026-the-year-of-proving-they-still-know-how-to-operate/
8. https://stackoverflow.blog/2025/12/19/last-week-in-aws-re-invent-with-corey-quinn/
9. https://www.duckbillhq.com/blog/the-complete-guide-to-cloudfronts-flat-rate-pricing/
10. https://www.lastweekinaws.com/podcast/screaming-in-the-cloud/
11. https://www.lastweekinaws.com/podcast/aws-morning-brief/how-aws-is-still-egregiously-egressing/
12. https://www.lastweekinaws.com/blog/aws-data-transfer-charges-ingress-actually-is-free/
13. https://x.com/quinnypig/status/1070451608050315264
14. https://x.com/QuinnyPig/status/2044220187441016850
15. https://www.lastweekinaws.com/blog/the-future-of-aws-marketing-is-a-good-story/
16. https://www.linkedin.com/posts/coquinn_figmas-300k-daily-aws-bill-isnt-the-scandal-activity-7349211523438759938-okkE
