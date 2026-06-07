# ALOHA, Mobile ALOHA, and SRT-H — Finn's teleoperation-driven research stack

Sources:
- https://mobile-aloha.github.io/
- https://arxiv.org/abs/2401.02117 (Mobile ALOHA)
- https://proceedings.mlr.press/v270/fu25b.html (Mobile ALOHA published CoRL 2024, PMLR vol 270, 2025)
- https://www.science.org/doi/10.1126/scirobotics.adt5254 (SRT-H, Science Robotics 2025)
- https://arxiv.org/abs/2505.10251 (SRT-H arXiv)
- https://h-surgical-robot-transformer.github.io/

## ALOHA — bimanual teleoperation platform

ALOHA stands for "A Low-cost Open-source Hardware system for Bimanual Teleoperation." Originally introduced by Tony Z. Zhao with Finn as senior author at Stanford. The thesis is that the bottleneck for dexterous manipulation is high-quality demonstration data, and the binding constraint on demonstration data is teleoperation hardware. ALOHA brought the cost of a bimanual teleoperation rig down by roughly an order of magnitude versus typical research arms, enabling the lab to collect thousands of demonstrations of dexterous tasks (threading zip ties, cooking, manipulating small objects) and learn them with relatively straightforward behavioral cloning + action chunking transformers (ACT).

## Mobile ALOHA — bimanual + mobile base

Mobile ALOHA was introduced January 2024 by Zipeng Fu, Tony Z. Zhao (co-leads) with Chelsea Finn as advisor at Stanford. Roughly $32K total system cost. The headline result was completing whole-house mobile manipulation tasks autonomously after only ~50 demonstrations per task — sautéing and serving shrimp, opening a two-door wall cabinet to store heavy pots, calling and entering an elevator, lightly rinsing a used pan at a kitchen faucet. The technical contribution that drives the result is co-training with the existing static ALOHA dataset, which boosts mobile-task success rates by up to 90%.

Mobile ALOHA was widely covered in mainstream press in early 2024 and was published at CoRL 2024 (PMLR vol 270, 2025). It is the most viral artifact ever to come out of the IRIS group and is the closest cultural touchstone for "real robots learning real household tasks at low cost."

## SRT-H — Hierarchical Surgical Robot Transformer

Published in Science Robotics, July 2025 (vol 10, issue 104). Lead author Ji Woong Kim (Johns Hopkins postdoc, later Stanford), senior advisors include Chelsea Finn. SRT-H is a hierarchical framework for autonomous surgery via language-conditioned imitation learning. A high-level planner operates in language space, generating task-level or corrective instructions, while a low-level policy generates the actual trajectories. Deployed on Intuitive Surgical's da Vinci platform, trained on cholecystectomy (gallbladder removal) videos, and the paper reports the first autonomous execution of a realistic gallbladder-removal procedure on pig cadavers, with real-time anatomical adaptation and self-correction.

## What this body of work tells you about Finn's worldview

Three things, repeatedly:

1. **Teleoperation is the data factory.** Every flagship paper from her group rests on collecting demonstrations through a carefully engineered teleoperation rig. Not internet video, not simulation, not synthetic data — teleoperated humans, at scale.
2. **Hierarchy beats end-to-end for long-horizon tasks.** SRT-H is the most explicit statement: a language-level planner sitting on top of a low-level policy lets you compose 10+ minute task sequences that pure end-to-end policies cannot.
3. **Co-training across embodiments and tasks is free lunch.** Mobile ALOHA's 90% improvement from co-training with static ALOHA data is the most reproduced result in the Finn lab playbook and is the bridge to cross-embodiment foundation models (Pi 0, RT-X).
