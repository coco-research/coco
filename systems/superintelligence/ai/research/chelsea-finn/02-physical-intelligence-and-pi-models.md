# Physical Intelligence and the Pi family of robot foundation models

Sources:
- https://www.pi.website/blog/pi05 (Pi 0.5 blog post, accessed 2026-05-27)
- https://arxiv.org/abs/2410.24164 (Pi 0 paper, October 2024)
- https://arxiv.org/abs/2504.16054 (Pi 0.5 paper, April 2025)
- https://arxiv.org/abs/2511.14759 (Pi*0.6 paper, November 2025)
- https://eutechfuture.com/artificial-intelligence/physical-intelligence-building-foundation-models-for-robots-to-interact-with-the-real-world/

## Founding

Physical Intelligence (often stylized as Pi or π) was founded in March 2024 by:

- Chelsea Finn (Stanford Assistant Professor, co-founder and Research Lead).
- Sergey Levine (UC Berkeley Associate Professor, co-founder; was Finn's PhD co-advisor).
- Karol Hausman (formerly Google Brain / DeepMind robotics; CEO).
- Brian Ichter (formerly Google Brain; co-author of RT-2 and SayCan).
- Lachy Groom (operating co-founder; previously Stripe).

The company raised an initial round in March 2024 and a follow-on round reported at roughly $400M at a $2.8B valuation, with later reporting up to $600M. The team origin is heavily Stanford / Berkeley / Google Brain robotics.

## Pi 0 — "Our First Generalist Policy"

Released October 2024. A Vision-Language-Action flow model for general robot control. Architecture combines a VLM backbone with flow-matching for continuous action generation, mapping camera images plus a language instruction to target joint positions at 50 Hz. Roughly 100M-parameter action expert built on top of a much larger VLM. Trained on a large in-house teleoperation dataset across several embodiments. The release positioned Pi as the leader for a single foundation policy across heterogeneous robot platforms.

## Pi 0.5 — "A VLA with Open-World Generalization"

Released April 2025 (arXiv 2504.16054). Extends Pi 0 with substantially better generalization to environments outside the training distribution. The demonstration headline was a mobile manipulator cleaning an entirely new kitchen or bedroom — locations that the model had never seen during training. Technically Pi 0.5 uses a separate MLP to project the flow-matching timestep and applies adaptive RMSNorm to inject it into each layer of the action expert, rather than concatenating the timestep with the noisy action as Pi 0 did.

## Pi*0.6 — "A VLA That Learns From Experience"

Released November 18, 2025 (arXiv 2511.14759). The headline contribution is RECAP — "RL with Experience and Corrections via Advantage-conditioned Policies" — which lets a VLA improve from a mix of demonstrations, on-policy collected rollouts, and teleoperated interventions during autonomous execution. On the hardest tasks Pi*0.6 more than doubles task throughput and roughly halves the failure rate vs Pi 0.5. Demonstrated tasks include making espresso end to end, assembling cardboard boxes reliably, and folding laundry in real homes. 56 authors are listed including Chelsea Finn, Sergey Levine, and Brian Ichter.

## Finn's role and stance

In her ICLR 2025 invited talk "Data-Driven Pre-Training and Post-Training for Robot Foundation Models," Finn frames the Pi program in two complementary stages: pre-training on a large, diverse teleoperation corpus to give the model a generalist prior, then post-training (RL with on-policy collection and human corrections) to teach the model what it cannot learn from pure imitation. RECAP is the technical embodiment of that post-training thesis.

Her recurring claim in 2025: "scale is necessary, but subordinate to solving the problem." Data diversity beats raw data volume; the data factory (teleoperation infrastructure) is the binding constraint, not parameters or FLOPs.
