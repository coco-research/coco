# Compression, Pruning, and Efficiency — Research Notes

Source documents:

- https://arxiv.org/abs/1911.05248 — "What Do Compressed Deep Neural Networks Forget?" (Hooker, Courville, Clark, Dauphin, Frome; 2019)
- https://research.google/pubs/pub49777/
- https://raulingaverage.dev/Summarizing-Compressed-Deep-NNs/
- https://www.sarahooker.me/research.html

## Headline paper

"What Do Compressed Deep Neural Networks Forget?" (2019) is Hooker's most-cited empirical paper. Co-authors include Aaron Courville (her later Ph.D. supervisor) and Andrea Frome.

### Core finding

Pruned and quantized models can show *identical top-line accuracy* to the unpruned baseline while quietly degrading on a narrow, identifiable subset of inputs that Hooker names **Pruning Identified Exemplars (PIEs)**. PIEs over-index on the long tail of the data distribution: atypical, noisy, or minority-group inputs.

### Why this matters

It is a fairness / safety argument disguised as an efficiency paper. The standard "we pruned 90% of the weights and only lost 0.3% accuracy" headline systematically hides disparate impact on the most underrepresented inputs. Top-line accuracy is a misleading summary metric when the cost of compression is paid almost entirely by the long tail.

This paper is the empirical bridge between the Hardware Lottery thesis and her later work on global-majority AI access. The same logic — that aggregate metrics conceal systematic disparate impact on the people least represented in the training distribution — is the seed of the Aya program.

## Other efficiency thread papers

Her research page lists multiple sparsity/pruning works through the late 2010s and early 2020s:

- "Selective Brain Damage: Measuring the Disparate Impact of Model Pruning" — a direct follow-up sharpening the disparate-impact finding.
- "Moving Beyond the Fairness Rhetoric in Machine Learning."
- "Lottery Ticket Hypothesis"-adjacent commentary on sparsity at init.

## Signature stance

Across this body of work, she advances a consistent claim:

> Efficiency is not value-neutral. Every method that reduces model cost also redistributes who pays the cost of imperfection. Pruning, distillation, quantization, and (later) inference-time adaptation all need to be measured with disaggregated metrics, not just aggregate accuracy.

This is the position she carries into the Aya program (multilingual evaluation must be disaggregated by language; English-average accuracy hides Bambara catastrophic failure) and into her critique of FLOP-based AI governance (FLOPs measure compute, not the disparate impact of the resulting system).

## How this shows up in 2025 discourse

In her March 2025 Khipu AI talk on "the slow death of scaling" (linked from her own X account), she revives the compression framing for the post-pretraining era: if dense pretraining is hitting saturation, then the optimization space is expanding into adaptation, inference-time compute, and data curation — and all of those moves recapitulate the disparate-impact problem unless they are measured carefully.
