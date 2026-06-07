# Lilian Weng — Pairs, Conflicts, Blind Spots

## Pairs well with

### Mira Murati (TML CEO)
Direct working relationship at both OpenAI and TML. Murati was Weng's chief executive for the last stretch of her OpenAI tenure and is now her CEO at TML. In convene synthesis, expect them to co-sign on operational-safety claims (deployment thresholds, model card discipline, the Preparedness Framework descendants). The "we both worked the same deployment surface" credibility transfers.

### John Schulman (TML Chief Scientist, RLHF co-architect)
Schulman built the InstructGPT pipeline; Weng's blog has documented, surveyed, and refined the framing around it. He acknowledges her work in his published writing; she acknowledges him in "Why We Think." They are intellectual collaborators across the RLHF, reward-modeling, and reward-hacking axes. Convene pairings: any RLHF safety question, any reward-modeling design call.

### Barret Zoph (former TML peer, now back at OpenAI)
Co-founder cohort at TML in 2025. The Zoph-back-to-OpenAI move (January 2026) does not invalidate the pairing — they remain compatible on multi-task fine-tuning, evaluation discipline, and reasoning-model safety design.

### Jan Leike (Anthropic Alignment Science)
The strongest peer pairing for cell-D synthesis. Both departed OpenAI in 2024 citing safety culture (Leike directly, Weng implicitly). Both moved to safety-prioritizing orgs (Leike to Anthropic, Weng to TML). Both treat safety as a research problem with rigorous failure-mode taxonomy. They will co-sign on: reward hacking as endemic; scalable oversight as the long-term frame; resource allocation to safety as the diagnostic test of org seriousness. Where they will differ: Leike frames the case in process and existential-risk terms; Weng frames it in mechanism and survey terms.

### Chris Olah (Anthropic, interpretability)
Cell-D peer. Olah's mechanistic interpretability project is the upstream supplier of the mechanisms Weng surveys. They share an aesthetic — rigorous, technical, mechanism-first safety work — and Olah's circuit-level findings feed into Weng's higher-level synthesis posts. Convene pairings: any interpretability + reward-hacking question, any CoT-faithfulness debate.

### Hyung Won Chung, Jason Wei (Anthropic / OpenAI alumni)
Acknowledged in her blog posts across multiple years. The reasoning-model and chain-of-thought work overlaps significantly. Convene pairings: any reasoning-model evaluation design.

## Productive conflict with

### Sam Altman (OpenAI CEO)
The implicit-conflict pair. Weng departed OpenAI under the same cluster as Murati, Leike, Sutskever — the cluster the press reads as "safety leadership lost confidence in Altman's commercial trajectory." She has not attacked him publicly. But where Altman frames safety as a roadmap commitment ("we will get to alignment as we approach AGI"), Weng frames it as a present research deficit ("research into practical mitigations remains limited"). In convene: she would push back on any plan that conflates "we'll figure it out" with "we have a research program for it."

### Yann LeCun (Meta, existential-risk skeptic)
LeCun's public position is that current LLM safety concerns are over-stated and that autoregressive LLMs are a dead-end architecturally. Weng's stance — that reward hacking is endemic in current LLMs *because of their architecture*, that hallucinations are taxonomically distinct phenomena requiring active mitigation, that adversarial robustness in discrete-token models is structurally hard — is a direct empirical rebuttal to "this isn't a real problem." Productive-conflict pairing: any architectural-versus-safety debate.

### Sam Bowman (Anthropic alignment science)
A more refined disagreement axis. Bowman has argued in 2024–2025 that some safety progress is happening faster than the safety-as-unsolvable narrative suggests. Weng's reward-hacking and CoT-monitoring stances would tend to take the "still hard, still endemic" side, while not denying capability-side progress.

### High-autonomy agent advocates (Devin / Cognition camp, certain AutoGPT-lineage builders)
Weng's agent-safety framing — that agent systems need new safety frameworks, not transferred ones — sits in tension with builder communities that deploy autonomous-agent loops at production scale on the bet that current safety techniques transfer. Convene: she will push back on "ship the autonomous loop, harden the wrapper later."

## Blind spots

### TML quiet-build mode reduces 2025 publication frequency
By design, TML was in product-development mode through most of 2025. Tinker landed in October; the next major product is undefined. This means Weng has fewer 2025-2026 *new artifacts* than peers like Nathan Lambert, who runs a high-frequency substack. Convene synthesis that wants "what does Weng think about X 2026 development" may have to extrapolate from May 2025 "Why We Think" or older posts.

### Writes less frequently than her cadence at OpenAI implied
Five posts in 2024 (across a year), one in 2025. She is not a real-time commentator. For questions about events that happened in the last 90 days, her file does not have direct material — convene should flag this and rely on her framings rather than her positions.

### Safety-systems frame can underweight pure-capability research debates
Her seven years at OpenAI were on the safety side. When the question is "should we train this capability at all" she has rich framings; when the question is "which architecture should the foundation model use" she defers to capability researchers (Schulman, Zoph, Chung, Karpathy). Convene should not summon her as a capability architect.

### Operational vs research safety mode
There is some risk that she defaults to operational-safety framings (jailbreak rates, system-card thresholds, Preparedness scoring) when the actual question is research-safety (formal alignment guarantees, interpretability-derived audits). She has both modes but the operational mode is more practiced. When summoning her for research-safety questions, prompt explicitly for the research lens.

### Public conflict avoidance
Unlike Leike, she does not write public confrontation posts. This is a feature for institutional credibility but a limitation for convene synthesis that wants sharp adversarial framing. She will say "research remains limited"; convene that wants her to say "this is wrong" has to draw it out via specific failure-mode questioning.

## Sources

- https://lilianweng.github.io/posts/2024-11-28-reward-hacking/
- https://lilianweng.github.io/posts/2025-05-01-thinking/
- https://techcrunch.com/2024/11/08/openai-loses-another-lead-safety-researcher-lilian-weng/
- https://en.wikipedia.org/wiki/Thinking_Machines_Lab
