# High-Flyer Capital → DeepSeek funding model

Sources:
- https://en.wikipedia.org/wiki/Liang_Wenfeng
- https://en.wikipedia.org/wiki/DeepSeek
- https://www.technologyreview.com/2025/01/24/1110526/china-deepseek-top-ai-despite-sanctions/
- https://saharaai.com/blog/understanding-deepseek
- TheChinaAcademy interview (already in 02-)

Retrieved: 2026-05-28

## Structural setup

- **High-Flyer Quantitative Investment Management Partnership** (Ningbo, 2016): quant hedge fund Liang co-founded with two Zhejiang University engineering classmates.
- By 2019, High-Flyer managed >10B yuan (~$1.4B AUM) using ML-driven systematic strategies.
- **2019:** Created **High-Flyer AI** as an internal AI research division.
- **2021:** Began accumulating thousands of Nvidia GPUs for ML training — initially classmates were skeptical that a quant fund could compete with ByteDance/Alibaba on AI infrastructure.
- **Pre-export-restriction stockpile:** Wikipedia and MIT Tech Review both report High-Flyer acquired ~10,000 Nvidia A100s before the October 2022 US export controls tightened. This is the chip base that funded the V1–V3 training runs.

## DeepSeek as a strategic carve-out

- **May 2023:** High-Flyer announced spin-off of DeepSeek as a dedicated AGI lab.
- **Cap table:** Per Wikipedia, Liang personally holds ~1% (in some filings up to 84% via shell corporations); High-Flyer holds ~99% directly. SCMP April 2026 reported Liang's personal stake had risen to 34%.
- **No external investors.** DeepSeek has explicitly stated no near-term plans for commercialization or fundraising. Funding comes entirely from High-Flyer's hedge-fund cash flow.
- Liang on this in the July 2024 interview: *"We have no short-term fundraising plans. Our main problem has never been money — it's the export restrictions on high-end chips."*

## Why this matters strategically

1. **No quarterly investor pressure.** No board pushing for product revenue. Liang has stated this lets DeepSeek "avoid commercial pressure and rigid KPIs."
2. **No exit pressure.** DeepSeek is not on a path to IPO or acquisition. Compare to Anthropic ($60B+ valuation, taking $4B from Amazon), SSI ($32B valuation, $3B raised, no product).
3. **Quant DNA carries over.** High-Flyer's institutional muscle was building large-scale GPU compute and using ML on massive datasets — the same primitives as LLM pretraining. Liang himself draws the connection.
4. **Compute-efficiency obsession.** Quant trading rewards every basis point of compute efficiency. Liang's lab has consistently shipped models that punch above their FLOP-cost weight (V3 at $6M vs GPT-4 at $100M+; R1 matching o1 at 1/30 the API cost).
5. **MIT license = ecosystem moat.** With no need to monetize the model directly, releasing under MIT is not a giveaway — it is the strategy. The "real moat" Liang names is team know-how, not weights.

## The closest Western analog

- There is no clean Western analog. The closest structural parallel is **Renaissance Technologies → Medallion** as a research-driven, profit-funded, no-external-investor org. Liang explicitly cites Jim Simons (in the 2021 preface to *The Man Who Solved the Market*) as his model: *"There must be a way to model prices."*
- Liang's frame is essentially: *quant fund pays for AGI research; AGI research is the next regime of pricing intelligence.*

## Compute story under export controls

- The 2022 US controls on H100/A100 sales to China are the central operational constraint.
- DeepSeek trained R1 on ~2,048 H800 GPUs (the export-control-compliant H100 variant). $5.6M reported pretraining cost.
- V4 (April 2026) reportedly trained partly on **Huawei chips** — per Tom's Hardware, this is the first major Chinese frontier model to ship with significant Huawei chip dependency. Politically loaded, given concurrent US accusations of IP theft.
- Liang in the July 2024 interview: *"Bans on shipments of advanced chips are the problem."* The constraint is structural, not financial.
