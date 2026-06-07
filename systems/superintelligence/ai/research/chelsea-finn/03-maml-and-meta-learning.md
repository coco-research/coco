# MAML and Finn's meta-learning agenda

Sources:
- https://proceedings.mlr.press/v70/finn17a.html (MAML, ICML 2017)
- https://github.com/cbfinn/maml (reference implementation)
- https://bair.berkeley.edu/blog/2017/07/18/learning-to-learn/ (BAIR blog companion)

## The paper

"Model-Agnostic Meta-Learning for Fast Adaptation of Deep Networks" — Chelsea Finn, Pieter Abbeel, Sergey Levine. Proceedings of the 34th International Conference on Machine Learning (ICML), August 2017.

The contribution is an algorithm for meta-learning that is "model-agnostic" — compatible with any model trained with gradient descent and applicable across classification, regression, and reinforcement learning. The core trick: train the model parameters such that a small number of gradient steps on a small new task quickly produces strong generalization on that task. Concretely, the meta-objective is the loss after a few inner-loop SGD steps, optimized by gradient-through-gradient on the outer loop.

At publication time MAML achieved state-of-the-art on two few-shot image classification benchmarks (Omniglot and miniImageNet), competitive results on few-shot regression, and accelerated fine-tuning for policy-gradient RL with neural network policies.

## Why it matters as a framing

MAML defined a generation of meta-learning research and put "learning to learn" back on the map. The pitch is durable even when the algorithm itself has been overtaken by larger pre-training: rather than train one network that solves the task, train an initialization that solves the task fast given a small number of examples. The framing — that few-shot adaptation is a first-class objective, not a downstream nice-to-have — runs straight through to Finn's foundation-model work, where the post-training and few-shot specialization phase is given equal weight to pre-training.

Finn's 2018 dissertation "Learning to Learn with Gradients" expanded MAML into model-based RL, probabilistic meta-learning, and continual / online meta-learning. The ACM 2018 Doctoral Dissertation Award was given for this body of work.

## The relationship to her current Physical Intelligence work

In her own framing of the Pi roadmap, the pretrain-then-fast-adapt pattern from MAML is still the right shape. Pi 0 is the pretrained generalist; Pi*0.6 / RECAP is the few-shot, on-policy specialization step that fits a new task or new embodiment using a small amount of additional data. MAML's spirit survives even as the inner-loop has shifted from gradient steps to in-context demonstrations, RL fine-tuning, and teleoperated corrections.

## Caveat from the field

By 2022-2024 the scaling-pilled wing of the field (LeCun, parts of DeepMind, much of OpenAI) had largely concluded that big pre-training plus prompting beats explicit meta-learning for most domains. Finn does not concede this for robotics — her position is that the data regime in robotics is small enough that fast-adaptation methods still pay rent. This is one of her sharper points of productive conflict with the "scale is all you need" camp.
