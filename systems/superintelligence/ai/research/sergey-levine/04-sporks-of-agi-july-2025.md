# Substack — "Sporks of AGI: Why the Real Thing is better than the Next Best Thing"

Source: https://sergeylevine.substack.com/p/sporks-of-agi
Date: July 21, 2025
Author: Sergey Levine, on his personal Substack "Learning and Control"

This essay is the most direct articulation of Levine's position on surrogate data in robotics. The metaphor is the load-bearing rhetorical move.

## The spork metaphor

A spork claims to do the job of both a fork and a spoon. In practice it does both jobs badly. Sergey Levine uses this image to describe attempts to substitute real-world robot data with:

- Simulation rollouts.
- Human video data (third-person YouTube cooking videos, ego-centric video).
- Teleoperation with simplified end effectors.
- Cross-task transfer from unrelated robot platforms.

Each of these looks attractive because it sidesteps the cost and slowness of real robot data collection. Each suffers from the same structural failure: it can only teach the model what is in the **intersection** of three constrained sets.

## The intersection problem

For surrogate data to be useful, a behaviour must lie inside all three of:

1. What the target robot can physically do.
2. What the surrogate medium can express (a YouTube video cannot include joint torques; a simulator cannot include real cloth dynamics).
3. What does not expose a domain gap to the model.

As models become stronger and better at picking up subtle distributional shifts, set 3 contracts. The smarter the model, the more it notices that the simulator is not the world.

## "Information hiding is a dead end"

A common workaround is to **hide information from the model** to prevent it from detecting the domain gap — for example, by zeroing out depth, occluding pixel ranges, or normalizing away texture. Levine argues this is structurally backwards:

> Restricting the model's access to complex patterns weakens the model. The strength of foundation models is precisely the breadth of pattern they can absorb.

So the more aggressively you hide information to make surrogate data look real, the more you degrade the very capability you are trying to bootstrap.

## Generalization works against you

The model's capacity to generalize — the desired property — is what punishes surrogate data. It extrapolates patterns from the surrogate into the real domain, where the correspondence does not hold. The same generalization that lets a VLA fold a t-shirt it has never seen will also let it confidently apply simulator-only artifacts to the real world.

## The prescription

Use surrogate data as **supplement**, not **substitute**:

- Real robot data is the load-bearing distribution. It must dominate the training corpus.
- Human video, simulator rollouts, and cross-embodiment transfer are auxiliary — they enrich the model the way pretraining text enriches an LLM but do not replace the supervised fine-tune.
- The roadmap is: collect real data at scale, with real robots, in real environments, then add surrogate sources around it.

## Connection to the broader Levine thesis

This essay is the data-side companion to his "generalist robotic policies" position. He has argued for years that the bottleneck on robot learning is data, not algorithms. "Sporks of AGI" closes off the standard escape hatch (sim, video) and forces the conclusion that whoever ships real-world data infrastructure first wins the foundation-model-for-robots race.

It also indirectly defends Physical Intelligence's strategic choice to collect tens of thousands of hours of real robot data rather than rely on simulation, a choice that looked operationally expensive in 2024 and now reads as the only sustainable path.

## Quotable lines (paraphrased from essay)

- "A spork does the job of a fork and a spoon, badly."
- "Real data is indispensable if we are to truly build robotic foundation [models] with broad generalization."
- "The smarter the model gets, the smaller the safe intersection of surrogate data becomes."
- "Hiding information from the model to make surrogate data look real makes the model worse."
