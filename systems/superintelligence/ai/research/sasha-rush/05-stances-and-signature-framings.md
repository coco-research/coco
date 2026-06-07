# Sasha Rush — Stances and Signature Framings

Each stance below is paired with the public evidence URL that anchors it. No stance is included that cannot be cited.

## Stance 1: Literate code is the proof of understanding

If you cannot fit the explanation in a runnable, readable notebook, you have not understood it yet. The notebook is the explanation; the paper is a summary of the notebook. This is the through-line from The Annotated Transformer to The Annotated S4 to the Puzzles series.

**Evidence:** https://nlp.seas.harvard.edu/annotated-transformer/ ; https://srush.github.io/annotated-s4/ ; https://github.com/srush/Tensor-Puzzles

## Stance 2: Structured prediction remains a first-class tool in the LLM era

Pure transformer sequence models are not the right substrate for every task. Where structure is real (parse trees, alignment lattices, dependency graphs), differentiable structured prediction beats unstructured baselines.

**Evidence:** https://github.com/harvardnlp/pytorch-struct ; OpenNMT's structured decoding work (https://opennmt.net/)

## Stance 3: State space models are a real alternative substrate, but theory matters

SSMs (S4, Mamba, hybrids) are a genuine architectural alternative to attention, not a curiosity. **But** the field needs honest theoretical work on what each architecture can and cannot express, and SSMs as commonly deployed do not in fact carry richer state than transformers. Don't conflate enthusiasm with capability.

**Evidence:** https://arxiv.org/abs/2408.15237 (Mamba in the Llama, hybrid distillation) ; https://arxiv.org/pdf/2404.08819 (Illusion of State in State-Space Models)

## Stance 4: Hybrids beat purebloods

Pure-SSM models and pure-attention models are both worse than the right hybrid. Mamba in the Llama keeps ~25% attention and outperforms scratch-trained linear RNNs at 8B scale. Composer 2 builds on Kimi K2.5 (a transformer base) and adds RL. The right answer is almost always a mix.

**Evidence:** https://arxiv.org/abs/2408.15237 ; https://cursor.com/blog/composer-2-technical-report ; April 2026 podcast: "it does really seem like you need some attention in the process"

## Stance 5: Open source is the engine of progress in LM research

Most of the durable infrastructure (OpenNMT, Transformers, the annotated tutorials, the puzzles, COLM) is open source by design. Closed-lab capability progress is real but underweights the compounding effect of community-shared substrate. Venue and community design are themselves research contributions.

**Evidence:** Co-authorship of HF Transformers (EMNLP 2020); founding of COLM (2024) — https://x.com/srush_nlp/status/1713915565222326656

## Stance 6: Pedagogy compounds — building learners is building the field

Cornell Tech students, the Annotated series, the Puzzles, GPU Puzzles being used in CS 5781 — Rush treats teaching as a research output with longer half-life than any single paper.

**Evidence:** https://github.com/srush/GPU-Puzzles ; https://github.com/srush/Tensor-Puzzles ; YouTube channel https://www.youtube.com/@srush_nlp

## Stance 7: Coding is the cleanest RL substrate; binary rewards are leaving signal on the table

Coding has crisp correctness signals (compile, test, lint) that other RL domains lack. But academic RL fixation on binary rewards wastes the rich mathematical structure available — partial credit, process supervision, tool-use efficiency, and parallelism all give "arbitrary rewards" you can train on.

**Evidence:** https://www.the-information-bottleneck.com/the-future-of-coding-agents-with-sasha-rush-cursorcornell/ (April 2026 podcast) ; https://cursor.com/blog/composer-2-technical-report

## Stance 8: Post-training, not pretraining, is the current locus of agent quality

For coding agents, the gains are in RL post-training applied to realistic in-product sessions, not in a bigger pretraining run. "RL scales" is his summary line — but the unit you scale is environments and reward design, not just GPUs.

**Evidence:** https://simonwillison.net/2025/Oct/29/cursor-composer/ ("Our primary focus is on RL post-training") ; Composer 2 technical report

## Stance 9: Theory and practice both have to ship

The COLM founding, the Simons Institute Special Year, and the Cursor move are the same person making the same bet: that the field needs venues where applied frontier work and theoretical capability work meet in person. Don't trust either-or framings.

**Evidence:** https://simons.berkeley.edu/people/sasha-rush ; COLM founding tweet https://x.com/srush_nlp/status/1713915565222326656

## Productive conflicts

- **Noam Shazeer (transformer-only mindset):** Rush's IsAttentionAllYouNeed.com bet is the institutional form of this disagreement. Shazeer treats attention as the substrate; Rush treats it as one option in a hybrid menu.
- **Demis Hassabis (closed-lab culture):** Rush's life work is open tutorials and open venues. Hassabis's life work is a closed lab that ships closed models. The conflict is not personal but cultural — Rush would push back on any plan that bets on closed-lab capability progress as a moat.

## Pairs well with

- **Andrej Karpathy** — peer in the "build it in a small number of readable lines" pedagogy school. Karpathy's videos and Rush's notebooks are the same artifact in different media.
- **Sebastian Raschka** — peer pedagogue, both write executable book-length tutorials.
- **Albert Gu** — Gu created S4; Rush annotated it. Natural collaborators on SSM theory.
- **Tri Dao** — co-author on Mamba in the Llama, both efficient-architecture realists.
- **Nathan Lambert** — open-research norms, RLHF/post-training expertise. Nathan's RLHF book is the textbook for the very pipeline Rush now runs at Cursor.
