# Physical Intelligence (Pi) — Company Profile (extracted 2026-05-27)

Primary sources:
- https://www.pi.website/ (formerly physicalintelligence.company)
- https://www.therobotreport.com/physical-intelligence-raises-400m-for-foundation-models-for-robotics/
- https://www.bloomberg.com/news/articles/2025-11-20/robotics-startup-physical-intelligence-valued-at-5-6-billion-in-new-funding
- https://techcrunch.com/2026/03/27/physical-intelligence-is-reportedly-in-talks-to-raise-1-billion-again/
- https://eutechfuture.com/artificial-intelligence/physical-intelligence-building-foundation-models-for-robots-to-interact-with-the-real-world/

## Founding

- **Founded:** March 2024 (publicly announced by Levine on X on March 13, 2024).
- **Tagline / mission:** "Bringing general-purpose AI into the physical world." A single foundation model that can drive many robots across many tasks.
- **Co-founders:**
  - **Karol Hausman** — CEO. Formerly Google DeepMind.
  - **Sergey Levine** — Chief Scientist. UC Berkeley professor (concurrent).
  - **Chelsea Finn** — Research lead. Stanford professor (concurrent).
  - **Brian Ichter** — Co-founder. Formerly Google Research.
  - **Lachy Groom** — Co-founder / business lead. Earlier at Stripe, also angel investor.
  - **Adnan Esmail** — Co-founder; hardware / robot-platform focus.

## Capital raises

| Date | Round | Amount | Valuation | Lead investors |
|---|---|---|---|---|
| Mar 2024 | Seed | ~$70M | ~$400M | OpenAI, Khosla Ventures, Thrive |
| Nov 2024 | Series A | $400M | ~$2.4B | Jeff Bezos, Thrive, Lux, OpenAI |
| Nov 2025 | Series B | $600M | ~$5.6B | CapitalG (lead); Lux, Bond, Redpoint, Sequoia, T. Rowe Price, NVIDIA's NVentures |
| Mar 2026 | In talks (Series C) | ~$1B | ~$11B (target) | Founders Fund (lead reported), Lightspeed |

Total raised through May 2026: roughly $1.1B confirmed; potentially ~$2.1B once Series C closes.

## Headcount

- ~80 employees as of January 2026 (per TechCrunch).
- Mix of Berkeley / Stanford / Google DeepMind / Google Brain alumni.

## Product timeline

- **π₀ (pi0)** — Released October–November 2024 (paper "π₀: A Vision-Language-Action Flow Model for General Robot Control" — arXiv 2410.24164). 3B-parameter transformer built on PaliGemma with an action expert. Trained on >10,000 hours of real robot data, 7 robot embodiments, 68 tasks. First publicly demonstrated generalist policy for cross-embodiment manipulation.
- **π₀-FAST** — Faster inference variant of π₀.
- **π₀.5 (pi0.5)** — Paper arXiv 2504.16054, submitted April 22, 2025. A VLA with open-world generalization: long-horizon dexterous tasks (cleaning a kitchen or bedroom) in entirely new homes the model has never seen. Adds co-training across heterogeneous tasks, multiple robots, web data, and explicit semantic subtask prediction.
- **π₁** — Referenced in roadmap discussions through 2025–2026; user brief mentions it; canonical launch artifact has not been independently confirmed as of 2026-05-27. Treated as forthcoming.

## Strategic stance

- **Generalist over specialist** — one model across many robots, not a stack of task-specific controllers.
- **Real-world data flywheel** — deploy systems, collect real data, retrain. Surrogate data is supplement, not substitute.
- **Imitation first, RL later** — pre-train on imitation data to get a competent base, then fine-tune with RL once there is a usable policy to improve.
- **Open-source friendly base models** — uses PaliGemma / Gemma; extends with action experts rather than training from scratch.

## Public quotes from Levine (2025–2026)

- "Think of it like ChatGPT, but for robots." — Levine, paraphrased in TechCrunch coverage of the March 2026 raise.
- "Real data is indispensable if we are to truly build robotic foundation systems with broad generalization." — Sporks of AGI essay, July 2025.
- "Robots get smarter the more they are deployed." — Repeated framing of the data flywheel across Dwarkesh podcast and conference keynotes.
