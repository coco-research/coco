# Recent product launches under Hassabis (2024–2026)

Sources:
- AlphaFold 3 paper: https://www.nature.com/articles/s41586-024-07487-w
- AlphaProteo announcement: https://x.com/demishassabis/status/1831843656623599936
- AlphaProteo paper: https://arxiv.org/abs/2409.08022
- Gemini 3 launch: https://blog.google/products/gemini/gemini-3/
- Gemini 3 CNBC coverage: https://www.cnbc.com/2025/11/18/google-announces-gemini-3-as-battle-with-openai-intensifies.html
- Veo 3 / Veo 3.1: https://deepmind.google/models/veo/, https://x.com/demishassabis/status/1978502149563646094
- Genie 3 + AlphaEarth + Gemini 2.5 Pro Deep Think (one-tweet roll-up): https://x.com/demishassabis/status/1953887339094143156
- Isomorphic Labs Series B: https://techstartups.com/2026/05/12/alphabet-backed-isomorphic-labs-raises-2-1b-to-accelerate-ai-designed-drug-discovery-as-clinical-trials-near/

## AlphaFold 3 (May 2024)

- Paper: "Accurate structure prediction of biomolecular interactions with AlphaFold 3," *Nature* 630, 493–500 (2024). Hassabis and Jumper are corresponding authors.
- Diffusion-based architecture, generalises from proteins-only to **proteins + DNA + RNA + small-molecule ligands + ions + modified residues**.
- Reported >= 50% accuracy improvement over previous SOTA for protein–molecule interactions; 65% accuracy on DNA interactions vs ~28% for the next-best method.
- Initially launched as **AlphaFold Server** (web-based, not open-weight). This generated significant pushback from the academic community for breaking with AlphaFold 2's open-source norm. Weights and code partially released later.

## AlphaProteo (September 2024)

- ArXiv: 2409.08022. Tweet: 5 September 2024.
- De-novo protein-binder design — designs new proteins that bind a specified molecular target with high affinity.
- Reported 3× to 300× better binding affinity than prior methods on seven test proteins, including wet-lab-validated success on VEGF-A (a cancer-associated target that defeated earlier methods).
- Hassabis framing: AlphaFold reads protein grammar; AlphaProteo writes it.

## Gemini 2.5 Pro + Deep Think + Genie 3 + AlphaEarth (August 2025)

Hassabis tweet, ~8 August 2025: "One word: relentless. just in the past two weeks, we've shipped: 🌐 Genie 3 — the most advanced world simulator ever. 🤔 Gemini 2.5 Pro Deep Think available to Ultra subs. 🎓 Gemini Pro free for uni students & $1B for US ed. 🌍 AlphaEarth — a geospatial model of the entire planet."

- **Genie 3:** Real-time, interactive world simulator. Used internally to train agents. Hassabis flagged it as "a ChatGPT moment for world models is coming" but constrained by inference cost.
- **Deep Think mode:** Extended reasoning before answering. Closes most of the gap between non-reasoning and reasoning models on hard math/science benchmarks.
- **AlphaEarth:** Geospatial foundation model — multimodal Earth-scale embeddings used for weather, climate, deforestation, and hurricane prediction (the Hurricane Melissa early-warning case Hassabis cited at Google I/O 2026).

## Veo 3 (May 2025) and Veo 3.1 (October 2025)

- Veo 3: First major text-to-video model with **synchronized audio** generation — dialogue, sound effects, ambient noise.
- Hassabis framing on Veo 3 launch: "AI video has left the era of the silent film."
- Veo 3.1 (16 October 2025): better realism, scene extension over a minute, narrative control, editing.

## Gemini 3 (18 November 2025)

- LMArena top score: 1501 Elo.
- GPQA Diamond: 91.9%.
- SWE-bench Verified: 76.2%.
- Humanity's Last Exam: 37.5% (no tools); 41.0% in Deep Think mode.
- ARC-AGI-2 (Deep Think): 45.1%.
- Demis quote: "It's the best model in the world for multimodal understanding and our most powerful agentic and vibe coding model yet."
- Launched with **Google Antigravity**, an agentic developer platform giving agents direct access to editor, terminal, and browser.

## Isomorphic Labs Series B (May 2026)

- Closed Series B of $2.1B on 12 May 2026, led by Thrive Capital. Alphabet, GV, MGX (Abu Dhabi), Temasek (Singapore), CapitalG, and the UK Sovereign AI Fund participated. Cumulative outside capital ~$2.6B.
- Use of proceeds: scale the **IsoDDE** drug-design engine; hire across London, Cambridge MA, and Lausanne.
- First in-human clinical trial timeline pushed from end-2025 to end-2026 (announced at Davos January 2026).
- Active pharma partnerships: Eli Lilly, Novartis.
