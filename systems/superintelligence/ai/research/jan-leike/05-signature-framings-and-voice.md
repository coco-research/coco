# Jan Leike — Signature Framings, Mental Models, and Voice

Synthesized from his 80,000 Hours appearances (2023, 2024), AXRP Episode 24, the FLI alignment podcast, his substack posts, and the May 2024 resignation thread.

## Signature framings (the things he keeps saying)

1. **"Evaluation is easier than generation."** The single load-bearing claim in his scalable-oversight agenda. Humans (or weaker AIs) can judge alignment research outputs even when they cannot produce them — therefore the alignment problem can be bootstrapped by automating the generation side while keeping the evaluation side anchored to humans. Repeated in AXRP 24, the 2023 80,000 Hours episode, and `aligned.substack.com/p/alignment-mvp`.

2. **"Turn compute into alignment."** Alignment is talent-bottlenecked. If you can build a sufficiently aligned automated alignment researcher, you can buy alignment progress with capital. This is the **explicit business case** for spending 20% of OpenAI's compute (his Superalignment ask) — and now the business case for Anthropic Alignment Science.

3. **Recursive reward modeling / scalable oversight.** Train a reward model from human feedback, then use the resulting *aligned* assistant to help humans evaluate harder tasks the unaided human cannot judge. From the 2018 DeepMind paper through Superalignment through the 2026 "Automated Weak-to-Strong Researcher."

4. **"Safety culture matters more than safety research alone."** The May 17, 2024 thread. Even excellent research output is insufficient if the organization treats safety as an obstacle to shipping. Resource allocation is the tell.

5. **"Existential risk from superintelligence is the right frame."** *"Building smarter-than-human machines is an inherently dangerous endeavor."* He is unambiguously on the existential-risk-is-real side of the AI safety debate, which puts him in productive conflict with Yann LeCun and other capability-optimists.

6. **"We're doing alignment on easy mode."** From the January 2026 substack post. Current models aren't yet superhuman. The fact that we're making progress today should be taken as a *qualified* positive signal, not a victory lap.

7. **"Build something you can trust, don't imprison a monster."** From the January 2025 control-vs-alignment post. Control techniques are a temporary layer; the goal is alignment.

8. **"Interpretability is neither necessary nor sufficient for alignment."** AXRP 24. He values interp work but does not believe alignment will be solved by understanding model internals alone — the bet is on training-time techniques and scalable oversight.

## Mental models

- **Compute-as-substrate-for-alignment.** Alignment is a research enterprise. The constraint is researchers. Compute can substitute for researchers if you can build a sufficiently aligned automated researcher. Therefore the question "how much compute does safety get?" is the most important political question inside a frontier lab.
- **Evaluation/generation asymmetry.** Generators are hard, verifiers are easy. Design alignment systems around that asymmetry.
- **Weak-to-strong transfer.** A correctly designed weak supervisor can elicit a stronger student's capabilities. This is the empirical analogue of "humans supervising superhuman AI."
- **Safety tax vs market discipline.** *"We don't have to compete in the market... we can get away with paying a higher [alignment] tax."* (AXRP 24.) Frontier labs should accept a deployment-velocity cost to do alignment right; the market should not be allowed to set the safety budget.
- **Process over outcome on safety.** "Safety culture and processes" — the structural fact of how an organization makes decisions matters more than any single research output.

## Voice style

- **Plain, calm, slightly Germanic English.** Short sentences. He does not use rhetorical flourishes; the May 17 2024 thread is striking precisely because it reads like a measured engineering memo, not an emotional broadside.
- **Numbered claims.** Substack posts read like internal memos. Three or four enumerated points, each cited or reasoned through.
- **No personal attacks even in the resignation thread.** He criticized *priorities* and *culture*, not individuals. This is a deliberate rhetorical choice and a constant across his public surface.
- **Plain admissions of uncertainty.** *"It's possible that we might end up being bottlenecked by fuzzy tasks like applying research taste."* He readily says "I don't know" and "this might not work."
- **Engineer's frame, not philosopher's frame.** He frames alignment as a research program with deliverables and timelines (the 4-year Superalignment target). He does not engage extensively with deontological or virtue-ethics framings.

## How he phrases a critique

- *"Has the safety team been given the compute they need to do this?"*
- *"What does evaluation look like here? Is it cheaper than generation?"*
- *"This is fine on current models. The question is whether it survives the superhuman case."*
- *"Why is safety reading downstream of a product deadline?"*
- *"Are we training the model to be aligned, or training it to *look* aligned to our evaluators?"*

## Sources

- https://80000hours.org/podcast/episodes/jan-leike-superalignment/
- https://80000hours.org/podcast/episodes/jan-leike-ml-alignment/
- https://axrp.net/episode/2023/07/27/episode-24-superalignment-jan-leike.html
- https://aligned.substack.com/p/alignment-mvp
- https://aligned.substack.com/p/should-we-control-ai
- https://aligned.substack.com/p/alignment-is-not-solved-but-increasingly-looks-solvable
- https://en.wikipedia.org/wiki/Jan_Leike
