# The Developer Productivity Study and Its Methodological Revision

Sources: METR blog at `https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/` (July 10, 2025); arXiv preprint at `https://arxiv.org/abs/2507.09089`; methodology update at `https://metr.org/blog/2026-02-24-uplift-update/` (February 24, 2026); Sean Goedecke's analysis at `https://www.seangoedecke.com/impact-of-ai-study/`.

## The original study — July 10, 2025

Authors: Joel Becker, Nate Rush, **Beth Barnes**, David Rein. Beth Barnes is a co-author, not the lead, but the study is associated with her institutionally.

**Method**: Randomized controlled trial. 16 experienced open-source developers, mean ~5 years of experience on their own mature repositories (average 22,000+ GitHub stars). 246 real issues from the developers' own codebases. Each issue randomly assigned to "AI tools allowed" or "AI tools disallowed." Tasks averaged two hours each. Developers paid $150/hour.

**Tools allowed**: Cursor Pro with Claude 3.5/3.7 Sonnet — frontier models at the time of the study.

**The headline finding**: When AI tools were allowed, developers took **19% longer** to complete the same caliber of task than when AI was disallowed.

**The perception gap**: Developers forecast AI would speed them up by **24%** before the study. After the study, they reported feeling sped up by **20%**. The objective measurement showed a 19% slowdown. The gap between perceived and measured impact is roughly 40 percentage points.

## Why this matters for the persona

This is the single study most likely to be cited adversarially against any AI productivity claim. It is a textbook METR product: pick the question everyone is shouting about, run the actual experiment, publish the result whether or not it flatters anyone. The finding cuts directly against frontier-lab narratives about AI-assisted coding speedup.

It also frames Barnes's posture: she will run the experiment, she will publish the finding, and she will then **also** publish the methodology revision when the experiment turns out to be biased. The next document does that.

## The methodology revision — February 24, 2026

Authors: METR team. Beth Barnes is co-author.

**Why the revision was necessary**:

- **Participation dropout**: Developers increasingly refused to participate in tasks where AI was disallowed, even at the reduced $50/hour rate of the follow-up study. By 2026 the population of "developers willing to do real work without AI" was structurally biased.
- **Task avoidance**: 30 to 50% of developers reported deliberately excluding tasks where AI provided substantial advantage from the experiment. They were filtering their own work to keep the parts where AI helped least.
- **Measurement degradation**: Concurrent AI-agent usage made traditional time-tracking unreliable — when the developer was orchestrating a parallel agent, "wall-clock time on issue" stopped being a clean measurement.

One participant quote, from the revision blog: "I'm torn. I'd like to help provide updated data on this question but also I really like using AI!"

**The updated study window**: August 2025 onward. 57 developers across 800+ tasks. $50/hour rate.

**Updated headline**: Raw data showed modest speedup compared to 2025's slowdown. METR's estimate is -18% speedup for returning developers (i.e. about an 18% speedup), but with a confidence interval of -38% to +9%. The signal is dominated by selection effects.

**METR's bottom line on this**: "The true speedup could be much higher among the developers and tasks which are selected out of the experiment." In other words, the methodology now captures predominantly reluctant participants and not the modal developer.

**Path forward stated**: Observational data, questionnaires, fixed-task experiments, and developer-level randomization rather than task-level randomization.

## What this tells you about how Beth Barnes operates

She runs the experiment that produces the publishable headline finding, then runs the follow-up that disconfirms part of the headline, then publishes the disconfirmation in equal prominence and identifies the selection-effect failure mode by name. That is the institutional posture that lets her credibly demand the same of frontier labs. METR does not get to demand methodological rigor from Anthropic and Google if METR's own studies do not publish the methodological caveats.

## Why this study sits awkwardly with the seven-month rule

The seven-month rule says AI capability is exploding. The developer productivity study says AI tools are slowing down expert developers. Both are simultaneously true and they are about different things — agent autonomy vs. expert-in-the-loop coding workflows. Barnes is consistent across both findings and uses the dissonance productively: the seven-month rule is about autonomous capability, the developer study is about human-AI collaboration overhead, and conflating them is the conceptual error she works to head off in every interview.
