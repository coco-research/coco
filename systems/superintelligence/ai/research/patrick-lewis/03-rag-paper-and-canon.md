# Patrick Lewis — the RAG paper and the canonical research line

## "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"

- arXiv: <https://arxiv.org/abs/2005.11401>
- NeurIPS proceedings: <https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html>
- Meta AI mirror: <https://ai.meta.com/research/publications/retrieval-augmented-generation-for-knowledge-intensive-nlp-tasks/>

### Author list (Lewis is first author)

Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, Douwe Kiela.

### Core thesis

The paper introduces a model class that combines a **pre-trained parametric memory** (a seq2seq transformer, BART) with a **non-parametric memory** (a dense vector index of Wikipedia accessed through a neural retriever — DPR). At generation time, the retriever returns top-K passages; the generator conditions on them via cross-attention. Two variants: RAG-Sequence (one document per output sequence) and RAG-Token (allows different documents per token).

### Reported results

- State of the art on three open-domain QA tasks at the time (Natural Questions, TriviaQA, WebQuestions).
- Outperforms both parametric seq2seq baselines and extractive retrieve-and-extract pipelines.
- "More specific, diverse and factual" generations versus parametric baselines.

### Why this is the load-bearing paper for the persona

The 2020 RAG paper defines Lewis's intellectual position for the rest of his career. Three claims survive into 2025-2026:

1. **Retrieval is not a post-hoc augmentation; it is an architectural choice.** The model is trained end-to-end with the retriever in the loop, not bolted on at inference.
2. **Dense retrieval + cross-attention is the right composition for knowledge-intensive tasks.** Lewis later reinforces this through DPR (Karpukhin lead, Lewis co-author) and Atlas (Izacard / Lewis joint first).
3. **Knowledge-intensive evaluation is a distinct measurement problem.** This becomes KILT (NAACL 2021), which formalises the benchmark suite for the entire RAG ecosystem.

## The wider canonical line

- **Dense Passage Retrieval for Open-Domain QA** (EMNLP 2020). DPR is the dense-retriever component that RAG uses. Karpukhin lead-author, Lewis core co-author. This is the paper that retired BM25-only retrieval as a default in academic open-domain QA.
- **KILT: a Benchmark for Knowledge Intensive Language Tasks** (NAACL 2021). Petroni lead, Lewis co-author. Wikipedia-grounded benchmark across QA, fact checking, slot filling, dialogue, entity linking. The structural counterpart to the RAG modeling paper — gives the community a way to *measure* what RAG was supposed to do.
- **Question and Answer Test-Train Overlap in Open-Domain QA Datasets** (EACL 2021, Best Paper). Lewis first author. The paper that showed roughly 30% of test questions in popular open-domain QA benchmarks have near-duplicates in training, calling into question how much "knowledge" the underlying parametric models had actually learned vs. memorized. This is a methodological / evaluation paper and a key Lewis signature move: the most-cited follow-up to the RAG paper is *not* a bigger model but a measurement critique.
- **PAQ: 65 Million Probably-Asked Questions** (TACL 2021). Lewis first author. A scaled QA-augmentation corpus and an early synthetic-data play.
- **Atlas: Few-shot Learning with Retrieval-Augmented Language Models** (preprint 2022, JMLR 2023). Izacard / Lewis joint first author. A retrieval-augmented LM that achieves strong few-shot performance with very few parameters. This is the paper that argued retrieval can substitute for parameter count, which is the strategic claim under his entire Cohere agenda.
- **Language Models as Knowledge Bases?** (EMNLP 2019). Petroni lead, Lewis co-author. The LAMA probe. Foundational to the "what does the model actually know?" discourse that RAG is a structural answer to.

## Bibliographic completeness

His full publications page (<https://www.patricklewis.io/publication/>) lists 25+ papers through 2022. Post-2022 he publishes less under his own first-author byline, instead directing the Cohere modelling team's RAG, tool-use, and agentic work. This is the standard transition from senior research scientist to research director.
