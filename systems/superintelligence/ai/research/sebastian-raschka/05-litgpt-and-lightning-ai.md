# LitGPT and Lightning AI

Source: https://github.com/Lightning-AI/litgpt

## What LitGPT is

Tagline from the repo: "20+ high-performance LLMs with recipes to pretrain, finetune and deploy at scale." Apache 2.0. Maintained by Lightning AI, the company behind PyTorch Lightning and Lightning Fabric.

## Raschka's role

Senior / Staff Research Engineer at Lightning AI since 2022. LitGPT is the company's open-source LLM library; Raschka is one of the primary contributors and the public face of the project (his Ahead of AI posts frequently lean on LitGPT for examples).

In his August 2024 Interconnects interview Raschka framed LitGPT as "a nanoGPT from Andrej Karpathy, but for all types of LLMs." That sentence is the design brief: keep nanoGPT's transparency but cover the whole modern LLM zoo (Llama, Qwen, Phi, Gemma, Mistral) with the same readable-code standard.

## Design principles (from the README)

- **Transparency and control**: "from scratch implementations" with "no abstractions"
- **Readable, easy-to-modify code** — explicit goal that a researcher can drop in and modify model internals
- **Enterprise-ready**: Flash Attention, FSDP, quantization, distributed training
- **Apache 2.0** — commercial use permitted

The dual orientation (transparent + production-ready) is unusual. Most LLM frameworks pick one. LitGPT positions itself between Karpathy-style nanoGPT (transparent, single-machine) and Hugging Face Transformers (general-purpose, abstracted).

## Recent (2025–2026) updates

- v0.5.12 (December 2025) — current release as of writing.
- 28 total releases since project inception.
- Added support for Qwen3, Phi 4 variants, Gemma 3 in 2025.
- Active GitHub maintenance throughout 2025–2026.

## Why this matters for the persona

LitGPT is the production proof point behind Raschka's pedagogy. It demonstrates that "readable from-scratch code" can scale — the same codebase that fits in a book chapter also trains models on H100 clusters. When Raschka says "build it to understand it," LitGPT is his answer to anyone who says "but production code can't be readable."

This is also a point of pairing with **Karpathy**: nanochat and LitGPT share a design philosophy but differ in scope. Karpathy keeps the scope deliberately tiny (8,000 lines for a full pipeline); Raschka keeps the readability constraint but lets the line count grow with the model zoo.
