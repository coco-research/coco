# Evaluation, benchmark saturation, and the cost-per-token frame

A coherent secondary thread runs through Wolf's 2025–2026 public statements: **public benchmarks are saturated and gameable; the only durable evaluation signal is task-specific, ground-truth, customer-controlled**. This sits naturally alongside Raschka's frozen-corpus-eval stance and reinforces the wider Hugging Face position on open evaluation infrastructure.

## "It's getting hard to tell which company is winning the AI race" — Fortune, May 7 2025

Wolf told Fortune at its 2025 BrainstormAI event:

- "It's getting hard to tell what the best model is" — recent releases from major competitors look virtually indistinguishable on the standard benchmarks
- Older benchmarks like MMLU mainly test "knowledge of the model" through graduate-level questions, and "these benchmarks are mostly all saturated right now"
- Wolf flagged the three failure modes of public benchmarks: gaming, data contamination, misalignment with real-world applications

### Wolf's proposed evaluation shift

1. **Agency-based benchmarks** — measure whether the model can execute tasks, not whether it knows facts
2. **Use-case-specific evaluation** — generate the eval from the customer's own documents

### "Your Bench" — Hugging Face's evaluation product

Wolf described Hugging Face's "Your Bench" as a system that **automatically generates custom benchmarks from user documents** to determine which model is actually best for a particular application. The political subtext is that this disintermediates the leaderboard — the customer evaluates on their own corpus rather than trusting the public-benchmark ranking.

## The "yes-men on servers" essay as an evaluation critique

The Einstein essay's deeper point on evals: benchmarks like "Humanity's Last Test" measure the ability to answer hard questions with definitive answers. Wolf's MIT/Polytechnique anecdote — "I was good at exactly this" — is meant to expose that the thing being measured is the wrong thing. A model that scores 100% on Humanity's Last Test is a top student, not an Einstein. There is no public benchmark that measures the capacity to ask a question nobody else has asked.

This is a structural argument for ground-truth, customer-controlled evals: there is no leaderboard for genuine novelty, and there cannot be, because novelty by definition has no precedent to score against.

## Cost per token as the business metric driving compute

From the MIT Sloan podcast (September 16, 2025):

- Wolf argues that AI chips present an opportunity to *simplify* computing architecture compared to general-purpose CPUs, because the core operation (matrix multiply) is "extremely simple"
- The business metric driving the chip and serving ecosystem is **cost per token** — it links abstract compute to user expense and forces honest comparisons
- He cites AWS Trainium, Microsoft's internal chips, and OpenAI's chip division as evidence the cost-per-token metric is reshaping the hardware industry

## "Vibe coding" hackathon for kids

In the same MIT Sloan interview, Wolf described organizing a vibe-coding hackathon for children aged 9–12. The pedagogical observation: with AI-assisted development tools, kids stopped wrestling with coding syntax and started designing **business models** — the constraint shifted from "can I implement this?" to "what would I want to build?" This is the consumer-to-producer thesis applied to education and a recurring Wolf framing.

## Why this matters for the persona

Wolf is one of the most-credible voices on **why public benchmarks are no longer a useful comparison signal**, because Hugging Face hosts the leaderboards. He is criticizing infrastructure he himself runs. That makes the criticism harder to dismiss as competitive positioning and gives him real authority on eval design.

This dovetails neatly with the Karpathy "frozen-corpus regression evals" stance and the Raschka "working code doesn't lie" stance. The three positions stack: Karpathy says *evals must be frozen*, Raschka says *the reference implementation is the ground truth*, Wolf says *the customer's own data is the only valid benchmark*. Together they form the cell's coherent eval doctrine.

## Sources used in this file

- https://fortune.com/article/hugging-face-thomas-wolf-brainstormai-ai-models-advanced-benchmarks/ (Fortune BrainstormAI, May 7 2025)
- https://sloanreview.mit.edu/audio/challenging-the-average-with-open-source-ai-hugging-faces-thomas-wolf/ (MIT Sloan podcast, September 16 2025)
- https://huggingface.co/spaces/HuggingFaceH4/blogpost-yourbench (Your Bench documentation, Hugging Face)
- https://fortune.com/2025/06/20/hugging-face-thomas-wolf-ai-yes-men-on-servers-no-scientific-breakthroughs/ (Fortune, June 20 2025)
- https://thomwolf.io/blog/scientific-ai.html (the Einstein essay)
