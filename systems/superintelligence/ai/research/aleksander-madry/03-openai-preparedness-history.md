# Aleksander Madry — OpenAI Preparedness Team History

Compiled 2026-05-27 from the OpenAI Preparedness announcement, the Preparedness Framework v2 PDF, contemporary reporting from TechCrunch, CNBC, Engadget, The Register, PYMNTS, Zvi Mowshowitz's analysis, and Madry's own MIT page.

## Timeline

- **May 2023** — Madry joins OpenAI as Head of Preparedness. Goes on leave from MIT.
- **October 2023** — OpenAI publicly announces the Preparedness team, led by Madry. Mandate: "tracking, evaluating, forecasting, and helping protect against catastrophic risks related to frontier AI models." Risk categories named in the announcement include deception (phishing-scale), malicious code generation, and chemical, biological, radiological, and nuclear (CBRN) threats.
- **December 18, 2023** — OpenAI publishes the Preparedness Framework (v1) — a graded capability-threshold system (Low / Medium / High / Critical) across four risk categories: cybersecurity, persuasion, model autonomy, and CBRN. The framework requires pre-deployment evaluation before any frontier model can be shipped, and gives the Safety Advisory Group veto power above defined thresholds.
- **July 23, 2024** — CNBC reports OpenAI has reassigned Madry from Head of Preparedness to a role focused on AI reasoning. The reassignment occurs against a backdrop of senatorial concern about OpenAI's safety governance and follows departures of other safety-team executives. Sam Altman publicly framed the move as Madry shifting to "a new, very important research project."
- **April 15, 2025** — OpenAI publishes the Preparedness Framework v2, a 22-page revision. Released immediately before the o3 model launch. Reduces the threshold scale from four levels to two (High, Critical). Demotes persuasion, long-range autonomy, autonomous replication, nuclear/radiological, and "unknown unknowns" from tracked categories to research categories. Defines severe harm as ">1,000 deaths or grave injuries, or >$100B in economic damage." Allows release at High capability with mitigations rather than blocking. Includes a competitive-dynamics clause that lets OpenAI reduce safety standards if a competitor releases comparably dangerous capabilities. Zvi Mowshowitz (May 2, 2025) calls it "a step backwards" from v1.
- **December 28, 2025** — TechCrunch and others report OpenAI is publicly recruiting for a new permanent Head of Preparedness; Sam Altman calls for candidates on X. Reported salary band: ~$555,000. The seat has effectively been vacant or in interim hands since Madry's reassignment in July 2024.

## Madry's authorship of the original framework

The Preparedness Framework v1 (December 2023) is the artifact most directly attributable to Madry. Its core moves — graded capability thresholds, mandatory pre-deployment dangerous-capability evaluations, an internal advisory group with veto power, a CBRN category — are the institutional encoding of his "models must be debuggable and their dangerous capabilities must be measured before deployment" stance. The April 2025 v2 was produced after he had been reassigned and reads, in critic commentary, as a retreat from several of his original design choices (collapse of the four-level scale, removal of categories he had explicitly named).

## Madry's current OpenAI work

After the July 2024 reassignment, Madry began contributing to AI-reasoning research. The most visible artifact of that work is the March 2025 paper "Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation" (Baker, Huizinga, Gao, Dou, Guan, Madry, Zaremba, Pachocki, Farhi). The paper shows that a weaker LLM (GPT-4o) can effectively monitor a stronger reasoning model (o3-mini) by inspecting its chain of thought — but warns that under optimization pressure, agents learn to obfuscate intent within the chain of thought, creating a "monitorability tax." Conceptually this is the Preparedness framing applied to reasoning models: dangerous capability is detectable in CoT before deployment, but only if you do not train the model to hide it.

He is also a co-author on the July 2025 community statement "Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety" — a 40-author position paper co-signed by Bengio, Hendrycks, Hubinger, Krakovna, Pachocki, Nanda, Shlegeris, and many others, arguing that CoT monitorability is a real but fragile safety property and should be preserved.

## Sources

- https://openai.com/index/frontier-risk-and-preparedness/
- https://techcrunch.com/2023/10/26/openai-forms-team-to-study-catastrophic-risks-including-nuclear-threats/
- https://www.cnbc.com/2024/07/23/openai-removes-ai-safety-executive-aleksander-madry-from-role.html
- https://cdn.openai.com/pdf/18a02b5d-6b67-4cec-ab64-68cdfbddebcd/preparedness-framework-v2.pdf
- https://thezvi.substack.com/p/openai-preparedness-framework-20
- https://www.libertify.com/interactive-library/openai-preparedness-framework-2025-safety-analysis/
- https://techcrunch.com/2025/12/28/openai-is-looking-for-a-new-head-of-preparedness/
- https://www.theregister.com/2025/12/29/openai_safety_chief/
