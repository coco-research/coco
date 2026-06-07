# Patrick Lewis — Cohere role, Command A, and the institutional signal

## Title progression at Cohere

Lewis joined Cohere in 2022 (per TIME 100 AI profile). His title has shifted as the company scaled and as the product surface around RAG / tools / agents grew:

1. **Research Scientist** (2022) — initial hire, IC role, framed as RAG modelling lead.
2. **Director of Machine Learning** (2023-2024) — surfaced in TheOrg and TIME 100 AI 2024 profile.
3. **Modelling Lead, RAG / Tool-use / Agents** (2024-2025) — overlapping title used internally on LinkedIn.
4. **Senior Director of Agentic AI** (2025-2026, current) — promotion visible on Google Scholar and LinkedIn header.

His current LinkedIn headline reads "Sr. Director, Agentic AI@Cohere, leading RAG, Tool-use and Agents."

Source: <https://uk.linkedin.com/in/patrick-s-h-lewis>
Source: <https://www.getprog.ai/profile/15031366>
Source: <https://scholar.google.com/citations?user=JN7Zg-kAAAAJ&hl=en>

## What "Senior Director of Agentic AI" means inside Cohere

Cohere ships three product surfaces that are downstream of Lewis's research direction:

1. **Command A / Command A+ models** — RAG-grounded, agent-optimised, 23-language enterprise models with native citation grounding. Command A+ at 218B parameters under Apache 2.0 explicitly generates grounding spans that link every claim to source documents. The native-citation behaviour is Lewis-architected.
2. **Embed / Rerank API line** — Cohere's dense retrieval and reranking primitives that customers compose with their own document stores. The "retrieval as a service" expression of Lewis's thesis.
3. **North agentic platform** (EAP January 2025) — Cohere's enterprise agent workspace, co-developed with RBC, Dell, Ensemble Health, Bell. The agents are RAG-grounded by default and tool-using; this is the integrated commercial expression of the "retrieval + tools = agents" view that Lewis articulates on MLST.

## Cohere institutional signals 2025-2026 (relevant to Lewis's scope)

These are signals visible on Cohere's official channels that Lewis's organisation is directly responsible for or contributed to:

- **Command A launch** (April 2025). Cohere's enterprise flagship at 23 languages with best-in-class RAG, grounding, and tool use. Cohere blog: <https://docs.cohere.com/page/migrating-prompts>. Lewis's modelling team is the source of the RAG and grounding behaviour that is the headline competitive feature.
- **North EAP** (January 2025). The agentic platform. <https://cohere.com/blog/north-eap>. Lewis's team is the source of the agent / tool-use behaviour.
- **Tiny Aya** open-weight multilingual edge models (February 2026). <https://techcrunch.com/2026/02/17/cohere-launches-a-family-of-open-multilingual-models/>. Cohere Labs (Hooker / Fadaee) leads Aya, but the edge-deployment retrieval story is Lewis-adjacent.
- **Cohere Transcribe** open-source 2B speech-to-text (March 2026). <https://techcrunch.com/2026/03/26/cohere-launches-an-open-source-voice-model-specifically-for-transcription/>. Voice as a new retrieval-modality entry into North.
- **Saab partnership** (March 2026). <https://www.pminsights.com/insights/coheres-short-term-returns-turn-positive-at-2-07-as-saab-partnership-breaks-into-aerospace>. Defence / aerospace enterprise. The grounding + citation behaviour is what makes the surveillance use case auditable.
- **Aleph Alpha acquisition** (April 2026). <https://en.wikipedia.org/wiki/Cohere>. Cohere folds the German enterprise / sovereign AI champion. Multilingual + sovereign RAG becomes transatlantic. Lewis's organisation has to integrate the Aleph Alpha modelling stack.

## Why Lewis is the right fit for Cell A "model architects" with role "specialist"

He is not a CEO or a public-frontier-lab spokesman, so "lead-driver" overstates his organisational scope. He is also not a generalist co-signer like a validator. He is the specialist whose narrow deep expertise — retrieval-augmented architectures — is now load-bearing for an entire product surface across the industry. RAG is a primitive everyone uses; the person who invented it sitting inside the model-architects cell as the retrieval specialist is the right mapping.

## Voice and posture (inferred from cumulative public output)

- Soft-spoken, plain-English, occasionally British-dry. Self-deprecating about the RAG acronym. Not interested in self-branding.
- Treats retrieval architecture questions as architecture questions, not as add-on questions. Pushes back when retrieval is framed as a "RAG pipeline" bolted onto a base model.
- Defaults to citations-first framings — if a model cannot cite its source, he treats it as a deployment-blocker, not a UX nuisance.
- Allergic to "long-context will replace retrieval" arguments. Reframes long-context as "retrieval-in-the-prompt without auditability."
- Generally aligned with Gomez on enterprise / sovereign / multilingual, but more technical-architect-shaped than commercial-founder-shaped.
