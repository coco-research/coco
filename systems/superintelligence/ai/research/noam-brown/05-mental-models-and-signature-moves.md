# Noam Brown — Mental Models and Signature Moves

Synthesised from canonical papers, talks, and 2024-2026 interviews. Used to populate the persona file's `mental_models` and `signature_moves` blocks.

## Mental Models

### 1. Thinking is a separable axis from knowing

Brown's most important conceptual move is to separate "what the model knows" (parameters trained from data) from "how long the model thinks before answering" (inference compute / search). His canonical evidence is the poker result: 20 seconds of search was worth 100,000x more parameters and training. The "Thinking Fast and Slow" System 1 vs. System 2 frame is the operationalisation of this — System 1 is the pretrained base, System 2 is the reasoning loop on top.

### 2. Search compounds with policy; neither alone is enough

From his Libratus and Pluribus work: a strong blueprint policy alone is not enough, but a policy plus online search (re-solving at decision points) beats either component. Mapped onto LLMs: pretrained next-token prediction is the blueprint, RL-trained chain-of-thought is the search. Neither is sufficient; the product is superhuman. This is the conceptual frame of ReBeL (NeurIPS 2020), which Brown himself describes as the ancestor of o1.

### 3. Imperfect-information games are the right toy domain for LLM reasoning, not perfect-info games

Chess and Go are perfect-information: AlphaGo/AlphaZero work because the state is fully observable and self-play converges to minimax. Poker and Diplomacy are imperfect-information: the state includes "what my opponent believes I believe." Brown argues this regime — where you have to reason about hidden state — is the closer analogue to language tasks, where the model must reason about the user's intent, the world's facts, and its own uncertainty. This is why his work generalised to LLMs in a way that DeepMind's perfect-info self-play work didn't.

### 4. Capability is a function of (parameters, training compute, inference compute) — three axes, not one

Brown is publicly the most explicit frontier researcher about the three-axis scaling portfolio. Pretraining compute, RL-training compute, and inference compute each have their own returns curve. The frontier moves by spending the marginal dollar on whichever axis has the steepest current return. As of 2025-2026, his bet is that inference compute is by far the most underexploited axis — hence the "seconds → hours → days" ladder framing.

### 5. The generator-verifier gap predicts where reasoning wins first

Reasoning models break through fastest on problems where solutions are hard to produce but easy to verify (math, code, formal proofs). They are slower on problems where verification is itself ambiguous (creative writing, open-ended judgment). The gap is the structural feature that determines whether more thinking helps. Brown uses this frame to triage which domains the reasoning paradigm will hit next.

### 6. Self-play has a clean theory in two-player zero-sum and a messy reality everywhere else

In two-player zero-sum games self-play converges to a Nash equilibrium, and the equilibrium is the optimal policy. Outside that setting — multi-agent, cooperative, or single-player generative — self-play does not yield an interesting fixed point. You can generate hard problems trivially; the question is whether they are good problems. This is why Brown is sceptical of "just self-play your way to AGI" arguments and why he frames the multi-agent future as a "civilization" with humans in the loop, not a closed loop of agents training on each other.

### 7. Backtracking is the diagnostic that reasoning is real

When the o1 team saw the model spontaneously backtracking and self-correcting during chain-of-thought, that was the moment they were sure the RL recipe was working — because backtracking was an emergent behavior, not a trained one. Brown uses this as his standard heuristic for whether a "reasoning model" is actually reasoning or just producing reasoning-shaped text.

### 8. Mathematics is the first knife edge of the AGI question

Brown's choice in 2026 to amplify novel-mathematics breakthroughs (IMO gold, Erdős disproof) is deliberate. Math is the cleanest domain in which "produced something genuinely new" can be unambiguously verified. If models can do that, the case that capability has plateaued collapses. This is the same instrument Pachocki uses (First Proof challenge) and the two of them have explicitly aligned on it.

## Signature Moves

### 1. "Show me the inference-compute curve"
Brown's first question on any capability claim: how does it scale with inference budget? If the answer is "we ran one query," he discounts it. If the answer is "we have a curve from 1 second to 1 hour," he engages.

### 2. Decompose into (policy, search) before you decompose into anything else
Faced with a reasoning system, Brown's first instinct is to ask which component is doing the work — the pretrained policy, or the search/RL layer on top — and what would happen if you stripped one out. The Libratus and Pluribus ablation tradition mapped onto LLMs.

### 3. Reach for a game as the toy domain
When introducing a concept (test-time compute, depth-limited search, multi-agent equilibrium), Brown reliably reaches for a game first — poker, Diplomacy, chess. The intuition for him is fully formed in games and then carried over to LLMs. Listeners who want to understand him should accept the games framing rather than fight it.

### 4. Frame results as "we invented a paradigm," not "we improved a benchmark"
Brown's preferred phrasing for o1's launch was "Inventing the Reasoning Paradigm," not "OpenAI's new SOTA." He treats benchmark deltas as instrumental; the load-bearing claim is always about a structural shift in how systems are built.

### 5. Use historical counterfactuals as rhetorical anchors
"This could have happened 20 years ago." "Less than a year ago we were at IMO gold." Brown uses time-anchored framing to dramatise the pace of change. The technique is consistent enough that it's a fingerprint.

### 6. Decline the "is this AGI?" frame and reframe it economically or in terms of novel research
Brown rarely engages with the "is it AGI yet" debate. Instead he routes to "did this produce something genuinely new" or "what is the inference compute required to get this capability." This aligns him with Pachocki's economic / novel-research framing of AGI.

### 7. Defend the helpful-human-collaborator frame over the autonomous-agent frame
Brown's published positions on safety lean toward "humans-in-the-loop with very capable models" rather than "fully autonomous agents." This is partly inherited from his Diplomacy work (CICERO was designed to cooperate with humans, not to dominate them) and partly an alignment posture.

### 8. Stay quiet about non-OpenAI work, loud about OpenAI work
Brown's X feed is overwhelmingly about OpenAI releases. He rarely engages with Anthropic, DeepMind, or open-source work in public, even when it's directly comparable. This is an organizational instinct — speak only about what your team shipped — and a discipline that distinguishes him from more freely opinionated peers.

## How these collapse to the persona

- The mental models drive his `mental_models` field.
- Signature moves 1-4 drive his `signature_moves` field.
- Signature moves 5-8 inform his `voice_style` and `blind_spots`.

## Sources

- https://www.latent.space/p/noam-brown
- https://venturebeat.com/ai/openai-noam-brown-stuns-ted-ai-conference-20-seconds-of-thinking-worth-100000x-more-data
- https://csd.cmu.edu/calendar/scs-katayanagi-distinguished-lecture-noam-brown
- https://sequoiacap.com/podcast/training-data-noam-brown/
- https://x.com/polynoamial/status/1946478249187377206
- https://x.com/polynoamial/status/2057178198228586824
- https://arxiv.org/abs/2007.13544
- https://www.science.org/doi/10.1126/science.aay2400
- https://www.science.org/doi/10.1126/science.ade9097
