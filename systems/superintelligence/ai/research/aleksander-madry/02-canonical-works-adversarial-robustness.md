# Aleksander Madry — Canonical Works on Adversarial Robustness and Model Debuggability

Compiled 2026-05-27 from OpenReview, arXiv, dblp, MadryLab pages, and the gradientscience.org blog.

## The defining paper

**"Towards Deep Learning Models Resistant to Adversarial Attacks"** — Madry, Makelov, Schmidt, Tsipras, Vladu. ICLR 2018. URL: https://openreview.net/forum?id=rJzIBfZAb.

Frames adversarial defense as a saddle-point (min-max) optimization problem. The inner maximization is tractable using first-order methods, so projected gradient descent (PGD) becomes both the canonical attack and the canonical training adversary. Training against PGD yields over 89.3% robust accuracy on MNIST at ε = 0.3 against white-box attacks and over 64% on CIFAR-10 at ε = 8 under black-box transfer attacks. The paper effectively defines the modern adversarial-robustness research program. dblp lists 56 community implementations as of 2026; the paper has become the standard reference for white-box defense.

## Other foundational adversarial-robustness and debuggability works

- **"Robustness May Be at Odds with Accuracy"** — Tsipras, Santurkar, Engstrom, Turner, Madry. ICLR 2019. Showed that robust and standard models learn fundamentally different representations and that the robustness–accuracy trade-off is a property of the data distribution, not just the training procedure.
- **"Adversarial Examples Are Not Bugs, They Are Features"** — Ilyas, Santurkar, Tsipras, Engstrom, Tran, Madry. NeurIPS 2019. Argued that adversarial vulnerability is rooted in non-robust features that are predictive on the data distribution but imperceptible to humans — flipping the field's framing from "models have bugs" to "models learn the data's real but human-irrelevant signal."
- **"BREEDS: Benchmarks for Subpopulation Shift"** — Santurkar, Tsipras, Madry. ICLR 2021. Established a benchmark suite for subpopulation shift, complementing ImageNet-A / ImageNet-C in the robustness literature.
- **"Unadversarial Examples: Designing Objects for Robust Vision"** — Salman, Ilyas, Engstrom, Vemprala, Madry, Kapoor. NeurIPS 2021. Inverted the adversarial-examples lens: design objects in the physical world that are easier for models to recognize correctly.
- **"Editing a Classifier by Rewriting Its Prediction Rules"** — Santurkar, Tsipras, Elango, Bau, Torralba, Madry. NeurIPS 2021. Practical model editing — surgically modify what a classifier does without retraining.
- **"3DB: A Framework for Debugging Computer Vision Models"** — used 3D rendering as a stress-testing harness for vision models.
- **"TRAK: Attributing Model Behavior at Scale"** — Park, Georgiev, Ilyas, Leclerc, Madry. ICML 2023. Scalable data attribution that traces a model's predictions back to specific training examples. Open-sourced as the TRAK PyTorch library.
- **"ContextCite: Attributing Model Generation to Context"** — Cohen-Wang, Schoch, Giorgi, Madry. NeurIPS 2024. The LLM analogue of TRAK — attribute every generated statement back to the in-context passages that justify it.

## Software artifacts

- `MadryLab/mnist_challenge` — public reference implementation of the PGD-trained MNIST defense; community-attacked for years and largely held up.
- `MadryLab/cifar10_challenge` — companion CIFAR-10 defense challenge.
- `MadryLab/robustness` — robustness library used throughout the deep-learning-robustness literature.
- `MadryLab/trak` — scalable training-data attribution.
- `MadryLab/contextcite` — context attribution for LLM generations.
- `MadryLab/ffcv` — Fast Forward Computer Vision data loader, used to accelerate vision-model training.

## Why these matter for the persona

The through-line of the corpus is *models as debuggable systems*. Robustness, attribution, editing, and benchmark-cleaning are all instances of the same instinct: when a model behaves strangely, isolate the mechanical cause, ideally to a specific training point or learned feature, then intervene at training time. Madry distrusts post-hoc patches and distrusts evaluation numbers that cannot be traced back to data.

## Sources

- https://openreview.net/forum?id=rJzIBfZAb
- https://adversarial-ml-tutorial.org/adversarial_ml_slides_parts_2_3.pdf
- https://madrylab.mit.edu/
- https://github.com/MadryLab/
- https://gradientscience.org/
- https://dblp.org/pid/67/2454.html
