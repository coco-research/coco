# Source 03 — VentureBeat: Cohere Command A+ launch

Fetched: 2026-05-27
URL: https://venturebeat.com/technology/cohere-cracks-lossless-quantization-and-native-citations-with-first-full-apache-2-0-licensed-open-model-command-a

## Headline facts

- **Model:** Command A+ — Cohere's first fully Apache 2.0 open-source flagship model
- **Size:** 218 billion parameters
- **Hardware target:** runs on a single NVIDIA Blackwell B200 GPU or just two NVIDIA H100 GPUs
- **License:** Apache 2.0 (Cohere's first fully permissive flagship release)

## Engineering hooks

- **Native citation generation** — when the model retrieves information from an external tool, it generates explicit "grounding spans" and directly links every factual claim to the source document or database row.
- **Lossless quantization** — Cohere claims minimal quality loss going down to lower-precision formats, enabling the single-GPU deployment story.
- **Use cases:** complex reasoning, multimodal document processing, agentic workflows.

## Strategic framing

- Apache 2.0 licensing is the explicit pitch — "use, modify, distribute, and commercialize the model without paying licensing fees."
- Hardware efficiency (single B200) is Cohere's enterprise pitch: deploy on-prem without renting a 100-GPU cluster.
- Native citations are the enterprise pitch on hallucinations: every claim is traceable to its source.

## Why this matters for the persona

This is the synthesis of every Aidan Gomez stance: enterprise-first deployment (on-prem-able), RAG-as-architecture (native citations are RAG made constitutional), data-privacy moat (your data never leaves your infrastructure because the model runs inside it), and Apache 2.0 as the competitive lever against closed-API competitors.
