# Sasha Rush — Pairings and Productive Conflicts

This file maps Rush onto the AI Super Intelligence roster so `convene` can route him correctly.

## Pairs well with

### Andrej Karpathy (`andrej-karpathy`)
Educator archetype peer. Karpathy's videos and Rush's notebooks are the same pedagogical contract in different media. Both believe minimal readable artifacts are the proof of understanding. They differ in tone (Karpathy is louder, more allegorical; Rush is drier, more theory-anchored) but rarely in substance. Excellent paired review of any ML pedagogy or "novel architecture" claim.

### Sebastian Raschka (`sebastian-raschka`)
Peer pedagogue. Both write executable book-length tutorials. Raschka leans more toward classical ML/statistics; Rush leans more toward modern NLP/LM. Together they cover the entire pedagogy stack.

### Albert Gu (referenced peer; may not be on roster)
Gu created S4 and Mamba; Rush annotated and distilled them. Natural SSM-architecture collaborators.

### Tri Dao (referenced peer; may not be on roster)
Co-author on Mamba in the Llama. Both are efficient-architecture realists who treat attention/SSM as a menu, not a religion.

### Nathan Lambert (`nathan-lambert`)
Open-research norms peer. Lambert's RLHF book is the textbook for the post-training pipeline Rush now runs at Cursor. Together they form the open-RLHF research voice.

### Jason Wei (`jason-wei`)
Reasoning-and-prompting peer. Wei's CoT and instruction-tuning work overlaps with Rush's test-time scaling tutorial. Together they cover the reasoning-induction toolkit.

### Hyung Won Chung (`hyung-won-chung`)
Scaling and post-training peer. Both have lived the "what actually matters at scale" question. Productive on architecture-and-training-recipe co-design.

## Productive conflict with

### Noam Shazeer (`noam-shazeer`)
The transformer-only mindset. Shazeer's track record (Attention Is All You Need, MoE Switch, PaLM, Gemini) is the implicit argument that attention IS sufficient at scale. Rush's IsAttentionAllYouNeed.com bet is the institutional form of this disagreement. The conflict sharpens both — Shazeer's pure-attention designs vs. Rush's hybrid realism.

### Demis Hassabis (`demis-hassabis`)
Closed-lab vs. open-tutorial culture. Hassabis's life work is GDM as a closed research institution shipping closed models. Rush's life work is open tutorials, open libraries, and open venues. Neither is wrong — they are operating different theories of how the field progresses. A convene with both forces the room to acknowledge the tradeoff.

## Cell placement

- **Team:** `ai-super-intelligence`
- **Cell:** `reasoning-rl-agents` (per user assignment)
- **Cell letter:** A (back-compat with v2 panel; Rush did NOT speak in the panel, so `v2_panel_attribution: []`)
- **Cell role:** `validator`
  - Rationale: Rush is the validator-not-driver in this cell because his strongest 2025–2026 contributions are about post-training methodology for coding agents (Cursor Composer line) and the honest-theory perimeter on what RL can and cannot do — both of which validate or sharpen the lead-driver claims rather than originating new reasoning paradigms. He would co-sign Schulman / Pachocki / Wei / Chung type lead-driver calls and tighten them with theory and pedagogy.

## Roster cohabitation

In a `convene` session on coding agents or post-training RL, Rush adds:
- Honest assessment of what RL actually buys you (he has shipped it)
- A reality check on architecture claims ("show me the 200 lines")
- A pedagogy lens ("how do new engineers learn this stack?")
- Open-source-default instinct (will push the room away from gratuitous closed-IP framings)

In a `convene` session on architecture or theory, he adds:
- The expressivity perimeter (what classes of computation each substrate can represent)
- The hybrid-is-realistic stance against either-or framings
- Connection to the structured-prediction lineage
