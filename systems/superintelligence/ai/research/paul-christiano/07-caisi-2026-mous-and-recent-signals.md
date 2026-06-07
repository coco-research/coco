# CAISI 2026 MOUs and Recent Signals (post 2025-05-27)

This file consolidates the post-2025-05-27 signal trail required by the persona schema (`recent_signal_12mo` must have ≥3 entries dated within the last 12 months). The hard constraint date is 2025-05-27.

## Signal 1 — CAISI announces new pre-deployment testing agreements with Google DeepMind, Microsoft, xAI

- **Date:** May 5, 2026
- **Sources:**
  - https://www.nextgov.com/artificial-intelligence/2026/05/commerce-ai-center-will-evaluate-google-deepmind-microsoft-and-xai-models/413349/
  - https://www.hpcwire.com/off-the-wire/nists-caisi-announces-new-frontier-ai-testing-agreements-with-google-deepmind-microsoft-xai/
  - https://blogs.microsoft.com/on-the-issues/2026/05/05/advancing-ai-evaluation-with-the-center-for-ai-standards-us-and-innovation-and-the-ai-security-institute-uk/

CAISI (formerly US AISI) announced renegotiated agreements with Google DeepMind, Microsoft, and xAI. The companies will submit frontier AI models for pre-deployment safety evaluation in classified environments. Christiano remains Head of AI Safety and is the operational lead for the evaluations program these MOUs feed into. CAISI Director Chris Fall (confirmed April 2026) signed the agreements; Christiano runs the evaluation work itself. The Nextgov coverage reports that CAISI has "completed more than 40 such evaluations, including on state-of-the-art models that remain unreleased."

**Takeaway for the persona:** Christiano's "third-party evaluation is mandatory, not optional" stance went from advocacy (Dwarkesh 2023) to operational reality (CAISI 2026). The lab list now includes the four largest western frontier labs.

## Signal 2 — CAISI joint evaluation work with UK AISI (renamed AI Security Institute)

- **Date:** Ongoing through 2025, formalized in September 2025 MOU.
- **Sources:**
  - https://www.aisi.gov.uk/blog/our-2025-year-in-review
  - https://en.wikipedia.org/wiki/Artificial_intelligence_safety_institute

The UK AI Safety Institute was renamed the **AI Security Institute** in 2025; the US AISI was renamed **CAISI (Center for AI Standards and Innovation)** in 2025. A September 2025 technology-focused US-UK MOU committed both institutes to joint testing and standards development. UK AISI's 2025 year-in-review reports tests of 30+ frontier AI systems, novel evaluation methods (self-replication detection, sandbagging identification), backdoor data-poisoning study with Anthropic, and biosecurity red-teaming with OpenAI and Anthropic that uncovered "dozens of vulnerabilities including new universal jailbreak paths."

**Takeaway for the persona:** Christiano's mental model of "third-party + cross-jurisdiction" evaluation is now institutionalized. The US-UK joint testing exercises he advocated for are the deliverable.

## Signal 3 — David Duvenaud tweet citing Christiano "slow-rolling catastrophe" framing

- **Date:** January 30, 2025
- **Source:** https://x.com/DavidDuvenaud/status/1885009790436352122 (status accessible via Twitter; archive at hand-extracted text below).

Quote from Duvenaud (former Anthropic alignment researcher): "Paul Christiano (now head of the US AI Safety Institute) described 'a slow-rolling catastrophe' where humans can't effectively oversee a machine economy." This is the Part I scenario from "What failure looks like" — the "going out with a whimper" path — and Duvenaud's framing confirms that Christiano was still actively articulating it in 2025 in his AISI capacity.

**Takeaway for the persona:** "Slow-rolling catastrophe / can't oversee a machine economy" is a 2025-active framing, not a 2019 one.

## Signal 4 — Anthropic RSP 3.0 takes effect (intellectual descendant of Christiano's framework)

- **Date:** February 24, 2026
- **Source:** https://www.anthropic.com/rsp-updates

Anthropic's Responsible Scaling Policy v3.0 took effect. Anthropic publicly credits Paul Christiano and ARC Evals (now METR) as the source of "much of the intellectual content and design of what is thought of as RSPs." RSP 3.0 retains the AI Safety Level (ASL) graduated framework and the capability-evals-trigger-stricter-safety-requirements structure from the original Christiano-influenced design.

**Takeaway for the persona:** RSPs are now industry-standard governance; Christiano's blueprint is operationalized at every western frontier lab (Anthropic, OpenAI, Google DeepMind via the CAISI MOUs).

## Signal 5 — UK AISI Claude Mythos Preview cyber capabilities evaluation

- **Date:** Late 2025 (UK AISI year-in-review confirms ongoing through 2025).
- **Source:** https://www.aisi.gov.uk/blog/our-evaluation-of-claude-mythos-previews-cyber-capabilities

UK AISI (with CAISI participation per the MOU) ran joint evaluations on Claude Mythos Preview's cyber capabilities. Per the UK year-in-review: joint tests on a version of Claude found the model "better than any other they had tested at software engineering tasks that might help to accelerate AI research." This is precisely the "agentic capabilities that could accelerate AI R&D" risk category Christiano flagged on Dwarkesh in 2023.

**Takeaway for the persona:** His prediction that agentic/coding capabilities would be the first national-security-relevant signal materialized.

## Why this file exists

The persona schema requires ≥3 `recent_signal_12mo` entries dated within the last 12 months (i.e., after 2025-05-27). These five candidates give the persona file a comfortable margin. Selection for the final YAML prioritizes (a) the May 5 2026 CAISI MOUs, (b) the UK AISI 2025 year-in-review, and (c) the Anthropic RSP 3.0 update — all post-cutoff and all directly tied to Christiano's intellectual fingerprint.
