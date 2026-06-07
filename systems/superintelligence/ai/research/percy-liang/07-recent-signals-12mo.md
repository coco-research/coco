# Percy Liang — recent signals (post 2025-05-27)

Compiled 2026-05-27.

Goal: ≥3 dated signals from the trailing 12 months for the YAML `recent_signal_12mo` field.

## Signal 1 — Marin open lab announcement (2025-05-19)
- URL: http://marin.community/blog/2025/05/19/announcement/
- Marin 8B Base and Instruct released. Marin 8B Base outperforms Llama 3.1 8B on 14 of 19 standard benchmarks.
- The blog post itself defines "open development" — pre-registered experiments, public PRs, public failures.
- Takeaway: This is Liang's strongest 2025 statement that **the open-source AI ecosystem must extend beyond weights to the full development process**.

## Signal 2 — AHELM (Audio HELM) paper (2025-08-29)
- URL: https://arxiv.org/abs/2508.21376
- Liang as senior author. Tony Lee + Haoqin Tu primary.
- Covers 10 dimensions for audio-language models including bias, fairness, multilinguality, toxicity, safety.
- Takeaway: Holistic evaluation playbook extending into modalities. **The HELM thesis is being applied as method, not retired as product.**

## Signal 3 — PyTorch Conference 2025 keynote: "Marin: An Open Lab for Frontier AI"
- URL: https://pytorchconference.sched.com/event/27SII/keynote-marin-an-open-lab-for-frontier-ai-percy-liang-associate-professor-of-computer-science-stanford-university-co-founder-together
- Percy Liang keynote at PyTorch Conference 2025 (Q4 2025).
- Pitched Marin directly to the open-frameworks community.
- Takeaway: This is the venue and audience he chose to evangelize Marin — open-frameworks engineers, not closed-lab researchers.

## Signal 4 — 2025 Foundation Model Transparency Index (2025-12, arXiv 2512.10169)
- URL: https://arxiv.org/abs/2512.10169
- Liang co-author. Third edition. Average score fell from 58 (2024) to 40 (2025).
- IBM at 95, xAI/Midjourney at 14.
- Takeaway: Transparency is getting **worse**, and Liang is willing to be publicly critical year-over-year. He's not a "let's all play nice" academic — he names names.

## Signal 5 — HELM transition to maintenance mode (announced for 2026-06-01)
- URL: https://github.com/stanford-crfm/helm
- HELM v0.5.16 latest release (April 30, 2026). Maintenance mode policy effective June 1, 2026.
- Takeaway: **Graceful version retirement** — the group is signaling that HELM's job is done and they're pivoting to Marin / AHELM / FMTI. Important to anyone betting tooling on HELM.

## Signal 6 — DSPy 3.2.1 release (2026-05-05)
- URL: https://github.com/stanfordnlp/dspy/releases
- DSPy v3.2.1 latest, 109 total releases, 34.7k GitHub stars.
- Takeaway: The "programming with prompts" abstraction is mainstream. Liang's bet on declarative LLM programming has paid off.

## Cross-references for the persona
Of these six, the three strongest as `recent_signal_12mo` entries are:
1. Marin announcement (2025-05-19) — defining open-development statement.
2. FMTI 2025 (December 2025) — annual transparency report with sharp findings.
3. HELM maintenance mode (April 30, 2026 release + June 1, 2026 policy) — lifecycle signal.

Backup signals: AHELM (Aug 2025), PyTorch keynote (Q4 2025), DSPy v3.2.1 (May 2026).
