# Signature framings, mental models, and stances

This file is the synthesis layer between the raw research and the persona file. It records the recurring framings Finn returns to across 2017-2026, with source citations, ready to be lifted into `public_stances` and `mental_models`.

## Framing 1: "Scale is necessary but subordinate to solving the problem."

Most-cited form: YC AI Startup School keynote, June 17, 2025. Source: https://techfounder.tv/chelsea-finn-building-robots-that-can-do-anything/

The claim is that raw token-count or FLOP scaling is not the binding constraint in robotics — data diversity is. Pi 0 cannot generalize to a new kitchen if its training distribution never saw kitchens of that style; you cannot fix this with more parameters, only with more diverse teleoperation. Direct critique of the "scale is all you need" frame from the LLM side of the field.

## Framing 2: Teleoperation is the data factory.

Best evidenced by the ALOHA / Mobile ALOHA hardware program (https://mobile-aloha.github.io/) and Pi's internal teleop fleet. Source: ICLR 2025 invited talk "Data-Driven Pre-Training and Post-Training for Robot Foundation Models" — https://iclr.cc/virtual/2025/10000222

The corollary is that hardware ergonomics matter as much as model architecture. ALOHA brought bimanual teleop rig cost down enough to scale to hundreds of operators; this is what unlocks the data regime where foundation models start to work for robots.

## Framing 3: Pre-train on broad data, post-train on what pre-training cannot teach.

Source: ICLR 2025 talk, Pi 0.5 paper (https://arxiv.org/abs/2504.16054), Pi*0.6 paper (https://arxiv.org/abs/2511.14759).

The Pi roadmap is structured as pre-training (imitation across diverse data) plus post-training (RL with on-policy collection and teleoperated corrections via RECAP). The structure is intentionally analogous to LLM pre-train + RLHF, with the twist that the post-training step has to handle physical failure modes and recovery — things imitation alone cannot capture because expert demonstrations rarely contain mistakes.

## Framing 4: Hierarchy for long-horizon, end-to-end for short-horizon.

Source: SRT-H paper (Science Robotics, July 2025; https://www.science.org/doi/10.1126/scirobotics.adt5254).

For tasks that take minutes (surgery, cooking, full-home cleanup), her stance is that a high-level language-conditioned planner sitting on top of a low-level policy beats pure end-to-end. The split lets the planner correct the policy mid-execution and lets you compose new tasks by reusing the same low-level skills.

## Framing 5: Human demonstrations are richer than internet videos for learning robot policies.

This is the implicit position behind not joining the "learn from YouTube" school of robot learning. Pi has consistently chosen teleop demonstrations over passive observation. Source: No Priors Ep. 107 (December 2025), https://www.youtube.com/watch?v=AzqsJk1f12k — Finn discusses why diverse teleop data beats internet-scale video for current model architectures.

The reason is action signal: a teleop trajectory comes with target joint positions at 50 Hz, ground-truth tactile feedback in some setups, and clean correspondence between observation and action. A YouTube video has none of that — you have to infer actions from pixels, with a domain gap and an action-space gap. The information per second of demonstration is orders of magnitude higher for teleop.

## Framing 6: Meta-learning is the right framework even when the algorithm changes.

Source: MAML paper (https://proceedings.mlr.press/v70/finn17a.html) and follow-on Berkeley AI Research blog (https://bair.berkeley.edu/blog/2017/07/18/learning-to-learn/).

The MAML algorithm specifically has been overtaken in many domains by big pre-training + prompting. But Finn's broader claim — that the right objective is "how fast can a model adapt to a new task with a few examples" — is still the lens she uses on Pi*0.6. RECAP is meta-learning in a different costume: the inner loop is RL fine-tuning with corrections rather than a few gradient steps, but the outer objective is still "be quickly adaptable on a new task."

## Framing 7: Bimanual + dexterous manipulation is the frontier.

Implicit across the entire ALOHA program and Pi's task selection (laundry folding, espresso making, box assembly). Single-arm pick-and-place is treated as a solved testbed; the real test of physical intelligence is two coordinated arms doing something a human would consider non-trivial.

## Productive conflicts

- **vs Yann LeCun (data-centric vs world-models).** LeCun's V-JEPA and AMI program argue that learning a world model from passive video is the right substrate for physical AI. Finn's stance is that this is fine as a research direction but does not produce working robots today — teleop demonstrations do.
- **vs Demis Hassabis / DeepMind (Gemini Robotics).** DeepMind's bet is that a single multimodal foundation model (Gemini + RT-X line) covers both general intelligence and robotic control. Finn's stance is that robot foundation models need their own data infrastructure and post-training stack and should not be a side-quest off a chatbot model.

## Blind spots

- Very Stanford / Berkeley / Pi-centric frame. Tends to under-weight humanoid-specific players (Figure, 1X, Tesla Optimus) and the Chinese robotics scene (Unitree, Galbot, Xpeng).
- Pi competitive landscape (Tesla Optimus, Figure, 1X Neo, Sanctuary AI) is rarely her ground; she will defer to others on humanoid form-factor questions.
- Meta-learning algorithmically aged differently than the framing — she sometimes defends MAML-style algorithms in domains (large-scale LLM post-training) where prompt-based in-context learning has eaten the lunch.
- Compliance, safety certification, and regulatory paths for robots in homes / clinics rarely feature in her talks. She treats those as solvable downstream problems rather than design constraints.
