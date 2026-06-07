# Together AI and Percy Liang's open-AI stance

Sources:
- Together AI homepage: https://www.together.ai/
- Together AI about: https://www.together.ai/about-us
- Air Street Press interview: https://press.airstreet.com/p/percy-liang-on-truly-open-ai (Nov 11, 2024)
Retrieved: 2026-05-27

## Together AI — corporate role
- Percy Liang is **co-founder and chief scientist** of Together AI.
- Together AI was founded in 2022, positions itself as "The AI Native Cloud."
- Customers include Cursor, Decagon, Cohere, DeepMind, ElevenLabs, Mozilla, Salesforce.
- Together AI hosts Marin models for inference (direct overlap with the Stanford open-development initiative).

## Together AI — 2025-2026 platform launches
- **FlashAttention-4**: Up to 1.3x faster than cuDNN on NVIDIA Blackwell. (Tri Dao co-affiliation here.)
- **ATLAS**: Runtime-learning accelerators delivering up to 4x faster LLM inference.
- **Batch Inference API**: Process billions of tokens at reduced cost.
- **Fine-Tuning platform upgrades**: Extended model sizes and context windows.
- **Serverless inference, dedicated model, container inference, accelerated GPU clusters** (self-serve up to thousands of GPUs).

## Liang's stance on open AI (Air Street, Nov 2024)

### On what "open" means
Distinguishes "open-weight" vs "open-source" models. True openness requires more than released weights. Cites Open Source Initiative definition — users must be able to "use the system for any purpose," "study how it works," "modify the system," and "share it with others."

### On evaluation
> "Current model evaluation is fundamentally broken."
- Due to test-train contamination.
- Among 30 major language models studied, **only 9 provided sufficient information about overlap**.
- Cites GPT-4 scoring perfectly on pre-2021 Codeforces problems vs. **0% on newer ones** — evidence of inflated benchmark claims.

### On barriers to openness
- Companies avoid disclosing training data to protect competitive advantages and reduce legal exposure (Anthropic Books3, NYT v. OpenAI overhang).
- Documents that **5-7% of previously available training data has been restricted recently**, with rates reaching **20-33% for valuable sources** like news and social media.

### On openness and safety
> "Not only is there no trade-off between openness and safety, but openness is essential for safety."
- Open models enable significant safety research (Llama, by giving researchers full weight access, has led to meaningful work that may not otherwise have happened).
- Safety controls on closed models are "bypassed within hours by red-teamers."
- Open models prevent power concentration.

## Implications for persona
- The Together AI role gives Liang **commercial-credibility-with-Open-AI-ethos** — he's not just an academic critic.
- The "fundamentally broken" eval framing is one of his signature rhetorical moves.
- His openness-vs-safety stance is one of the **two productive-conflict axes against Dario Amodei and Sam Altman** — closed labs argue safety requires control, Liang argues openness IS safety.
- The "5-7% / 20-33%" data restriction stat is the kind of concrete number Liang loves to cite — fights vibes with data.
