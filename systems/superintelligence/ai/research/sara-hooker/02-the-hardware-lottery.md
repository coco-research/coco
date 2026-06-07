# The Hardware Lottery (Hooker, 2020) — Research Notes

Source documents:

- https://arxiv.org/abs/2009.06489
- https://cacm.acm.org/research/the-hardware-lottery/
- https://hardwarelottery.github.io/
- https://research.google/pubs/pub49502/

## Bibliographic data

- Author: Sara Hooker (sole author).
- Affiliation at time of publication: Google Research, Brain Team.
- arXiv submission: September 14, 2020. arXiv ID 2009.06489.
- Republished as a Communications of the ACM "Research Highlights" piece.

## Defining claim

> "A hardware lottery is when a research idea wins because it is suited to the available software and hardware and not because the idea is superior to alternative research directions."

This is the line every secondary source quotes back. It is the load-bearing definition for the entire later body of her efficiency, sparsity, and compute-equity work.

## Argument structure

The essay has three moves:

1. **Historical proof of the mechanism.** She walks through cases from early computer science where the dominant hardware substrate effectively decided which research direction was canonized as "the right path" — Babbage's Analytical Engine, the dominance of CPUs over alternative computational substrates, the late-1980s collapse of neural-network research when general-purpose hardware made deep networks intractable. The historical examples are not nostalgia; they are existence proofs that better ideas have been suppressed by accidents of hardware availability.

2. **The current moment is a special-purpose lottery.** With the rise of GPUs, TPUs, and other domain-specific accelerators, the lottery has become more aggressive, not less. Specialized hardware now disproportionately rewards the dense-matrix-multiplication patterns of contemporary deep learning. Research ideas that do not pattern-match to "lots of multiply-accumulate on dense tensors" face a steeper and steeper barrier to demonstrating competitive performance.

3. **The cost is borne unevenly.** The communities most equipped to bend hardware to their ideas (well-funded industrial labs) get to win lotteries. Communities without that compute leverage do not. The widening gap between favored and unfavored research directions is a structural problem, not a meritocratic outcome.

## Why this matters for her later work

Every subsequent thread in Hooker's career is downstream of the Hardware Lottery thesis:

- The pruning / sparsity work ("What Do Compressed Deep Neural Networks Forget?", "When Less is More") is a direct attempt to make non-dense architectures competitive.
- The Aya / multilingual program at Cohere For AI is the global-majority equity case applied to data and language coverage.
- The compute-thresholds critique (Hooker, 2024) is the policy expression of the same thesis: regulating by FLOPs locks in the lottery winners.
- Adaption Labs (2025–2026) is the next escalation — she now argues that the dense-pretraining lottery is itself a dead end, and the next era will be won by efficient adaptation rather than ever-larger pretraining runs.

## Most-cited line in secondary discussion

In her MLST and TWIML appearances she frequently restates the essay as: "Hardware doesn't just enable research, it determines which research wins." When she says this, she is making a normative claim, not a descriptive one.
