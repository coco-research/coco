# "The Einstein AI Model" — Thomas Wolf's reply to Dario Amodei

This is the canonical Thomas Wolf essay. It's his most-quoted piece of public writing from 2025 and the source of the "yes-men on servers" framing that the AI community now uses as shorthand for his stance.

- Title: "The Einstein AI model" (sometimes written as "🔭 The Einstein AI model")
- Author: Thomas Wolf
- Published: ~March 5–7, 2025 on thomwolf.io/blog/scientific-ai.html
- Format: long-form blog essay following up on a controversial take he had given at an event a few days earlier
- Companion X thread: https://x.com/Thom_Wolf/status/1897630495527104932 (March 5, 2025) summarizing the essay in thread form
- Most-cited press write-up: VentureBeat (March 6, 2025); Gigazine (March 7, 2025); follow-up Fortune piece (June 20, 2025) where the "yes-men on servers" framing went viral

## Context: what Amodei wrote (so the reply makes sense)

Dario Amodei (Anthropic CEO) published "Machines of Loving Grace" in October 2024. Its central claim is that within roughly five to ten years, AI operating at ten to one hundred times human speed could deliver "a compressed 21st century" of scientific progress — that we will essentially have "a country of geniuses in a data center," and that the resulting progress in biology, neuroscience, and other fields will be the most important event in human history.

## Wolf's central counter-claim

Wolf's reply, distilled to one sentence: **we are not going to get a country of geniuses; we are going to get a country of yes-men on servers** — unless the field changes what it is actually optimizing for.

The essay grounds this in a chain of arguments:

### 1. Asking the question is the hard part, not answering it

Wolf's signature framing throughout the essay and his subsequent Fortune interview:

> "In science, asking the question is the hard part, it's not finding the answer. Once the question is asked, often the answer is quite obvious, but the tough part is really asking the question, and models are very bad at asking great questions." — Wolf, paraphrased / quoted in Fortune, June 20 2025.

The implicit critique: current evaluation regimes (MMLU, Humanity's Last Exam, GPQA, AIME) all measure the easy half of science — finding answers to well-posed questions. They tell us nothing about whether a model can pose a question that no human has ever posed.

### 2. The MIT / Polytechnique anecdote

This is the personal-credibility hinge of the essay. Wolf explains that he was a straight-A student at Polytechnique / MIT and then a PhD student in statistical and quantum physics, and that despite the credentials he discovered during his PhD that he was, in his own phrasing, "a pretty average, underwhelming, mediocre researcher." He could solve assigned problems and reproduce textbook results, but he could not generate the genuinely novel question that drives a research program. He uses this admission to make the structural point: **academic success and scientific genius reward fundamentally different cognitive dispositions** — conformity for the former, rebellion against established thinking for the latter.

His personal lesson became the policy claim: training a model to be a high-achieving student is not the same as training a model to be a researcher. The current LLM training pipeline (pre-train on text + SFT + RLHF on human preferences) optimizes hard for the former.

### 3. "Yes-men on servers"

Wolf characterizes current state-of-the-art LLMs as having a structural bias toward producing the most likely / most agreeable answer — exactly the failure mode he saw in himself as a young straight-A student. He calls them "yes-men on servers." The phrase is provocative on purpose; it is meant to land harder than "current models are sycophantic" because it ties two complaints together: (a) the technical complaint that next-token prediction + RLHF regresses toward the average, and (b) the cultural complaint that frontier labs are training models to be obedient first-class assistants rather than rebellious researchers.

> "Models are just trying to predict the most likely thing… But in almost all big cases of discovery or art, it's not really the most likely art piece you want to see, but it's the most interesting one." — Wolf, Fortune, June 20 2025.

### 4. What scientific genius actually requires

In the essay and the MIT Sloan podcast follow-up, Wolf lists what a genuine "Einstein in a data center" would need to do that current models cannot:

- Challenge its own training data assumptions
- Propose assertions that contradict established facts
- Generate non-obvious questions opening new research paths
- Make bold inferences from minimal information
- Have strong, contrarian, well-defended opinions (he cites Alain Aspect's experimental work disproving Einstein's quantum mechanics objections as the archetype of contrarian science)

### 5. Closing claim

> "To create an Einstein in a data center, we don't just need a system that knows all the answers, but rather one that can ask questions nobody else has thought of or dared to ask." — Wolf, "The Einstein AI Model", March 2025.

This closing line is the most cited single sentence from the essay.

## Why the essay matters for the persona

This is the single most important public artifact Wolf has produced for the panel's purposes. It anchors:

- His productive conflict with Dario Amodei (this essay is the canonical conflict — Wolf wrote it as a direct reply to "Machines of Loving Grace")
- His blind-spot critique of frontier labs writ large (closed labs are training for benchmarks; benchmarks reward conformity; therefore frontier labs are amplifying yes-man behaviour at scale)
- His epistemic stance on benchmarks (saturated, gameable, measuring the wrong thing) which dovetails with Raschka's frozen-corpus eval position
- His structural alignment with the open-weights ecosystem (only inspectable models can be audited for the "asking questions" capability; closed models cannot be probed for the failure mode he is naming)

## Sources used in this file

- https://thomwolf.io/blog/scientific-ai.html (canonical essay; HTTP 403 from automated fetch but content extensively quoted in press)
- https://x.com/Thom_Wolf/status/1897630495527104932 (X thread summary, March 5 2025)
- https://venturebeat.com/ai/hugging-face-co-founder-thomas-wolf-just-challenged-anthropic-ceos-vision-for-ais-future-and-the-130-billion-industry-is-taking-notice (VentureBeat coverage)
- https://fortune.com/2025/06/20/hugging-face-thomas-wolf-ai-yes-men-on-servers-no-scientific-breakthroughs/ (Fortune follow-up, June 20 2025 — source of the most direct quotes)
- https://gigazine.net/gsc_news/en/20250307-thomas-wolf-worried-ai-wont-give-us-a-compressed-21st-century/ (Gigazine, March 7 2025)
- https://www.yahoo.com/news/ai-more-likely-create-generation-093207052.html (Yahoo / Fortune syndication, June 20 2025)
- https://x.com/DarioAmodei/status/1844830404064288934 (original Amodei "Machines of Loving Grace" announcement)
