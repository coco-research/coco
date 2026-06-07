# Recent signals (post 2025-05-27)

This file collects public Finn signals from the trailing 12 months, in date order. The persona's `recent_signal_12mo` field draws from this list.

## 2025-06-17 — Y Combinator AI Startup School keynote

Event: Y Combinator AI Startup School, San Francisco.
Title: "Building Robots That Can Do Anything."
Sources: https://techfounder.tv/chelsea-finn-building-robots-that-can-do-anything/, https://www.podcosmos.com/ycombinator/ai-startup-school/chelsea-finn-building-robots-that-can-do-anything

Key claims:
- The goal of Physical Intelligence is a universal model that lets any robot do any task in any environment.
- "Scale is necessary, but subordinate to solving the problem." Data volume alone is not sufficient; data diversity is the critical variable.
- Teleoperation by trained operators (e.g. lighting a match and lighting a candle with that match) is how Pi collects training data.
- Pi 0 was a ~100M-parameter action expert on top of a much larger VLM, mapping camera images to target joint positions at 50 Hz.
- Foundation models for robotics will follow a similar trajectory to language models, but the data infrastructure (teleop fleet, cross-embodiment co-training) is the binding constraint that does not exist in the language domain.

## 2025-07 — SRT-H published in Science Robotics

Source: https://www.science.org/doi/10.1126/scirobotics.adt5254, https://hub.jhu.edu/2025/07/09/robot-performs-first-realistic-surgery-without-human-help/

Hierarchical surgical robot transformer; first autonomous gallbladder removal on pig cadavers. Major mainstream press coverage including Johns Hopkins Hub, Science, and general technology press. Finn's lab provided the imitation-learning + transformer architecture; the surgical robotics expertise came from Johns Hopkins.

## 2025-08 — "Self-Guided Action Diffusion"

arXiv 2508.12189. Lead author Rhea Malhotra (Stanford), with Finn as senior author. Diffusion-based action policies for robot manipulation with a self-guidance mechanism that improves sample efficiency during inference. Continues the IRIS group's program of pushing imitation-learning policy architectures past straightforward behavioral cloning.

## 2025-09 — Pi 0.5 release (open-world generalization)

Source: https://www.pi.website/blog/pi05, https://arxiv.org/abs/2504.16054

Pi 0.5 with mobile manipulator cleaning an entirely new kitchen / bedroom. Open-world generalization beyond the training set. The most-discussed Pi launch of the year up to that point.

## 2025-10 — Ctrl-World: controllable generative world model for robot manipulation

Source: https://arxiv.org/abs/2510.10125

Ctrl-World paper (October 2025) — controllable generative world model for robot manipulation, with Finn as a co-author. Signals that her group is now investing in world-models as a complement to (not replacement for) VLA imitation policies.

## 2025-11-18 — Pi*0.6 / RECAP release

Source: https://arxiv.org/abs/2511.14759, https://www.pi.website/download/pistar06.pdf

VLA that learns from experience via RECAP (RL + on-policy data + teleoperated corrections). Doubles throughput and roughly halves failure rate on hardest tasks. Demonstrated end-to-end espresso making, box assembly, real-home laundry folding. 56 authors including Finn.

## 2025-12 — "The Robotics Revolution" on No Priors podcast

Source: https://www.youtube.com/watch?v=AzqsJk1f12k (No Priors Ep. 107), https://podscripts.co/podcasts/no-priors-artificial-intelligence-technology-startups/the-robotics-revolution-with-physical-intelligences-cofounder-chelsea-finn

Long-form podcast with Sarah Guo and Elad Gil. Themes:
- How robots learn: cross-embodiment policies, transfer from VLMs and LLMs, dexterous skills via imitation learning are "core ingredients."
- Why diverse data matters more than raw scale.
- Open-source vs closed-source robotics — Pi has released openpi (selective open weights) while keeping the full proprietary model closed.
- The "any robot, any task" north star is hard but Pi has the building blocks.

## 2025 Spring — CS 224R taught and released

Source: https://cs224r.stanford.edu/, video lectures released publicly on YouTube. Spring 2025 edition of Stanford's Deep Reinforcement Learning course, led by Finn. Course covers imitation learning, model-free and model-based RL, with applications to language models and robotics. The Lecture 18 "Frontiers" lecture is the most-cited single video for her current 2025 thinking on where RL is going.
