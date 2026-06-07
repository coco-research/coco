# Canonical RL papers — TRPO, GAE, PPO

## TRPO — Trust Region Policy Optimization (ICML 2015)

Source: https://arxiv.org/abs/1502.05477

- Authors: John Schulman, Sergey Levine, Philipp Moritz, Michael I. Jordan, Pieter Abbeel.
- Submitted February 19, 2015. Published at ICML 2015.
- Core idea: iterative policy optimization with monotonic improvement guarantees, derived from natural policy gradient methods. Constrains each policy update so the KL divergence between old and new policy stays inside a trust region.
- Empirical claim: works on large nonlinear policies (neural nets) across simulated locomotion and Atari, with little hyperparameter tuning.
- Significance: first algorithm to make policy-gradient methods reliably train deep neural-net policies at scale. Set up everything that followed.

## GAE — Generalized Advantage Estimation (2015)

Source: https://arxiv.org/abs/1506.02438

- Title: "High-Dimensional Continuous Control Using Generalized Advantage Estimation."
- Authors: John Schulman, Philipp Moritz, Sergey Levine, Michael Jordan, Pieter Abbeel.
- Submitted June 8, 2015; last revised October 20, 2018.
- Core contribution: an exponentially-weighted estimator of the advantage function (parameter lambda), analogous to TD(lambda), that trades bias against variance in policy-gradient estimates.
- Demonstrated on 3D bipedal and quadrupedal locomotion learned end-to-end from raw kinematics to joint torques, model-free, in roughly 1-2 weeks of simulated real time.
- Significance: the variance-reduction half of Schulman's RL stack. PPO + GAE is still the canonical combination shipped in most production RL pipelines in 2026.

## PPO — Proximal Policy Optimization (2017)

Source: https://arxiv.org/abs/1707.06347

- Authors: John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, Oleg Klimov.
- Submitted July 20, 2017.
- Core idea: replace TRPO's hard KL-divergence trust-region constraint with a clipped surrogate objective. The clip on the probability ratio keeps updates near the old policy without solving a constrained optimization at every step.
- Allows multiple epochs of minibatch SGD per rollout, which TRPO's constraint structure does not.
- Authors' headline claim: "PPO retains some of the benefits of TRPO, but is much simpler to implement, more general, and has better sample complexity (empirically)."
- Empirical scope: simulated robotic locomotion and Atari.
- Subsequent significance — and this is the single most important applied-RL fact of the decade:
  - PPO is the default RL algorithm in essentially every major RLHF pipeline.
  - ChatGPT, GPT-4 post-training, Claude post-training, every major open-weights RLHF stack (Llama, Qwen, Mistral) ship with PPO or a PPO variant.
  - The 2017 PPO paper is by far Schulman's most cited and most economically consequential work.

## Why this matters for the persona

Schulman's identity as "the RL guy" comes from this trilogy. When he speaks about RL, hallucination, or post-training, the implicit context is always: "I built the algorithm that everyone is using, so I know exactly what it does and doesn't do." His critique of competing approaches almost always carries the subtext that he has done the experiment.
