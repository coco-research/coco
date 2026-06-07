# Marin: An Open Lab for Foundation Models (announcement)

Source: http://marin.community/blog/2025/05/19/announcement/
Date: 2025-05-19
Retrieved: 2026-05-27

## Vision
Marin is an effort to advance open-source AI beyond just released model weights. Led by Percy Liang at Stanford's CRFM, the initiative aims to democratize foundation model development by making the entire research and engineering process transparent and collaborative. The framing question is: **"How do we build the best model with a fixed resource budget?"** — quality and resource efficiency, not raw scale, drive innovation.

## Released models
1. **Marin 8B Base (deeper-starling)** — Trained on 12.7 trillion tokens, dense Transformer architecture. Outperforms Llama 3.1 8B Base on 14 of 19 standard evaluation benchmarks.
2. **Marin 8B Instruct (deeper-starling-05-15)** — Supervised fine-tuning on ~5B tokens. Surpasses OLMo 2 on instruction-following tasks; trails Llama 3.1 Tulu.

Both available on Hugging Face. Can be tested via Together AI.

## "Open development" methodology
Transparency mechanism operates through:
- **GitHub Issues** as preregistration documents declaring hypotheses upfront.
- **Pull Requests** containing experiment code before execution.
- **Live monitoring** of training via public dashboards with WandB integration.
- **Community review** enabling detailed scrutiny of experimental design.
- **Complete reproducibility** with all code, data, and results open.

The approach **normalizes failure** — the team publicly documented mistakes in their 8B training run — and eliminates cherry-picking of results.

## Contributors
- **Core team**: David Hall, Ahmed Ahmed, Christopher Chou, and others.
- **Advisors**: Siddharth Karamcheti, Suhas Kotha, Nelson Liu, additional Stanford researchers.
- **Institutional support**: Google TPU Research Cloud (primary compute), Google JAX team, Anyscale, Together AI, Stanford AI Lab community.
- **Prior art credited**: EleutherAI, AI2, Hugging Face, BigScience.

## Recent extension
PyTorch Conference 2025 keynote: "Marin: An Open Lab for Frontier AI" — Percy Liang. Indicates Marin pitched directly at the open-frameworks community.

## Implications for persona
- This is the strongest 2025 signal for Liang's stance that the open-source ecosystem must extend beyond weights to the full development process.
- Pre-registration of failed experiments is a deeply academic frame applied to model training — captures his reproducibility ethos.
- Marin 8B beating Llama 3.1 8B on 14/19 benchmarks is the concrete artifact backing the open-development thesis.
