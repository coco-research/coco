# Arthur Mensch — Chinchilla scaling-laws paper

## Citation

Hoffmann, J., Borgeaud, S., **Mensch, A.**, Buchatskaya, E., Cai, T., Rutherford, E., de Las Casas, D., Hendricks, L. A., Welbl, J., Clark, A., Hennigan, T., Noland, E., Millican, K., van den Driessche, G., Damoc, B., Guy, A., Osindero, S., Simonyan, K., Elsen, E., Rae, J. W., Vinyals, O., Sifre, L. **"Training Compute-Optimal Large Language Models."** arXiv:2203.15556, March 29, 2022.

Source: https://arxiv.org/abs/2203.15556

Mensch is the third-listed author in a paper where author order at DeepMind typically signals contribution; the paper is widely cited as the canonical empirical statement of compute-optimal scaling and Mensch is consistently named as a co-author of central significance. (Note: arXiv page itself does not annotate co-first-author designation; the paper was presented at NeurIPS 2022.)

## Headline claim

For compute-optimal training, model parameters and training tokens should be scaled **equally**. For every doubling of model size, training tokens should also double.

Implication: most existing large language models (Gopher, GPT-3, Megatron-Turing NLG) were **significantly undertrained** — too many parameters for the data and compute used.

## Empirical method

- Trained 400+ language models from 70M to 16B parameters across varying token counts.
- Derived a scaling law that yielded the optimal point given a fixed compute budget.

## The Chinchilla result

The paper introduced **Chinchilla**, a 70B-parameter model trained on 4× the data of Gopher (which was 280B parameters) using the **same total compute**. Chinchilla outperformed Gopher, GPT-3, and Megatron-Turing NLG across a wide range of evaluation tasks. Notably 67.5% on MMLU, >7% absolute improvement over Gopher.

## Why this matters for the persona

Three operating principles flow from this paper into how Mensch later built Mistral:

1. **Smaller, better-trained models can beat larger under-trained ones.** Direct ancestry of Mistral 7B (September 2023) and the entire small-open-weights line — Mistral as an institution operationalized Chinchilla.
2. **Compute efficiency is a strategic axis.** A European lab without OpenAI-scale capital can compete by training on the optimal curve rather than the parameter-count curve.
3. **Data is half the equation.** The early Mistral models leaned on careful data curation and multilingual coverage (especially European languages) — natural fit for Chinchilla logic plus European-sovereignty framing.

## Productive conflict with Kaplan scaling

The Chinchilla result revised the earlier Kaplan et al. 2020 "Scaling Laws for Neural Language Models" (the OpenAI/Anthropic-lineage paper, https://arxiv.org/abs/2001.08361), which had implied model size was the dominant scaling axis and undercounted the value of more training tokens. The Hoffmann–Mensch result re-balanced the two. This is the substantive scientific disagreement underlying the "scaling-laws debate" between the DeepMind/Mistral lineage and the OpenAI/Anthropic lineage — and the structural basis for productive conflict between Mensch and Jared Kaplan / Dario Amodei.
