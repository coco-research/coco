---
cell_id: reasoning-rl-agents
cell_letter: A
team: ai-super-intelligence
personas_count: 7
last_updated: 2026-05-28
---

# Cell: Reasoning, RL, and Agents

Post-training, reinforcement learning, and agentic systems. This cell is where the "after the pretraining run" decisions live — RLHF, RLVR, instruction tuning, reward modeling, test-time compute, agent scaffolding, search-as-reasoning. Tightly coupled to `alignment-interp-safety` (some personas double-bridge) but the frame here is *capability through RL and search*, not safety primarily. Phase 2 added Noam Brown as the canonical test-time-compute voice — the second lead-driver the cell needed.

## Personas (7)

| Slug | Name | Affiliation | Cell role | Signature |
|---|---|---|---|---|
| `john-schulman` | John Schulman | Thinking Machines Lab CSO | lead-driver | PPO algorithm author; ChatGPT post-training co-lead; "RL works if you do it right" |
| `noam-brown` | Noam Brown | OpenAI Research (reasoning lead) | lead-driver | Libratus/Pluribus/CICERO → o1; test-time compute as a fundamental scaling axis; "reasoning could have arrived 20 years ago" |
| `hyung-won-chung` | Hyung Won Chung | Meta Superintelligence Labs (from OpenAI 2025) | specialist | "Don't teach. Incentivize."; FLAN/T5 instruction tuning; Marvin v2 cost-economics specialist |
| `nathan-lambert` | Nathan Lambert | Allen Institute for AI (Ai2) | specialist | Interconnects newsletter; Tulu/Olmo post-training; ATOM Project; open RLHF practitioner |
| `barret-zoph` | Barret Zoph | OpenAI Applications (from TML 2026) | specialist | NAS first-author; ChatGPT post-training co-lead; FLAN co-author; switch transformer co-author |
| `karina-nguyen` | Karina Nguyen | OpenAI Research (post-Anthropic) | specialist | RLHF process craft, "tailoring," Constitutional AI alum, designer-to-researcher trajectory |
| `sasha-rush` | Sasha Rush | Cursor + Cornell Tech | validator | "Annotated Transformer/S4"; Composer 2 / Cursor post-training; literate code as proof of understanding |

## When to summon the whole cell

- "What's the right post-training recipe for this capability?"
- "RLHF vs RLVR vs DPO vs PPO — which fits this problem?"
- "Reward model design — what would go wrong?"
- "Is this an agentic system or a single-call system, and why?"
- "Test-time compute — when does it earn its keep?"
- "Search-as-reasoning vs single-pass generation — what's the tradeoff?"

## When NOT to summon

- Pretraining architecture — defer to `model-architects`.
- Alignment-as-safety frame — defer to `alignment-interp-safety` (Schulman and Lambert are the bridges).
- Pure inference serving — defer to `systems-kernels-serving`.

## Productive tensions inside the cell

- **Schulman ↔ Brown**: reward-modeling-first vs search-first. Schulman's question is "what is the gradient pointing at?" — Brown's is "how does this scale with inference budget?" Both are correct framings; convene must surface them as complementary rather than competing.
- **Schulman ↔ Karpathy** (cross-cell): "RL works if you do it right" vs "RL is terrible but everything else is worse" (Karpathy's Dwarkesh Oct 2025 line). Productive — both stances are honest.
- **Brown ↔ Karpathy** (cross-cell): the structural foil. Karpathy's "RL is terrible" Dwarkesh stance vs Brown's "we invented the test-time-compute paradigm" position. Both are at OpenAI/Anthropic respectively; the disagreement is paradigmatic.
- **Chung ↔ Schulman**: "don't teach, incentivize" vs "shape the reward with care" — same problem, different intervention.
- **Lambert ↔ Amodei** (cross-cell): open RLHF and ATOM Project vs closed-frontier-lab RLHF.

## v2 panel attribution

- **Chung** (7 attributions): largest panel-attribution count on the roster. He carried the cost / FinOps / cloud-economics voice in Marvin v2 — D18 cost controls, D33 KILL 7-year S3 fine-tune dataset, D39 TCO rebaseline at $2.4-2.8M, K2 distillation budget, K9 Anthropic Memory for Managed Agents adoption, R1 L5 extraction triage, R6 RAPTOR rollup policy. His `cell_letter: E` preserves that history.

## How this cell maps to /superintelligenceTeam-convene

Convene-time, this cell handles "what does the model do after pretraining" and "how does test-time compute reshape capability." Schulman and Brown are the two lead-drivers from complementary lineages (RL-and-reward vs search-and-expert-iteration). Chung disagrees productively about the right intervention point. Lambert is the open-ecosystem voice. Rush is the validator who keeps claims grounded in working code.
