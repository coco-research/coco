# Tri Dao — Personal Site (tridao.me)

Source: https://tridao.me/
Extracted: 2026-05-27

## Current affiliations

- **Assistant Professor of Computer Science**, Princeton University (Dao AI Lab director)
- **Co-founder & Chief Scientist**, Together AI

## Education

- **PhD** in Computer Science, Stanford University (~2023)
- Stanford advisors per public record: Christopher Ré + Stefano Ermon (Hazy Research / Statistical ML lab lineage)

## Research focus statement

> "Machine learning and systems, with a focus on efficient training and inference,
> particularly emphasizing hardware-aware algorithms and sequence models capable of
> processing long-range dependencies."

The lab's two stated research domains:

1. **Hardware-aware algorithms** — computational methods optimized for specific hardware constraints (memory hierarchy, tensor cores, SFU, MMA throughput).
2. **Sequence models with long-range memory** — architectures capable of processing extended contextual information (state space models, sub-quadratic attention, hybrid models).

## Selected publications (highlighted on his site)

| Paper                               | Venue                          | Year | Recognition                                       |
| ----------------------------------- | ------------------------------ | ---- | ------------------------------------------------- |
| FlashAttention                      | NeurIPS                        | 2022 | Best Paper at ICML Hardware Workshop; Stanford OSS Prize 2024 |
| Monarch                             | ICML                           | 2022 | Outstanding Paper runner-up                       |
| Mamba                               | COLM                           | 2023 | Outstanding Paper                                 |
| Transformers are SSMs / Mamba-2     | ICML                           | 2024 | —                                                 |
| FlashAttention-3                    | NeurIPS                        | 2024 | Spotlight                                         |
| FlashAttention-4                    | MLSys / blog                   | 2026 | Blackwell-tuned                                   |
| Mamba-3                             | ICLR                           | 2026 | "Inference-first" SSM                             |
| SonicMoE                            | ICLR                           | 2026 | Hardware-efficient MoE                            |
| Speculative Speculative Decoding    | ICLR                           | 2026 | Tanishq Kumar + Tri Dao + Avner May               |
| Gram Newton-Schulz Algorithm        | blog series                    | 2026 | Hardware-optimized                                |

## Recent blog posts (2026)

- **FlashAttention-4: Algorithm and Kernel Pipelining Co-Design for Asymmetric Hardware Scaling** (Mar 5, 2026)
- **Mamba-3 Part 1** (Apr 2026) — "What would an SSM designed with **inference** in mind look like?"
- **Mamba-3 Part 2** (Apr 2026)
- **Gram Newton-Schulz Algorithm** (2026)
- **SonicMoE: Hardware-Efficient MoEs** (2026)

## Contact & socials (per site)

- Email: tri [at] tridao [dot] me
- GitHub: https://github.com/tridao
- X / Twitter: https://x.com/tri_dao (@tri_dao)
- Google Scholar: https://scholar.google.com/citations?user=NQRw0bQAAAAJ
- CV: PDF updated 01/2026

## Lab composition

~15 members. Faculty: Tri Dao (Assistant Professor). 8 PhD students (several co-advised cross-institution). 4 Master's / undergrad. Cross-institution collaborations with UC Berkeley.

## Key framing extracted

- The lab treats kernels and algorithms as **co-designed** — they don't separate "the math" from "what GPU memory hierarchy does."
- "Hardware-aware" is the recurring banner — appears in lab tagline, in his AI2050 fellowship description, and in every paper title.
- Sequence modeling is a sister axis to hardware work — FlashAttention pushes attention to its kernel limit; Mamba steps off attention onto SSMs. Both are answers to the same question: "How do you make sequence models that respect the memory hierarchy?"
