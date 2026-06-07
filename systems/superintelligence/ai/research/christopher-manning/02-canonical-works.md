# Christopher D. Manning — Canonical Works

Compiled 2026-05-27 from Stanford NLP group, ACL Anthology, Google Scholar, dblp.

## Textbooks

### Foundations of Statistical Natural Language Processing (1999)

- **Co-author:** Hinrich Schütze
- **Publisher:** MIT Press
- The defining graduate textbook for statistical NLP for the better part of two decades. Set the curriculum for an entire generation of NLP researchers. Cited as a foundational reference in nearly every CS224N era.

### Introduction to Information Retrieval (2008)

- **Co-authors:** Prabhakar Raghavan, Hinrich Schütze
- **Publisher:** Cambridge University Press
- The standard IR textbook. Free online at https://nlp.stanford.edu/IR-book/

### Complex Predicates and Information Spreading in LFG (1999)

- Monograph from Manning's linguistic-theory phase.

## Defining papers

### GloVe: Global Vectors for Word Representation (EMNLP 2014)

- **Co-authors:** Jeffrey Pennington, Richard Socher
- **URL:** https://nlp.stanford.edu/pubs/glove.pdf
- **Project page:** https://nlp.stanford.edu/projects/glove/
- One of the two defining word-embedding papers alongside Mikolov et al's word2vec. Trained on aggregated global word-word co-occurrence statistics; vector differences capture meaning. The "king − man + woman ≈ queen" demonstrations from this era come from this work. Massively cited.

### Effective Approaches to Attention-based Neural Machine Translation (EMNLP 2015)

- **Co-authors:** Minh-Thang Luong, Hieu Pham
- A pre-Transformer attention paper. Introduced the bilinear / multiplicative attention scoring form that is now standard in transformer cross-attention. Won the **ACL 2025 Test of Time Award** (10-year retrospective) — Manning's third consecutive Test of Time award.

### ELECTRA: Pre-training Text Encoders as Discriminators Rather Than Generators (ICLR 2020)

- **Co-authors:** Kevin Clark (lead), Minh-Thang Luong, Quoc Le, Christopher Manning
- A pretraining objective that uses a discriminator instead of a masked-LM head. Compute-efficient pretraining for the BERT generation.

### Emergent linguistic structure in artificial neural networks trained by self-supervision (PNAS 2020)

- **Co-authors:** Kevin Clark, John Hewitt, Urvashi Khandelwal, Omer Levy
- The "BERT learns syntax" result. Showed that transformer language models develop tree-structured syntactic representations without being told.

## Open-source software

- **Stanford CoreNLP** — long-running Java NLP pipeline (parsers, NER, coref). https://stanfordnlp.github.io/CoreNLP/
- **Stanza** — Python successor with neural pipelines for 60+ languages. https://stanfordnlp.github.io/stanza/
- **GloVe** — reference word-vector implementation and pretrained vectors. https://nlp.stanford.edu/projects/glove/

## CS224N — Natural Language Processing with Deep Learning

- **URL:** https://web.stanford.edu/class/cs224n/
- Annual Stanford course Manning has taught for over a decade. The lecture videos on YouTube (editions: 2017, 2019, 2021, 2023, 2024) are the canonical "how to learn deep-learning NLP" course for the global community.
- In Winter 2026 the course is being taught by Diyi Yang and Yejin Choi; Manning is on leave at AIX Ventures and the course continues under his frame.
- 2026 update: default final project shifted from BERT to a GPT-2 reproduction; new lectures on RLHF/DPO, LoRA, agents, and RAG.
- YouTube 2024 playlist: https://www.youtube.com/playlist?list=PLoROMvodv4rOaMFbaqxPDoLWjDaRAdP9D

## Other contributions

- **Universal Dependencies** — Manning is one of the principal contributors to the Universal Dependencies framework for cross-linguistic syntactic annotation. "Manning's Law" is a UD design principle.
- **Tree-structured recursive neural networks** — early architecture work (with Richard Socher).
- **SNLI corpus** — Stanford Natural Language Inference, a foundational textual-entailment benchmark.

## Sources for this document

- https://nlp.stanford.edu/~manning/
- https://aclanthology.org/people/christopher-d-manning/
- https://nlp.stanford.edu/projects/glove/
- https://web.stanford.edu/class/cs224n/
- https://stanfordnlp.github.io/CoreNLP/
- https://en.wikipedia.org/wiki/Christopher_D._Manning
