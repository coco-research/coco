# HELM (Holistic Evaluation of Language Models) and AHELM

Sources:
- Original HELM paper: https://arxiv.org/abs/2211.09110 (Liang et al., 2022)
- HELM repo: https://github.com/stanford-crfm/helm
- AHELM paper: https://arxiv.org/abs/2508.21376 (August 29, 2025)
Retrieved: 2026-05-27

## HELM (2022 — foundational)
- Authors: Percy Liang, Rishi Bommasani, Tony Lee, and ~47 others.
- Framework measures **7 metrics** (accuracy, calibration, robustness, fairness, bias, toxicity, efficiency) across **16 core scenarios**.
- 30 models densely benchmarked on standardized conditions.
- Has become the canonical reference frame for "evaluate models on more than just accuracy."

## HELM repo status (2026-05-27)
- **Latest release: v0.5.16 (April 30, 2026)**.
- Total releases: 25.
- **6,283 commits** on main branch.
- **CRITICAL: "HELM will enter maintenance mode on June 1, 2026."** Maintenance Mode Policy takes effect — reduced development activity.
- This is a major handoff signal: Liang's group is pivoting away from active HELM development toward Marin / AHELM / FMTI.

## HELM coverage in 2025-2026
HELM is no longer a single benchmark but a family:
- VHELM (vision-language)
- HEIM (text-to-image)
- MedHELM (medical applications)
- AHELM (audio-language)
- ToRR (table reasoning)
- Enterprise benchmarks
- Includes MMLU-Pro, GPQA, IFEval, WildBench in the unified suite.

## AHELM (2025)
- Authors: Tony Lee, Haoqin Tu, Chi Heem Wong, Zijun Wang, Siwei Yang, Yifan Mai, Yuyin Zhou, Cihang Xie, **Percy Liang**.
- Submitted August 29, 2025; revised September 2, 2025.
- Evaluates audio-language models across 10 dimensions: audio perception, knowledge, reasoning, emotion detection, bias, fairness, multilinguality, robustness, toxicity, safety.
- Tests 14 open-weight and closed-API models.
- Introduces two synthetic datasets: **PARADE** (stereotype evaluation) and **CoRe-Bench** (conversational reasoning).
- Positions itself as a **"living benchmark"** — explicitly designed for future expansion.

## Implications for persona
- HELM going into maintenance mode signals **graceful version retirement**, not abandonment. The Liang research group is consistent about lifecycle management.
- The proliferation into modality-specific HELMs (V, H, MedH, AH) shows the **holistic evaluation playbook is now method, not just product**.
- The "living benchmark" framing on AHELM is a clear Liang trademark: benchmarks must evolve or they become stale.
- He consistently lists himself last on AHELM (senior author position) — research-group convention, signals junior-first credit attribution.
