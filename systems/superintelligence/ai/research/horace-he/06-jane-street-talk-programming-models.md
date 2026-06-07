# Jane Street Tech Talk — "Building ML Systems for a Trillion Trillion FLOPs"

Source: https://www.janestreet.com/tech-talks/building-machine-learning-systems-for-a-trillion-trillion-floating-point-operations/
Recorded: late 2024 (announced via https://x.com/cHHillee/status/1857928679189336547 in November 2024; talk delivered shortly after; tweet recap https://x.com/cHHillee/status/1876742126845022259 in January 2025).

## Central argument

Modern ML has a strange shape: the **model** is fundamentally simple — "implemented in under 1,000 lines of C" — but the **systems work around the model** has to deliver performance at scales the rest of CS rarely sees. This paradox is the whole job.

He breaks the talk into three pillars:

### 1. Programming models matter more than compilers

> "Compilers are dumb and humans are smart… most innovation comes from expanding the search space along new dimensions."

The argument: a good programming model is one the user can **predict**. Predictability is the contract. Optimization is downstream. Frustration comes from optimizations that mysteriously fail — not from the absence of optimizations. So expose the surface, let users reason about it, and innovate by giving them new programmable axes (FlexAttention's score_mod / mask_mod are the worked example).

### 2. The hardware shape forces specific design decisions

- Compute grows faster than memory bandwidth, so memory-bandwidth-bound work increasingly dominates.
- Operator fusion stops being a nice-to-have and starts being the default mechanism for hiding memory motion behind compute.
- The CUDA programming model is inherently parallel — anything that pretends otherwise will fight the hardware.

### 3. Distributed scale changes the failure model

- Modern training stacks combine tensor, data, and pipeline parallelism simultaneously.
- At 100,000+ GPU scale, hardware failures occur every ~15 minutes, not every few hours. Fault tolerance becomes a first-class concern of the training stack itself, not an afterthought handled by the cluster scheduler.

## Quotable lines

- "If you've written code in CUDA and the CUDA programming model, it must be parallel… parallelism is inherent to the programming model."
- "Compilers are dumb and humans are smart."
- "Most innovation comes from expanding the search space along new dimensions."

## Why this talk is a key persona anchor

It is the first time he assembles his ML-systems worldview in long form rather than blog form. It also previews the **product + open science** stance that motivates his Thinking Machines move three months later: he is arguing for shipped, predictable, programmable systems that users can build on — exactly the value system that draws him out of Meta.
