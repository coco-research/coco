# Canonical Publications — Aditya Ramesh

## DALL·E (2021)

- **Title:** "Zero-Shot Text-to-Image Generation"
- **Authors:** Aditya Ramesh, Mikhail Pavlov, Gabriel Goh, Scott Gray, Chelsea Voss, Alec Radford, Mark Chen, Ilya Sutskever
- **Submission date:** February 24, 2021 (arXiv 2102.12092 v1; revised v2 Feb 26, 2021)
- **Published:** ICML 2021, Proceedings of the 38th International Conference on Machine Learning, PMLR vol. 139, pages 8821–8831. Spotlight talk.
- **arXiv:** https://arxiv.org/abs/2102.12092
- **PMLR:** https://proceedings.mlr.press/v139/ramesh21a.html
- **Verbatim abstract:** "Text-to-image generation has traditionally focused on finding better modeling assumptions for training on a fixed dataset. These assumptions might involve complex architectures, auxiliary losses, or side information such as object part labels or segmentation masks supplied during training. We describe a simple approach for this task based on a transformer that autoregressively models the text and image tokens as a single stream of data. With sufficient data and scale, our approach is competitive with previous domain-specific models when evaluated in a zero-shot fashion."
- **Significance for persona:** Ramesh is first author. The paper's stance — *"a simple approach based on a transformer that autoregressively models the text and image tokens as a single stream of data"* — is the canonical framing of his research worldview. Autoregressive transformers + scale beat domain-specific architectures with auxiliary losses. This is his "Software 2.0 for image gen" thesis.

## DALL·E 2 / unCLIP (2022)

- **Title:** "Hierarchical Text-Conditional Image Generation with CLIP Latents"
- **Authors:** Aditya Ramesh, Prafulla Dhariwal, Alex Nichol, Casey Chu, Mark Chen
- **arXiv:** https://arxiv.org/abs/2204.06125 (April 13, 2022)
- **Key technical move:** CLIP joint text-image embedding space → "prior" that maps CLIP text embedding → CLIP image embedding → diffusion decoder that inverts the CLIP image encoder back to pixels. This is the architecture pattern subsequently called "unCLIP."
- **Headline claim from the paper:** "Explicitly generating image representations improves image diversity with minimal loss in photorealism and caption similarity. Our decoders conditioned on image representations can also produce variations of an image that preserve both its semantics and style, while varying the non-essential details absent from the image representation. Moreover, the joint embedding space of CLIP enables language-guided image manipulations in a zero-shot fashion."
- **Significance:** Ramesh is first author. This paper is the canonical citation for "CLIP-conditioning is the key insight for text-to-image" and is the architectural ancestor of both DALL·E 3's caption-improvement pipeline and the Stable Diffusion line of work that came afterward.

## GLIDE (2022) — supporting author

- **Title:** "GLIDE: Towards Photorealistic Image Generation and Editing with Text-Guided Diffusion Models"
- **Authors:** Alex Nichol, Prafulla Dhariwal, Aditya Ramesh, Pranav Shyam, Pamela Mishkin, Bob McGrew, Ilya Sutskever, Mark Chen
- **Venue:** ICML 2022. https://arxiv.org/abs/2112.10741
- **Significance:** Ramesh is a middle author rather than first author here; the paper is led by Nichol and Dhariwal. But the GLIDE result — classifier-free guidance with diffusion outperforming DALL·E 1's autoregressive transformer on photorealism — informed the architectural transition that landed in DALL·E 2. Important for persona because it documents the "autoregressive transformer → diffusion + classifier-free guidance" turn in his thinking.

## DALL·E 3 (2023) — supporting author

- **Title:** "Improving Image Generation with Better Captions"
- **Authors led by:** James Betker, Gabriel Goh, Li Jing, Tim Brooks, Jianfeng Wang, Linjie Li, Long Ouyang, Juntang Zhuang, Joyce Lee, Yufei Guo, Wesam Manassra, Prafulla Dhariwal, Casey Chu, Yunxin Jiao, Aditya Ramesh
- **PDF:** https://cdn.openai.com/papers/dall-e-3.pdf
- **Central claim:** "The prompt following abilities of text-to-image models can be substantially improved by training on highly descriptive generated image captions." Train a bespoke captioner, recaption the dataset, ship. Synthetic-data flywheel applied to text-to-image.
- **Significance:** Ramesh is the senior figure on the team, not the writer. His role at this stage was "team lead who chose the synthetic-caption bet and integrated the model into ChatGPT," not paper-author. This marks the transition from research-scientist to product-research-lead in his career arc.

## Sora "Video Generation Models as World Simulators" (February 2024)

- **OpenAI technical report:** https://openai.com/index/video-generation-models-as-world-simulators/
- **Authors:** Tim Brooks, Bill Peebles, et al. Ramesh is the credited team lead (with Brooks and Peebles as co-leads).
- **Framing claim:** "Our results suggest that scaling video generation models is a promising path towards building general purpose simulators of the physical world."
- **Significance:** This is the report that converts "scale autoregressive/diffusion video models" into a research program with a physical-world target. It is the framing he will repeat through 2025 and into 2026.

## Sora 2 (September 30, 2025)

- **Launch post:** https://openai.com/index/sora-2/
- **System card:** https://cdn.openai.com/pdf/50d5973c-c4ff-4c2d-986f-c72b5d0ff069/sora_2_system_card.pdf
- **Key capabilities listed:** synchronized dialogue and sound effects, sharper physics (gravity, buoyancy, collisions, rigidity, failure-state modeling), multi-shot continuity, world-state persistence, expanded stylistic range, controllability that lets directors compose sequences rather than single shots.
- **Significance:** Sora 2 is the artifact behind Ramesh's 2025 stance that scaling pure video generation can deliver a physics-respecting model — Olympic-level gymnastics that respect rigid-body dynamics, paddleboard backflips that respect buoyancy. The system card is the closest thing to a 2025 Ramesh-authored technical document.

## Citation surface

- Ramesh's correct Google Scholar id is 60K82BkAAAAJ (NOT u_VdvwMAAAAJ, which is a different person at Cisco/UMich).
- Combined citation count across DALL·E 1, DALL·E 2, GLIDE, and DALL·E 3 papers is in the tens of thousands as of 2026. These four papers are the spine of modern text-to-image generation.
