# Thinking Machines Lab — Company Profile

Sources: Wikipedia (TML), TechCrunch (Feb 18 2025 launch), thinkingmachines.ai homepage, Built In, Contrary Research.

## Stated mission (homepage)

> "Building a future where everyone has access to the knowledge and tools to make AI work for their unique needs and goals."

## Three pillars (Murati launch tweet, Feb 18 2025)

1. Helping people **adapt** AI systems for specific needs.
2. Developing **strong foundations** for more capable AI systems.
3. Fostering industry **collaboration on AI safety** and best practices.

## Design principles (homepage)

- **Science is better when shared** — frequent publication of code, papers, blog posts.
- **AI that works for everyone** — multimodal, partnership-oriented (not autonomous).
- **Solid foundations matter** — frontier capability in science + programming; multimodal as first-class.
- **Learning by doing** — research and product inform each other; safety via real-world testing and red-teaming.

## Differentiator vs. OpenAI / Anthropic / Google DeepMind

- **Human-AI collaboration over autonomous agents.** Repeated framing — the company explicitly does NOT pursue the fully-autonomous-agent endgame as its primary product thesis.
- **Customization as first-class.** First product (Tinker) is a fine-tuning API, not a chatbot.
- **Multimodal-native interaction model** (May 2026) — challenges the industry consensus on turn-based architectures.

## Product timeline

| Date | Release | Significance |
|------|---------|--------------|
| Sept 10, 2025 | **Connectionism blog launched** with "Defeating Nondeterminism in LLM Inference" (Horace He) | First public technical artifact — 7 months after founding |
| Sept 26, 2025 | "Modular Manifolds" (Jeremy Bernstein) | Optimizer theory |
| Sept 29, 2025 | "LoRA Without Regret" (John Schulman + team) | Justifies Tinker's LoRA-only architecture |
| Oct 1, 2025 | **Tinker** — distributed fine-tuning API, private beta | First product. LoRA-only, low-level primitives (forward_backward, optim_step, sample, save_state) |
| Oct 27, 2025 | "On-Policy Distillation" (Kevin Lu + team) | RL methodology |
| April 22, 2026 | **Multi-billion Google Cloud deal** (single-digit billions, GB300 access) | First cloud-provider agreement |
| May 11, 2026 | **Interaction Models** research preview + **TML-Interaction-Small** (276B MoE / 12B active) | First in-house model. Multi-stream micro-turn architecture |

## Connectionism blog — research thrust mapping

- **Inference determinism** (Horace He) → infrastructure reliability for production agents.
- **Optimizer theory** (Bernstein) → training stability for the in-house multimodal model.
- **LoRA at scale** (Schulman) → justifies the Tinker product architecture publicly.
- **On-policy distillation** (Lu) → bridges large frontier models to smaller deployable ones.

The blog cadence (~monthly Sept–Oct 2025 then a long quiet period until May 2026) tracks Murati's stated principle that research and product should be released together rather than as marketing artifacts.

## Governance peculiarity

Murati holds a **deciding board vote** with majority decision-making capability. Founding shareholders hold votes weighted **100× regular shareholders**. This is unusual for a public benefit corporation and explicitly cited as her hedge against the OpenAI board-crisis pattern repeating against her.

## Funding rationale (synthesized from coverage)

- Investor pitch was **NOT a product** — TML had nothing public when it raised $2B at $12B. It was a team-and-mission pitch.
- a16z, Nvidia, AMD all bet on Murati's product-engineering operating system rather than a specific model class.
- Albanian government's $10M was symbolic / sovereign capital — Murati's heritage made it material.
- Google deal (April 2026) is significant because it diversifies compute beyond Nvidia and signals TML will train its own frontier multimodal models rather than only offer fine-tuning of others'.
