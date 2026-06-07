# Books, repos, and pedagogical philosophy

Source: https://www.manning.com/books/build-a-large-language-model-from-scratch, https://github.com/rasbt/LLMs-from-scratch, https://github.com/rasbt/reasoning-from-scratch, https://sebastianraschka.com/books/

## The Feynman framing

Raschka invokes a Richard Feynman line as the philosophical core of his work:

> "I don't understand anything I can't build."

Manning's marketing for *Build a Large Language Model (From Scratch)* uses this quote directly. It is the closest thing Raschka has to a personal manifesto. Pedagogy, in his model, is measured in working code. If you cannot implement the thing in PyTorch end-to-end, you do not yet understand it.

This puts him in the same archetype as Andrej Karpathy (nanoGPT, nanochat) — but Raschka's frame is **book-length systematic walkthrough**, where Karpathy's is **one-evening YouTube video plus a single-file repo**. They share the same first principle, executed at different time-scales.

## Build a Large Language Model (From Scratch) — structure

7 main chapters + 5 appendices (A–E):

1. Understanding LLMs
2. Working with text data (tokenization)
3. Coding attention mechanisms
4. Implementing a GPT model from scratch
5. Pretraining on unlabeled data
6. Finetuning for text classification
7. Finetuning to follow instructions

Bonus material includes alternative attention mechanisms (grouped-query attention, sliding window attention), MoE implementations, and modern architectures (Llama 3.2, Qwen3, Gemma 3). All in pure PyTorch, no external LLM libraries (no Transformers, no LangChain). Runs on a conventional laptop, with optional GPU.

## Build a Reasoning Model (From Scratch) — structure

8 chapters + appendices:

1. Text generation with pre-trained LLMs
2. Model evaluation methodologies
3. Inference-time scaling techniques
4. Self-refinement approaches
5. Reinforcement learning for reasoning (GRPO)
6. Model distillation
7. Chat interfaces
8. Advanced implementations

Techniques mirror DeepSeek R1 and GPT-5 Thinking. Chapters 2–4 work on CPUs; 5–6 benefit from GPU.

## Companion repos

- **LLMs-from-scratch** — 96.1k stars, 14.7k forks. Active CI on Linux, Windows, macOS.
- **reasoning-from-scratch** — 4.4k stars, 643 forks. Active.
- **machine-learning-book** — 5.2k stars, 1.8k forks. Code for *Machine Learning with PyTorch and Scikit-Learn*.
- **deeplearning-models** — 17.5k stars, 4.1k forks. Architecture grab-bag from his UW-Madison teaching years.
- **llm-architecture-gallery** — 1.3k stars. Source for the 2026 architecture gallery posts.
- **mini-coding-agent** — 886 stars. Minimal readable coding-agent harness. Created to back the April 4 2026 newsletter post on coding agents.
- **mlxtend** — scikit-learn extension library; his oldest still-used Python project, dating from the Madison years.

## Stated audience and prerequisites

The Manning page describes the audience as "intermediate Python proficiency and foundational machine learning knowledge." The book deliberately does not assume PhD-level math. This shapes Raschka's voice: he writes for the working engineer who wants to understand, not the academic who wants to publish.

## Why not use existing libraries

From the *Interconnects* interview (Aug 2024): Raschka built LitGPT explicitly as "a nanoGPT from Andrej Karpathy, but for all types of LLMs." He distrusts opaque frameworks not because they fail to work but because they fail to teach. His test for any LLM library: can a smart engineer read the file and understand what's happening in one sitting?
