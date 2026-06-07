# Open R1 — Hugging Face's full open reproduction of DeepSeek-R1

This is the second Wolf-led artifact from 2025 that anchors his "open ecosystem out-ships closed ecosystem" claim. Open R1 is interesting not just as a technical artifact but as a *political* artifact — Hugging Face shipped a public commitment to reproduce a model that another lab had only partially open-sourced, and used the reproduction to test whether the published claims held.

## Project facts

- Name: Open-R1
- Launched: January 28, 2025 (initial blog post + GitHub repo)
- Lead organization: Hugging Face
- Public faces: Thomas Wolf (CSO), Leandro von Werra (lvwerra), Elie Bakouch (eliebak), Lewis Tunstall (lewtun), and the broader open-r1 community
- GitHub: https://github.com/huggingface/open-r1
- HF org: https://huggingface.co/open-r1

## Why it existed

DeepSeek released DeepSeek-R1 in January 2025 — weights and technical report, but not the training code, not the reasoning-specific datasets, not the hyperparameter configs, not the scaling-law data. The community could *use* R1 but not *reproduce* it.

Wolf's framing of the project (paraphrased from his public comments at the time): "We started the project with the idea of testing if their claims were true. Pretty quickly we saw that, yeah, they are true." This is the operative move — Hugging Face used reproduction as the verification mechanism for a vendor's claim. Open weights without open training recipes are insufficient; you have to be able to retrace the steps to know what you really have.

## The three-step plan

1. **Replicate R1-Distill** — distill a high-quality reasoning dataset from R1 itself; turn that into a synthetic dataset suitable for fine-tuning existing or new LLMs into reasoning models.
2. **Replicate pure RL pipeline** — recreate DeepSeek-R1-Zero (pure RL without SFT) on math, reasoning, and code datasets, using Group Relative Policy Optimization (GRPO).
3. **Multi-stage training** — base model → SFT → RL → final reasoning model.

## What Hugging Face actually released

- Training scripts
- Evaluation harness reproducing R1's MATH-500 numbers
- Synthetic reasoning datasets (open)
- Public WandB logs of training runs
- Companion blog posts ("Open-R1: Update #1", subsequent updates)

## The political subtext

Wolf and von Werra were explicit that DeepSeek had historically not released training data or code for its prior models, so the community had to "make best guess estimates and see if we can get there ourselves." The Open R1 project is therefore a public statement of method: when a closed-ish release happens, the open community's response is *reproduction with full method transparency*, not just consumption.

This grounds three Wolf stances:

- Reproducibility is the only durable form of trust in model claims (parallel to Raschka's "working code doesn't lie")
- The open ecosystem has the shipping cadence to *follow up* on closed releases within weeks, not years
- "Open weights" is not the same as "open science" — open science requires data, code, recipe, and ablation logs as well

## Companion X thread on Amodei + DeepSeek + export controls

A few days before the Einstein essay, Wolf posted a sharp thread (Jan 30 2025, https://x.com/Thom_Wolf/status/1885093269022834943) responding to Dario Amodei's essay on DeepSeek and export controls. The thread is harsh:

> "Finally took time to go over Dario's essay on DeepSeek and export control and to be honest it was quite painful to read. And I say this as a great admirer of Anthropic and big user of Claude. The first half of the essay reads like a lengthy attempt to justify that closed-source [is the right path]…"

This is the prelude to the Einstein essay. Wolf's productive-conflict-with-Amodei pattern is established here.

## Sources used in this file

- https://huggingface.co/blog/open-r1
- https://huggingface.co/blog/open-r1/update-1
- https://github.com/huggingface/open-r1
- https://news.ycombinator.com/item?id=42841391 (HN discussion)
- https://www.marktechpost.com/2025/01/26/meet-open-r1-the-full-open-reproduction-of-deepseek-r1-challenging-the-status-quo-of-existing-proprietary-llms/
- https://x.com/Thom_Wolf/status/1885093269022834943 (Wolf's Amodei + DeepSeek + export controls thread, Jan 30 2025)
- https://www.emergingtechbrew.com/stories/2025/03/18/deepseek-open-model-developers-humanx (Wolf quoted: "We started the project with the idea of testing if their claims were true.")
