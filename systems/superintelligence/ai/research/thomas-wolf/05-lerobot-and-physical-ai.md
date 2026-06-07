# LeRobot and the "App Store for Robots" — Wolf's 2025–2026 physical-AI thesis

LeRobot is the second front of Wolf's open-ecosystem strategy, alongside open-weights LLMs. He treats it as the same play applied to a new substrate: provide accessible primitives (cheap hardware + simple Python tools + a Hub for datasets and models), let the community generate the long tail.

## LeRobot facts

- Started: ~mid-2024 (~18 months before November 2025 Sequoia interview)
- Public lead: Hugging Face robotics team
- Core platform: LeRobot library on GitHub + LeRobot Hub on Hugging Face for datasets and policies
- Growth: 1,145 community datasets at end of 2024 → 58,000+ by May 2026; ~50× growth in five months; robotics now the single largest dataset category on Hugging Face Hub
- GitHub stars: 12,000+ on LeRobot repo

## Hardware

- **SO-100**: ~$100 robotic arm, "the cheapest robotic arm" by design
- **Reachy 2**: full humanoid from Pollen Robotics (acquired April 2025)
- **Reachy Mini**: $299; lightweight humanoid intended for "agentic robotics appstore" experiments — 10,000 units announced in 2025
- **Phone teleoperation**: iOS/Android integration in LeRobot v0.4.0 (Oct 24 2025)
- Hardware plugin system in v0.4.0 so third parties can ship integrations cleanly

## Software / model releases

- **LeRobot v0.4.0** (October 24, 2025): Datasets v3.0 (chunked episodes, >400GB datasets like OXE / Droid), efficient video streaming, unified Parquet metadata, `lerobot-edit-dataset` CLI, PolicyProcessorPipeline + RobotProcessorPipeline, multi-GPU training via Accelerate
- **PI0 and PI0.5** (Physical Intelligence): vision-language-action models integrated in v0.4.0
- **GR00T N1.5** (NVIDIA): cross-embodiment foundation model — announced November 2024 collaboration, GR00T N1 released March 2025, N1.5 in v0.4.0
- LIBERO support: 130+ VLA tasks
- Meta-World integration: 50+ manipulation tasks
- LeRobot v0.5.0 ("Scaling Every Dimension") — Thomas's own article, more recent

## Wolf's framings on robotics (from Sequoia "Training Data" podcast, ~November 2025)

1. **Community as exponential multiplier** — "you bring all these platforms, all these basic building blocks for people to build really crazy things on top." LeRobot's 6,000–10,000 developer community is the lever, not the hardware.

2. **Data diversity beats data volume** — robotics doesn't have an "internet-scale" data corpus to scrape, so the constraint is diversity. Wolf: "you will lack a lot is the diversity. So you will basically be able to train a robot to do something very well in your room when everything looks the same, but once you put it in the next door room where maybe the walls are green instead of red, the robot has a lot of troubles to generalize."

3. **Cheap hardware is non-negotiable** — Wolf explicitly rejected the elitist scenario: "robots are kind of an elite thing because they cost $100,000" is "counterproductive." The SO-100 and Reachy Mini exist to refute this.

4. **Local deployment is mandatory** — unlike LLMs, robots cannot tolerate cloud latency or connection drops: "if your robots lose connection to the WiFi or something and then run into the wall or maybe run into your kids, it's going to be much more dramatic." This shapes LeRobot's edge-first architecture.

5. **Open science as a personal manifesto** — Wolf cites his own struggle as a young physicist to access Soviet superconductivity research as the origin of his open-science instinct. "It's nice to give a fish to someone to feed them, it's even better to teach them to fish" — meaning sharing the *training methodology* matters more than sharing the trained model.

6. **China is genuinely competitive in open robotics** — Wolf observed that Chinese firms compete partly through openness, and noted that one company (Zhipu) faced a hiring backlash after closing-sourcing and had to reverse course. The geopolitical layer of his open-source thesis lives here.

7. **10-year vision** — Wolf wants a world where "everyone feels like they can build with AI and not they're just consuming AI" — explicit parallel to how social media democratized content creation. The frame is consumer-vs-producer, and he believes today's AI is producing too many consumers.

## Why LeRobot matters for the persona

LeRobot is Wolf's main *new* front in 2025–2026. It extends the Wolf thesis beyond text into embodiment, and it's where his next 12 months of attention is concentrated. Any convene session that touches robotics, embodied AI, or local/edge model deployment should weight Wolf heavily.

It also widens his blind-spots: a 3-year R&D investment in robotics hardware is high-cost, slow-feedback work compared to text LLMs. He has been clear it's a 10-year bet, not a 1-year ship.

## Sources used in this file

- https://sequoiacap.com/podcast/training-data-thomas-wolf/ (Sequoia Training Data podcast, ~November 2025)
- https://inferencebysequoia.substack.com/p/building-the-app-store-for-robots (companion substack)
- https://huggingface.co/blog/hugging-face-pollen-robotics-acquisition (April 2025 acquisition)
- https://huggingface.co/blog/lerobot-release-v040 (Oct 24 2025 release notes)
- https://github.com/huggingface/lerobot
- https://huggingface.co/blog/lerobot-pollen-robotics (post-acquisition integration)
- https://www.techtimes.com/articles/317129/20260525/open-source-robotics-ai-reaches-inflection-point-lerobot-hub-surpasses-58000-datasets-one-year.htm (May 2026 dataset count)
- https://www.startuphub.ai/ai-news/ai-video/2025/hugging-faces-lerobot-ignites-physical-ai-revolution/ (industry coverage)
- https://actu.ai/en/thomas-wolf-from-hugging-face-the-ambition-to-democratize-robotics-through-open-source-54437.html
