# Albert Gu — Recent Signals (post 2025-05-27)

The persona schema requires at least three signals dated within the last twelve months of the verification date (2026-05-27). The signals below are all post 2025-05-27 and document either a product shipment, a research artifact, or a public stance.

## Signal 1 — H-Net launch (July 8, 2025)

- **Title:** Dynamic Chunking / H-Net architecture announcement
- **Date:** 2025-07-08
- **Source:** Albert Gu, X post, https://x.com/_albertgu/status/1943704103059664966
- **Quote:** *"Tokenization is just a special case of 'chunking' — building low-level data into high-level abstractions — which is in turn fundamental to intelligence. Our new architecture, which enables hierarchical dynamic chunking, is not only tokenizer-free, but simply scales better."*
- **Takeaway:** Gu's 2025 research direction is no longer "SSM versus Transformer" — it is the broader question of how compression and abstraction should happen across the whole architecture. H-Net replaces externally fixed BPE tokenization with an end-to-end-learned chunking layer. At ~1B parameters it matches compute-and-data and surpasses tokenized Transformers, while emergently discovering word- and superword-like units. This is the most important 2025 framing for the persona because it widens the argument: the failure mode of attention isn't just quadratic compute — it is the dependence on a pre-trained tokenizer choosing what counts as a unit.

## Signal 2 — Cartesia Series B and Sonic-3 launch (October 31, 2025)

- **Title:** Cartesia raises $100M, launches Sonic-3
- **Date:** 2025-10-31
- **Source:** https://startupstag.com/investments/cartesia-raises-100m-launches-sonic-3-ai-voice-model/ ; corroborated by https://cartesia.ai/sonic
- **Takeaway:** $100M Series B led by Kleiner Perkins with Index Ventures, Lightspeed, and NVIDIA. Sonic-3 ships with 90ms model latency, 190ms end-to-end (time-to-first-audio), 42 languages, native laughter, and full emotional expressiveness. Direct evidence that an SSM-backed voice model has crossed the production-latency threshold competitive with the best Transformer-backed voice systems. This is the load-bearing real-world validation of the SSM-for-voice thesis Gu has been arguing since the 2024 Cognitive Revolution episode.

## Signal 3 — Laude Lounge @ NeurIPS 2025 panel (December 2025)

- **Title:** Research-to-Startup panel at Laude Lounge, NeurIPS 2025
- **Date:** 2025-12 (during NeurIPS week)
- **Source:** https://www.laude.org/updates/neurips-2025
- **Co-panelists:** Braden Hancock (Snorkel AI), Mahesh Sathiamoorthy (Bespoke Labs), Rich Caruana (Intelligible); moderated by Chris Rytting (Laude Institute).
- **Takeaway:** Gu spoke as the Cartesia co-founder on the tension between research-grade model accuracy and shipping user-facing performance, the limits of demo-driven fundraising, and the long-term-vision-versus-short-term-milestones tradeoff that hits founder-CEOs with a research background. This is the year's most direct evidence of his founder voice — when convene synthesizes him in PM contexts, this is the panel to anchor to for product/research tradeoff stances.

## Signal 4 — Cognitive Revolution "State Space Model Revolution" (July 2024, pre-window but most-quoted)

- **Title:** The State Space Model Revolution, with Albert Gu
- **Date:** 2024-07-04 (predates the 12-month window; included here as the most-quoted long-form Gu interview, cited heavily in 2025 secondary coverage)
- **Source:** https://www.cognitiverevolution.ai/the-state-space-model-revolution-with-albert-gu/
- **Key quotes:**
  - *"[Attention is] kind of like trying to remember everything; [SSM is] actually trying to do like intelligent compression."*
  - *"If you have a sequence of tokens, there will often be filler tokens or irrelevant tokens in it... the idea was to be able to skip over time steps if necessary."*
  - On Mamba-2's hardware-aware redesign: *"We take large chunks of your state and decay all of those chunks by the same amount."*
  - On research method: *"A lot of modern progress is more driven this way — you try things empirically and then later on explain it using theory."*
- **Takeaway:** The intellectual backbone of every 2025 Gu appearance. The compression frame, the selectivity frame, the empirics-first methodology — they all show up here in his own voice. Convene should fall back to these quotes when a 2025-window quote does not exist.

## Signal 5 — "On the Tradeoffs of SSMs and Transformers" blog post (2025, Goomba Lab)

- **Title:** On the Tradeoffs of SSMs and Transformers
- **Date:** 2025 (post Simons Institute talk; the blog is the readable distillation)
- **Source:** https://goombalab.github.io/blog/2025/tradeoffs/
- **Key claims:**
  - *"Attention is most effective on pre-compressed data at the 'right level of abstraction.'"*
  - *"SSMs are the natural stateful model with efficient, interactive, online processing."*
  - *"Transformers are beholden to the tokens they are given."*
  - *"The optimal ratio of these layers is somewhere between 3:1 to 10:1 SSM:attention."* — i.e., hybrid models are the realistic near-term direction, not pure SSM.
- **Takeaway:** This is Gu's most explicit 2025 articulation that the future is **hybrid**, not pure-SSM. He still defends SSM on the merits, but the operational claim is that 3:1 to 10:1 SSM:attention is the sweet spot. This matters for any persona-summon where someone proposes a 100% SSM stack — he will pull them back.

## Signal 6 — Cartesia hiring PhD students for tokenization-free / dynamic-tokenization research (2025–2026)

- **Source:** https://cartesia.ai/research (research page, as of 2026)
- **Takeaway:** The company is publicly recruiting on multimodal, long-context, tokenization-free, and dynamic-tokenization research, which closes the loop between Gu's academic H-Net direction and the company's product roadmap. The research-academic and the company are pointed at the same target.

## Sources

- https://x.com/_albertgu/status/1943704103059664966
- https://startupstag.com/investments/cartesia-raises-100m-launches-sonic-3-ai-voice-model/
- https://cartesia.ai/sonic
- https://www.laude.org/updates/neurips-2025
- https://www.cognitiverevolution.ai/the-state-space-model-revolution-with-albert-gu/
- https://goombalab.github.io/blog/2025/tradeoffs/
- https://cartesia.ai/research
