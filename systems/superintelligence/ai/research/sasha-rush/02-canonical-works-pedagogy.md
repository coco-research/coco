# Sasha Rush — Canonical Works (Pedagogy Track)

Rush's signature contribution to the field is not any single paper but a **medium**: the "annotated" literate-code tutorial, executable as a Jupyter notebook, where every line of the original paper has corresponding runnable code immediately adjacent. He pioneered this format and his students and collaborators have extended it into a small genre.

## The Annotated Transformer (2018)

- **URL:** https://nlp.seas.harvard.edu/annotated-transformer/
- **Repo:** https://github.com/harvardnlp/annotated-transformer (≈7.3k stars, 1.5k forks)
- **Authors:** Sasha Rush, with later co-authors (Austin Huang, Suraj Subramanian et al.) on the updated 2022 version.
- **Format:** A line-by-line walkthrough of Vaswani et al.'s "Attention is All You Need," with every architectural component (multi-head attention, positional encoding, label smoothing, beam search) implemented in PyTorch immediately adjacent to the relevant prose from the paper.
- **Significance:** Became the canonical onboarding document for an entire generation of ML researchers learning the Transformer. The format is widely emulated; Karpathy's video genre is the YouTube-native sibling of this written-code-and-prose genre.
- **License:** MIT.

## The Annotated S4 (2022)

- **URL:** https://srush.github.io/annotated-s4/
- **Repo:** https://github.com/srush/annotated-s4
- **Co-authors:** Sasha Rush and Sidd Karamcheti.
- **Subject:** Albert Gu, Karan Goel, and Christopher Ré's S4 (Structured State Space for Sequences) — the paper that opened the modern SSM era and led to Mamba.
- **Implementation:** Re-implements S4 from scratch in JAX/Flax. Demonstrates the model on Long Range Arena, MNIST, CIFAR-10, QuickDraw.
- **Significance:** Made SSMs intellectually accessible at exactly the moment when the field needed an explainer that wasn't just the equations. Cited by every subsequent SSM survey and tutorial.

## OpenNMT (2016–2017)

- **URL:** https://opennmt.net/
- **Paper:** "OpenNMT: Open-Source Toolkit for Neural Machine Translation," Klein, Kim, Deng, Senellart, Rush. ACL 2017 Demo (best demo award).
- **Joint project** of Harvard NLP and SYSTRAN.
- **Significance:** One of the first widely-used open-source NMT toolkits. The model that proved Rush's instinct that the "infrastructure as research artifact" pattern was as productive as paper-writing. Direct lineage to Hugging Face Transformers a few years later.

## Hugging Face Transformers (2020)

- **Paper:** "Transformers: State-of-the-Art Natural Language Processing," Wolf et al. EMNLP 2020 demo. Rush is a listed co-author.
- **Significance:** The library that made every pretrained Transformer interoperable. Rush was the senior academic voice in early HF, helping shape its open-source-first publishing norms.

## Pytorch-Struct (2019–2020)

- **URL:** https://github.com/harvardnlp/pytorch-struct
- **Subject:** Fast, general, tested differentiable structured prediction primitives (CRFs, HMMs, dependency parsers, etc.) in PyTorch.
- **Significance:** Rush's argument-in-code that structured prediction remains a first-class tool in the deep-learning era. The library is the practical companion to his recurring stance that "structure still matters."

## The Puzzles Series (2022–present)

Rush has built a family of pedagogical "puzzle" notebooks, each forcing the reader to derive an entire subfield from primitives within a strict line-budget. The series:

- **Tensor Puzzles** — https://github.com/srush/Tensor-Puzzles — 21 one-line PyTorch broadcasting exercises.
- **GPU Puzzles** — https://github.com/srush/GPU-Puzzles — CUDA-via-Numba puzzles for learning GPU parallel programming. Used in CS 5781 at Cornell Tech and widely re-implemented in raw CUDA, Triton, Mojo, etc.
- **Triton Puzzles** — https://github.com/srush/Triton-Puzzles
- **Autodiff Puzzles** — https://github.com/srush/Autodiff-Puzzles
- **LLM Training Puzzles** — https://github.com/srush/LLM-Training-Puzzles — distributed-training/parallelism puzzles.

The puzzles are the most explicit instantiation of Rush's pedagogical contract: **if you can solve the puzzles, you have proven you understand the substrate**. The constraint (one line, strict primitives, no library shortcuts) is the proof.

## Thinking Like Transformers / RASP / RASPy (2022–2023)

- **URL:** https://srush.github.io/raspy/
- **Background:** Builds on Weiss, Goldberg, Yahav's "Thinking Like Transformers" (RASP language).
- **Contribution:** Rush built RASPy, a Python embedding of RASP, so people could write Transformer-equivalent programs and reason about what transformer attention can and cannot compute.
- **Significance:** Theory-meets-pedagogy. Foreshadows his later interest in "The Illusion of State in State-Space Models" (ICLR 2024) — what classes of computation different architectures can and cannot express.

## Sources

- https://nlp.seas.harvard.edu/annotated-transformer/
- https://github.com/harvardnlp/annotated-transformer
- https://srush.github.io/annotated-s4/
- https://github.com/srush/annotated-s4
- https://github.com/srush/Tensor-Puzzles
- https://github.com/srush/GPU-Puzzles
- https://srush.github.io/raspy/
- https://opennmt.net/
- https://aclanthology.org/P17-4012.pdf (OpenNMT paper)
