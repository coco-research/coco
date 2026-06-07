# The Seven-Month Rule and the Long-Task-Horizon Paper

Source: METR, "Measuring AI ability to complete long tasks." Blog post at `https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/`. arXiv preprint at `https://arxiv.org/abs/2503.14499` (submitted March 18, 2025; last revised February 25, 2026). AI Digest's expanded write-up at `https://theaidigest.org/time-horizons`.

## The headline result

The length of tasks AI agents can complete autonomously with 50% reliability has been doubling approximately every seven months for six years. The relevant operational metric is the **50%-task-completion time horizon** — the duration of work, measured by how long a human expert needs to complete the task, that a frontier model finishes with a 50% success rate.

As of the March 2025 publication, Claude 3.7 Sonnet sat at roughly 50 minutes on this metric. By the time the 80,000 Hours episode aired in June 2025, the round number being cited was "AI models today have a 50% chance of successfully completing a task that would take an expert human an hour. Seven months ago, that number was roughly 30 minutes — and seven months before that, 15 minutes."

GPT-5 (per the METR GPT-5 evaluation, August 2025) reached approximately 2h17m (65m to 4h25m, 95% confidence interval), up from o3 at 1h30m.

## The methodology

- METR researchers timed skilled humans completing a suite of 66 newly constructed software-engineering and reasoning tasks, plus existing benchmarks (HCAST, RE-Bench, SWE-Bench, and Software Atomic Actions).
- Frontier models were then evaluated on the same task suite under realistic autonomous-agent conditions.
- The relationship between human task duration and model success rate is strongly inverse and monotonic: current models complete tasks under four minutes at near 100% reliability, but fall below 10% reliability above roughly four hours of human time.
- The metric is calibrated against human time, not against abstract benchmark scores, which is the central methodological move.

## Authorship

The paper has roughly 25 authors. Thomas Kwa is first author; Ben West and Joel Becker are central authors. Beth Barnes is on the author list. The first-authorship choice matters for sociology of the field — METR explicitly avoids putting the CEO's name first on technical papers.

## The acceleration update

The paper's central headline is seven months, but it carries a second figure: over the more recent 2024 to 2025 window, the doubling rate has been closer to four months. The robustness check against SWE-Bench specifically shows a doubling time below three months. Beth Barnes treats the seven-month figure as the long-run trend baseline and the four-month figure as the recent-acceleration signal.

## Why this is "the most important graph in AI right now"

Both the EA Forum coverage and the 80,000 Hours podcast titling explicitly frame this as the single most actionable AI-forecasting artifact. The framing is: capability has been measured the wrong way for years (saturating benchmarks, multiple-choice questions, contest-style problems). The right measurement is autonomous-task duration. Once you measure that way, the curve is exponential, the doubling rate is short, and the extrapolation puts agents completing weeks-of-human-work tasks within a decade.

## Direct quote (80,000 Hours, June 2, 2025)

"Over that time there's a pretty good fit to a doubling of something like every six months."

She notes the range of estimates spans "basically between three months and one year" depending on which subset of tasks you select.

## On timeline urgency (same episode)

"It seems hard to rule out even shorter [timelines]. Is there 1% chance of six, nine months? Yeah, that seems pretty plausible."

"The experts are not on top of this. And to the extent that I am an expert, I am an expert telling you you should freak out."

## Strategic implication Barnes draws

The seven-month rule is the operational backbone of her dangerous-capability forecasting. When METR's GPT-5 report concludes that GPT-5 "seems unlikely" to pose catastrophic risk via self-improvement, the reasoning is anchored on the gap between GPT-5's measured 2h17m time horizon and the estimated 40-hour (one work-week) time horizon needed for a 10x researcher acceleration threshold. The seven-month doubling rate then tells you when to expect that 40-hour threshold to be reached — approximately three doublings from a one-hour baseline, which is two years at the seven-month rate or roughly one year at the four-month rate.

This is the central reason Barnes argues "the world is not on track to keep risk from AI to an acceptable level" — the forecast horizon for catastrophic-capability thresholds is short and the policy response is not commensurate.
