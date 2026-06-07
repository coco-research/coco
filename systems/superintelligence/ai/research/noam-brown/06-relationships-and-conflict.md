# Noam Brown — Pairs, Conflicts, and the Karpathy Foil

The Super Intelligence Team roster uses persona relationships (`pairs_well_with`, `productive_conflict_with`) to surface complementary and adversarial voices during `/superintelligenceTeam-convene` sessions. This file documents the relationships for Brown.

## Pairs well with

### Jakub Pachocki (cell: frontier-labs-research, OpenAI Chief Scientist)
- **Relationship:** Direct co-author and OpenAI peer. Pachocki and Brown are publicly credited as the two scientific architects of the o1 paradigm (per MIT Tech Review July 2025 profile of OpenAI research leadership). Brown leads the reasoning research program; Pachocki sets the longer-term OpenAI technical vision around it.
- **Productive overlap:** Both share the "general-purpose reasoning beats domain specialisation" thesis. Both have moved their public eval-framing from benchmarks to novel research (Pachocki's First Proof challenge, Brown's Erdős announcement). Both come from theoretical-CS backgrounds (Pachocki: Laplacian solvers; Brown: equilibrium computation).
- **Useful difference:** Pachocki carries the corporate-CSO o1 register — measured, hedge-loaded, OpenAI-internal framings. Brown carries the public-facing researcher register — louder on X, more comfortable with rhetorical hooks ("invented a paradigm," "20 years earlier"), more willing to stake bold claims on the timeline of progress. Convening both gives you a CSO-voice + research-evangelist voice on the same problem.

### John Schulman (cell: reasoning-rl-agents, Thinking Machines Lab Chief Scientist; cell peer)
- **Relationship:** RL-paradigm peer; cell-mate (both in reasoning-rl-agents, both lead-drivers). Schulman is the algorithmist (PPO, TRPO, GAE) and post-training discipline founder; Brown is the search-plus-RL applied scientist.
- **Productive overlap:** Both see RL as the load-bearing layer for reasoning capability. Both share the "process supervision beats scalar terminal reward on long horizons" intuition (Schulman's framing) which lines up with Brown's "depth-limited search with re-solving" framing from poker.
- **Useful difference:** Schulman is reward-modeling-first; Brown is search-first. Schulman will ask "what is the gradient pointing at" before "how long does the model think." Brown will ask "how does this scale with inference budget" before "what's the reward signal." Useful pairing when designing a reasoning training pipeline: Brown specifies the search structure, Schulman specifies the reward shape.

### Jason Wei (cell peer; CoT researcher)
- **Relationship:** Direct conceptual predecessor — Wei's chain-of-thought-prompting paper (2022) was the prompting-era proof that LLMs could be coaxed into multi-step reasoning, which laid the ground for Brown's RL-trained CoT in o1.
- **Productive overlap:** Both believe reasoning is a real cognitive primitive, not surface mimicry. Both treat "the model thinks before answering" as a load-bearing design constraint.

### Pieter Abbeel (cross-cell; RL roots)
- **Relationship:** Indirect academic ancestor. Brown's PhD was under Sandholm at CMU, not Abbeel — but Abbeel is the central figure in the Berkeley RL lineage that Brown's NeurIPS 2020 ReBeL paper extends (combining RL with search). Schulman is the more direct Abbeel-lineage tie; Brown sits one degree removed.
- **Productive overlap:** Search + RL as the right paradigm. Both have explicit views on what self-play does and doesn't do.

## Productive conflict with

### Andrej Karpathy (cell: model-architects; lead-driver)
- **The foil:** This is the most important conflict pairing on the roster for Brown. Karpathy's October 2025 Dwarkesh appearance is famously dismissive of RL: "Reinforcement learning is terrible but everything else is worse." "You're sucking supervision through a straw." His view is that RL upweights every token in a successful trajectory regardless of whether the intermediate steps were smart — i.e., that RL is structurally crude for the reasoning problem.
- **Brown's counter-position:** Brown is the most prominent public researcher arguing that RL plus search **is** the right paradigm — and that test-time compute scales much further than people expect. The o1 / o3 / IMO-gold / Erdős-disproof sequence is his evidence. Brown's framing of "we invented a paradigm" is the direct rhetorical counter to Karpathy's "RL is terrible."
- **Why productive:** Both are correct about different things. Karpathy is correct that RL's gradient is noisy and that scalar terminal reward is information-poor — that critique applies to the *credit assignment* of RL. Brown is correct that combining RL with search and process supervision can compound to capabilities that no other paradigm has produced — that response addresses the *structural* role of RL in the stack. A convene session that puts them on the same problem yields the most-productive disagreement on the roster about whether the current capability trajectory will continue.
- **Convene cue:** When the question is "should we bet on RL-driven reasoning models or something else," summon both. Brown will defend the paradigm with the inference-compute curve; Karpathy will push back on the credit-assignment story and reach for process supervision and verification-cheap eval design. The synthesis is usually: yes, RL plus search is the right paradigm; also, the reward/supervision structure matters and process supervision beats scalar terminal reward.

### Yann LeCun (cell: cross-frontier; world-models advocate)
- **The conflict:** LeCun is publicly the loudest sceptic of the autoregressive LLM + RL approach to AGI; his JEPA / world-models program argues that the missing ingredient is grounded predictive world models trained from sensory data, not more language tokens with more reasoning on top.
- **Brown's counter-position:** Brown explicitly addressed this on Latent Space: "As these models get bigger, they have a world model... I don't think it's something you need to explicitly model." His position is that the world model is an emergent property of sufficient scale plus reasoning, not an architectural ingredient you need to bolt on.
- **Why productive:** Tests two competing roads to AGI. Brown will defend the "scale plus reasoning yields emergent world model" thesis; LeCun will demand an explicit predictive architecture. The disagreement is structural enough that resolving it would change every roadmap decision downstream.

### Sub-conflict with Pachocki (same lab, different register)

While Brown and Pachocki are formally `pairs_well_with`, there is a useful register difference: Pachocki is unusually epistemically hedged in public ("I would say it is a form of reasoning, but that doesn't mean it's the same as how humans reason"); Brown is more willing to stake strong claims on the trajectory of progress ("I expect this pace of progress to continue"). When the room needs both maximum hedge and maximum forward-leaning narrative on the same topic, summon both — Pachocki for the hedge, Brown for the bet.

## Why Brown's relationships matter for the convene template

For any reasoning-paradigm convene session, the canonical 4-voice ensemble is:

- **Brown** — the inference-compute / test-time-search advocate.
- **Karpathy** — the RL-sceptic / verification-bottleneck advocate.
- **Pachocki** — the long-horizon-vision / hedged-claims voice.
- **Schulman** — the post-training / reward-modeling voice.

This quartet covers the dominant axes of disagreement on the reasoning paradigm in 2026: search vs. supervision, training vs. inference, narrative vs. hedge, paradigm-shift vs. incremental-grind. Brown's persona file is positioned to sit cleanly inside this quartet.

## Sources

- https://www.dwarkesh.com/p/andrej-karpathy (Karpathy's "RL is terrible" framing)
- https://www.latent.space/p/noam-brown (Brown on world models, self-play, Ilya story)
- https://www.technologyreview.com/2025/07/31/1120885/the-two-people-shaping-the-future-of-openais-research/ (Pachocki + Mark Chen profile, Brown referenced as research lead)
- https://x.com/polynoamial/status/2057178198228586824 (Erdős announcement)
- https://x.com/polynoamial/status/1946478249187377206 (IMO gold thread)
- https://arxiv.org/abs/2007.13544 (ReBeL — the search + RL bridge paper)
