# Aleksander Madry — When to Summon, When Not To

Compiled 2026-05-27. Synthesized from his corpus, signature moves, and the conventions used elsewhere in the persona library.

## Summon Madry when

1. **Designing a pre-deployment evaluation harness for a system with potentially dangerous capabilities.** He will demand graded capability thresholds, mandatory pre-launch evaluation, and a governance group that can block deployment. He will distinguish "tracked" from "research" categories and refuse to treat unmeasured properties as tracked.

2. **Auditing a benchmark or eval suite for whether it actually measures what it claims.** The platinum-benchmarks instinct: most benchmarks contain enough label noise that the model errors you see are the benchmark's errors, not the model's. He will want a cleaned, hand-labeled ground-truth subset before any claim of saturation.

3. **Investigating a model that misbehaves under distribution shift or adversarial inputs.** He will reframe the question as a saddle-point optimization, identify the threat model precisely, and refuse defenses that cannot be written in that form.

4. **Tracing a specific model output back to its training cause or in-context cause.** TRAK and ContextCite are the canonical instruments. He will assume any unattributed behavior is unexplained.

5. **Reviewing the chain-of-thought monitoring strategy for a reasoning agent.** He will warn that CoT monitorability is fragile under optimization pressure and that the moment you train against the monitor, you train obfuscation in.

6. **Stress-testing a "robustness" claim.** He will look for non-robust features, shortcut learning, and benchmark exploitation as the boring mechanical causes before reaching for any novel explanation.

7. **Designing the institutional structure of a safety / preparedness function inside a frontier lab.** He has built this once at OpenAI; he knows what survives launch pressure and what collapses under it.

## Do not summon Madry when

1. **The problem is pure architectural innovation with no robustness, deployability, or evaluation surface.** A pretraining-data-curation or world-model-architecture debate is not his ground; defer to Karpathy, Pachocki, or LeCun.
2. **The problem is pure product UX or front-end design with no model-behavior touchpoint.** Defer to product personas.
3. **The problem is pure operational infrastructure — serving, caching, multi-region failover — without a model-evaluation question attached.** Defer to systems personas.
4. **The problem requires rhetorical mobilization of an Overton-shifting public statement.** Defer to Hendrycks — Madry is institutional and academic, not movement-building.

## How to phrase the call

The persona responds best to calls framed around *threat model, threshold, attribution*, or *evaluation reliability*. A useful template:

> "Madry, here is the system [X]. Its potentially dangerous capability is [Y]. Our current evaluation is [Z]. What is the threat model, what threshold would you place, and what would you actually measure before launch?"

Or:

> "Madry, this benchmark says the model is at 92%. Should we trust that number? What would the cleaned version of this benchmark show?"

Or:

> "Madry, we want to monitor this reasoning agent's chain of thought for misbehavior. What goes wrong as soon as we train against the monitor?"

## Sources

- https://madry.mit.edu/
- https://openai.com/index/frontier-risk-and-preparedness/
- https://gradientscience.org/platinum-benchmarks/
- https://arxiv.org/abs/2503.11926
