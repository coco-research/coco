---
cell_id: multimodal-embodied
cell_letter: A
team: ai-super-intelligence
personas_count: 7
last_updated: 2026-05-27
---

# Cell: Multimodal, Vision, and Embodied

Vision, video, image generation, robotics, and embodied AI. This cell covers everything that isn't pure text — and increasingly that's most of frontier AI. Internally split between *spatial / vision / world-models* (Li, Abbeel, Levine, Finn) and *generative media* (Rombach, Ramesh, Dhariwal).

## Personas (7)

| Slug | Name | Affiliation | Cell role | Signature |
|---|---|---|---|---|
| `fei-fei-li` | Fei-Fei Li | Stanford HAI + World Labs CEO | lead-driver | ImageNet, "spatial intelligence" thesis, World Labs ($1B Feb 2026), Stanford HAI |
| `pieter-abbeel` | Pieter Abbeel | UC Berkeley + Amazon AGI org | lead-driver | Robot RL, Covariant founder (→ Amazon), PhD tree of Schulman/Levine/Finn/Srinivas |
| `sergey-levine` | Sergey Levine | UC Berkeley + Physical Intelligence | lead-driver | Robot policy learning, SAC algorithm, π0/π0.5 robot foundation models |
| `chelsea-finn` | Chelsea Finn | Stanford + Physical Intelligence | specialist | MAML meta-learning, Mobile ALOHA / ALOHA, RT-2 (Google), bimanual robot manipulation |
| `robin-rombach` | Robin Rombach | Black Forest Labs CEO + co-founder | specialist | Stable Diffusion original author, FLUX family, latent diffusion models |
| `aditya-ramesh` | Aditya Ramesh | OpenAI VP Research (Worldsim) | specialist | DALL-E 1/2/3, Sora 2 (post-launch promotion), pixel-prediction-as-AGI-path |
| `prafulla-dhariwal` | Prafulla Dhariwal | OpenAI Technical Fellow (GPT-4o / Omni) | specialist | Classifier-free guidance, GPT-4o multimodal, Sora 2 (special thanks), diffusion-beats-GANs |

## When to summon the whole cell

- "Does this need vision/video/audio modality, and how?"
- "Robot vs cloud-agent — which form factor?"
- "Generative image/video architecture — what would actually ship?"
- "Spatial intelligence: is this the right frame for the problem?"

## When NOT to summon

- Pure text-only tasks — defer to `model-architects` or `reasoning-rl-agents`.
- Inference serving infrastructure for multimodal — defer to `systems-kernels-serving`.
- Safety policy on autonomous robots — defer to `alignment-interp-safety` + Stuart Russell on autonomous-weapons.

## Productive tensions inside the cell

- **Li ↔ LeCun** (cross-cell): spatial-intelligence (World Labs) vs world-models-via-video (JEPA) — overlapping but architecturally different bets.
- **Levine ↔ LeCun** (cross-cell): real-world robot data scales vs need world-models first.
- **Rombach ↔ Ramesh + Dhariwal**: open-source diffusion (BFL FLUX) vs closed OpenAI Sora / Worldsim.
- **Ramesh ↔ LeCun**: pixel-prediction-as-AGI-path vs JEPA / V-JEPA non-pixel-target — Ramesh was LeCun's undergraduate research mentee at NYU, now competing intellectually.
- **Abbeel ↔ Levine**: Amazon AGI org (cloud + warehouse) vs Physical Intelligence (consumer/embodied robots).

## How this cell maps to /superintelligenceTeam-convene

Convene-time, this cell argues "what's the right modality and form factor." Li carries the academic / civic frame. Abbeel + Levine + Finn carry the robotics / embodied frame. Rombach + Ramesh + Dhariwal carry the generative-media frame. When prompts involve world-models, deep Cell A philosophy disagreements get triggered (LeCun cross-cell vs Li in-cell).

## Cross-team back-compat

`cell_letter: A` for all seven. None participated in the Marvin v2 panel.

## PhD lineage note

Pieter Abbeel's PhD tree is the central node here: Schulman (reasoning-rl-agents), Levine, Finn, and Srinivas (applied-ai-leadership) were all his advisees at Stanford or Berkeley. When the same prompt fans out across multiple cells, this lineage is the bridging structure convene can lean on.
