# Dwarkesh Podcast — Jeff Dean & Noam Shazeer, "25 years at Google: from PageRank to AGI" (Feb 12, 2025)

Source: https://www.dwarkesh.com/p/jeff-dean-and-noam-shazeer
Coverage: https://www.techmeme.com/250215/p11
Apple Podcasts: https://podcasts.apple.com/us/podcast/jeff-dean-noam-shazeer-25-years-at-google-from-pagerank/

This is the single most important Shazeer public source from the last 12 months. He very rarely does podcasts. The episode runs ~2 hours with Jeff Dean as co-guest, covering MapReduce, BigTable, TensorFlow, AlphaChip, MoE, the Transformer, TPUs, and Gemini.

## Shazeer's framings, quoted or paraphrased

### On the long-term ambition

> "I've stopped cleaning my garage because I'm waiting for the robots."

Casual reference to his stated New Year's resolution from 2000: "to live to see the year 3000, and to achieve this by inventing AI." He is openly a transhumanist-adjacent fast-takeoff believer.

### On the scale of AI's economic potential

> "A trillion dollars is not cool anymore. What's cool is a quadrillion dollars."

He frames AI's payoff not as a Schmidt-style ten-baggar but as a substrate change in the size of the global economy.

### On inference cost

> "You're getting a million tokens to the dollar."

Frames LLM inference as "100 times cheaper than reading a paperback" and orders of magnitude cheaper than any professional service. His view: the right unit is cents-per-trillion-tokens, and the trend line is favorable for as far as he can see.

### On hardware and data movement

> "Arithmetic is very, very cheap, and moving data around is comparatively much more expensive."

This is the bandwidth thesis that drives his architectural choices: MoE saves compute but requires careful sharding; attention scales quadratically in sequence but linearly in moved bytes; the whole architecture has to be designed around the memory hierarchy.

### On his own research style

> "I wake up in the morning, come up with an idea, hack it up in a day, run some experiments, get initial results in a day."

He sees one-day-to-signal as the right cadence for architectural research. This is his pedagogical model and his hiring filter.

### On stacking improvements

> "It happens 50% of the time" — when ablations show two improvements that look additive in isolation fail to stack at scale.

The 50% number is a Shazeer one-liner that has circulated in ML Twitter as the "Shazeer law" of architecture research: do not assume two locally-winning ideas will compose.

### On MoE

> "I found experts to be relatively easy to understand."

Lifelong stance, restated. He treats mixture-of-experts as essentially the natural form of a deep network and treats dense models as the special case.

### On safety and verification

> "Analyzing text seems to be easier than generating text. So language models that can figure out what is problematic or dangerous will actually be the solution to a lot of these control issues."

This is his entire safety position in one sentence. He believes verifier models will scale to handle alignment because verification is computationally easier than generation.

### On misuse and concentration of capability

> "If somebody takes your thing and creates a million evil software engineers, that doesn't empower people."

Notable because it is one of the few times he has publicly acknowledged a misuse concern. His framing is still capability-distribution, not value alignment.

### On AGI definition

(Echoing the Wikipedia quote) — he does not particularly care about AGI as a "do everything a human can do" target. He cares about LLMs generating value across narrow but very high-impact domains.

## What the podcast does NOT show

- Any acknowledgement of the Setzer lawsuit.
- Any direct engagement with Anthropic or OpenAI specifically.
- Any concession on the velocity-vs-caution debate that drove him out of Google in 2021.

## Why this matters for the persona

This is the single most quote-rich source. The persona file's voice_style and sample direct quotes should be anchored here.
