# Horace He — Personal Site and Biographical Anchor

Source: https://horace.io/
LinkedIn: https://www.linkedin.com/in/horacehe/
GitHub: https://github.com/chillee (handle "Chillee")
Google Scholar: https://scholar.google.com/citations?user=exzHWOwAAAAJ&hl=en
X / Twitter: https://x.com/cHHillee (~49.6K followers)

## Identity

- Real name: **Horace He** (handle `cHHillee` on X, `Chillee` on GitHub)
- Substack: **Thonk From First Principles** (https://www.thonking.ai/)
- Personal site tagline: "ML Systems researcher / engineer focused on the engineering side of fast ML"

## Education

- **Cornell University** — BS Computer Science / Mathematics, graduated 2020
- Competed for Cornell in the **ICPC World Finals** (competitive programming)
- Previously maintained one of the most popular **VSCodeVim** extensions (open-source community track record predates ML work)

## Career timeline

- 2018 — Compilers intern, Google
- 2019 — PyTorch intern, Facebook (now Meta)
- 2020–2025 — **PyTorch Core Compilers team at Meta**. Primary contributor on torch.compile and FlexAttention. Co-author of the PyTorch 2 paper at ASPLOS 2024.
- 2025 (~March) — Departs Meta. Announces move to **Thinking Machines Lab** (Mira Murati's startup) in a Substack post dated March 4, 2025 titled "Why PyTorch is an amazing place to work… and Why I'm Joining Thinking Machines."
- 2025–present — Thinking Machines Lab, ML systems / kernels / inference research.

## Canonical written works

1. **"Making Deep Learning Go Brrrr From First Principles"** — https://horace.io/brrr_intro.html
   The single most-cited introductory text in the modern ML-performance pedagogy stack. Established his three-regime framework (compute-bound, memory-bandwidth-bound, overhead-bound).
2. **"State of Machine Learning Frameworks"** — The Gradient, written after his PyTorch internship.
3. **"Why PyTorch is an amazing place to work… and Why I'm Joining Thinking Machines"** — https://www.thonking.ai/p/why-pytorch-is-an-amazing-place-to (March 4, 2025).
4. **"Defeating Nondeterminism in LLM Inference"** — https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ (September 10, 2025). First post on Thinking Machines' Connectionism research blog.
5. **PyTorch blog: "FlexAttention: The Flexibility of PyTorch with the Performance of FlashAttention"** — https://pytorch.org/blog/flexattention/ (August 7, 2024), co-authored with Driss Guessous, Yanbo Liang, Joy Dong.

## Canonical engineering artifacts

- **torch.compile** — primary contributor. The default compile path in PyTorch 2.x.
- **FlexAttention** — PyTorch 2.5 (October 2024) ships `torch.nn.attention.flex_attention`. He is the principal designer.
- **gpt-fast** — open-source transformer-inference reference. "<1000 lines of native PyTorch with quantization, speculative decoding, NVIDIA + AMD support."
- **batch-invariant-ops** — https://github.com/thinking-machines-lab/batch_invariant_ops (released September 2025). Drop-in `torch.Library` replacements for RMSNorm, MatMul, Softmax, Attention that produce identical outputs regardless of batch size.

## Notes on identity confidence

- Identifier confirmed across personal site, LinkedIn, GitHub, X, Google Scholar, PyTorch blog bylines, MLSys 2025 paper authorship list, ASPLOS 2024 paper authorship list, and Thinking Machines Lab Connectionism byline. Confidence very high.
- Sole Horace He in the ML systems community. There is a separate "Prof. Qile (Horace) He" in the social sciences in the UK — unrelated person.
