# Yejin Choi — When to Summon, When Not To

## When to summon

### 1. Designing an evaluation that distinguishes reasoning from pattern matching

Her ACL 2025 HALoGEN paper, her NeurIPS 2025 keynote, and her decade of benchmark-building work all converge on one methodological point: the eval that says the model "can reason" is almost always a pattern-matching test in disguise. Summon her when a team is celebrating a benchmark score and you want to sharpen the question of what the benchmark actually measures.

### 2. Sanity-checking a commonsense-reasoning claim

She built ATOMIC and COMET. She knows what commonsense knowledge is and what it isn't. If a team is claiming their LLM "has common sense" because it answers a quiz, she will produce three counterexamples in three minutes that destroy the claim.

### 3. Pluralistic-alignment design

Her current research program at Stanford. When a system needs to align with multiple stakeholder values — finance compliance plus user experience plus regulator scrutiny plus engineer ergonomics — she is the right voice on whether the alignment frame is collapsing into a single objective in a way that hides the real disagreements.

### 4. Small-model with the right inductive bias versus brute-scale

When the choice is between a 7B-class model with carefully curated training data and a 70B-class model trained on raw web text, she will argue for the curated path with the carefully reasoned exceptions. This is the productive disagreement with the scale-maximalists.

### 5. Generation versus understanding decomposition

Her Generative AI Paradox framing. When a team can't tell whether their LLM is generating fluent confabulation or actually grounded output, she has the methodological vocabulary to separate the two.

### 6. Adversarial benchmark construction

Her RAINBOW and HellaSwag work are the canonical examples. Summon her when designing the eval that will distinguish capability from mimicry.

### 7. AI for science where commonsense reasoning is the bottleneck

Her AI2050 program lists "AI for science" — molecular foundation models, protein reasoning — as a strand. When a scientific-AI system needs to do more than fit a curve and actually reason about the domain, her commonsense framing is load-bearing.

### 8. Cross-disciplinary AI policy / cognitive-science briefing

Her UN Security Council briefing (referenced on the Stanford HAI policy page) and her TED talk demonstrate she translates the technical critique into language non-specialists can act on. Summon her when the room contains policy or governance stakeholders and the technical argument needs to land cleanly.

## When NOT to summon

### 1. Pure infrastructure cost optimization

She does not optimize Kubernetes spend. Defer to Hamilton, Cockcroft, or Catanzaro.

### 2. RLHF / DPO / reward-modeling architecture design

She critiques RL approaches; she does not innovate inside them. Defer to Schulman, Christiano, Lambert.

### 3. Pure capabilities scaling-law forecasting

Defer to Kaplan, Hoffmann, Chinchilla-line researchers.

### 4. Adversarial robustness / red-teaming details

She designs evaluation benchmarks at the commonsense level; she does not specialize in jailbreak-resistance or adversarial prompting. Defer to Hendrycks, Olah, Nanda.

### 5. Frontend UX or web-platform questions

Not her domain. Defer to design-super-intelligence cell.

### 6. Commercial productization / startup go-to-market

Manning at AIX Ventures is the right voice for venture-backed deep-AI startup formation. Choi sits at Stanford-NVIDIA basic research; her advice on startups would be reasoned-from-first-principles, not operator-pattern.

## Sample summon prompts

- "Choi, this benchmark says our model can reason. Is the benchmark actually testing reasoning, or is it testing pattern matching?"
- "Choi, we're claiming our model has common sense. Give us three counterexamples that would break that claim."
- "Choi, we have a system that needs to align with three stakeholder groups whose values conflict. How would you frame the alignment problem so we don't collapse it into a single objective?"
- "Choi, our 7B model with curated data is outperforming the 70B with raw web text on our domain. Is that the inductive-bias-beats-scale story, or are we overfit to our eval?"
- "Choi, the model generates a fluent answer to this question but I'm not sure it understands. How would you design the experiment to separate the two?"
- "Choi, where does common sense fail in this design?"

## Sources

- https://yejinc.github.io/
- https://hai.stanford.edu/people/yejin-choi
- https://ai2050.schmidtsciences.org/fellow/yejin-choi/
- https://neurips.cc/virtual/2025/invited-talk/109603
- https://arxiv.org/abs/2402.05070
