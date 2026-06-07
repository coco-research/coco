# Mike Fuller — research notes

**Research date:** 2026-05-30
**Slug:** mike-fuller
**Cell:** finops-cost (engineering team)
**Cell role:** specialist
**Status decision:** active (≥3 recent signals dated after 2025-05-30 confirmed — see below)

---

## Identity confirmation

Mike Fuller is unambiguously identified. He is the CTO of the FinOps Foundation
and the co-author (with J.R. Storment) of O'Reilly's *Cloud FinOps* — "the FinOps
book." There is no identity ambiguity: the brief's framing (Cloud FinOps co-author,
Atlassian origin, FOCUS spec, the engineering/automation side of FinOps) matches
the public record exactly.

- CTO, FinOps Foundation (current). Source: https://www.finops.org/about/staff/
  ("Mike Fuller … Chief Technology Officer").
- FOCUS governance: **Steering Committee Chair / Steering Committee member /
  Maintainer** of the FinOps Open Cost & Usage Specification (FOCUS). Source:
  https://focus.finops.org/about-focus/ — listed with title "FinOps Foundation, CTO"
  as a Steering Committee member and Maintainer, and as "Steering Committee Chair"
  in the staff section.
- Co-author, *Cloud FinOps* (1st ed. 2019/2020, 2nd ed. 2023). Sources:
  https://www.amazon.com/Cloud-FinOps-Collaborative-Real-Time-Decision/dp/1492098353
  https://www.finops.org/community/finops-book/

---

## Background (verified)

From the O'Reilly author bio (relayed via search; oreilly.com/pub/au/7842 returned
403 to direct fetch but bio content surfaced consistently across multiple sources)
and the *Cloud FinOps* "About the Authors":

- **Atlassian (Australia), >10 years, Principal Engineer on the cloud FinOps team.**
  Built and led a dedicated FinOps team (data engineers, analysts, FinOps
  practitioners). Key member in building Atlassian's **cloud center of excellence**
  (design, governance, implementation of best practices). In that role he managed
  cloud billing data from multiple cloud providers — the lived experience behind
  his later FOCUS work.
- **9 AWS certifications.** Bachelor's degree in computer science from the
  **University of Wollongong** (Australia).
- Presented at multiple **AWS re:Invent and AWS Summit** events on AWS Security
  and Cost Optimisation.
- Served on the FinOps Foundation **Technical Advisory Council (TAC)**; later a
  member of its **governing board**; now CTO.
- Source: https://www.oreilly.com/pub/au/7842 (bio text relayed via search),
  https://se-radio.net/2023/02/episode-550-j-r-storment-and-mike-fuller-on-cloud-finops-financial-operations/,
  https://www.oreilly.com/library/view/cloud-finops/9781492054610/colophon01.html

> NOTE / corrected assumption: The brief says "origin at Atlassian." Confirmed —
> Atlassian is where his FinOps practice originated. He was a *principal engineer*
> there (an IC engineering track role), which reinforces the brief's framing of him
> as "the engineering/automation side of FinOps" rather than the finance/operations
> side (that is more Storment's lane). Fuller is the engineer; Storment is the
> evangelist/operator. This is the key differentiator to preserve in the persona.

---

## FOCUS — the technical centerpiece

FOCUS (FinOps Open Cost & Usage Specification) is the open, vendor-agnostic spec
that defines a unified schema for technology billing data. It is Fuller's signature
technical artifact at the Foundation.

- Project kicked off 2023; **FOCUS 1.0 GA in June 2024**, with native support from
  major clouds. Source:
  https://www.prnewswire.com/news-releases/finops-open-cost-and-usage-specification-focus-1-0-is-generally-available-leading-clouds-launch-native-support-302176745.html
- Quote (Fuller, CTO): *"We are establishing FOCUS as the cornerstone lexicon of
  FinOps by providing an open-source, vendor-agnostic specification featuring a
  unified schema and language."* Source: FinOps Foundation / FOCUS launch coverage
  (https://focus.finops.org/what-is-focus/ and launch PR).
- **FOCUS 1.3 ratified by the Steering Committee 2025-12-04/05; launched
  2025-12-11.** New: Contract Commitments supplemental dataset, Split Cost
  Allocation columns (K8s pods, DB instances), Recency & Completeness dimensions
  (last-updated metadata + completeness flag), Service Provider / Host Provider
  columns replacing deprecated Provider / Publisher. Sources:
  https://www.finops.org/insights/introducing-focus-1-3/ (pub 2025-12-11, author
  Matt Cowsert),
  https://www.linuxfoundation.org/press/finops-foundation-launches-focus-1.3-to-deepen-cloud-and-saas-billing-transparency-announces-expanded-vendor-support-for-focus-1.2
- FOCUS spec maintained openly on GitHub:
  https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec (Fuller is a
  Maintainer/Steering Committee member). Foundation org repo:
  https://github.com/FinOps-Open-Cost-and-Usage-Spec/foundation

> NOTE: No direct Fuller quote was located in the FOCUS 1.3 launch materials
> themselves (those quote Storment). Fuller's authorship/leadership of FOCUS is
> attributed via the governance pages and his GitHub maintainer role, not a
> launch-day pull quote. Logged so the persona does not over-claim a specific 1.3
> quote.

---

## Recent signals (all dated AFTER 2025-05-30 — ≥3 confirmed)

1. **FinOps X 2025 Day 2 keynote — "FinOps for AI is just FinOps!"** (2025-06-04
   article; event early June 2025). Fuller's central message: all prior FinOps
   learning/experience applies to AI cost; build an *AI Scope* that serves your
   org's strategy; AI decisions span Data Center, SaaS, and cloud scopes; multiple
   optimization levers across the AI infrastructure stack. Source:
   https://www.finops.org/insights/finops-x-2025-day-2-keynote/
   Supporting coverage: https://www.computerweekly.com/blog/CW-Developer-Network/FinOps-X-Foundation-FinOps-for-AI-comes-before-AI-for-FinOps
   ("FinOps for AI comes before AI for FinOps").

2. **FOCUS 1.3 launch** (2025-12-11; ratified 2025-12-04). Fuller chairs the
   Steering Committee that ratified it. Source:
   https://www.finops.org/insights/introducing-focus-1-3/

3. **"Bringing Data Center into Modern FinOps Using FOCUS"** — authored by Mike
   Fuller, published **2026-04-03**. Core argument: integrate on-prem/hybrid data
   center into FinOps via pragmatic cost modeling + FOCUS alignment; don't wait for
   accounting-grade precision. Unit economics (per vCPU-hour, per GB-month) as the
   shared language; showback before chargeback; FOCUS as the unifier across cloud /
   SaaS / data center; incremental field population over immediate full conformance.
   Quotes he relays: *"Unit economics are incredibly important to good decision
   making. Otherwise, you're not dealing with good data."* (FinOps lead, large
   digital bank); *"I should see that shift. If not, I'm getting double bubble
   costs."* (practice lead, North American bank). Source:
   https://www.finops.org/insights/finops-for-data-center-focus/

4. **FOCUS Conformance Certification Program for data generators (2026).** Public
   sample data + conformance gap reports + native→FOCUS column mapping; validates
   FOCUS 1.2, with FOCUS 1.3 criteria due ahead of FinOps X (June 8-11, 2026).
   This is the engineering/automation push Fuller drives — making conformance
   machine-checkable and public. Sources:
   https://www.finops.org/certification-for-organizations/finops-certified-focus-conformant/
   https://www.finops.org/insights/focus-sandbox/ (FOCUS Sandbox — MySQL DB of
   anonymized real billing data from AWS/GCP/OCI/Azure; authored by Mike Fuller,
   pub 2024-12-11 — slightly older than the 12mo window but supports the
   conformance/automation theme).

> Recency bar MET: signals #1, #2, #3 are all dated after 2025-05-30, with #4 as
> supporting 2026 material. status:active is justified; no need for archetype.

---

## Direct/attributed quotes (for voice)

- *"FinOps for AI is just FinOps!"* — FinOps X 2025 Day 2 keynote.
  https://www.finops.org/insights/finops-x-2025-day-2-keynote/
- *"We are establishing FOCUS as the cornerstone lexicon of FinOps by providing an
  open-source, vendor-agnostic specification featuring a unified schema and
  language."* — FOCUS launch. https://focus.finops.org/what-is-focus/
- *"FOCUS defines clear requirements for providers to generate billing files in a
  single format, eliminating the complexity of data normalization."* — FOCUS
  Sandbox post. https://www.finops.org/insights/focus-sandbox/
- (Relayed in his data-center article) *"Unit economics are incredibly important to
  good decision making. Otherwise, you're not dealing with good data."*
  https://www.finops.org/insights/finops-for-data-center-focus/

---

## Pairs / conflicts (ROSTER.md verification)

finops-cost cell (ROSTER.md §5): corey-quinn, jr-storment, mike-fuller, erik-peterson.

- **pairs_well_with: jr-storment** — co-author of *Cloud FinOps*; Storment is
  Executive Director of FinOps Foundation, Fuller is CTO. Direct, decade-long
  collaboration. Confirmed real slug.
- **pairs_well_with: erik-peterson** — CloudZero CTO; cost-per-feature / unit
  economics. Aligns tightly with Fuller's unit-economics framing. Confirmed real
  slug.
- **productive_conflict_with: corey-quinn** — Duckbill; AWS billing snark.
  Quinn's stance is that the AWS bill is intentionally opaque and the answer is
  expert human interpretation + negotiation; Fuller's answer is an open *standard*
  (FOCUS) that removes the need for per-vendor expertise. Standard-vs-snark is a
  genuine productive tension. Confirmed real slug (ROSTER §5).
- **productive_conflict_with: dhh** (David Heinemeier Hansson, architecture-testing-craft
  §9) — DHH's "leaving the cloud" / repatriation thesis says the cloud premium is
  the problem and the fix is owning hardware. Fuller's data-center FOCUS work says
  the fix is *visibility and unit economics across* cloud AND on-prem, not a
  wholesale exit. Real, substantive conflict on the same subject (data-center
  economics). Confirmed real slug.

> Both productive-conflict slugs (corey-quinn, dhh) are verified present in
> ROSTER.md. jr-storment and erik-peterson confirmed as pairs per the brief and the
> finops-cost cell list.

---

## Sources (master list, all real URLs)

1. https://www.finops.org/about/staff/
2. https://focus.finops.org/about-focus/
3. https://www.finops.org/community/finops-book/
4. https://www.amazon.com/Cloud-FinOps-Collaborative-Real-Time-Decision/dp/1492098353
5. https://se-radio.net/2023/02/episode-550-j-r-storment-and-mike-fuller-on-cloud-finops-financial-operations/
6. https://www.finops.org/insights/finops-x-2025-day-2-keynote/
7. https://www.finops.org/insights/introducing-focus-1-3/
8. https://www.finops.org/insights/finops-for-data-center-focus/
9. https://www.finops.org/insights/focus-sandbox/
10. https://focus.finops.org/what-is-focus/
11. https://focus.finops.org/focus-specification/v1-3/
12. https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec
13. https://www.finops.org/certification-for-organizations/finops-certified-focus-conformant/
14. https://www.linuxfoundation.org/press/finops-foundation-launches-focus-1.3-to-deepen-cloud-and-saas-billing-transparency-announces-expanded-vendor-support-for-focus-1.2
15. https://www.computerweekly.com/blog/CW-Developer-Network/FinOps-X-Foundation-FinOps-for-AI-comes-before-AI-for-FinOps
16. https://www.prnewswire.com/news-releases/finops-open-cost-and-usage-specification-focus-1-0-is-generally-available-leading-clouds-launch-native-support-302176745.html
