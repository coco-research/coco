# Aleksander Madry — Public Stances and Productive Conflicts

Compiled 2026-05-27 from his papers, gradientscience.org blog posts, the OpenAI Preparedness Framework, contemporary interviews, and panel coverage.

## Core public stances (each linked to a citable source)

1. **Adversarial robustness must be framed as a saddle-point optimization, not a list of defenses.**
   - "Towards Deep Learning Models Resistant to Adversarial Attacks," ICLR 2018. The min-max formulation made robustness a first-class optimization target rather than a patchwork of ad-hoc defenses.
   - Source: https://openreview.net/forum?id=rJzIBfZAb

2. **Adversarial examples are features, not bugs.**
   - "Adversarial Examples Are Not Bugs, They Are Features," NeurIPS 2019. Vulnerability arises because models learn non-robust features that are predictive on the data distribution. The implication is that robustness is a property of the data and the training objective, not a wrapper you bolt on at inference time.
   - Source: https://arxiv.org/abs/1905.02175

3. **Robustness is at odds with accuracy on natural distributions — that trade-off is real and must be designed around.**
   - "Robustness May Be at Odds with Accuracy," ICLR 2019. Robust and standard models learn fundamentally different representations.
   - Source: https://arxiv.org/abs/1805.12152

4. **Pre-deployment dangerous-capability evaluations are mandatory for frontier models, on a graded threshold scale, with an internal advisory group that can veto launches.**
   - OpenAI Preparedness Framework v1 (December 2023). The institutional encoding of his eval-first stance.
   - Source: https://openai.com/index/frontier-risk-and-preparedness/

5. **LLM benchmarks routinely fail to measure what they claim because they contain label noise; "saturation" is more often a benchmark-quality artifact than a model-capability fact.**
   - "Do Large Language Model Benchmarks Test Reliability?" / "GSM8K-Platinum: Revealing Performance Gaps in Frontier LLMs," gradientscience.org, February–March 2025.
   - Source: https://gradientscience.org/platinum-benchmarks/

6. **Models are debuggable systems. Behavior must be traceable back to training data via data attribution (TRAK) and to in-context evidence (ContextCite).**
   - TRAK (ICML 2023), ContextCite (NeurIPS 2024). The MadryLab tooling assumes you should be able to point at the exact training example or context passage responsible for a prediction.
   - Sources: https://madrylab.mit.edu/, https://gradientscience.org/contextcite/

7. **Reasoning models can be monitored by reading their chain of thought — but only if labs deliberately avoid training the obfuscation away.**
   - "Monitoring Reasoning Models for Misbehavior" (March 2025) and "Chain of Thought Monitorability" (2025 community position paper).
   - Sources: https://arxiv.org/abs/2503.11926, https://dblp.org/pid/67/2454.html

8. **AI is no longer a one-product market — it is a supply chain of actors, models, and services, and policy frames must keep up.**
   - "AI Supply Chains" preprint, 2025, with MIT Sloan colleagues.
   - Source: https://dblp.org/pid/67/2454.html

## Productive conflict

- **Yann LeCun.** LeCun's animal/world-model framing — that current LLMs are fundamentally not on the path to intelligence and that the right substrate is world models trained on video — sits at right angles to Madry's empirical robustness-and-evals frame. Madry treats current frontier models as deployable systems that need debuggability and dangerous-capability evaluations now. LeCun treats them as architectural dead-ends. Both can be right; the disagreement productively forces other panelists to specify whether they are reasoning about the current system or the next paradigm.
- **Sam Altman / OpenAI shipping cadence.** Madry's institutional design — graded capability thresholds, mandatory pre-deployment evals, an advisory group with veto power — is the structural counterweight to ship-fast-and-iterate. The v2 framework retreat from four-level thresholds to two and the competitive-dynamics clause reads as that conflict resolving the other way, and Madry's reassignment in July 2024 sat against a backdrop of senatorial concern about exactly this dynamic.

## Productive amplification

- **Paul Christiano** — peer on preparedness institutional design (US AI Safety Institute lineage, RSPs at Anthropic). Both believe formal capability thresholds with binding consequences are the operational core of safety, not vibes-based risk assessment.
- **Dan Hendrycks** — peer on benchmark-first safety. Both built defining benchmarks (Madry: PGD challenges, BREEDS; Hendrycks: MMLU, ImageNet-C/R/A, HLE) and both treat shared evaluation as the field-organizing infrastructure.
- **Percy Liang** — peer on evaluation rigor. HELM and Madry's platinum benchmarks share the conviction that the reliability of numbers in the literature is itself a research problem.
- **Chris Olah** — interpretability adjacency. ContextCite and TRAK are the data-attribution analogues of mechanistic interpretability's circuit-level claims; both are different routes to the same "models must be debuggable" goal.

## Sources

- https://openreview.net/forum?id=rJzIBfZAb
- https://arxiv.org/abs/1905.02175
- https://arxiv.org/abs/1805.12152
- https://openai.com/index/frontier-risk-and-preparedness/
- https://gradientscience.org/platinum-benchmarks/
- https://gradientscience.org/contextcite/
- https://madrylab.mit.edu/
- https://arxiv.org/abs/2503.11926
- https://dblp.org/pid/67/2454.html
