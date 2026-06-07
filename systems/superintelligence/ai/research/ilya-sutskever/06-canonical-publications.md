# Ilya Sutskever — canonical publications

Sources:
- https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks (AlexNet)
- https://arxiv.org/abs/1409.3215 (Seq2Seq)
- https://www.nature.com/articles/nature16961 (AlphaGo Nature paper)
- https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf (GPT-1)
- https://en.wikipedia.org/wiki/Ilya_Sutskever (composite)

Fetched: 2026-05-27

## 1. ImageNet Classification with Deep Convolutional Neural Networks (AlexNet)

- Authors: Alex Krizhevsky, Ilya Sutskever, Geoffrey Hinton
- Venue: NeurIPS 2012
- Citation count: 100,000+ (as of 2026)
- Significance: Won the ImageNet Large Scale Visual Recognition Challenge by a margin large enough to mark the beginning of the modern deep learning era. Demonstrated that depth, GPU acceleration, dropout, and ReLU activations could be combined into a system that beat hand-engineered features by an order of magnitude.
- Sutskever's contribution: Co-designed and trained the network alongside Krizhevsky on two GTX 580 GPUs.

## 2. Sequence to Sequence Learning with Neural Networks

- Authors: Ilya Sutskever, Oriol Vinyals, Quoc V. Le
- Venue: NeurIPS 2014
- arXiv: 1409.3215
- Citation count: ~28,000 (as of 2026)
- Significance: Introduced the encoder-decoder architecture that became the foundation for neural machine translation, then for the original Transformer (2017) and ultimately for GPT. NeurIPS 2024 Test of Time award.
- Key insight: Variable-length input and output sequences can be mapped end-to-end by a deep LSTM-LSTM pair without intermediate hand-engineered representations.

## 3. AlphaGo (Nature paper, 2016)

- Authors: David Silver, Aja Huang, Chris J. Maddison, ..., Ilya Sutskever (co-author), ..., Demis Hassabis
- Venue: Nature, January 2016
- Significance: First system to defeat a professional Go player; demonstrated that deep RL + Monte Carlo Tree Search could solve a game considered intractable for a decade.
- Sutskever's contribution: Co-author on the deep learning components.

## 4. Improving Language Understanding by Generative Pre-Training (GPT-1)

- Authors: Alec Radford, Karthik Narasimhan, Tim Salimans, Ilya Sutskever
- Venue: OpenAI technical report, June 2018
- Significance: Introduced the GPT lineage — generative pre-training of a Transformer language model followed by task-specific fine-tuning. Direct ancestor of GPT-2, GPT-3, GPT-4, o1.
- Sutskever's contribution: Senior author; the strategic bet on scaling generative pre-training was his.

## 5. Training Recurrent Neural Networks (PhD thesis)

- Author: Ilya Sutskever
- Year: 2013
- Institution: University of Toronto
- Advisor: Geoffrey Hinton
- Significance: Foundational work on optimization for RNNs (Hessian-free methods, careful initialization). Predates the LSTM-driven Seq2Seq era but established the optimization vocabulary.

## 6. Conversation as the AI interface (Lex Fridman podcast, 2020)

- Not a publication, but a primary public talk where Sutskever first crystallized the "scaling hypothesis as a research program" view that defined his OpenAI era.

## 7. Co-authorship on AlphaGo, TensorFlow, CLIP, DALL-E

- Sutskever's name appears on or is associated with the early architectural decisions behind most of OpenAI's flagship systems (GPT lineage, CLIP, DALL-E, o1).
- His direct technical authorship after ~2018 is harder to disentangle from his role as chief scientist, but he is credited as research lead on the GPT and reasoning-model directions.

## Pattern across publications

Sutskever's name shows up at moments when a particular bet was being made:
- 2012: bet that depth + GPU + ReLU would beat hand-engineered features (AlexNet).
- 2014: bet that end-to-end neural sequence mapping would replace pipeline NMT (Seq2Seq).
- 2018-2020: bet that scaling generative pre-training was the path to general capability (GPT).
- 2024-onward: bet that something *beyond* the GPT regime is needed for superintelligence (SSI).

The through-line is a willingness to commit early to a large-scale empirical bet before the evidence is conclusive.
