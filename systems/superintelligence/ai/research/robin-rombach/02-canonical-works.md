# Robin Rombach — Canonical Works and Publications

## Papers (formal, with venue)

### 1. High-Resolution Image Synthesis with Latent Diffusion Models — CVPR 2022 (Oral)

- **Authors:** Robin Rombach (lead author), Andreas Blattmann, Dominik Lorenz, Patrick Esser, Björn Ommer.
- **Affiliations at time of publication:** LMU Munich, IWR Heidelberg, Runway.
- **arXiv:** https://arxiv.org/abs/2112.10752 (preprint December 2021)
- **CVPR Open Access:** https://openaccess.thecvf.com/content/CVPR2022/html/Rombach_High-Resolution_Image_Synthesis_With_Latent_Diffusion_Models_CVPR_2022_paper.html
- **One-liner:** Latent diffusion — run the diffusion process in the latent space of a pretrained autoencoder, not in pixel space. Cut training and sampling compute by orders of magnitude. The architectural backbone of Stable Diffusion.
- **Citation impact:** One of the most-cited generative modelling papers of the decade; ground truth reference for diffusion in latent space.
- **Recognition:** Recipient of the German AI Prize 2024 (for the line of work, awarded to the Ommer Lab including Rombach).

### 2. Taming Transformers for High-Resolution Image Synthesis (VQGAN) — CVPR 2021 (Oral)

- **Authors:** Patrick Esser, Robin Rombach, Björn Ommer.
- **One-liner:** Combine the perceptual compression of VQ-VAE-style codebooks with the expressivity of transformers. The compression precursor that made latent diffusion practical.

### 3. Scaling Rectified Flow Transformers for High-Resolution Image Synthesis (SD3) — March 2024

- **arXiv:** https://arxiv.org/abs/2403.03206
- **Authors:** Patrick Esser, Sumith Kulal, Andreas Blattmann, Rahim Entezari, Jonas Müller, Harry Saini, Yam Levi, Dominik Lorenz, Axel Sauer, Frederic Boesel, Dustin Podell, Tim Dockhorn, Zion English, Kyle Lacey, Alex Goodwin, Yannik Marek, Robin Rombach.
- **One-liner:** Rectified flow + MM-DiT transformer architecture. The bridge between Stable Diffusion XL and FLUX. Published the same month Rombach and the core team left Stability AI.

## Released models

### Stable Diffusion (August 2022)

- Open release under CreativeML Open RAIL-M license. The model that democratized text-to-image. Triggered the explosion of derivative tooling, fine-tunes, ControlNet, LoRAs, ComfyUI, and the entire open-source visual-AI ecosystem.

### FLUX.1 family (August 2024) — Black Forest Labs

- **FLUX.1 [pro]** — proprietary, API-only.
- **FLUX.1 [dev]** — open-weights, source-available, non-commercial license.
- **FLUX.1 [schnell]** — 4-step distilled model under Apache 2.0. Quote from Rombach on release: "We love Open Source and release FLUX.1 [schnell]: An ultra efficient, 4-step model, coming with an Apache 2.0 license. It closely matches the performance of [dev] and [pro]." ([@robrombach 2024-08-01](https://x.com/robrombach/status/1819015251632803944))
- **Architecture:** 12B-parameter rectified flow transformer.
- **Performance:** Surpassed Midjourney v6 and OpenAI image generators on Artificial Analysis user ranking at launch.

### FLUX.1.1 Pro (October 2024) + Ultra/Raw modes (November 2024)

- Ultra mode: 2K-resolution images in under 4 seconds. Co-developed with Mistral AI for Le Chat integration.

### FLUX.1 Kontext (May 29, 2025)

- **Models:** Kontext [pro], Kontext [max], Kontext [dev].
- **Capability:** Image generation AND editing in a single flow-matching architecture. Character consistency, local edits, scene transformations, multi-step refinements.
- **Inference:** Up to 8× faster than leading alternatives at launch.
- **Rombach quote:** "FLUX.1 Kontext represents a fundamental shift from traditional editing approaches by unifying image generation and editing in a single flow matching architecture." ([Business Wire, 2025-05-29](https://www.businesswire.com/news/home/20250529605562/en/Black-Forest-Labs-Launches-FLUX.1-Kontext-a-Breakthrough-in-Context-aware-Image-Generation-and-Editing))

### FLUX.2 family (November 25, 2025)

- **FLUX.2 [dev]** — 32B-parameter open-weights checkpoint, text-to-image AND image editing unified.
- **FLUX.2 [pro]** — highest tier, lowest latency.
- **FLUX.2 [flex]** — exposes sampling steps and guidance scale; tune speed/quality tradeoff.
- **FLUX.2 [klein]** — fastest variant, sub-second generation, deployable on consumer hardware. Released January 15, 2026.
- **Architecture:** Latent flow matching paired with Mistral-3 vision-language model for understanding multi-image references.
- **Capabilities:** Up to 4 MP output, JSON prompting, hex-color specification, multilingual prompting, multi-reference editing (up to 4 reference images), accurate text rendering, "physical-world understanding" (hands, faces, fabrics, logos, lighting, depth).

## Sources

- https://arxiv.org/abs/2112.10752
- https://openaccess.thecvf.com/content/CVPR2022/papers/Rombach_High-Resolution_Image_Synthesis_With_Latent_Diffusion_Models_CVPR_2022_paper.pdf
- https://arxiv.org/abs/2403.03206
- https://ommer-lab.com/research/latent-diffusion-models/
- https://www.businesswire.com/news/home/20250529605562/en/Black-Forest-Labs-Launches-FLUX.1-Kontext-a-Breakthrough-in-Context-aware-Image-Generation-and-Editing
- https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev
- https://github.com/black-forest-labs/flux2
- https://blog.cloudflare.com/flux-2-workers-ai/
- https://en.wikipedia.org/wiki/Flux_(text-to-image_model)
- https://x.com/robrombach/status/1819015251632803944
