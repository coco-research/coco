---
name: maker-mdap
description: "Knowledge base from \"Solving a Million-Step LLM Task with Zero Errors\" (Meyerson, Paolo, Dailey, Shahrzad, Francon, Hayes, Qiu, Hodjat, Miikkulainen — arXiv:2511.09030). Use when designing long-horizon, multi-step agentic LLM pipelines that need very high reliability, applying Maximal Agentic Decomposition (MAD), first-to-ahead-by-k voting, or red-flagging error correction, estimating cost/reliability scaling laws for multi-agent systems, or studying Massively Decomposed Agentic Processes (MDAPs)."
domain: engineering
required: true
baseline: maker-mdap
---

<!-- argument-hint: [topic, framework name, or chapter number] -->

# Solving a Million-Step LLM Task with Zero Errors
**Authors**: Elliot Meyerson, Giuseppe Paolo, Roberto Dailey, Hormoz Shahrzad, Olivier Francon,
Conor F. Hayes, Xin Qiu, Babak Hodjat, Risto Miikkulainen (Cognizant AI Lab / UT Austin)
**Source**: arXiv:2511.09030 (Nov 2025) | **Pages**: ~29 | **Chapters**: 7 | **Generated**: 2026-08-26

## How to Use This Skill

- **Without arguments** — load core frameworks below for reference
- **With a topic** — ask about `voting`, `red-flagging`, `cost scaling`, `decomposition`, or
  another indexed topic; I find and read the relevant chapter
- **With a chapter** — ask for `ch03`; I load that specific chapter
- **Browse** — ask "what chapters do you have?" to see the full index

When you ask about a topic not covered in Core Frameworks below, I will read the relevant
chapter file before answering.

---

## Core Frameworks & Mental Models

**The problem**: LLMs have a persistent per-step error rate. A 1%-per-step error rate is
expected to fail by step ~100. Standard benchmarks (independent examples, averaged accuracy)
hide this — they don't expose what happens once you chain thousands or millions of *dependent*
steps. This paper solves a task requiring over **one million** dependent LLM steps with **zero
errors**, and argues the fix is architectural, not "wait for a smarter model."

**MDAP (Massively Decomposed Agentic Process)** — the general paradigm: decompose a task into
the smallest possible subtasks, then apply subtask-level error correction. **MAKER** is this
paper's concrete implementation: **M**aximal **A**gentic decomposition + first-to-ahead-by-**K**
**E**rror correction + **R**ed-flagging.

**1. Maximal Agentic Decomposition (MAD)** — set subtask size m=1 (one action per LLM call).
Each agent gets only `(current state, fixed strategy)` — never the accumulated history of past
actions. This avoids the reliability degradation single agents suffer as their own context
grows, and lets you use small, cheap, non-reasoning models. *Use X when Y*: use MAD whenever a
task decomposes into a chain/recursion of minimal, independently-checkable actions.

**2. First-to-ahead-by-k voting** — resample a subtask until one candidate has been chosen k
more times than every other candidate. Grounded in the Sequential Probability Ratio Test and
the gambler's-ruin problem. Critically, `k_min` (the smallest k hitting a target success
probability) grows only **`Θ(ln s)`** — logarithmically in total step count s.

**3. Red-flagging** — discard (don't repair) any response whose structure signals confusion:
overlong output, or output that fails a *strict* format parser. Its main benefit is suppressing
**correlated errors** (independent votes colliding on the same wrong answer), not just raising
average per-step success rate.

**The scaling-law punchline** (the single most important equation): total expected cost is
**`Θ(p^-m · c · s · ln s)`** — **exponential in subtask size m**, but only **log-linear in
total step count s**. Corollary: decompose maximally (small m); don't fear long tasks (large
s). Bundling steps "for efficiency" is the single biggest cost mistake this framework warns
against.

**Model/cost selection rule**: rank candidate models by **`c/p`** (cost per token ÷ per-step
success rate), not by raw price or "reasoning" reputation. Calibrate p on a small, cheap,
ground-truth-known sample *before* committing to a large-scale run. In this paper's
experiments, small non-reasoning models matched or beat reasoning models on cost-effectiveness.

**Verify voting is actually working**: don't trust average error rate alone — explicitly count
*collisions* (steps whose first two independent votes are both wrong). A low average error rate
can still hide dangerous correlated failures that only collision-counting exposes.

**Scope**: this paper covers *execution* (faithfully carrying out a given strategy) — not
*insight* (generating the strategy/plan itself). Know which one your problem needs.

---

## Chapter Index

| # | Title | Key Frameworks |
|---|-------|----------------|
| [ch01](chapters/ch01-introduction.md) | Introduction — Why Million-Step Tasks Break LLMs | MDAP, MAKER, multi-agent advantage |
| [ch02](chapters/ch02-background.md) | Background — Error Correction and the Hanoi Testbed | LbAs, voting/ensembling, decomposition granularity |
| [ch03](chapters/ch03-methods.md) | Methods — MAD, Voting, Red-Flagging | MAD, first-to-ahead-by-k voting, red-flagging, cost/scaling equations |
| [ch04](chapters/ch04-experiments.md) | Experiments — The 20-Disk Zero-Error Run | Calibrate-then-scale, model/cost selection, convergence behavior |
| [ch05](chapters/ch05-discussion.md) | Red-Flagging Impact, Discussion, Future Work | Collision counting, insight-vs-execution, microservices analogy, safety |
| [ch06](chapters/ch06-appendix-derivations.md) | Appendix A/B — k_min Derivation | Full derivation of k_min = Θ(ln s) |
| [ch07](chapters/ch07-appendix-prompts-parsers.md) | Appendix C/D — Prompts, Parsers, Samples | Reusable prompt template, repairing vs. red-flagging parsers |

## Topic Index

- **Calibrate-then-scale workflow** → ch04
- **Collision counting / correlated errors** → ch05
- **Cost scaling laws (Θ(s ln s), Θ(p^-m))** → ch03, ch04, ch06
- **Decomposition granularity (m)** → ch02, ch03
- **First-to-ahead-by-k voting** → ch03, ch06
- **Insight vs. execution** → ch05
- **k_min derivation** → ch03, ch06
- **MAD (Maximal Agentic Decomposition)** → ch01, ch03
- **MAKER (the implementation)** → ch01, ch03, ch04
- **MDAP (the general framework)** → ch01
- **Microservices analogy** → ch05
- **Model selection / cost projection** → ch04
- **Multi-agent advantage** → ch01
- **Parsers (repairing vs. red-flagging)** → ch03, ch07
- **Prompt template (Towers of Hanoi agent)** → ch07
- **Red-flagging** → ch03, ch05, ch07
- **Safety implications of decomposition** → ch05
- **Towers of Hanoi benchmark** → ch02, ch04
- **Voting theory (SPRT, gambler's ruin)** → ch02, ch03

## Supporting Files

- [glossary.md](glossary.md) — all key terms with definitions
- [patterns.md](patterns.md) — MAD, voting, red-flagging, calibrate-then-scale, collision counting
- [cheatsheet.md](cheatsheet.md) — decision rules, thresholds, model-selection matrix

---

## Scope & Limits

This skill covers this single paper's content only (arXiv:2511.09030, v1, Nov 2025). It
addresses *execution* of long-horizon agentic tasks, not open-ended plan/strategy generation
("insight"). Numeric thresholds cited (e.g. the ~700-token red-flagging cutoff) are specific to
this paper's Towers-of-Hanoi setup and prompt design — re-derive them empirically for any other
domain rather than reusing them as universal constants. For applying these ideas to your own
codebase or agent framework, combine with project-specific tools; for topics beyond this paper,
ask directly.
