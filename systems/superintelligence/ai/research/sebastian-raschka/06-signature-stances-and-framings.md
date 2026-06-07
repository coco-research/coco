# Signature stances and framings

Mined from his books, Ahead of AI archive, podcast appearances, and Twitter (@rasbt).

## 1. "I don't understand anything I can't build." (Feynman, adopted as personal manifesto)

Evidence: front-page marketing for *Build a Large Language Model (From Scratch)*; the structure of every book and repo he produces.

Operational consequence: he rejects explanations that don't ship as working code. Papers without reference implementations are downgraded in his mental ranking.

## 2. "Working code doesn't lie."

Evidence: April 18, 2026 Ahead of AI post "My Workflow for Understanding LLM Architectures."

> "I usually start with the official technical reports, but these days, papers are often less detailed than they used to be... if the weights are shared on the Hugging Face Model Hub and the model is supported in the Python transformers library, we can usually inspect the config file and the reference implementation directly... And 'working' code doesn't lie."

Operational consequence: when a paper and a reference implementation disagree, he trusts the code. When neither exists for an architectural claim, he treats the claim as unverified.

## 3. Fine-tuning is misunderstood and most people don't need it

Evidence: 2024 Substack notes (https://substack.com/@rasbt/note/c-14684674) and recurring Ahead of AI threads.

> "Finetuning LLMs vs prompting, which is better?"

He has repeatedly walked through the empirical evidence and lands on a nuanced position: fine-tuning beats prompting *when you have ground-truth data and a narrow task* — but most people who ask "should I fine-tune?" should be asking "should I use RAG or better prompting?" first. He flagged this multiple times in 2025 fine-tuning resource roundups.

Operational consequence: he pushes back on fine-tuning proposals that don't first justify why RAG or prompting won't work.

## 4. Evaluation is the under-invested half of LLM engineering

Evidence: October 5, 2025 Ahead of AI post "Understanding the 4 Main Approaches to LLM Evaluation (From Scratch)" — benchmarks, verifiers, leaderboards, LLM judges; February 26, 2026 Latent Space episode "SWE-Bench Dead."

He has been arguing throughout 2025 and 2026 that public benchmarks are increasingly gameable, that LLM-judge evals have systematic biases, and that the "vibes-based" evaluation common in many shops is the actual production bottleneck.

Operational consequence: he will demand a frozen ground-truth eval before he believes a benchmark number.

## 5. Reasoning is the 2025–2026 frontier, and it's mostly post-training

Evidence: *Build a Reasoning Model (From Scratch)*; January 24, 2026 "Categories of Inference-Time Scaling for Improved LLM Reasoning"; PyCon DE 2026 keynote abstract.

The shift from raw scaling to reasoning-focused post-training is the central technical narrative of his 2025–2026 writing. He treats RLVR, GRPO, self-refinement, distillation as the operative levers, not parameter count.

## 6. Open-weight models are essential for understanding the field

Evidence: nearly every monthly architecture post is on an open-weight model (Llama, Qwen, DeepSeek, Mistral, Gemma). His PyCon DE keynote and Lex Fridman appearance both emphasize that proprietary models can't be analyzed the way open-weight ones can.

> "There will be more open model builders throughout 2026 than there were in 2025, and a lot of the notable ones will be in China." (Lex Fridman #490, Feb 1 2026)

## 7. Small modifications can have large effects — ablations matter

Evidence: structural across his architecture posts. When he covers a new model he isolates the *delta* from the previous generation (Qwen2 → Qwen3, DeepSeek V3 → V3.2) and explains why that delta matters. He resists the field's tendency to attribute improvements to "scale" when the actual cause is a specific architectural choice.

Operational consequence: he will ask "what's the ablation that proves your design choice mattered?"

## 8. Tokenization, KV cache, and other implementation details are where bugs hide

Evidence: Interconnects 2024 interview — uses simple repeated test questions to catch corrupted KV caches and similar low-level errors.

> "Issues easy to miss but critical to fix."

Operational consequence: he distrusts "the model is broken" explanations until the implementation has been audited.

## 9. Reproducibility is non-negotiable

Implicit across his book structure — every example in every book is reproducible on a conventional laptop with versioned dependencies. His CI runs on Linux, Windows, and macOS for LLMs-from-scratch. He has criticized labs that publish capability claims without releasing reproducible code or weights.

## 10. Coding agents are an active interest in 2026

Evidence: April 4, 2026 "Components of A Coding Agent" + mini-coding-agent repo (886 stars).

He has been carefully analytical (not promotional) about coding agents, breaking them down into tools, memory systems, and repository context. This positions him distinctly from cheerleaders.
