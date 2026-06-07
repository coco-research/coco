# Scaling Laws for Neural Language Models — Kaplan et al., 2020

## Citation

- Title: "Scaling Laws for Neural Language Models"
- arXiv: 2001.08361
- Submission date: January 23, 2020
- URL: https://arxiv.org/abs/2001.08361

## Authors (in published order)

1. **Jared Kaplan** (first author)
2. Sam McCandlish
3. Tom Henighan
4. Tom B. Brown
5. Benjamin Chess
6. Rewon Child
7. Scott Gray
8. Alec Radford
9. Jeffrey Wu
10. Dario Amodei

Kaplan and McCandlish are credited as lead investigators in the abstract and Anthropic public material; the paper acknowledges Kaplan as the first author and primary author of the analysis.

## Abstract (direct quote)

> "We study empirical scaling laws for language model performance on the cross-entropy loss. The loss scales as a power-law with model size, dataset size, and the amount of compute used for training, with some trends spanning more than seven orders of magnitude. Other architectural details such as network width or depth have minimal effects within a wide range. Simple equations govern the dependence of overfitting on model/dataset size and the dependence of training speed on model size. These relationships allow us to determine the optimal allocation of a fixed compute budget. Larger models are significantly more sample-efficient, such that optimally compute-efficient training involves training very large models on a relatively modest amount of data and stopping significantly before convergence."

## Key claims that became the foundation of Kaplan's stances

- **Loss is a power-law function** of model size, dataset size, and training compute — across more than seven orders of magnitude.
- **Architecture details (width, depth) matter very little** within a reasonable band; size dominates.
- **Larger models are more sample-efficient.** Optimally compute-efficient training pushes very large models, modest data, and early-stopping.
- **Predictable overfitting** as a function of the model-to-data ratio.
- **Optimal compute allocation** can be derived from the empirical curves.

## Why this is Kaplan's signature work

The paper is treated across all subsequent profiles as the foundational empirical result that motivated the "scale-up" strategy at OpenAI (GPT-3 and successors), at Anthropic (Claude), and at most subsequent labs. Anthropic's Responsible Scaling Policy is explicitly framed as the safety-side complement: if capabilities scale with compute predictably, safety measures must scale with capabilities equally predictably.

## Sequel: Scaling Laws for Autoregressive Generative Modeling

- arXiv: 2010.14701, October 2020
- First author: Tom Henighan. Kaplan is second author.
- Extended the same empirical-power-law framework from text to image generation, video, multimodal image-text, and mathematical problem solving — argued the same scaling pattern is approximately universal.
- URL: https://arxiv.org/abs/2010.14701
