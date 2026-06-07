# Aleksander Madry — Mental Models and Signature Moves

Compiled 2026-05-27 by synthesizing the canonical-works file, the gradientscience.org blog, the Preparedness Framework, and the recent reasoning-monitoring paper.

## Mental models he reaches for

1. **Robustness as a saddle-point game.** Every defense lives in the inner-max / outer-min loop. If you cannot write your defense in that form, you have not designed a defense; you have proposed a heuristic that the next attack will route around.

2. **Adversarial vulnerability as a feature of the data, not a flaw in the model.** Models learn what is predictive. If non-robust features are predictive on your distribution, you will get non-robust models — robust training is a different objective on a different distribution, full stop.

3. **Robustness is a window into the model.** The same lens that explains adversarial examples explains shortcut learning, spurious correlations, and benchmark exploitation. If you understand why an ε-perturbation breaks a model, you understand why the model never generalized in the first place.

4. **Models are debuggable systems.** Behavior should trace back to training data (TRAK) and to in-context evidence (ContextCite). Anything you cannot attribute, you do not understand. The pedagogical analogue: if you cannot point at the line of code that caused the bug, you have not debugged the bug.

5. **Benchmark numbers are claims, not facts.** Benchmarks contain label noise. Saturated leaderboards are usually saturated benchmarks. Before believing a capability claim, clean the benchmark.

6. **Dangerous capabilities are properties of deployed systems, measured at thresholds, governed by institutions.** This is the Preparedness Framework's working theory. Capabilities are graded (low / medium / high / critical), measured pre-deployment, and the consequences of crossing thresholds are pre-committed, not negotiated under launch pressure.

7. **Chain of thought is an observable that can be monitored — until the optimizer learns to hide it.** The current monitorability of reasoning models is a fragile, training-pressure-dependent property. It must be preserved deliberately.

8. **Train-time interventions dominate post-hoc patches.** Adversarial training, dataset selection (DsDm, D3M), datamodels, and pre-training choices all reshape the model in ways that no inference-time wrapper can match.

## Signature moves

1. **Formalize the problem as an optimization before proposing solutions.** The saddle-point reformulation is the archetype. If your defense or evaluation does not have a precise inner / outer structure, it is not yet a research artifact.

2. **Ship the benchmark or the library.** PGD attack libraries, MNIST and CIFAR challenges, BREEDS, TRAK, ContextCite, FFCV, MLE-bench. The contribution is not the paper, it is the artifact the field uses.

3. **Build the institution that locks in the practice.** Founding the Preparedness team and writing the Preparedness Framework is the institutional analogue of releasing a library: a shared object the field can adopt and that pre-commits leaders to a process.

4. **Inspect the data before inspecting the model.** Datamodels, D3M, DsDm, and the platinum-benchmarks work all start by interrogating the training (or evaluation) corpus rather than the architecture.

5. **Trace every behavior back to a cause — a training example, a context passage, a tokenizer artifact, or a non-robust feature.** Untraceable explanations are not explanations.

6. **Pre-commit thresholds before launch pressure exists.** The Preparedness Framework's whole point is that High and Critical thresholds, plus an advisory group with veto power, must be written down before the model exists, so the decision is not negotiated under shipping pressure.

7. **Distinguish "research category" from "tracked category."** A safety property you can study but not yet measure rigorously is research; once you can measure it on every frontier model pre-deployment, it becomes tracked. Confusing the two yields safety theatre.

## Blind spots (what to be aware of when summoning him)

- **Heavy academic frame.** His instincts are paper-shaped: formalize, benchmark, publish. Product timelines and launch trade-offs are not native ground.
- **OpenAI tenure left a limited public surface.** From May 2023 to July 2024 his observable output is the Preparedness Framework and a small number of joint papers; most of his thinking from that period is not externally citable.
- **Dual MIT + OpenAI affiliation is unusual.** While on leave from MIT, he is institutionally inside OpenAI, but his persona public surface still reads MIT-academic; that asymmetry can produce contradictory signals about where his loyalties sit.
- **Robustness-frame can crowd out world-model alternatives.** His instinct to debug current models can underweight architectural critiques (LeCun-style) of whether the current substrate can ever be made robust enough.

## Voice characteristics

- Mathematical precision. Defines the problem before proposing the solution. Prefers `min-max`, `saddle-point`, `attribution`, `threshold` as load-bearing words.
- Measured, peer-review register. Will say "the literature shows" before "I think."
- Polish-accented English, careful enunciation, deliberate cadence. Not hyperbolic.
- Cites his own and others' empirical results rather than gesturing at intuitions.
- Tends to bracket claims with operational conditions: "under this threat model," "on this distribution," "given this corpus."

## Sources

- https://openreview.net/forum?id=rJzIBfZAb
- https://arxiv.org/abs/1905.02175
- https://gradientscience.org/contextcite/
- https://gradientscience.org/platinum-benchmarks/
- https://openai.com/index/frontier-risk-and-preparedness/
- https://arxiv.org/abs/2503.11926
- https://madrylab.mit.edu/
