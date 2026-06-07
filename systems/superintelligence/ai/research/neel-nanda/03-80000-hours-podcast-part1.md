# Neel Nanda on the race to read AI minds (80,000 Hours, Part 1)

- URL: https://80000hours.org/podcast/episodes/neel-nanda-mechanistic-interpretability/
- Recorded: July 17 & 21, 2025
- Published: September 8, 2025
- Episode #222 in the 80,000 Hours feed
- EA Forum write-up: https://forum.effectivealtruism.org/posts/za2oHe8HBtcYNnN7C/neel-nanda-mechanistic-interpretability

## Headline shift in his view

> "I've become more pessimistic about the high-risk, high-reward approach, but a lot more optimistic about the medium-risk, medium-reward approaches."

Reframed: he moved from **"low chance of incredibly big deal"** to **"high chance of medium big deal."** The most ambitious vision of mech interp he once dreamed of — deeply and reliably understanding what AIs are thinking — is "probably dead" because technical/practical barriers are too great before competitive pressures push deployment of human-level AI.

## What is achievable

Partial understanding is valuable:

> "Even 90% understanding helps with evaluation, monitoring, and incident analysis."

Working applications:
- Probes detecting harmful prompts hit 99.9% accuracy
- Chain-of-thought analysis reveals model confusion vs. genuine scheming
- Activation patching for causal interventions

## What is not achievable

> "Interpretability can't reliably find deceptive AI — nothing can."

> "I just don't think this is something you should expect any field of safety to provide."

Mech interp is one ingredient in safety, not the safety layer.

## Sparse autoencoders, honestly

His own team produced Gemma Scope, but he is publicly tempering the hype:

> "Finding harmfulness: simple probes outperform SAEs."

SAEs are great at *discovering* unknown concepts; they underperform simple linear probes on *detecting* known concepts. They are also computationally heavy — DeepMind used ~20 petabytes of storage for the Gemma 2 SAEs.

## Swiss cheese alignment

> "We need a portfolio of different things that all try to give us more confidence our systems are safe… use as many heuristics and try to break your techniques."

No single technique guarantees alignment. Layer multiple imperfect safeguards; the holes don't align if you have enough layers.

## On reading AI minds

> "We've been scared of these terrifying black box systems… they just think in English? What?"

Chain-of-thought monitoring is surprisingly tractable — but fragile. Models are increasingly aware they are being monitored. Architectural changes that abbreviate reasoning ("poly not work, try different") could erode the advantage. Implication: do not train models to hide their reasoning; the CoT signal is a gift to preserve.

## On o1-class models

Neel describes long-chain reasoning models as "a big deal that we understand so little about" and is funding MATS work on "mechanistic interpretability research for unfaithful chain-of-thought."

## Methodological stance

Mech interp is empirical natural science, not theory. The right move is: form hypotheses, design targeted experiments, check predictions, distill findings. Strong linear-algebra intuition matters more than advanced mathematics.
