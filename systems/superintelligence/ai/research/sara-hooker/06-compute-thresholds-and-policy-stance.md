# Compute Thresholds and the Policy Stance

Source documents:

- https://arxiv.org/abs/2407.05694 — "On the Limitations of Compute Thresholds as a Governance Strategy" (Hooker, July 8, 2024)
- https://huggingface.co/papers/2407.05694
- https://cyberscoop.com/radio/sara-hooker-vp-for-research-at-cohere-sits-down-with-host-elias-groll-to-discuss-whether-compute-thresholds-can-serve-as-an-effective-ai-governance-tool…
- https://podcasts.apple.com/us/podcast/sara-hooker-why-us-ai-act-compute-thresholds-are-misguided/id1510472996?i=1000662683676 — MLST appearance (July 2024)

## Paper

"On the Limitations of Compute Thresholds as a Governance Strategy." Sole-authored. Submitted July 8, 2024 to arXiv (2407.05694). Published while she was still VP of Research at Cohere.

### Two driving questions

1. Is FLOP (floating-point operations) a meaningful metric to estimate the risk of an AI model?
2. Are hard-coded compute thresholds (such as the 10^26 FLOP threshold in the original Biden Executive Order on AI Safety, or the 10^25 FLOP threshold in the EU AI Act) effective at mitigating that risk?

### Conclusion

Both U.S. and EU compute thresholds, as currently implemented, are short-sighted and likely to fail to mitigate the risks they are supposed to govern. FLOP count is a poor proxy for capability, harm potential, or societal impact. A model trained more cheaply on better data can be more dangerous than a model trained with ten times the compute on worse data. Governance by FLOPs locks in the existing distribution of compute access and creates a regulatory advantage for whoever already has compute.

### Why this paper is consistent with the broader stance

This is the Hardware Lottery thesis applied to policy. If hardware availability determines which research wins, then governance that uses hardware-usage as its primary instrument will:

1. Calcify the lottery winners as the regulated "frontier" actors.
2. Push everyone else into a regulatory shadow where they are simultaneously less powerful and less governable.
3. Misclassify risk because risk does not actually correlate cleanly with FLOP count.

## Public delivery

- **MLST podcast, July 2024**: "Sara Hooker — Why US AI Act Compute Thresholds Are Misguided." This is the long-form public delivery of the paper. She walks through why FLOPs is the wrong instrument and what better instruments might look like.
- **CyberScoop / Radio**: shorter mainstream-policy framing.

## Where the policy stance lives in 2025–2026

After leaving Cohere she has stayed on the compute-equity argument, but has shifted register from "regulators should not use FLOPs" to "the industry assumption that scaling produces more capable models is itself wrong, so a FLOP-based governance regime is governing the wrong variable." The Adaption Labs thesis is partly a falsification argument against the implicit theory of capability that compute thresholds embed.
