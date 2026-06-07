# Berkeley EECS Colloquium — "Reinforcement Learning from Human Feedback: Progress and Challenges" (April 19, 2023)

Sources:
- https://news.berkeley.edu/2023/04/24/berkeley-talks-chatgpt-developer-john-schulman/
- https://eecs.berkeley.edu/research/colloquium/230419-2/
- https://www.youtube.com/watch?v=hhiLw5Q_UFg

## What this is

Schulman's most cited public exposition of his views on RLHF, hallucination, and the design of reward models. Delivered at UC Berkeley's EECS Colloquium series, Banatao Auditorium, on April 19, 2023, while he was still leading post-training at OpenAI. Treated by the RLHF research community as the canonical "where we are, what's hard" survey from the person who actually shipped the algorithm into ChatGPT.

Although the user's hint referred to this as a "blog post," the primary artifact is the video lecture and the Berkeley News write-up. There is no canonical Schulman-authored long-form blog version. The community substitute (Chip Huyen's RLHF post, https://huyenchip.com/2023/05/02/rlhf.html) cites this talk as the source.

## Core claims

### Hallucination is a behavioral / reward problem

Schulman frames hallucination as having two distinct mechanisms:

1. **Behavioral reluctance to admit ignorance.** Language models are trained to pattern-complete. When caught mid-error, they continue fabricating rather than admit uncertainty, because the loss landscape they were trained on did not reward stopping.

2. **Genuine knowledge gaps.** Models also guess incorrectly on fuzzy material they have seen only partially during training.

The first mechanism is reward-shaped. The second is information-theoretic.

### The "I don't know" fix

Direct quote from the talk: "The model doesn't know that it's allowed to say 'I don't know' or express uncertainty. If you tell a chatbot that it's allowed to do that … that partially fixes the problem."

This is the canonical Schulman framing on hallucination: it is not a fundamental limit of language models. It is what happens when the reward model fails to teach the policy that calibrated abstention is valuable.

### Calibration as a learnable objective

Schulman argues that calibration — the model's reported confidence matching its actual probability of correctness — can be incentivized through RL. The reward model has to score "I don't know" higher than a confidently wrong answer. Done right, RLHF can RL calibration into the policy. This is the cleanest statement of his broader view: alignment behaviors are RL targets, not philosophical postures.

### Process supervision hint

Schulman sketches the early case for process supervision (rewarding reasoning steps, not just final answers) as a path past the "single scalar reward" limit of pure RLHF. The 2023 OpenAI process-supervision paper (Lightman et al., "Let's Verify Step by Step") was contemporary; Schulman's talk references the same intuition.

## Why this matters for the persona

The "hallucination is fundamentally a reward-modeling problem" framing in the persona's public_stances comes directly from this talk. It is the framing he reuses in the Dwarkesh interview a year later, and it remains his stable, citable claim through 2026. The signature framing "safe behavior can be RL'd in if the reward model is right" follows from the same talk: he is the strongest public advocate for the position that alignment is an RL design problem, not an interpretability problem.
