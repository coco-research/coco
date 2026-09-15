# Chapter 1: Introduction — Why Million-Step Tasks Break LLMs

## Core Idea
A system with a 1% per-step error rate is *expected to fail after only 100 steps*. Solving a
task that needs a million dependent, error-free steps is therefore not a matter of using a
smarter model — it requires a fundamentally different architecture: Massively Decomposed
Agentic Processes (MDAPs).

## Frameworks Introduced
- **MDAP (Massively Decomposed Agentic Process)**: the general framework/paradigm — break a
  large task into the smallest possible subtasks, then apply subtask-level error correction.
  - When to use: any task whose accuracy requirement is much higher than a single LLM call's
    reliability can sustain over the task's step count (e.g. "must complete N steps with zero
    errors" rather than "score well on average over independent examples").
  - How: (1) decompose into minimal subtasks, (2) vote/error-correct at each subtask, (3)
    red-flag and discard suspicious outputs to reduce correlated errors.
- **MAKER**: the paper's first concrete implementation of MDAP — **M**aximal **A**gentic
  decomposition, first-to-ahead-by-**K** **E**rror correction, and **R**ed-flagging.

## Key Concepts
- **Per-step error rate (1−p)**: the probability a single LLM call in the chain gets its step
  wrong. Even a "good" 99% accuracy (1% error) benchmark score is catastrophic once you chain
  100+ dependent steps.
- **Multi-agent advantage**: analogous to quantum advantage — a solution reachable by a
  decomposed multi-agent system that is *not* reachable by any single monolithic agent, no
  matter how capable.
- **Micro-roles vs anthropomorphized roles**: assign each agent one tiny mechanical step
  instead of a human-like role. This exploits the machine-like, resamplable nature of LLMs
  (you can call the same "role" many times and vote) rather than treating agents as unique
  personas.

## Mental Models
- Think of a long agentic task the way you'd think of a classic benchmark score: "99% accuracy"
  sounds good in isolation, but translate it to "expected failure after ~100 steps" before
  trusting it on a long chain.
- Treat scaling reliability as an *orthogonal axis* to scaling raw model intelligence (Figure 1
  of the paper): instead of buying a smarter/more expensive base LLM, buy reliability through
  decomposition + voting with a cheap, small model.

## Anti-patterns
- **Judging LLM agentic reliability from short-benchmark accuracy alone**: a benchmark with a
  handful of dependent steps and an averaged accuracy score hides the exponential decay that
  shows up once you chain thousands+ of steps.
- **Assuming more capable/reasoning models fix long-horizon execution**: the paper's central
  surprise is that state-of-the-art reasoning models are *not required* — relatively small,
  non-reasoning models suffice once you add decomposition + voting.

## Key Takeaways
1. A 1%-per-step error rate fails almost surely after ~100 steps — "high accuracy" on
   short benchmarks says little about long-horizon reliability.
2. MDAPs are proposed as an orthogonal scaling axis to "make the base LLM smarter."
3. MAKER = Maximal Agentic decomposition + first-to-ahead-by-K voting + Red-flagging.
4. The paper's three core contributions: (a) the MDAP framework design, (b) a formalization
   yielding scaling laws for success probability and cost, (c) an empirical million-step,
   zero-error demonstration.

## Connects To
- **Ch 3**: the formal MAD / voting / red-flagging mechanics referenced here.
- **Ch 4**: the empirical million-step Towers-of-Hanoi validation of these claims.
