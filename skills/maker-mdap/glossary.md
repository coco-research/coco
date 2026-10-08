# Glossary — MAKER / MDAP

**a_i (action)** — the extracted action at step i, `a_{i+1} = ψ_a(r_{i+1})` (Ch 3).

**c / c_sample / c_sub / c_full** — cost of one LLM call / one sampled subtask attempt / one
fully-voted subtask / the entire task (Ch 3).

**Collision** — a step whose first two independent votes are *both* wrong; used to detect
correlated errors beyond what an average error rate shows (Ch 5).

**Correlated errors** — errors that cluster on particular steps/inputs rather than occurring
independently at a uniform rate; the main threat that plain i.i.d.-assumption voting theory
doesn't cover (Ch 5).

**Decomposition granularity (m)** — the number of original steps bundled into one subtask that
a single LLM call handles; m=1 is Maximal Agentic Decomposition (Ch 3).

**Decorrelation** — techniques (prompt paraphrasing, injected noise, model diversity) to reduce
correlated errors between independent samples; flagged as future work here, not yet
implemented in this paper's experiments (Ch 5).

**Execution (vs. insight)** — following through on an already-given strategy/plan, as opposed
to creatively generating the strategy itself; this paper's MAKER targets execution only (Ch 5).

**First-to-ahead-by-k voting** — resample a subtask until one candidate answer has been chosen
k more times than every other candidate, then declare it the winner; grounded in SPRT and the
gambler's-ruin problem (Ch 3).

**k / k_min** — the vote margin required by first-to-ahead-by-k voting; k_min is the smallest
k achieving a target overall success probability, and grows only `Θ(ln s)` (Ch 3, Ch 6).

**Language-based Algorithms (LbAs)** — framing LLM call chains as algorithms running on a new,
nondeterministic computing substrate, requiring their own error-correction theory (Ch 2).

**MAD (Maximal Agentic Decomposition)** — decomposing a task into subtasks of size m=1 (single
action per LLM call) (Ch 3).

**MAKER** — Maximal Agentic decomposition, first-to-ahead-by-K Error correction, and
Red-flagging; the paper's first concrete implementation of the MDAP framework (Ch 1, Ch 3).

**MDAP (Massively Decomposed Agentic Process)** — the general paradigm: decompose a task into
minimal subtasks and apply subtask-level error correction to make massive-scale, high-reliability
execution feasible (Ch 1).

**Micro-role** — assigning an agent one tiny, mechanical, non-anthropomorphized task rather than
a human-like role, so the agent can be freely resampled/voted on (Ch 1).

**Multi-agent advantage** — a solution achievable by a decomposed multi-agent system that is not
achievable by any single monolithic agent, drawn as an analogy to quantum advantage (Ch 1).

**p / (1−p)** — per-step success / error probability of the underlying LLM+prompt+parser
pipeline for one subtask (Ch 3).

**p_alt** — probability of sampling the single most-likely *incorrect* alternative for a
subtask, `(1−p)·p^(m−1)` (Ch 3).

**p_full** — probability the voting procedure succeeds on every subtask in the whole task, i.e.
the full task completes correctly (Ch 3).

**p_sub** — probability the voting procedure succeeds on one subtask (Ch 3).

**p_vote** — probability of sampling the correct answer for a subtask, `p^m` (Ch 3).

**Red-flagging** — discarding an LLM response before voting if its structure (overlong, or
incorrectly formatted) signals it likely came from a confused generation; the main lever for
reducing correlated errors (Ch 3, Ch 5).

**Semantic density** — a measure of how consistently an LLM's sampled outputs agree in meaning
for a given prompt; higher consistency correlates with higher correctness (Ch 2).

**SPRT (Sequential Probability Ratio Test)** — the statistical test that motivates the
optimality of first-to-ahead-by-k voting (Ch 3).

**Towers of Hanoi (benchmark)** — D-disk, 3-peg puzzle used as the paper's testbed; optimal
solution length is `2^D − 1` steps; 20 disks ≈ 1,048,575 steps (Ch 2, Ch 4).

**v** — the probability a sampled response passes red-flagging (has no red flags); folds into
the effective expected cost as `Θ(c·s·ln(s) / (v·p))` (Ch 3).

**x_i (state)** — the extracted state after step i, `x_{i+1} = ψ_x(r_{i+1})`, the only thing fed
forward to the next agent under MAD (Ch 3).

**ψ_a, ψ_x, φ** — extractor functions: `ψ_a` parses the action from a raw LLM response, `ψ_x`
parses the next-state, and `φ` is the templating function mapping (input, subtask spec) to a
prompt (Ch 3, Ch 7).
