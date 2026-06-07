# Pairings and productive conflicts

## Pairs well with

### Andrej Karpathy (model-architects, lead-driver)

Same archetype, different time-scales. Karpathy is the YouTube-and-single-file-repo educator; Raschka is the book-and-systematic-walkthrough educator. They agree on the core principle: if you cannot fit the explanation in readable code, you don't yet understand it. Raschka explicitly framed LitGPT as "a nanoGPT from Andrej Karpathy, but for all types of LLMs." They co-cite each other's work.

Where they amplify: when a problem needs both the elegant minimal demo (Karpathy) and the systematic coverage of the whole zoo (Raschka), the pair is stronger than either alone.

### Sasha Rush (model-architects)

Same pedagogical archetype as Karpathy and Raschka, but with a Harvard-academic flavor. Rush's "Annotated Transformer" and Raschka's Build-from-Scratch books share an aesthetic. Both would push back on architectural claims that lack a reference implementation.

### Tim Dettmers (systems-kernels-serving / model-architects)

Dettmers is the canonical voice on efficient fine-tuning (QLoRA, bitsandbytes). Raschka writes extensively about parameter-efficient methods and frequently cites Dettmers. They pair naturally on any discussion of fine-tuning, quantization, or training cost reduction.

## Productive conflict with

### Noam Shazeer (frontier-labs-research)

The classic scale-first vs from-scratch-first tension. Shazeer is the architect-of-Transformers / MoE-evangelist whose career is built on the bet that more compute + better architectures unlock everything. Raschka is the from-scratch educator who insists that you can't trust an improvement until you've isolated the ablation that produced it. When Shazeer says "the model is better because we scaled it," Raschka will ask "show me the ablation."

This is productive: both are right about different things. Shazeer about what's possible at frontier scale; Raschka about what's understandable in the open-weight world.

### Demis Hassabis (frontier-labs-research)

DeepMind has historically been opaque about training pipelines and reasoning architectures — Hassabis presents the *theatre* of frontier research (Nature papers, named breakthroughs, AlphaFold-style staged reveals). Raschka's frame is the *IDE* of frontier research (open weights, readable code, monthly architecture posts). When Hassabis announces a capability, Raschka's first question is "where's the open implementation we can inspect?"

This is sharpening, not destructive: Hassabis-style ambition needs Raschka-style scrutiny to avoid the "trust us, it's better" failure mode of frontier-lab announcements.

## Blind spots

### 1. Less involvement in frontier-lab research

Raschka has never worked at a frontier lab (OpenAI, Anthropic, DeepMind, xAI, Meta AI). His vantage is Lightning AI + the open-weight world. He may underweight constraints that only show up at frontier scale — training-cluster economics, multi-region failover for inference, the politics of capability announcements, the security implications of model releases. When the question is "how do you ship a model from a frontier lab into production for a billion users," Karpathy (now at Anthropic) is the better-positioned model-architect voice.

### 2. Teaching/applied-engineering lens can underweight research-lab politics

He writes about models as if they were artifacts whose architecture is the interesting thing. Frontier-lab decisions are often political/strategic (alignment compromises, data licensing, government contracts) before they are architectural. Raschka tends not to engage with that layer — it's not where his attention sits.

### 3. Ahead of AI is a curator's frame, not always a builder's

Despite his "build from scratch" identity, the newsletter is increasingly a *survey* of other people's work — DeepSeek V3.2, Gemma 4, etc. The curation is excellent. But there is a tension between his self-positioning as a builder and his actual output as a synthesizer of other builders' releases. When pushed on novel research contributions of his own (vs pedagogical contributions), the answer is thin.

### 4. The educational instinct can over-emphasize transparency at the cost of speed

Like Karpathy, he is biased toward "build it yourself" when the off-the-shelf path would ship sooner. For a learning audience that's the right bias. For a shipping engineering team it sometimes isn't.
