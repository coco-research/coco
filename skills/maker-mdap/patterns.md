# Patterns — MAKER / MDAP

## Maximal Agentic Decomposition (MAD)
**When to use**: a long agentic task can be expressed as a chain/recursion of minimal actions,
each fully specified by (current state, fixed overall strategy).
**How**: set subtask size m=1. Each agent call receives only the current state and the
strategy — never the accumulated history of prior actions. Extract the action *and* the next
state from each response; feed only the next state forward.
**Trade-offs**: turns 1 expensive point of failure into s cheap points of failure — but each
point is now individually protectable with voting. Requires the task to be expressible as
truly minimal, independent-per-call steps; doesn't help "insight" tasks where the plan itself
must be generated open-endedly.

## First-to-Ahead-by-k Voting
**When to use**: per-step success probability p > 0.5, and you need a target overall success
probability t across many dependent steps.
**How**: draw independent samples for a subtask; maintain vote counts; declare a candidate the
winner once its vote count exceeds every other candidate's by at least k. Pick `k_min` via
`k_min = ⌈ ln(t^(−m/s) − 1) / ln((1−p)/p) ⌉`, which grows only `Θ(ln s)`.
**Trade-offs**: cost per subtask grows with k (more samples needed), but k_min grows only
logarithmically with total step count s — so voting cost stays manageable even at extreme
scale. Requires a way to detect "the same answer" across samples (exact match here; could
generalize to semantic equivalence).

## Red-Flagging
**When to use**: whenever independent-sample voting is used and you suspect malformed or
overlong outputs correlate with underlying confusion/error.
**How**: define structural red flags (e.g. response length past an empirically-found
threshold; output that fails a strict format parser). Discard any flagged response outright —
do not attempt to repair it — and resample.
**Trade-offs**: costs a bit of extra sampling (lower effective v), but the paper shows this is
a good trade: raises average per-step success rate somewhat, and substantially reduces
*correlated* errors (collisions) compared to a "helpful" repairing parser.

## Calibrate-Then-Scale
**When to use**: before running any large, expensive multi-step agentic job.
**How**: batch-sample a small subset of steps where ground truth is knowable in advance (or at
least verifiable). Estimate p and mean output tokens per candidate model. Plug into the cost
formula `E[cost] ≈ c·s·k_min / (v·(2p−1))` and pick the model minimizing this, not the model
with the lowest $/token or the highest raw benchmark score.
**Trade-offs**: adds an upfront calibration pass, but avoids picking a model that is either
individually cheap-per-token yet needs an enormous k_min (bad), or nominally "smart" but
needlessly expensive once per-step reliability is factored in.

## Correlated-Error Detection via Collision Counting
**When to use**: any time you rely on the i.i.d.-errors assumption behind voting-based error
correction, to check whether that assumption actually holds.
**How**: count how many steps have their first two independent votes both land on the *same*
wrong answer ("collisions"). Compare the observed count against the i.i.d.-expected baseline
(roughly 1–2 collisions across a large experiment, if errors were truly independent).
**Trade-offs**: requires access to ground truth (or a way to know a vote was wrong) to compute
collisions directly; a proxy metric (e.g. flag rate by response-length bucket) can substitute
when ground truth isn't available.
