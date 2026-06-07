# Interaction Models — TML-Interaction-Small (May 11, 2026)

Sources: Unite.AI, MarkTechPost, VentureBeat, Analytics Drift, TechStory, NewsBytes, Connectionism blog post "Interaction Models: A Scalable Approach to Human-AI Collaboration" (May 11 2026).

## Headline claim

> "Every major AI lab has built its interaction layer as an afterthought, and the resulting latency and limitation is not a tuning problem but an architectural one."
> — Thinking Machines Lab, May 11 2026 blog post

This is a direct, named critique of OpenAI's GPT-Realtime, Google's Gemini Live, and by extension every voice-mode product shipped in the 2024–2026 wave. TML positions its work as a *fundamental* architectural break.

## Model specifications

| Attribute | Value |
|-----------|-------|
| Name | **TML-Interaction-Small** |
| Total parameters | 276 B (mixture-of-experts) |
| Active parameters per token | 12 B |
| Input/output processing unit | **200 ms micro-turns** |
| Modalities (input + output) | Audio, video, text — all native |

## The "multi-stream micro-turn" architectural break

**Standard industry approach (criticized):**
- All inputs flattened into a single ordered token sequence.
- Audio chunked → tokenized → fed to LLM → LLM emits tokens → vocoder.
- "The model's perception freezes while it is generating a response."
- Turn-taking handled by external scaffolding (voice-activity detection, push-to-talk, server-side silence timers).

**TML's approach:**
- **Continuous parallel streams** for audio, video, text — run simultaneously, grounded in wall-clock time.
- The model perceives user actions *while* generating its own response. No frozen-perception window.
- **200 ms input chunk + 200 ms output chunk processed simultaneously each tick.** No "end-of-turn" signal needed.
- All modality encoders trained end-to-end from scratch with the transformer — no bolted-on Whisper/CLIP-style standalone encoders.
  - Audio: dMel features through a lightweight embedding layer.
  - Video: 40×40 patches.
  - Text: co-trained.

## Self-reported benchmarks (FD-bench)

**Turn-taking latency (FD-bench V1, lower is better):**

| Model | Latency |
|-------|---------|
| **TML-Interaction-Small** | **0.40 s** |
| Gemini-3.1-flash-live | 0.57 s |
| GPT-Realtime-2.0 (minimal) | 1.18 s |

**Interaction quality (FD-bench V1.5, higher is better):**

| Model | Score |
|-------|-------|
| **TML-Interaction-Small** | **77.8** |
| GPT-Realtime-2.0 | 46.8 |
| Gemini-3.1-flash-live | 45.5 |

(Caveat: FD-bench is TML's own benchmark. External replication pending.)

## Why this is the strategically right "first model"

Murati's pre-TML career spans:
- Tesla Model X (multimodal perception — cameras, radar, ultrasonic).
- Leap Motion (real-time hand-tracking).
- ChatGPT (text-only conversation made consumer).
- GPT-4o voice mode (first major multimodal-realtime ChatGPT release, under her CTO tenure).

The Interaction Model is the synthesis: the next-generation GPT-4o-style product, but with the architectural rebuild that her team always wanted to do but couldn't ship inside OpenAI's product cadence. Multiple TML team members (Schulman, Zoph, Weng) worked on GPT-4o's voice mode and watched the bolt-on-real-time approach hit its ceiling.

## Distribution

- Research preview to a limited group of researchers as of May 11 2026.
- Wider release planned for later 2026.
- Larger models pending solution to latency-vs-scale tradeoff.

## What's NOT in this release

- No agentic / tool-use story attached.
- No code-generation story.
- No comparison vs. open-source voice models (Moshi, etc.).

The product surface is deliberately narrow: **the AI you talk to in real time.** Not the AI that does your work autonomously. This is the operational form of TML's "human-AI collaboration over fully autonomous agents" thesis.

## How this maps to Murati's stated framings

- "AI as an extension of individual agency" → real-time multimodal back-and-forth keeps the human in the loop on every 200ms micro-turn.
- "Multimodality as the path to broad usefulness" → first-principles multimodal architecture, not text-with-voice-stapled-on.
- "Capability and safety go hand in hand" → faster turn-taking means the human can interrupt mid-generation, which is a form of safety control unavailable in turn-based architectures.
