# Barret Zoph — Canonical Works and Publications

Source: Google Scholar (user NL_7iTwAAAAJ), arXiv, JMLR, and personal site barretzoph.github.io. Citation counts as of May 2026.

## First-author / defining papers

### "Neural Architecture Search with Reinforcement Learning"
- Co-author: Quoc V. Le. ICLR 2017. arXiv 1611.01578.
- Submitted as a Google Brain Resident — Zoph's defining paper.
- Method: use an RNN controller, trained with REINFORCE, to generate the description of a child neural network; reward = child's validation accuracy.
- Results: CIFAR-10 test error 3.65% (state-of-the-art at the time, 1.05× faster than prior best); on Penn Treebank discovered a new recurrent cell beating LSTM.
- ~8,300 citations. Founded the modern NAS / AutoML research thread.
- URL: https://arxiv.org/abs/1611.01578

### "Learning Transferable Architectures for Scalable Image Recognition"
- Co-authors: Vasudevan, Shlens, Le. CVPR 2018.
- The "NASNet" follow-up. Searches a smaller cell space on CIFAR-10 and transfers it to ImageNet.
- ~8,900 citations.

### "Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity"
- Co-authors: William Fedus (first), Noam Shazeer. JMLR 2022. arXiv 2101.03961.
- Simplified Mixture-of-Experts routing (top-1 instead of top-2), enabling stable training of trillion-parameter sparse models. 7× pre-training speedup vs T5.
- URL: https://arxiv.org/abs/2101.03961

### "ST-MoE: Designing Stable and Transferable Sparse Expert Models"
- Co-authors: Fedus, Bello, et al. 2022. arXiv 2202.08906.
- Follow-up addressing training instability and transfer learning weaknesses in MoE.
- URL: https://arxiv.org/abs/2202.08906

## Major co-author works

### "Scaling Instruction-Finetuned Language Models" (FLAN-T5 / FLAN-PaLM)
- Authors: Chung, Hou, Longpre, Zoph, et al. JMLR 2024 (arXiv 2210.11416, October 2022).
- Demonstrated that instruction tuning at scale (1,836 tasks) substantially improves performance, generalization, and reasoning.
- ~6,077 citations. Co-authored with Hyung Won Chung and Jason Wei (both pair-relevant).

### "Emergent Abilities of Large Language Models"
- Authors: Wei, Tay, Bommasani, Raffel, Zoph, Borgeaud, Yogatama, Bosma, Zhou, Metzler, Chi, Hashimoto, Vinyals, Liang, Dean, Fedus. TMLR 2022. arXiv 2206.07682.
- Defined the "emergent ability" concept: an ability is emergent if absent in smaller models but present in larger models.
- ~6,300 citations.

### "GLaM: Efficient Scaling of Language Models with Mixture-of-Experts"
- 2021. Du et al., Zoph as co-author. Decoder-only sparse MoE language model.

### "GPT-4 Technical Report" and "GPT-4o System Card"
- 2023 and 2024 respectively. Listed as one of many OpenAI co-authors reflecting his post-training leadership role.

### "AutoAugment", "RandAugment", "SpecAugment"
- 2018–2019. Cubuk et al., Zoph as co-author. Highly-cited data augmentation policy work. Influence persists across vision and ASR pipelines.

## Talks and non-paper artifacts

### "ChatGPT and The Art of Post-Training"
- With John Schulman. Stanford HAI Seminar, January 28, 2025. Not recorded; slides public.
- Slides URL: https://docs.google.com/presentation/d/11KWCKUORnPpVMSY6vXgBeFSWo7fJcuGQ9yuR6vC1pzE/edit
- Schulman X thread announcing slides: https://x.com/johnschulman2/status/1891539960743743756

### "Scaling Transformers" — Stanford CS25
- Earlier Google Brain era talk on sparse expert scaling. ~1h05m.

### Data Exchange Podcast Ep. 125
- With William Fedus (Liam Fedus). Google Brain era discussion on sparse models.
- URL: https://www.youtube.com/watch?v=LYeTmjJXSDo

## Citation totals

- ~133,000 total citations.
- h-index 62.
- Confirms Tier-1 academic standing in addition to applied OpenAI/TML work.
