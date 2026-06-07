# Jason Wei — jasonwei.net Essays

Wei is unusual among frontier researchers in maintaining a long-running personal blog of short, sharp essays. Many of his most-quoted framings appear here first, before X threads or talks.

## Site

https://www.jasonwei.net/

The site is organized as a chronologically reverse-ordered list of essays. Posts are short (300-800 words), heavy on first-person framings, and almost always anchored to a single thesis.

## Representative essays (with takeaways)

### "How to do high-impact research"

- **URL:** https://www.jasonwei.net/blog/how-to-do-high-impact-research
- **Thesis:** Pick the right problem. Talent is necessary but research taste matters more than raw IQ or effort. You can work very hard on the wrong problem and produce a paper that nobody cites. He gives a heuristic: "what would be obvious in 5 years if we just kept scaling?" — work on that now.
- **Wei voice signature:** Plain English, opinionated, lists.

### "Successful language model evals"

- **URL:** https://www.jasonwei.net/blog/evals
- **Thesis:** A successful eval has (1) high signal: even minor model changes move the number; (2) high coverage: the metric reflects something a customer would notice; (3) low noise: variance across seeds is small. MMLU and GSM8K hit these; many "vibes" evals do not.
- **Wei voice signature:** Three-part framework, examples, prescriptive close.

### "Asymmetry of verification" (multiple posts)

- **URL:** https://www.jasonwei.net/blog/asymmetry-of-verification-and-verifiers-law
- **Thesis:** "Verifier's Law" — for tasks where verifying a solution is much cheaper than producing one, RL on a verifier signal scales effortlessly. This is why math, code, and proofs got crushed first. Open-ended creative writing is hard precisely because verification is expensive.
- **Wei voice signature:** Coins a "law," picks one mechanism (asymmetry), runs it through three examples.

### "Inference compute is the new scaling axis"

- **URL:** https://www.jasonwei.net/blog/inference-time-scaling (or sibling)
- **Thesis:** Pretraining FLOPs plateaued as the dominant scaling axis. Inference-time compute (more reasoning, more sampling, more search) is now the marginal-improvement frontier. o1, o3, Claude 3.7 thinking modes all reflect this.
- **Wei voice signature:** Names the new axis, predicts the consequence.

### "Some intuitions about large language models"

- **URL:** https://www.jasonwei.net/blog/some-intuitions-about-large-language-models
- **Thesis:** Lists 10-15 intuitions, e.g. "training data is the spec," "the right level of abstraction for LLM behaviour is the next-token-prediction objective," "in-context learning is a meta-learned implicit gradient step."
- **Wei voice signature:** Numbered list, one-line each, no defense — assertions of taste.

## Recurring themes across the blog

1. **Research taste matters more than research effort.**
2. **Verifiability is the dominant axis for what gets solved next.**
3. **Emergence is real and matters.** (Repeated defense against the "mirage" critique.)
4. **Inference compute is the new scaling axis.**
5. **Instruction tuning is the bridge from pretraining to usefulness.**
6. **Chain-of-thought works because it gives the model space to think.**
7. **The right path to AGI is "give the model more compute at inference time" combined with RL on verifiable tasks.**

## Voice fingerprint from the blog

- Short paragraphs.
- One thesis per post.
- First-person; signs off with "thanks for reading."
- Uses "I think" rather than "we believe."
- Never cites his own papers explicitly — assumes the reader knows the field.
- Comfortable with "I might be wrong about this." Rare in frontier-lab researchers.
- Lists of 3 or 5 or 7. Almost never 4 or 6.

## Sources

- https://www.jasonwei.net/
- https://www.jasonwei.net/blog (index)
