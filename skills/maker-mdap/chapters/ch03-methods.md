# Chapter 3: Methods — MAD, First-to-Ahead-by-k Voting, and Red-Flagging

## Core Idea
Three ingredients combine multiplicatively: (1) decompose into single-step subtasks (MAD), (2)
resolve each subtask by first-to-ahead-by-k voting among independent samples, (3) discard
("red-flag") any sample that looks structurally unreliable before it even reaches a vote. Cost
grows only log-linearly with the number of steps s under MAD, vs. exponentially with subtask
size m.

## Frameworks Introduced

- **Maximal Agentic Decomposition (MAD)**: set the subtask size m = 1 (one action per LLM
  call), the extreme end of the general decomposition spectrum where m = s is "single-agent."
  - When to use: whenever the task can be broken into a linear/recursive chain of minimal
    actions, each expressible with just (a) the current state and (b) the overall strategy.
  - How: for each step i, sample a response `r_{i+1} ~ M(φ(x_i))`, extract the action
    `a_{i+1} = ψ_a(r_{i+1})`, extract the next state `x_{i+1} = ψ_x(r_{i+1})`. Feed only
    `x_{i+1}` forward — never the growing transcript of past actions.
  - Why it works: an auto-regressive single agent gets *increasingly burdened* by its own
    growing context as it generates more of a long chain, and reliability degrades as context
    grows. MAD caps each agent's context at "just enough to do this one step," sidestepping
    that degradation and letting you use much smaller/cheaper models.

- **First-to-ahead-by-k voting** (Algorithm 2/3 in the paper): draw independent samples for a
  subtask until one candidate has been chosen k more times than every other candidate; declare
  that candidate the winner.
  - When to use: whenever per-step success probability p > 0.5 (majority of independent
    samples favor the correct answer) but not so close to 1 that no correction is needed.
  - How (Algorithm 2, `do_voting(x, M, k)`): maintain vote counts V; repeatedly call
    `get_vote(x, M)` (Algorithm 3 — resample until a response has no red flags, then extract);
    increment V[y]; stop and return y once `V[y] ≥ k + max_{v≠y} V[v]`.
  - Grounded in the Sequential Probability Ratio Test (SPRT) and the classic gambler's-ruin
    problem — first-to-ahead-by-k is the optimality-motivated generalization of "first past the
    post."

- **Red-flagging** (Section 3.3): discard any LLM response whose *structure* signals it was
  produced from a "confused" state, before it's even counted as a vote.
  - When to use: as a cheap pre-filter before voting, especially on tasks with a strict output
    format.
  - How: this paper used two concrete flags — (1) response length over ~700–750 tokens
    (empirically, error rate spikes sharply past this point), and (2) incorrectly-formatted
    output (fails the strict parser). Flagged responses are simply discarded and resampled —
    cheap, because each step is cheap in MAD.
  - Why it works — the deeper insight: the two most useful effects are (a) raising the average
    per-step success rate p, and (b) far more importantly, **reducing correlated errors**
    (multiple votes landing on the *same* wrong answer). Discarding "confused" transcripts
    breaks the correlation that would otherwise defeat independent-sample voting.

## Key Concepts
- **p / (1−p)**: per-step success / error probability of the underlying LLM+prompt+parser.
- **m**: number of steps bundled into one subtask (decomposition granularity). MAD = m=1.
- **k / k_min**: the vote margin required to declare a winner; `k_min` is the *smallest* k that
  hits a target overall success probability t. **k_min grows only O(ln s)** — logarithmically
  in the number of total steps (Eq. 14).
- **p_vote / p_alt**: probability of sampling the correct vs. the single most-likely alternative
  for a subtask — `p_vote = p^m`, `p_alt = (1−p)·p^(m-1)`. Both terms shrink as m grows, which is
  exactly why large m (little decomposition) is disastrous.
- **p_sub / p_full**: probability the voting procedure succeeds on one subtask / on every
  subtask in the whole task (Eq. 12–13). `p_full` is what must stay near 1 across a million
  steps.
- **c / c_sample / c_sub / c_full**: cost of one LLM call / one full subtask sample / a subtask
  after voting / the entire task. Cost is **Θ(p^-m · c · s · ln s)** in general — **exponential
  in m**, but only **log-linear in s** when m=1 (Eq. 17–18). This is the paper's central
  scaling-law punchline.
- **v**: probability a response passes red-flagging (has no red flags). With red-flagging,
  effective expected cost becomes `Θ(c·s·ln(s) / (v·p))` (Eq. 19) — red-flagging trades a
  little discard overhead (lower v) for a higher effective p.

## Mental Models
- **"Weakest link, but recoverable"**: MAD turns 1 point of failure into s points of failure —
  but each point is now cheap enough (single tiny step) to protect with independent voting.
  Without MAD you have 1 expensive, unprotectable point of failure; with MAD you have s cheap,
  protectable ones.
- **"Exponential-in-m is the real enemy, not s"**: don't fear task length (s) — fear subtask
  size (m). A task with a million steps and m=1 is tractable; a task with a thousand steps and
  large m can be effectively infeasible (Figure 5).
- **"Discard, don't repair"**: when a response looks malformed or overlong, the paper's finding
  is that trying to *repair* it (a "helpful" parser) is worse than just throwing it away and
  resampling — malformed output is a symptom of a confused generation, not just a formatting
  slip, and repairing it lets a likely-wrong answer back into the vote.

## Anti-patterns
- **Larger subtasks "for efficiency"**: increasing m to reduce the number of LLM calls looks
  efficient but makes cost blow up *exponentially* (Figure 5) — the opposite of efficient once
  more than a handful of steps are bundled.
- **Feeding the full action history back into each agent's context**: MAD's benefit depends on
  keeping each agent's input to "current state + strategy," not the accumulated transcript —
  reintroducing full history reintroduces the auto-regressive degradation MAD is designed to
  avoid.
- **Using a "helpful" repairing parser instead of red-flagging**: Section 4.5 shows this
  directly increases *correlated* error collisions compared to a strict discard-and-resample
  parser, even though it looks more user-friendly.
- **Assuming errors are independent by default**: the theory (Eq. 9–19) assumes i.i.d. errors;
  real systems can have anomalously error-prone individual steps (Ch 4/5) that violate this and
  must be actively guarded against (red-flagging, and future decorrelation methods).

## Key Takeaways
1. MAD (m=1) plus per-subtask voting plus red-flagging together cut a million-step task's
   expected cost down to `Θ(s ln s)` — log-linear in the number of steps.
2. `k_min`, the vote margin needed for a target success probability, grows only logarithmically
   in s (Eq. 14) — you don't need dramatically more votes as tasks get longer.
3. Subtask size m is the dangerous scaling knob (cost is exponential in m); step count s is the
   safe one (cost is log-linear in s) — decompose maximally, don't bundle steps for efficiency.
4. Red-flagging's real value is suppressing *correlated* errors, not just raising the average
   per-step success rate.
5. Discard-and-resample beats repair-and-keep for malformed LLM outputs in this setting.

## Connects To
- **Ch 4**: empirically validates every equation here on the 20-disk (1M+ step) experiment.
- **Ch 7 (Appendix C)**: the actual prompt templates and both parser implementations
  (repairing vs. red-flagging) referenced above.
- **Ch 6 (Appendix B)**: full derivation of `k_min = Θ(ln s)` (Eq. 14).
