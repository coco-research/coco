# DSPy and Percy Liang's canonical works

Sources:
- DSPy repo: https://github.com/stanfordnlp/dspy
- HELM paper: https://arxiv.org/abs/2211.09110
- FMTI 2025: https://arxiv.org/abs/2512.10169
- Foundation Models report (CRFM 2021): https://arxiv.org/abs/2108.07258
Retrieved: 2026-05-27

## DSPy — Declarative Self-improving Python
- A framework for **programming language models rather than prompting them**.
- "Iterate fast on building modular AI systems with algorithms for optimizing their prompts and weights."
- Authors include Omar Khattab (primary), Arnav Singhvi, Paridhi Maheshwari, Zhiyuan Zhang, Christopher Potts, Matei Zaharia, others. Percy Liang advises / co-leads through the Stanford NLP group.
- Latest release: **v3.2.1 (May 5, 2026)**.
- Total releases: 109.
- 4,541 commits on main.
- **34.7k GitHub stars, 2.9k forks** — substantial adoption.
- 99.4% Python.
- Discord community.
- Documentation at dspy.ai.

The DSPy thesis aligns with Liang's long-standing argument: prompt engineering is brittle and unprincipled; we need **declarative abstractions that can be compiled and optimized**, the same way SQL was the abstraction for databases. Liang's involvement positions DSPy as the "programming with prompts is the right abstraction" public stance.

## Canonical works inventory

### "On the Opportunities and Risks of Foundation Models" (CRFM, 2021)
- arXiv: 2108.07258
- ~100 co-authors led by Bommasani, with Liang as senior author.
- **Coined the term "foundation model."**
- Set the agenda for the field — what makes a foundation model, social implications, technical structure.
- This is **the single most-cited piece of his recent career** and the founding artifact of CRFM.

### HELM (2022)
- Already detailed in 04-helm-and-ahelm.md.
- The defining LLM evaluation framework.

### SQuAD (2016)
- Stanford Question Answering Dataset.
- With Pranav Rajpurkar, Konstantin Lopyrev, Liang.
- Defined extractive QA benchmark.

### CodaLab Worksheets
- A reproducibility infrastructure project.
- Maintains full experimental provenance from raw data to final results.
- Enables "executable papers."
- Pre-dates Marin and shows Liang's reproducibility obsession is decade-old.

### AlpacaEval
- Stanford project for automated LLM-as-judge evaluation.
- Liang involved as senior CRFM faculty.

### Foundation Model Transparency Index
- Already detailed in 03-foundation-model-transparency-index-2025.md.

### Marin
- Already detailed in 02-marin-announcement-may-2025.md.

## Implications for persona
- The canonical-works arc is consistent: **dataset → benchmark → framework → infrastructure → open lab**.
- Each artifact is reusable by other researchers — Liang's work compounds because he ships public goods.
- The DSPy involvement reinforces his stance that **the right abstraction matters more than raw model power** — there's a strong "programming languages" sensibility (compilation, optimization, declarative semantics) baked into his AI worldview.
