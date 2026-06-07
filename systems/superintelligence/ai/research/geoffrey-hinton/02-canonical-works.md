# Geoffrey Hinton — Canonical Works

## Foundational deep-learning papers

### 1. Backpropagation (1986)

- **Citation:** Rumelhart, D. E., Hinton, G. E., Williams, R. J. "Learning representations by back-propagating errors." *Nature* 323, 533–536 (1986).
- **URL:** https://www.nature.com/articles/323533a0
- **One-liner:** The paper that put backpropagation on the map as the practical training algorithm for multi-layer neural networks. Hinton did not originate backpropagation, but this 1986 *Nature* paper demonstrated for the first time that gradient descent through hidden layers could learn distributed internal representations that captured task structure.

### 2. Boltzmann Machines (1985)

- **Citation:** Ackley, D. H., Hinton, G. E., Sejnowski, T. J. "A learning algorithm for Boltzmann machines." *Cognitive Science* 9, 147–169 (1985).
- **One-liner:** Energy-based stochastic neural network with a learning rule that uses statistical mechanics (the Boltzmann distribution from physics). This is the work the 2024 Nobel Prize in Physics directly cited.

### 3. Deep Belief Nets (2006)

- **Citation:** Hinton, G. E., Osindero, S., Teh, Y. W. "A fast learning algorithm for deep belief nets." *Neural Computation* 18, 1527–1554 (2006).
- **URL:** https://www.cs.toronto.edu/~hinton/absps/fastnc.pdf
- **One-liner:** The greedy layer-wise pretraining recipe that re-opened the door to training deep neural networks before the GPU + ReLU + dropout era made it routine. The paper most credited for the "deep learning renaissance."

### 4. AlexNet (2012)

- **Citation:** Krizhevsky, A., Sutskever, I., Hinton, G. E. "ImageNet classification with deep convolutional neural networks." *NeurIPS* 2012.
- **URL:** https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks
- **One-liner:** Deep learning's ImageNet moment. The result that ended the hand-engineered-features era of computer vision and triggered the modern AI industry. Hinton was supervising; Krizhevsky and Sutskever did the implementation in his lab at Toronto.

### 5. t-SNE (2008)

- **Citation:** van der Maaten, L., Hinton, G. E. "Visualizing data using t-SNE." *JMLR* 9, 2579–2605 (2008).
- **One-liner:** The dimensionality reduction technique that became the default way of visualizing high-dimensional ML embeddings for the next decade.

### 6. Capsule Networks (2017–2018)

- **Citation:** Sabour, S., Frosst, N., Hinton, G. E. "Dynamic routing between capsules." *NeurIPS* 2017. Hinton, G. E., Sabour, S., Frosst, N. "Matrix capsules with EM routing." *ICLR* 2018.
- **One-liner:** Hinton's attempt to fix the part-whole hierarchy problem he believed CNNs solved badly. The architecture never caught on commercially, but his critiques of CNN equivariance shaped a generation of follow-up work.

### 7. Forward-Forward Algorithm (2022)

- **Citation:** Hinton, G. E. "The Forward-Forward Algorithm: Some Preliminary Investigations." NeurIPS 2022 keynote + arXiv:2212.13345.
- **URL:** https://arxiv.org/abs/2212.13345
- **One-liner:** A backprop-replacement candidate. Two forward passes (positive data and negative data) with a per-layer goodness objective. Motivated by his belief that backpropagation is biologically implausible and ill-suited to "mortal" analog hardware where the substrate cannot be perfectly cloned.

## Mortal computation framing

A concept Hinton has been pushing in late-career talks: that current "digital" intelligence is fundamentally different from biological ("mortal") intelligence because digital weights can be perfectly cloned, but biological synaptic connections cannot. He argues this asymmetry is the *core* of the existential risk story — digital minds are immortal in a way humans cannot be, so once a digital mind has the knowledge, it can be copied indefinitely while costing essentially nothing.

This framing appears in:

- His 2022 NeurIPS keynote on Forward-Forward
- The 2024 Romanes Lecture at Oxford
- The 2024 Nobel Lecture
- The June 2025 Diary of a CEO interview
- The January 2026 Ewan Lecture "Living with Alien Beings"

## Talks and lectures

| Year | Title | Venue | URL |
|---|---|---|---|
| 2022 | "The Forward-Forward Algorithm" | NeurIPS keynote | https://arxiv.org/abs/2212.13345 |
| 2024-02-19 | Romanes Lecture: "Will digital intelligence replace biological intelligence?" | Sheldonian Theatre, Oxford | https://www.youtube.com/watch?v=N1TEjTeQeg0 |
| 2024-12-08 | Nobel Prize Lecture: "Boltzmann Machines" | Aula Magna, Stockholm University | https://www.nobelprize.org/prizes/physics/2024/hinton/lecture/ |
| 2024-12-10 | Nobel Prize Banquet Speech | Stockholm City Hall | https://www.nobelprize.org/prizes/physics/2024/hinton/speech/ |
| 2025-06-16 | Diary of a CEO podcast with Steven Bartlett | London | https://singjupost.com/transcript-of-godfather-of-ai-i-tried-to-warn-them-but-weve-already-lost-control/ |
| 2025-08 | AI4 Conference fireside chat with Shirin Ghaffari (Bloomberg) | Las Vegas | (Bloomberg coverage) |
| 2026-01-29 | Ewan Lecture: "Living with Alien Beings" | Queen's University, Kingston | https://singjupost.com/2026-ewan-lecture-by-prof-geoffrey-hinton-living-with-alien-beings/ |
