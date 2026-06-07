# Eliciting Latent Knowledge (ELK) and the Alignment Research Center

Primary sources:
- ELK Report (ARC, Dec 2021): https://www.alignment.org/blog/arcs-first-technical-report-eliciting-latent-knowledge/
- Alignment Forum mirror: https://www.alignmentforum.org/posts/qHCDysDnvhteW7kRd/arc-s-first-technical-report-eliciting-latent-knowledge
- AI Alignment Forum distillation: https://www.alignmentforum.org/posts/rxoBY9CMkqDsHt25t/eliciting-latent-knowledge-elk-distillation-summary
- Christiano's older blog post: https://ai-alignment.com/eliciting-latent-knowledge-f977478608fc

## ARC — founding

- **Founder:** Paul Christiano.
- **Year:** 2021 (immediately after his departure from OpenAI).
- **Mission, per ARC:** A nonprofit research organization working to align future machine learning systems with human interests, with a particular focus on theoretical research.
- **Notable spin-off:** ARC Evals → renamed **METR (Model Evaluation and Threat Research)**. METR became the primary third-party evaluator for OpenAI and Anthropic frontier-model pre-release testing throughout 2023–2026.

## ELK — the framing in Christiano's own words

ELK ("Eliciting Latent Knowledge") was ARC's first technical report (Christiano and Mark Xu, December 2021). The core question Christiano poses:

> "Suppose a prediction model knows something — for example, that the camera was tampered with — but that information is not visible on camera. How do we train this model to *report* its latent knowledge to us, when our only training signal is what humans observing the same camera feed would say?"

This is the canonical formulation. The "SmartVault" thought experiment is the worked example: a vault guarded by an AI; humans watch a camera; the AI's job is to keep the diamond safe; a sufficiently smart AI may know the diamond was stolen even when the human-visible video shows nothing wrong.

## "Human simulator" vs "direct translator"

ELK draws the failure mode crisply. Two functions can both achieve low loss on the training signal:

- **Human simulator** — the AI learns to predict what a human observer would say given the same inputs. This is *what we trained for* but not *what we wanted*. It fails on exactly the cases where the AI knows more than the human can see.
- **Direct translator** — the AI faithfully reports its own latent representation of the world in human terms. This is what we want.

The ELK challenge is to design a training procedure that systematically prefers the direct translator over the human simulator. ARC's 2021 report frames this as **the central open problem of alignment** and offers a prize competition.

## Prize competition

ARC offered prizes of $5K–$20K for proposed ELK algorithms in January–February 2022. They received **197 proposals** and awarded **32 prizes**. The exercise was an explicit attempt to recruit the broader field into the framing.

## Why ELK is "the central open problem"

In Christiano's worldview, RLHF, debate, iterated amplification, and constitutional AI are *all* downstream of ELK. Each method assumes you have some way to elicit what the model knows; if that elicitation is unreliable, every downstream technique inherits the failure mode. This is the reason he treats ELK as load-bearing.

## Why this matters for the persona

The ELK report and the ARC founding are what distinguish Christiano from a generic "OpenAI alumnus who worries about AI." They are his proof-of-work as a theoretician. When the persona is asked "what is the open problem?" the answer should be ELK, not RLHF, not interpretability, not capability evals — those are downstream.
