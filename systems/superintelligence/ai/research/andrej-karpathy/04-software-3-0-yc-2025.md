# Karpathy — "Software is Changing (Again)" / Software 3.0

Source: https://www.latent.space/p/s3 (deep summary)
Original talk: YC AI Startup School keynote, 2025
Companion: https://www.ycombinator.com/library/MW-andrej-karpathy-software-is-changing-again

## The three eras

| Era | Substrate | Authored by |
|---|---|---|
| **Software 1.0** | Explicit code | Human programmers |
| **Software 2.0** | Neural network weights | Data + gradient descent |
| **Software 3.0** | Natural-language prompts orchestrating LLMs | Prompt authors |

**Karpathy:** "Software 3.0 is eating 1.0/2.0." "A huge amount of software will be rewritten."

## Eight key concepts from the talk

### 1. Partial autonomy

Rather than full autonomous systems, advocate **autonomy sliders** that let users control AI behavior levels — minimal assistance to full agent mode. Cursor's Tab → Cmd+K → Cmd+L progression is the exemplar.

### 2. Jagged intelligence

> "Some things work extremely well while others fail catastrophically, and it's not always obvious which is which."

LLMs' uneven capability distribution — fundamentally different shape from human learning's linear progression.

### 3. Anterograde amnesia

> "LLMs are like a coworker with anterograde amnesia — they don't consolidate long-running knowledge once training ends."

His proposed direction: **system-prompt learning** for persistent knowledge accumulation.

### 4. Demo-product gap

> "Demo is works.any(), product is works.all()."

The gap between impressive demonstrations and reliable production systems is precisely why partial autonomy matters.

### 5. Build for agents

Toolmakers must recognize **agents as a new digital information consumer category** — alongside humans (with GUIs) and computers (with APIs). LLMs require agent-optimized interfaces.

### 6. LLMs.txt standard

HTML is poorly parseable for LLMs. Dedicated text documentation (an LLM-targeted equivalent to robots.txt) improves agent comprehension significantly.

### 7. Generation-verification loop

> "To improve verification: make it easy, fast to win. To improve generation: keep AI on tight leash."

The collaborative framework: humans verify, AI generates, the loop tightens over time.

### 8. LLMs as infrastructure

Karpathy positions LLMs as **fundamental utilities** — comparable to cloud computing, semiconductor fabs, and operating systems. Reshaping technological foundations, not just adding a feature.

## Why this matters for v2_panel_attribution

The "make the right thing the default" framing in the Marvin Memory v2 panel synthesis (specifically the L4-floor + L1-drill-up + L5-NER-gated hot path, NOT all 5 layers) is Karpathy's stance carried over from this talk. Default = fast, deep retrieval is opt-in. Same shape as his Cursor autonomy slider — depth comes by request, not by default.
