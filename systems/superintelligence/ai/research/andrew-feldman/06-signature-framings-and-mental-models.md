# Andrew Feldman — Signature Framings, Mental Models, and Recurring Rhetoric

## Sources
- https://thestartupproject.io/transcripts/andrew-feldman-cerebras-ai-chip
- https://www.unite.ai/andrew-feldman-co-founder-ceo-of-cerebras-systems-interview-series/
- https://www.ark-invest.com/podcast/cerebras-wafer-scale-engine-ai-chip-with-ceo-andrew-feldman
- https://thedataexchange.media/cerebras-inference/
- https://eclipse.capital/blog/accelerating-discovery-andrew-feldman-co-founder-and-ceo-cerebras-systems
- https://www.cerebras.ai/blog/2026Insights
- https://www.benzinga.com/Opinion/26/03/50968857/cerebras-ceo-andrew-feldman-on-challenging-nvidia-ipo-plans
- https://cryptobriefing.com/cerebras-ceo-feldman-largest-ai-chip/
- https://aimmediahouse.com/market-industry/the-future-of-ai-is-wafer-scale-says-andrew-feldman

## The seven framings Feldman returns to

### 1. "GPUs were designed for graphics, not for AI"

The structural argument: GPUs were optimized for the graphics pattern, where data moves into the chip once and then a lot of arithmetic is performed on it before results come back out. AI inference has the opposite pattern — model weights have to be moved across the memory bus for every token generated, and the model is enormous relative to the activations being computed on. Quote (paraphrased from the Startup Project transcript):

> "Graphics was a problem where you'd move data once, do a lot of work on it, and then bring the results back."

The corollary, used repeatedly: "GPU systems were never designed for this phase of AI." (Cerebras 2026 Insights blog.)

### 2. "Moving data is really expensive in power and time"

This is the physics statement underneath the architecture argument. Off-chip DRAM access (HBM included) is two orders of magnitude more expensive per byte than on-chip SRAM access, both in latency and in joules. Wafer-scale is a forcing function that eliminates the off-chip access path entirely.

Concrete illustration Feldman uses on multiple podcasts: generating a single token from a 70B-parameter model requires moving roughly **"100 full-length movies' worth of data"** across the memory interface on a GPU system. Wafer-scale's 21 PB/s of on-chip bandwidth turns that movie-streaming problem into an on-die problem.

### 3. "Inference is the real market, and inference speed is the real constraint"

Until mid-2024, the dominant industry framing was that training compute would scale indefinitely and inference would be a comparatively cheap downstream concern. Feldman's repeated 2024–2026 framing is that this is wrong: inference token volume is growing faster than training compute, and reasoning-style models multiply the inference cost per query by orders of magnitude. From the Cerebras 2026 blog:

> "inference speed is not a bragging point. It is the real constraint that determines what AI systems can do."

From the March 2026 Benzinga interview:

> "Right now, inference time computes — improving the quality of the answer based on additional use of tokens through reasoning is an extremely powerful tool."

The Cerebras Scaling Law (Cerebras's company-branded reframe): **"models that can think more in the same amount of time produce better results."**

### 4. "It's very hard to get paid for software when you're selling chips"

This is the vertical-integration argument, lifted directly from the SeaMicro retrospective. Feldman explicitly does not sell bare WSE-3 wafers. Cerebras ships systems in a rack (CS-3), data-center clusters (Condor Galaxy), or a hosted inference API. The rationale: chip-component margins are competed away; system, software, and service margins are not. NVIDIA's DGX strategy is his explicit reference point.

This framing also explains why Feldman is allergic to OEM/partnership models that would put another company's brand between Cerebras and the customer.

### 5. "Switching cost from NVIDIA is 10 keystrokes"

The contrarian moat claim. The CUDA developer ecosystem is widely treated as NVIDIA's primary structural advantage. Feldman's counter, repeated in the March 2026 Benzinga interview:

> "To move from using NVIDIA GPUs, for inference, to Cerebras in our cloud will take about 10 keystrokes and should take you less than a minute."

The implicit argument: CUDA is a moat in the *training* market (where you write kernels, do custom optimization, manage gradient flow) but is a thin moat in the *inference* market (where 90% of traffic flows through standardized APIs — OpenAI-compatible endpoints, vLLM, TGI). For inference customers, the switching cost is changing a base URL and an API key. If inference is the market that matters, CUDA is not the moat NVIDIA needs it to be.

### 6. "We are not in a winner-take-all market"

Pluralism as strategy. From March 2026 Benzinga:

> "This is a huge market, there's lots of opportunity… I think there'll be many winners."

This framing is also a Washington/CFIUS-shaped argument: AI compute is a strategic resource, the US shouldn't treat any single supplier as a single point of failure, and Cerebras-as-NVIDIA-alternative is a national-resilience argument as well as a commercial one. Useful framing both with regulators and with hyperscaler procurement teams that don't want NVIDIA monopoly pricing.

### 7. "Experience compounds in chip companies"

The defense against the "kids in a garage will disrupt you" framing. Software startups can be founded by 22-year-olds; chip companies cannot. Foundry relationships (TSMC), EDA tool licensing, package and substrate vendors, advanced cooling, IP libraries — all of these require multi-decade industry relationships. Feldman's argument, from the Startup Project transcript: returns to experience are higher in deep-tech than in software, so a senior team with multiple prior exits is a structural advantage, not a liability. This is also the implicit answer to "why hasn't NVIDIA copied wafer-scale" — they would need 5–7 years and $2–3B, and Cerebras would still be 10 years ahead.

## Mental models he reasons through

1. **Bandwidth-per-byte-of-model-weight as the binding constraint.** Once a model is too large to fit in on-die SRAM on a single GPU, every additional layer of memory hierarchy adds latency and power. Wafer-scale dissolves the hierarchy.

2. **Architectures are downstream of workloads, not the other way around.** GPUs fit graphics. Routers fit packet-switched IP. Microservers fit hyperscale web. Wafer-scale fits dense matrix operations on enormous parameter sets. Choose the architecture from the workload, not the workload from the architecture you happen to own.

3. **Sell the system, not the component.** Margin and software defensibility live at the system level. (Riverstone → Force10 → SeaMicro → Cerebras is the same lesson learned four times.)

4. **Time-to-foundry-tape-out is the chip-company analogue of time-to-product-market-fit.** Until you have working silicon on a customer's floor, you have nothing. Cerebras's 2019 packaging crisis was the analog of a SaaS company's pre-product-market-fit cash crunch — only with $8M/month burn and "no existing vendors or manufacturing partners to help."

5. **The right architecture wins the long arc, even when the wrong architecture wins the short one.** GPUs dominated the 2015–2024 deep-learning era because they were available and the software stack matured around them, not because they were the right architecture. The right architecture (purpose-built for AI dataflow) wins in the regime where the workload's properties dominate over the ecosystem's inertia — which Feldman argues is now, in inference.

6. **Vertical integration is the moat, not the chip.** A chip is a feature. A vertically integrated chip + system + software + hosted-service stack is a moat. This is the lesson he extracted from the AMD SeaMicro absorption.

## Voice characteristics

- **MBA-cadence:** structured, three-points, "let me give you the three things going on here." Stanford GSB rhythms.
- **Concrete-number-heavy:** 56× the size of the largest GPU; 21 PB/s vs. 8 TB/s; 2,500 TPS vs. 1,000 TPS; $200M and $8M/month burn; 10 keystrokes; 10 to 15 years. Almost every framing is anchored to a hard number.
- **Analogies to physical scale:** dinner plate, 100 full-length movies, a wafer.
- **Generous with co-founder credit:** Sean Lie in particular is repeatedly named as the engineering counterpart.
- **Pitchy register:** there is a sales/keynote tempo even in unscripted contexts. This is the blind spot — when convening him alongside someone like Karpathy or Catanzaro, the polish can read as evangelism.
- **Comfortable in geopolitics:** TSMC, CFIUS, G42, US onshoring, export controls — he speaks fluently about the policy envelope around frontier compute. This separates him from most chip CEOs who avoid the topic.
