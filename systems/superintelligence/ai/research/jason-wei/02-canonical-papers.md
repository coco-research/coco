# Jason Wei — Canonical Publications

Jason Wei's published work clusters into four research arcs: instruction tuning, chain-of-thought reasoning, emergent abilities / scaling, and post-training with verifiable rewards. The first three were published 2021–2023 while at Google Brain; the fourth is his ongoing arc at OpenAI then Anthropic.

## Arc 1 — Instruction tuning (the "usefulness" bridge)

### Finetuned Language Models Are Zero-Shot Learners (FLAN)

- **Authors:** Jason Wei*, Maarten Bosma, Vincent Y. Zhao, Kelvin Guu, Adams Wei Yu, Brian Lester, Nan Du, Andrew M. Dai, Quoc V. Le
- **Venue:** ICLR 2022
- **arXiv:** https://arxiv.org/abs/2109.01652
- **One-liner:** Showed that finetuning a 137B LM on a mixture of NLP tasks described in natural language improves zero-shot generalization to unseen tasks. The first widely-cited paper to operationalize "instruction tuning."

Wei is first author. This paper is the conceptual ancestor of every modern instruction-tuned model (GPT-3.5-Turbo, Claude, Gemini, etc.).

### Scaling Instruction-Finetuned Language Models (FLAN-T5)

- **Authors:** Hyung Won Chung, Le Hou, Shayne Longpre, Barret Zoph, Yi Tay, William Fedus, Yunxuan Li, Xuezhi Wang, Mostafa Dehghani, Siddhartha Brahma, Albert Webson, Shixiang Shane Gu, Zhuyun Dai, Mirac Suzgun, Xinyun Chen, Aakanksha Chowdhery, Sharan Narang, Gaurav Mishra, Adams Yu, Vincent Zhao, Yanping Huang, Andrew Dai, Hongkun Yu, Slav Petrov, Ed H. Chi, Jeff Dean, Jacob Devlin, Adam Roberts, Denny Zhou, Quoc V. Le, **Jason Wei**
- **Venue:** JMLR 2024 (initially arXiv 2022)
- **arXiv:** https://arxiv.org/abs/2210.11416
- **One-liner:** Scaled FLAN to 1.8k tasks and trained models from T5-small to PaLM-540B. Established the empirical scaling law of instruction tuning.

## Arc 2 — Chain-of-Thought (the "give the model space to think" move)

### Chain-of-Thought Prompting Elicits Reasoning in Large Language Models

- **Authors:** Jason Wei*, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed H. Chi, Quoc V. Le, Denny Zhou
- **Venue:** NeurIPS 2022 (oral)
- **arXiv:** https://arxiv.org/abs/2201.11903
- **One-liner:** Demonstrated that prompting an LLM with intermediate reasoning steps ("chain-of-thought") dramatically improves performance on arithmetic, commonsense, and symbolic reasoning tasks. Coined the term "chain-of-thought prompting."

This is Wei's most-cited paper. As of 2026, it has 13,000+ citations. The technique was the conceptual seed for o1's inference-time reasoning and for the entire RLVR (reinforcement learning with verifiable rewards) post-training arc.

### Self-Consistency Improves Chain of Thought Reasoning

- **Authors:** Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc V. Le, Ed H. Chi, Sharan Narang, Aakanksha Chowdhery, Denny Zhou
- **Venue:** ICLR 2023
- **arXiv:** https://arxiv.org/abs/2203.11171
- **One-liner:** Sampling multiple CoT reasoning paths and majority-voting the final answer significantly outperforms greedy decoding. Set up the path to inference-time scaling.

## Arc 3 — Emergence and scaling

### Emergent Abilities of Large Language Models

- **Authors:** Jason Wei, Yi Tay, Rishi Bommasani, Colin Raffel, Barret Zoph, Sebastian Borgeaud, Dani Yogatama, Maarten Bosma, Denny Zhou, Donald Metzler, Ed H. Chi, Tatsunori Hashimoto, Oriol Vinyals, Percy Liang, Jeff Dean, William Fedus
- **Venue:** TMLR 2022
- **arXiv:** https://arxiv.org/abs/2206.07682
- **One-liner:** Defined an "emergent ability" of an LLM as a capability that is not present in smaller models but is present in larger models. Catalogued 137 emergent abilities. The canonical reference for "phase transitions in LLM capability."

This paper drew significant pushback in 2023 from Schaeffer et al. ("Are Emergent Abilities of Large Language Models a Mirage?"). Wei has consistently defended the framing on X and at NeurIPS panels — see recent_signal section for his 2025 restatement.

### Inverse scaling can become U-shaped

- **Authors:** Jason Wei, Yi Tay, Quoc V. Le
- **Venue:** EMNLP 2023
- **arXiv:** https://arxiv.org/abs/2211.02011
- **One-liner:** Tasks where scaling initially hurts performance can become U-shaped at sufficient scale — i.e., capability returns at the high end. A direct empirical attack on the "scaling will plateau" position.

## Arc 4 — Post-training, RL, and verification (OpenAI / Anthropic era)

### Larger Language Models Do In-Context Learning Differently

- **Authors:** Jerry Wei, Jason Wei, Yi Tay, Dustin Tran, Albert Webson, Yifeng Lu, Xinyun Chen, Hanxiao Liu, Da Huang, Denny Zhou, Tengyu Ma
- **arXiv:** https://arxiv.org/abs/2303.03846
- **One-liner:** Larger models can override semantic priors with in-context examples; smaller models cannot. Sets up a scaling-driven view of in-context learning.

### Public talks and essays substituting for papers at OpenAI / Anthropic

After joining OpenAI in 2023, Wei published far fewer formal papers — partly because OpenAI publishes less and partly because his work moved into post-training pipelines that aren't paper-shaped. His thinking from 2023 onward is best read through:

- His personal site essays at https://www.jasonwei.net/
- Stanford CS25 lectures
- Latent Space podcast appearances
- X / Twitter threads

See `03-jasonwei-net-essays.md`, `04-talks-and-podcasts.md`, and `05-recent-signals.md`.

## Why this body of work matters

Jason Wei is, with Hyung Won Chung and Denny Zhou, one of the architects of the "post-training matters" thesis. The Chain-of-Thought → Self-Consistency → CoT-RL → o1 line is one of the most direct intellectual chains in modern LLM history, and Wei sits at its origin. His emergence paper is also the canonical citation for "scaling produces capability discontinuities" — the central tenet of the optimistic-scaling camp at Anthropic, OpenAI, and DeepMind.
