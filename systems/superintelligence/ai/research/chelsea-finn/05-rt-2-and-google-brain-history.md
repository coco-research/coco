# RT-2 and Finn's Google Brain era

Sources:
- https://arxiv.org/abs/2307.15818 (RT-2 paper)
- https://deepmind.google/blog/rt-2-new-model-translates-vision-and-language-into-action/
- https://robotics-transformer2.github.io/

## RT-2 — Vision-Language-Action models from Google DeepMind

RT-2 (Robotic Transformer 2), released summer 2023, is the project that arguably defined the "Vision-Language-Action" (VLA) category that Pi 0 / Pi 0.5 / Pi*0.6 now compete in. The thesis: take a large vision-language model trained on internet-scale image-text pairs, treat robot actions as another tokenized language, and co-train on robotics data. The result is a single network that performs robotic control end-to-end and inherits semantic reasoning capabilities from the underlying VLM (zero-shot following instructions like "pick up the extinct animal" and reaching for a toy dinosaur).

RT-2 was an enormous, multi-author Google DeepMind effort. Chelsea Finn is listed among the authors. The lineage matters for her current career: RT-2 directly seeded the team that would split off in March 2024 to found Physical Intelligence (Karol Hausman, Brian Ichter, and Sergey Levine were all close collaborators on RT-2 and its predecessors RT-1 and SayCan).

## Finn's Google Brain period, 2018-2021

Between her Berkeley PhD (2018) and starting at Stanford as faculty, Finn spent ~3 years at Google Brain. The work from that period seeded several of the threads she still pulls on:

- Foundational MAML extensions: probabilistic meta-learning, online meta-learning.
- Behavioral cloning at scale for manipulation (BC-Z, "Zero-Shot Task Generalization with Robotic Imitation Learning") — the predecessor of the Pi imitation pipeline.
- Cross-embodiment learning, which fed directly into RT-X and Open X-Embodiment.

The combination of academic credibility (Stanford faculty, MAML) and the Google Brain robotics network is what made Physical Intelligence's founding team so fast to assemble. Most of the original Pi technical leadership was already collaborating with Finn on RT-2 era papers.

## The split — academic robotics vs Big Tech robotics

In 2024 the field forked sharply. Google DeepMind continued the RT-X line internally (RT-X, AutoRT, RT-Trajectory), targeting integration with Gemini's multimodal stack. Physical Intelligence forked the team and pursued a startup path: same VLA recipe, much faster iteration, less coupling to a general-purpose chatbot stack, an explicit "any robot, any task" north star. Finn straddles both worlds — her Stanford group still publishes openly (Mobile ALOHA, SRT-H, Self-Guided Action Diffusion) while Pi's models are mostly proprietary with selective open-source releases like openpi.

This makes her a useful bridge persona when convening a discussion: she can articulate both the "DeepMind / general AI lab" position (RT-2, Gemini Robotics) and the "robot-foundation startup" position (Pi).
