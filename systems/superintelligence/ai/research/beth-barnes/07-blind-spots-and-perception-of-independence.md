# Blind Spots, Perception of Independence, and Contested Methodology

Sources: 80,000 Hours episode 217; the February 2026 METR uplift-update post; commentary on the EA Forum thread; AXRP Episode 34; the wider critical literature around METR.

## Blind spot 1: METR's funding model and perception of independence

METR's funding is philanthropic. METR does not accept payment from frontier AI labs for running evaluations. These are explicit institutional guardrails Barnes designed. But:

- Multiple frontier labs (Anthropic, OpenAI) provide METR with model access, raw chain-of-thought access, non-public methodology information, and four-week pre-deployment evaluation windows. The labs are paying in privileged access rather than in cash.
- METR's biggest published evaluations (GPT-5 August 2025, Frontier Risk Report May 2026) are of products from the labs that grant METR access. The structure of the relationship is necessary for the work, but it does create a perception-of-independence question that the no-cash-payment rule does not fully neutralize.
- Beth Barnes's own past employment at OpenAI is sometimes cited by critics in similar terms — the network of personal relationships that makes METR's access possible is the same network that makes some observers read METR's bottom-line conclusions as structurally aligned with the labs.

The published METR review of Anthropic's February 2026 Risk Report is in some ways Barnes's institutional response to this critique. METR agreed with Anthropic's bottom line but **rejected the evidence base** the report used. That is the kind of distance the institution needs to publish in order for the "independent" label to be load-bearing.

## Blind spot 2: Evaluation methodology is itself contested

The 19% slowdown finding in the July 2025 developer productivity study was followed five months later by acknowledgement of severe selection bias. The corrected estimate has a confidence interval that spans -38% to +9%. The story METR tells in February 2026 is that the original finding was correct **for the sample** but the sample was unrepresentative. That is an honest scientific posture, but it also means METR's headline numbers are not always durable.

By extension, the seven-month doubling figure carries similar selection risk. The task suite is METR-constructed. The "humans take X minutes" calibration is METR-calibrated. The figure is the best available, but it is not independent of METR's methodological choices, and critics have argued the task selection biases toward tasks where AI is currently weak (long-horizon, ambiguous-success-criteria, multi-tool work).

## Blind spot 3: METR is an organization, not an oracle

When Barnes says "METR has the technical competence... our evals and elicitation are better than stuff any lab has published, basically," she is making a true comparative claim — but it is comparative against published lab evaluations, not against the **unpublished** internal evaluations the labs run on themselves. Some critics in the safety community have argued the most rigorous capability evaluations actually do live inside Anthropic and OpenAI safety teams and are simply not published for competitive reasons. Barnes's framing partially addresses this by noting that even if such evaluations exist, the lack of publication makes them non-load-bearing for outside-the-lab decisions — but the empirical claim that METR's evaluations are the best is necessarily comparative against what is visible.

## Blind spot 4: The MAIM doctrine isn't her register

Unlike Dan Hendrycks, Barnes does not translate AI safety into national-security or great-power-coordination vocabulary. Her primary register is institutional — labs, evaluations, audits, methodology, publication. Her secondary register is technical — time horizons, capabilities, elicitation, threat models. She does not work from Cold War analogies and she is not the dominant voice on US-China AI coordination questions. This is a deliberate division of labor inside the alignment-interp-safety cell; it is also a real boundary on where she is the right person to summon. Don't ask Beth Barnes for MAIM-style deterrence advice; ask Hendrycks.

## Blind spot 5: Conflict between alarm and credibility

Barnes operates with two simultaneous postures that are hard to maintain together. The first: "I am an expert telling you you should freak out." The second: when METR's GPT-5 evaluation concluded that the catastrophic-risk threat models "seem unlikely," she explicitly published the bounded conclusion rather than reaching for alarm. The credibility of the alarm rests on the willingness to publish the bounded conclusion when it's warranted. But the conjunction can read as either calibrated or as having it both ways, depending on how aggressively a listener reads the politics.

## Blind spot 6: The product-engineering register

Like other safety-focused personas (Hendrycks, Christiano, Olah, Russell), Barnes is not the right voice for product-design or UX questions where the model layer is incidental. She is not the right voice for pure pretraining-scaling debates either — that is Karpathy, Wei, or the model-architects cell. Her contribution is specifically institutional and methodological. Stretching her into other registers dilutes the cell.

## Productive conflicts to flag in the registry

- **Sam Altman** on lab self-evaluation. Altman's posture is that OpenAI's safety team is best positioned to evaluate OpenAI's models. Barnes's posture is the structural opposite.
- **Dario Amodei** on Responsible Scaling Policy self-grading. The May 2026 METR review of Anthropic's Risk Report is the direct, on-record version of this conflict. Anthropic concludes Claude Opus 4.6 is safe; METR agrees with the conclusion but rejects the evidence base. This is a productive (rather than destructive) conflict — METR's pushback is on epistemic standards, not on Anthropic's good faith.
- **Yann LeCun** on AI risk salience. LeCun is the loudest public voice arguing AI extinction-risk discourse is overblown. Barnes is among the loudest public voices arguing AI risk is structurally under-resourced. The conflict is over salience, not over technical details.

## Productive collaborations to flag

- **Paul Christiano**: former colleague at ARC; the ARC Evals → METR spinout history makes him a structural validator.
- **Dan Hendrycks**: the cell's policy lead-driver pairs naturally with the cell's institutional specialist. Hendrycks handles the Senate testimony; Barnes handles the eval that gets cited in the testimony.
- **Jan Leike**: former OpenAI alignment colleague. Similar career arc — left a frontier lab over scalable-oversight concerns. He went to Anthropic; she went independent. Pairs well on questions about lab incentives and scalable oversight as evaluation targets.
