# Dwarkesh Podcast — John Schulman appearance (May 15, 2024)

Source: https://www.dwarkesh.com/p/john-schulman

Episode title: "John Schulman (OpenAI Cofounder) — Reasoning, RLHF, and Plan for 2027 AGI."
Length: 1 hour 37 minutes.
Status at time of recording: still at OpenAI, leading post-training. The August 2024 Anthropic move had not yet happened.

## Key stances and direct quotes

### On post-training as a distinct discipline

"We're usually targeting a narrower range of behaviors where we want the model to behave like a kind of chat assistant." Post-training is the shift from imitating internet content to producing outputs humans will find useful. Most of GPT-4's roughly 100-point Elo improvement since release came from post-training, not new pre-trained checkpoints.

### On the plan if AGI arrives in 2025

"If AGI came way sooner than expected we would definitely want to be careful about it. We might want to slow down a little bit on training and deployment."

He frames this as a coordination problem: "You probably need some coordination. Everyone needs to agree on some reasonable limits to deployment or to further training." Pressed on what the equilibrium endpoint looks like, he answered plainly: "I don't have a good answer to that."

### On long-horizon RL

Long-horizon training enables "much more complex tasks" and "recovering from errors or dealing with edge cases." He expects models to become "more sample efficient" through generalization from pre-training. But he resists triumphalism: "I wouldn't expect improving the coherence a little bit to be all it takes to get to AGI. I guess I can't articulate exactly what are the main weaknesses."

### On reward modeling

"There's something of a moat because it's just a very complex operation and it takes a lot of skilled people to do it. There's a lot of tacit knowledge."

Preference learning is subtle: documentation matters as much as data. "You still need a decently long document to capture exactly what you want."

### On hallucination as a reward problem (the canonical Schulman framing)

Early ChatGPT versions hallucinated capabilities — claimed it could send emails or call an Uber. The fix was strikingly cheap: roughly "30 examples" showing the model its true limitations. The fix generalized to all kinds of capabilities the team had not specifically trained for.

The implication, which Schulman states explicitly elsewhere: hallucination is not a fundamental cognitive limitation. It is a reward-modeling problem. The base model's pattern-completion incentive is to keep generating; the post-training reward has to teach it that "I don't know" is an acceptable answer.

### On safety

Schulman advocates a "defense in depth" posture: well-trained models, hardened against misuse, plus monitoring layers that catch unforeseen failures. He pushes back on instrumental-convergence fearmongering for narrowly scoped tasks like coding, but acknowledges that goal-shaped tasks like "make money" can produce instrumental misbehavior.

He explicitly worries about competitive dynamics: "If firms with any humans in the loop were outcompeted by firms that didn't have any humans, then you would obviously need some kind of regulation."

### When does AI replace him?

"Maybe five years." Said with deliberate evenness.

## Signature framings to mine

- The "taming the shoggoth" frame in the episode title — post-training as the discipline that turns an unpredictable base model into a useful assistant.
- A four-stakeholder model: end user, developer, platform owner (e.g., OpenAI), broader humanity. Preference conflicts among these classes are unavoidable.
- "Helpful assistant" not "autonomous agent" as his preferred frame for near-term AI.
- His default rhetorical move when uncertain: admitting it plainly. "I don't have a good answer to that." That style separates him from Sutskever-style scaling maximalism and from Karpathy-style strong-priors framing.

## Relevance for persona

This is the single richest 2024-2025 source for Schulman's actual stances on RL, alignment, AGI timing, and reward modeling. Everything in the persona's `public_stances` and `mental_models` should be reconciled against this transcript first.
