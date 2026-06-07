# Arthur Mensch — Mistral AI product timeline

Sources: https://en.wikipedia.org/wiki/Mistral_AI ; https://mistral.ai/ ; coverage cited inline.

## Open-weights / mixed-license language model line

| Date | Model | Notes |
|---|---|---|
| 2023-09 | **Mistral 7B** | 7.3B parameters, Apache 2.0. The defining small-open-weights release. Outperformed LLaMA 2 13B on most benchmarks; matched LLaMA 34B. |
| 2023-12 | **Mixtral 8x7B** | 46.7B usable, sparse mixture-of-experts. Open weights. Beat LLaMA 2 70B and GPT-3.5 on most public benchmarks at release. |
| 2023-12 | **Mistral Medium** | Proprietary, multilingual. |
| 2024-02 | **Mistral Large** | Proprietary, coding-capable. Launched concurrently on Microsoft Azure. |
| 2024-02 | **Mistral Small** | Proprietary small-tier model. |
| 2024-04 | **Mixtral 8x22B** | 141B total parameters, sparse MoE. |
| 2024-07 | **Mistral Large 2** | 123B parameters, 128k context, open weights. |
| 2025-03 | **Mistral Small 3.1** | 24B parameters with image understanding. |
| 2025-12 | **Mistral Large 3** | 675B total / 41B active, sparse MoE. NVIDIA Nemotron Coalition co-trained. |
| 2025-12 | **Ministral 3 (3B / 8B / 14B)** | Edge-optimized line for NVIDIA Spark, RTX PCs, Jetson devices. |
| 2026-04 | **Medium 3.5** | 128B parameters, first flagship "merged model" combining lines. |

## Specialized models

| Date | Model | Notes |
|---|---|---|
| 2024-05 | **Codestral** | 22B-parameter code-generation model, fluent in 80+ programming languages. |
| 2024-07 | **Mathstral 7B** | STEM-focused, Apache 2.0. |
| 2024-11 | **Pixtral Large** | Vision-language: 1B visual encoder + Mistral Large 2. |
| 2025-06 | **Magistral Small / Medium** | Reasoning models. |
| 2025-12 | **Devstral 2** | 123B coding model. |
| 2026-03 | **Voxtral TTS** | First text-to-speech model, 4B parameters. |

## Consumer / enterprise products

- **Le Chat** (Nov 2024): Consumer chatbot with image generation via Flux Pro and integrated news sources.
- **Le Chat Mobile** (Feb 2025): iOS and Android apps.
- **Le Chat Pro** (2025): $14.99/month subscription tier.
- **AFP partnership** (2025): 2,000+ articles per day fed into Le Chat.

## Strategic implications for the persona

- **Speed of cadence.** Roughly a model release every 6–8 weeks across the family between 2023 and 2026. Mensch operationalized the "small team, capital-efficient, ship often" thesis.
- **Hybrid licensing.** Open weights for the small / research tier (7B, Mixtral, Mathstral) + proprietary tier for enterprise (Large, Medium). Mensch defended this explicitly: open weights are the moat against US incumbents while paid tiers underwrite training.
- **Multilingual-first.** Mistral models are trained with European-language coverage in mind from the start — a deliberate counterweight to the Anglo-Saxon bias of US-trained foundation models.
- **Enterprise / on-prem as the moat.** Mistral targets enterprise deployments where customers will not send data to a US-hosted API. CMA CGM (€100M, April 2025), Stellantis, TotalEnergies, BNP Paribas, and the French armed forces are anchor customers.
