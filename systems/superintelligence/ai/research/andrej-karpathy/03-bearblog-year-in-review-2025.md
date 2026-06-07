# Karpathy — 2025 LLM Year in Review

Source: https://karpathy.bearblog.dev/year-in-review-2025/
Published: December 19, 2025

## Six pillars of 2025

### 1. RLVR (Reinforcement Learning from Verifiable Rewards)

RLVR emerged as a major new training stage. Models develop reasoning strategies through optimization against objective reward functions. The shift moved compute allocation from pretraining → longer RL runs, with test-time compute becoming a controllable capability lever.

**Critique:** Benchmarks are "almost by construction verifiable environments" susceptible to overfitting through RLVR + synthetic data generation.

### 2. Ghosts vs animals / jagged intelligence

LLMs display fundamentally different intelligence patterns than biological entities. **"We are summoning ghosts, not evolving animals."** They exhibit jagged capability profiles—genius in certain domains, struggling in others—due to optimization pressures fundamentally distinct from human evolution.

**Quote:** "Everything about the LLM stack is different...so it should be no surprise that we are getting very different entities."

### 3. Cursor as new app layer

Cursor demonstrated a distinct LLM application layer that orchestrates multiple model calls, handles context engineering, provides domain-specific GUIs, and offers autonomy control. This separates LLM labs from specialized vertical applications.

### 4. Claude Code / local AI agents

Claude Code represents convincing agent architecture running locally on user computers with private data and context. Superior to cloud-based approaches for intermediate-capability scenarios requiring low-latency interaction.

**Critique:** OpenAI prioritized cloud-based agent deployments when local execution better serves current jagged capabilities.

### 5. Vibe coding

Programming via natural language crossed a capability threshold enabling non-professionals to build software AND professionals to create ephemeral, disposable code. Fundamentally democratizing software development.

**Quote:** "Code is suddenly free, ephemeral, malleable, discardable after single use."

### 6. Gemini Nano Banana / LLM GUI

Multimodal models providing visual, spatial output represent the GUI equivalent for LLM-era computing. Parallel to the historical CLI → GUI transition.

## Predictions

Karpathy holds simultaneous beliefs in:
- Rapid continued progress on the frontier
- Substantial remaining work before AGI

He suspects LLM labs will produce **generalists**; specialized applications will organize them into **professional teams** using private data and feedback loops. This shapes how he thinks about app-layer companies vs foundation-model labs.
