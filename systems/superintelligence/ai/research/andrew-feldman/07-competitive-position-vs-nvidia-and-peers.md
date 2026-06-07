# Competitive Position — Cerebras vs. NVIDIA, Groq, SambaNova, Tenstorrent, Tesla Dojo

## Sources
- https://futurumgroup.com/insights/cerebras-s-1-teardown-is-the-23b-wafer-scale-ipo-the-end-of-gpu-homogeneity/
- https://www.theregister.com/ai-ml/2026/05/15/cerebras-wafer-scale-ai-bet-delivers-blockbuster-ipo/5240821
- https://www.sdxcentral.com/analysis/cerebras-spins-nvidias-groq-tieup-as-proof-its-waferscale-bet-was-right/
- https://www.hpcwire.com/2023/10/30/cerebras-ceo-andrew-feldman-sounds-off-on-nvidias-roadmap-and-chiplets/
- https://cloudnews.tech/cerebras-vs-nvidia-why-a-giant-chip-can-win-in-inference/
- https://www.jarsy.com/blog/cerebras-vs-nvidia
- https://www.heygotrade.com/en/blog/cerebras-vs-nvidia-wafer-scale-engine-vs-gpu-ai-training/
- https://english.cw.com.tw/article/article.action?id=4792
- https://www.trendingtopics.eu/nvidia-bets-26-billion-on-open-source-ai-to-build-a-new-moat-next-to-cuda/

## The structural opposition: Cerebras (wafer-scale, vertically integrated, inference-first) vs. NVIDIA (chiplet, partner-ecosystem, training-first)

The Cerebras–NVIDIA opposition is the load-bearing competitive frame of Feldman's entire public persona, and it is the reason he and Bryan Catanzaro are the two opposite-pole lead drivers in the AI Super Intelligence Team's `systems-kernels-serving` cell.

Catanzaro's pole:
- The GPU + CUDA + Megatron + NeMo + Nemotron stack is the right substrate.
- Co-design across hardware × kernels × parallelism × precision × architecture × data is the moat.
- Open-model strategy is moat extension — Android played on AI compute.
- 4-bit pre-training (NVFP4) on Blackwell is the precision-regime moat.

Feldman's pole:
- The GPU was the wrong architecture for AI; the industry took a wrong turn.
- Wafer-scale + vertical integration is the moat.
- CUDA is a thin moat in the inference market where switching costs are 10 keystrokes.
- The right precision is irrelevant if your memory hierarchy is the bottleneck.
- Inference is the regime that matters; training is the past decade's question.

The two stances are not symmetrical. Catanzaro's stance is the incumbent's defense of an enormous installed base. Feldman's stance is the challenger's bet that the regime is changing in his favor. The productive conflict between them — when convened on the same problem — yields the right answer faster than either pole alone, because the workload truly does dictate the architecture and the workload mix is changing.

## Competitive position against the inference startup cohort

### Groq (LPU — Language Processing Unit)
- Different architectural bet: deterministic, fully scheduled VLIW-style architecture with on-chip SRAM, but at the chip rather than wafer scale.
- Comparable inference speed claims on small-to-mid models, but Groq has historically struggled with the largest models (405B+) where wafer-scale's bandwidth advantage compounds.
- The May 2025 NVIDIA–Groq partnership announcement was framed by Cerebras as "proof its wafer-scale bet was right" (SDxCentral analysis) — Cerebras's read was that NVIDIA chose to partner with the chip-scale challenger rather than buy or replicate the wafer-scale challenger, conceding that the wafer-scale moat is too expensive to reproduce.
- Feldman's likely framing in any panel: "Groq is the right idea at the wrong scale. You can't beat a memory-bandwidth wall by adding more chips on a board; you have to dissolve the board."

### SambaNova
- Reconfigurable dataflow architecture (RDU); systems sold as appliances; similar enterprise/sovereign-AI go-to-market profile to Cerebras.
- May 2025 Llama 4 Maverick benchmark: 794 TPS vs. Cerebras's 2,522 TPS — same architectural family (dataflow, on-chip memory) but at smaller scale, with significantly worse measured throughput.
- Feldman's likely framing: "Same direction, smaller bet. The wafer is the test of whether you actually believed it."

### Tenstorrent (Jim Keller)
- RISC-V-based AI accelerator family; explicit open-stack ecosystem strategy.
- Lower-end deployment focus to date; not yet a frontier-inference competitor.
- The interesting strategic axis: Tenstorrent's open-IP / open-RISC-V positioning is a different "alternative to NVIDIA" thesis than Cerebras's vertically integrated thesis. The two are not direct competitors at the high end but compete for the "NVIDIA alternative" mindshare.

### Tesla Dojo / Project Dojo
- Custom training silicon for Tesla's autonomy workloads.
- Productive conflict point with Elon Musk: Dojo is the "we'll just build our own purpose-built silicon" alternative pursued by a hyperscaler-scale customer, which is structurally what Feldman warns NVIDIA about. But Dojo's training-first focus and Tesla-internal scope make it a different market than Cerebras's external inference business.
- Feldman's likely framing: "Dojo proves the thesis. Every hyperscaler will eventually have a custom path. The question is whether they buy from us or rebuild from scratch — and how many years they're willing to lose."

### Cloud-vendor TPUs and ASICs
- Google TPU v5/v6: vertically integrated within Google, not externally sold at scale.
- AWS Trainium 2 / Inferentia: AWS-internal; the March 2026 Cerebras–AWS partnership for Bedrock is the strategically interesting countersignal — AWS hedged its own roadmap by buying Cerebras systems for Bedrock deployment.
- Azure Maia, Microsoft custom silicon: similar in-house pattern.
- Feldman's framing in this layer: each hyperscaler wants its own ASIC for cost, but each one also needs a credible external supplier to keep NVIDIA honest on pricing, and Cerebras is now that credible supplier.

## Why Cerebras's inference moat is structurally narrower than NVIDIA's training moat

The honest competitive read — one Feldman acknowledges in private and softens in public:

1. **CUDA developer ecosystem is two decades deep.** Cerebras's software stack is competitive for hosted inference (where the customer interacts via API) but is not yet competitive at the kernel-author / framework-internals level. If the inference market evolves toward more bespoke optimization, NVIDIA's tooling reasserts.

2. **HBM supply and TSMC capacity favor scale buyers.** NVIDIA's Blackwell ramp consumed roughly 60% of TSMC's advanced-packaging capacity in 2024. Cerebras gets the wafers it needs because demand is currently within TSMC's allocation — but a 10× scale-up of Cerebras would run into the same supply ceiling.

3. **Hyperscaler in-house silicon is a converging risk.** Every hyperscaler is building its own AI silicon. Cerebras's strategic window is the 3–5-year arc where NVIDIA pricing power is high enough to justify dual-sourcing and where the hyperscaler in-house silicon is not yet mature. After that window closes, the merchant inference market may shrink.

4. **G42/Gulf concentration risk.** Single-customer revenue concentration of 24%+ at IPO is a structural fragility. Diversifying into Meta, OpenAI, AWS, and enterprise sovereign-AI deployments through 2026 is the explicit countermove, but the concentration is real.

5. **Wafer yield economics are unproven at 10× volume.** Cerebras's redundancy schemes mean wafers with defects are still usable, but the unit economics of wafer-scale production at hundreds of thousands of CS-3 systems per year are not yet stress-tested. NVIDIA's per-die economics scale linearly; Cerebras's per-wafer economics may not.

## Why Cerebras's bet is real, not vanity

The Llama 4 Maverick result (2,522 vs. 1,038 TPS) is reproducible by Artificial Analysis, a neutral third party. The OpenAI $10B+ deal is a customer commitment from the most discerning inference buyer on the planet. The 68% IPO pop is a market vote. None of these prove Feldman is right about the long arc, but together they prove the thesis is no longer speculative — wafer-scale ships, performs, and sells.

## Implications for convene patterns

When convening a `systems-kernels-serving` panel:

- **Pair Feldman with Catanzaro** for the structural architecture debate. Catanzaro defends the GPU stack; Feldman attacks it. The convergence point is usually that the right answer depends on whether the workload is training (Catanzaro wins) or memory-bandwidth-bound inference (Feldman wins).
- **Pair Feldman with Tri Dao / Horace He** for the inference-kernel debate. Dao and He think in CUDA and Triton kernels for Hopper/Blackwell; Feldman thinks at the system level on wafer-scale. The friction is productive.
- **Pair Feldman with Woosuk Kwon** (vLLM) for the inference-serving layer. Different cells, complementary perspectives — Kwon optimizes for the GPU inference reality today; Feldman argues the substrate itself should be different.
- **Pair Feldman with Elon Musk** (productive conflict) on hyperscaler custom silicon. Dojo is the Cerebras strategy run by a customer.
- **Pair Feldman with Sam Altman** (productive conflict) on the NVIDIA-customer frame. Until January 2026, Altman was a NVIDIA-customer-by-default; after January 2026, the OpenAI–Cerebras deal makes them strategic partners. The dialogue is now richer.

When not to convene Feldman:
- Training scale-out kernel questions where the answer obviously runs on NVIDIA hardware.
- Alignment / safety / policy questions outside the compute-supply-chain seam.
- Pure software/framework questions where the silicon is incidental.
