# Pre-Deployment Evaluations, Independent Evaluation, and the Lab Self-Evaluation Critique

Sources: 80,000 Hours episode 217 (`https://80000hours.org/podcast/episodes/beth-barnes-ai-safety-evals/`, June 2, 2025; recorded February 17, 2025); AXRP Episode 34 (`https://axrp.net/episode/2024/07/28/episode-34-ai-evaluations-beth-barnes.html`, July 28, 2024); EA Forum summary (`https://forum.effectivealtruism.org/posts/QFQdW3iXnT7SHCm9y/`); METR review of Anthropic February 2026 Risk Report (`https://metr.org/blog/2026-05-08-rd-section-anthropic-risk-report-feb-2026-review/`, May 8, 2026).

## The Barnes thesis on evaluations

There are three Barnes claims that recur across every interview and that anchor her cell role:

1. **Pre-deployment is the worst time to evaluate model safety.** "Ideally, before you start training a model and before you commit a huge amount of expensive compute to producing this artefact, you look at the most capable models you have already." Evaluating only at pre-deployment misses the window to sound the alarm. By the time a lab is in pre-deployment, the model is built, the cost is sunk, the release plan is in motion, and the political economy of cancelling or substantially delaying a release is brutal. The right time to evaluate is during training — and ideally before training, by extrapolating from the previous generation.
2. **Pre-deployment evaluations could actually be bad.** From the 80,000 Hours episode, verbatim: "Pre-deployment evals could actually be bad, because delaying deployment could be bad if that means you miss the window to sound the alarm." This is the strong version of the claim. If the only evaluation gate is pre-deployment, the structural incentives push toward making the eval pass, not making the model safer.
3. **Independent third-party evaluation is structurally necessary.** Labs cannot grade their own homework on dangerous capabilities. "I haven't seen that much evidence that there are these really good benchmarks and they're just inside labs. That may be true, but I don't particularly have reason to believe that labs are super on top of this either." (AXRP Episode 34, July 2024.) The institutional posture matters more than the lab's internal team capability.

## The lab self-evaluation critique made concrete

The May 8, 2026 METR review of Anthropic's February 2026 Risk Report is the cleanest published instance of Barnes's framework applied. Co-authored by Nikola Jurkovic, Beth Barnes, and Hjalmar Wijk. Key claims:

- Anthropic's risk report uses an internal employee survey as one of its central pieces of evidence about AI R&D acceleration risk.
- The survey has sample-size, question-granularity, and framing problems severe enough that METR concludes the cited results "provide little evidence about the level of overall risk."
- A specific methodological flaw — counting a missing survey response as a negative response — biases conclusions.
- The Anthropic report omits the possibility of substantial AI R&D acceleration before full automation, narrowing the threat surface artificially.
- METR ends up agreeing with Anthropic's bottom-line that Claude Opus 4.6 does not pose catastrophic R&D-automation risk, **but rejects the report's evidence base as inadequate to establish that conclusion**. The independent reviewers carry the conclusion, not Anthropic's internal evidence.

This is the operational form of the lab self-evaluation critique. It is not "labs are lying"; it is "labs are not running the eval well enough for the result to be load-bearing."

## What labs actually want from external evaluators

From 80,000 Hours: "Labs more want a 'Can you promise that you will run an eval on all of our models when we want to?' sort of thing... that's not what we're excited about." Labs want on-demand eval-as-a-service that produces a clean number for the system card. METR wants an institutional posture that lets the evaluator say no, change methodology mid-study, or publish criticism of the lab's internal evaluation methods. The two postures are not the same and Barnes is publicly clear about which one METR will not become.

## METR's funding posture

To date, METR has not accepted payment from frontier AI labs for running evaluations. The organization is funded philanthropically. This is the explicit guardrail against capture. Barnes acknowledges in interviews that the perception-of-independence question is real — METR's evaluations of OpenAI and Anthropic models are read by some critics through the lens of who funds METR and through her own past employment at OpenAI. The structural answer is the no-payment-from-labs rule plus full publication of methodology.

## Elicitation gap

A recurring methodological theme. From AXRP Episode 34: "if you don't have fine-tuning access… you could be getting a wildly different result than you should be." The elicitation gap is the difference between (a) what a model can do under best-effort post-training elicitation by a determined adversary, and (b) what a model does on a standard evaluation prompt. The gap can be large and is unpredictable. METR's evaluation protocol explicitly:

- Reserves a held-out test set so prompt-engineering does not contaminate the result.
- Adds a safety margin for capability that could be unlocked by future post-training enhancements.
- Treats narrow task-specific elicitation as untrustworthy unless the elicitation distribution actually matches the real-world threat distribution.

## What goes in a Senate-staff version of the argument

The 80,000 Hours episode's most-quoted line for policy audiences: "I had a lot of fun chatting with Rob about METR's work. I stand by my claims here that the world is not on track to keep risk from AI to an acceptable level, and we desperately need more people working on these problems." (Beth Barnes on X, post about the 80,000 Hours interview, June 4, 2025, status URL `https://x.com/BethMayBarnes/status/1930091384213778743`.)

## Open-weight model reversal

Notable opinion shift documented in the 80,000 Hours episode: Barnes reversed her earlier position on open-source releases. She now views open-weight models as **net beneficial** for safety research because they reduce unhealthy lab secrecy and let third parties run the evaluations labs do not run themselves. This is the strongest available signal that she weights independent-evaluation access higher than the conventional "open weights are dangerous" framing.
