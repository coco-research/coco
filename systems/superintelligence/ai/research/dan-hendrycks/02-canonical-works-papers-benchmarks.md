# Dan Hendrycks — Canonical Works, Papers, Benchmarks

Sources: arXiv listings, Berkeley EECS publications page, GitHub `hendrycks/*` repos, CAIS publications page. Retrieved 2026-05-27.

## 1. GELU activation function (2016)

- Title: "Gaussian Error Linear Units (GELUs)"
- Authors: Dan Hendrycks, Kevin Gimpel
- arXiv: https://arxiv.org/abs/1606.08415
- First version: June 2016, revised through 2020.
- Significance: Now the default activation in BERT, GPT family (including GPT-3, GPT-4), LLaMA, Vision Transformers, and most frontier models. Hendrycks describes the intuition as smoothing the discontinuity of ReLU by composing the input with the CDF of a Gaussian. He emphasizes that adoption was empirical, not theoretical: "the general lesson is you don't want sharp things; you want things being smooth" (Cognitive Revolution interview, October 19, 2024).

## 2. ImageNet-C, ImageNet-R, ImageNet-A robustness benchmarks (2019-2021)

- "Benchmarking Neural Network Robustness to Common Corruptions and Perturbations" (ImageNet-C), Hendrycks & Dietterich, ICLR 2019. https://arxiv.org/abs/1903.12261
- "Natural Adversarial Examples" (ImageNet-A), Hendrycks et al, CVPR 2021. https://arxiv.org/abs/1907.07174
- "The Many Faces of Robustness" (ImageNet-R), Hendrycks et al, ICCV 2021. https://arxiv.org/abs/2006.16241
- Significance: Defined the modern distribution-shift evaluation suite. Forced the computer-vision robustness literature to converge on shared benchmarks. Demonstrated his pattern of "build the eval that defines the field."

## 3. MMLU — Massive Multitask Language Understanding (2020-2021)

- Title: "Measuring Massive Multitask Language Understanding"
- Authors: Dan Hendrycks, Collin Burns, Steven Basart, Andy Zou, Mantas Mazeika, Dawn Song, Jacob Steinhardt
- Venue: ICLR 2021
- arXiv: https://arxiv.org/abs/2009.03300 (Sep 7, 2020; final v Jan 12, 2021)
- GitHub: https://github.com/hendrycks/test
- Hugging Face: https://huggingface.co/datasets/cais/mmlu
- Structure: 57 tasks covering elementary math, US history, computer science, law, medicine, etc. Measures world-knowledge breadth, not syntactic understanding.
- Significance: Became the dominant LLM-capability benchmark of the 2021-2024 era. State of the art moved from ~32% (GPT-3) at release to >90% (Claude Opus, GPT-4 generation, Gemini 2) by 2024, motivating Humanity's Last Exam.
- Hendrycks' framing: existing benchmarks "weren't doing a good enough job at capturing capabilities." The lesson he draws repeatedly in 2024-2025 interviews is that benchmarks shape research priorities — "what you measure is what you optimize for."

## 4. ETHICS — "Aligning AI With Shared Human Values" (2020-2021)

- Title: "Aligning AI With Shared Human Values"
- Authors: Dan Hendrycks, Collin Burns, Steven Basart, Andrew Critch, Jerry Li, Dawn Song, Jacob Steinhardt
- Venue: ICLR 2021
- arXiv: https://arxiv.org/abs/2008.02275
- GitHub: https://github.com/hendrycks/ethics
- Coverage: justice, well-being, duties, virtues, commonsense morality.
- Significance: First broad benchmark for predicting human moral judgments. Made empirical progress on machine-ethics evaluation a respectable subfield. Now integrated into EleutherAI's lm-evaluation-harness.

## 5. Representation Engineering — "A Top-Down Approach to AI Transparency" (2023-2025)

- Authors: Andy Zou, Long Phan, Sarah Chen, James Campbell, Phillip Guo, Richard Ren, Alexander Pan, Xuwang Yin, Mantas Mazeika, Ann-Kathrin Dombrowski, Shashwat Goel, Nathaniel Li, Michael J. Byun, Zifan Wang, Alex Mallen, Steven Basart, Sanmi Koyejo, Dawn Song, Matt Fredrikson, J. Zico Kolter, Dan Hendrycks.
- arXiv: https://arxiv.org/abs/2310.01405 (initial Oct 2, 2023; latest revision Mar 3, 2025)
- Thesis: rather than reverse-engineering individual neurons and circuits ("mechanistic interpretability"), analyze and steer model behavior at the level of population-level representations across many neurons.
- Practical results: "unlearning dual-use concepts," honesty steering, refusal steering.
- Hendrycks position (2025): mechanistic interpretability has "roughly nonexistent" returns after a decade of investment; representation engineering is the productive alternative (see "The Misguided Quest for Mechanistic AI Interpretability," AI Frontiers, May 15, 2025, https://ai-frontiers.org/articles/the-misguided-quest-for-mechanistic-ai-interpretability).

## 6. Statement on AI Risk (CAIS, May 2023)

- URL: https://safe.ai/work/statement-on-ai-risk
- 22-word statement: "Mitigating the risk of extinction from AI should be a global priority alongside other societal-scale risks such as pandemics and nuclear war."
- Signatories: Geoffrey Hinton, Yoshua Bengio, Demis Hassabis, Sam Altman, Dario Amodei, Bill Gates, and 100+ AI professors and lab leaders.
- Hendrycks role: lead organizer and primary spokesperson.
- Significance: shifted the Overton window on AI existential risk from a fringe academic claim to a position publicly endorsed by the CEOs and CTOs of every major AI lab.

## 7. Introduction to AI Safety, Ethics, and Society (textbook, 2024)

- Author: Dan Hendrycks
- Publisher: Taylor & Francis / Routledge, 2024
- ISBN: 9781032869926
- Free online: https://www.aisafetybook.com/
- arXiv preprint: https://arxiv.org/abs/2411.01042
- Audio: available as audiobook on Spotify.
- Structure: consolidates AI safety, ethics, and AI-governance material for students, policymakers, and practitioners. The companion course (run by CAIS) had its spring 2025 session Feb 19 - May 9, 2025.

## 8. Humanity's Last Exam (HLE) (2025)

- Joint project of CAIS and Scale AI.
- Paper: published in Nature (2026), "A benchmark of expert-level academic questions to assess AI capabilities." https://www.nature.com/articles/s41586-025-09962-4
- Scale page: https://scale.com/research/humanitys-last-exam
- Leaderboard: https://labs.scale.com/leaderboard/humanitys_last_exam
- Structure: 2,500 expert-crafted questions across math (41%), physics, biology/medicine, humanities, CS, engineering, chemistry. ~14% multimodal, ~24% multiple-choice.
- Crowdsourcing process: questions filtered through frontier models; only those that confused the models passed to two rounds of expert review. $500,000 prize pool.
- Performance trajectory: at January 2025 release GPT-4o scored 2.7%, Claude 3.5 Sonnet 4.1%, o1 8.0%. By April 2026 top scores were Gemini 3.1 Pro Preview 46.44%, GPT-5.4 Pro 44.32%, Claude Opus 4.6 (Thinking) 34.44%.
- 2025 controversy: a July 2025 FutureHouse investigation flagged ~30% error rates in chemistry/biology answers, prompting CAIS+Scale to establish a continuous revision process.
- Origin story: per Hendrycks, the idea came from a conversation with Elon Musk who argued MMLU had become too easy.

## 9. Superintelligence Strategy (2025)

- Title: "Superintelligence Strategy: Expert Version"
- Authors: Dan Hendrycks, Eric Schmidt (former Google CEO), Alexandr Wang (Scale AI CEO)
- arXiv: https://arxiv.org/abs/2503.05628 (initial March 7, 2025; revised April 14, 2025)
- Companion site: https://www.nationalsecurity.ai/
- Core construct: MAIM — Mutual Assured AI Malfunction. Direct quote from the paper:
  > "A deterrence regime resembling nuclear mutual assured destruction (MAD) where any state's aggressive bid for unilateral AI dominance is met with preventive sabotage by rivals."
- Three pillars:
  1. Deterrence — detect and deter destabilizing AI projects via cyber espionage and sabotage.
  2. Nonproliferation — track AI chips, prevent rogue actors from acquiring weaponizable AI capabilities.
  3. Competitiveness — guarantee chip access through domestic manufacturing, integrate AI into military and civil capabilities.
- Position against a "Manhattan Project for AI" — Hendrycks argues a single-state crash program toward superintelligence would be detected and sabotaged by rivals. Stated in The Economist by-invitation column March 28, 2025: https://www.economist.com/by-invitation/2025/03/28/dan-hendrycks-warns-america-against-launching-a-manhattan-project-for-ai

## 10. AI Wellbeing research (May 2026)

- CAIS publication, May 2026: "AI Wellbeing: Measuring and Improving the Functional Pleasure and Pain of AIs"
- Coverage: AI Safety Newsletter #72. https://newsletter.safe.ai/p/aisn-72-new-research-on-ai-wellbeing
- Thesis: LLMs behave robustly as though they have functional wellbeing, even if not necessarily conscious. Significant for forthcoming AI welfare and AI moral-patient debates.
- Marks a recent expansion of Hendrycks' scope beyond pure existential-risk framing into questions of model-internal value.
