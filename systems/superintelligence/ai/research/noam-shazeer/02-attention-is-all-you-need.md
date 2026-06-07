# "Attention Is All You Need" — Shazeer's specific contribution

Source paper: https://arxiv.org/abs/1706.03762
Secondary sources:
- https://en.wikipedia.org/wiki/Attention_Is_All_You_Need
- https://www.semanticscholar.org/paper/Attention-is-All-you-Need-Vaswani-Shazeer/204e3073870fae3d05bcbc2f6a8e263d9b72e776
- https://aiwiki.ai/wiki/attention_is_all_you_need_transformer

## Publication

- **Venue:** NeurIPS 2017
- **Authors (in order):** Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin
- **Affiliation:** All authors at Google Brain or Google Research at the time.
- **Equal contribution note in the paper:** All authors contributed equally; the listed order was randomized after extensive contribution review.

## Shazeer's specific contributions (per secondary literature and post-hoc author accounts)

Shazeer is generally credited with the formulation that made the Transformer practical at scale:

1. **Multi-head attention.** The mechanism that runs `h` attention functions in parallel, each on a different learned linear projection of queries, keys, and values, then concatenates and projects again.
2. **Scaled dot-product attention with the 1/sqrt(d_k) scaling factor.** Without this scaling the dot products grow large in magnitude as `d_k` increases, pushing the softmax into a flat region where gradients vanish. Shazeer noticed this experimentally during the first ablations and proposed the fix that became canonical.
3. **The parameter-free position representation** approach used in the original paper (sinusoidal positional encodings).

Post-publication, Aidan Gomez and others on the team have publicly described Shazeer as "the other person involved in nearly every detail of the work alongside Vaswani" — effectively the second pillar of the paper.

## Why this matters for the persona

- Shazeer is one of the **eight people who literally invented the Transformer**. That single fact is the source of his standing.
- His specific moves on the paper — picking a softmax scaling constant to fix a vanishing-gradient problem he found by reading curves; replacing serial attention heads with parallel ones — are the seeds of his lifetime style: **architectural insight justified by hand-derived numerical reasoning, then validated by one well-designed ablation**.
- He has continued this style through MoE, GShard, Switch Transformer, GLU variants — each is a small architectural tweak with outsized empirical payoff.

## Citation note

As of 2026-05-27 the paper has well over **150,000 citations** on Google Scholar, making it one of the most cited papers in the history of computer science. Shazeer is the second-listed author on the canonical paper that defines modern AI.
