# Full output of one real `/SI-Decide` run, with persona names replaced by role archetypes

Command: `/SI-Decide "Should a 10-person startup move its public REST API to GraphQL this quarter?"`  
Model: Claude Sonnet 5.5, headless Claude Code, 2026-09-30, 9 turns, US$0.41.  
Persona names are replaced by role archetypes (personas are simulated from public writing and are not the views of any real person; see systems/superintelligence/DISCLAIMER.md). Otherwise unedited below. The two "Next action" lines come from the global style rules of the machine it ran on, not from CoCo; the README capture (`si-decide-run.txt`) trims them, keeps the persona and position columns only, and changes no words.

---

**Next action (2 min):** write down who is asking for GraphQL and what they can't do with REST today. That answer decides this.

**Verdict: NO to a migration this quarter. YES to a bounded additive pilot, only if that answer names a real consumer.**

Two caveats first:
- **Routing:** `meta_select.py` fell back to keywords because the embedding endpoint was down, and it ranked GTM first. I routed by hand to Engineering (8), Product Design (3), Strategy (2), Finance (1) and GTM (2), 16 personas in all.
- **Evidence:** the persona stances I read are about monoliths, discovery, decision quality and retention. None mentions GraphQL. Where I apply a stance to GraphQL, I mark it *(extrapolated)*.

## Round 1: independent positions

| Persona (team) | Position | Reasoning | Open question |
|---|---|---|---|
| Microservices architect (Eng) | No | "Default to a monolith… not a good choice for most startups" *(extrapolated: a new API layer is a new distributed surface)* | for: enterprise-architect, what is the reversible version? |
| Refactoring architect (Eng) | No | The "microservice premium" and prerequisites logic: pay a complexity premium only once the simple thing hurts *(extrapolated)* | for: anyone, who actually hurts today? |
| Monolith advocate (Eng) | Hard no | Programmer happiness, majestic monolith, operational tax. A rewrite for fashion is the tax. *(extrapolated)* | for: product-led-growth-lead, is DX a growth lever or a theory? |
| Enterprise architect (Eng) | Conditional | "Architecture decisions are economic decisions: sell options, make choices reversible." Add GraphQL beside REST, don't replace it. | for: customer-success-lead, what does deprecation cost customers? |
| Team-topology lead (Eng) | No | Cognitive load and team topology: 10 people have no spare capacity for two API stacks *(extrapolated)* | for: observability-lead, can you observe it? |
| Observability lead (Eng) | Conditional | "You are already testing in production"; GraphQL's single endpoint hides per-query cost, so ship it only with wide-event observability *(extrapolated)* | for: team-topology-lead |
| Security lead (Eng) | No this quarter | "Security is a process, not a product." Public, arbitrary-depth queries widen the attack surface; rate-limit and cost controls come first *(extrapolated)* | for: anyone, who owns query-cost limits? |
| Cloud-cost analyst (Eng) | Cost-skeptical | "Every line item is an architecture decision." Resolver fan-out and egress show up on the bill *(extrapolated)* | for: monolith-advocate |
| Product leader (PD) | Not yet | Teams get problems, not features. "Migrate to GraphQL" is a solution with no stated problem. Clear value risk first. | for: lean-startup-coach, is this a test or a build? |
| Discovery coach (PD) | Not yet | Weekly customer touchpoints and an opportunity tree. Ask integrators what they struggle with before choosing a solution. | for: anyone, have 5 integrators been asked? |
| Lean-startup coach (PD) | Pilot | An MVP is a learning vehicle. Expose one GraphQL endpoint to 2-3 willing customers and measure. | for: product-leader |
| Strategy scholar (Strat) | No | "Strategy must begin with challenges, not aspirations." There is no crux here, so it is a fashion move. | for: anyone, what is the bottleneck on growth? |
| Decision scientist (Strat) | Challenge the process | Improve decision architecture, not just individual biases. Who is pushing this and why? Run a pre-mortem and a devil's advocate. | for: decision-strategist |
| Decision strategist (Fin) | Not now, with a kill rule | Judge the decision by its reasoning, not its outcome. Quitting is a rational choice. Pre-commit a kill criterion for any pilot. | for: lean-startup-coach |
| Customer-success lead (GTM) | No breaking changes | Customer success means customers reach their desired outcome. A forced REST sunset breaks integrators who were succeeding. | for: product-led-growth-lead |
| Product-led-growth lead (GTM) | Conditional yes | PLG needs a frictionless "value before payment" path. If the API is the product, DX can be the growth surface. | for: customer-success-lead, monolith-advocate |

## React rounds

**Round 2.** Only listed conflict pairs reacted.
- **Monolith advocate vs Microservices architect, Refactoring architect** (*held*): all three agree on "no". Monolith advocate is blunter: a rewrite is the tax.
- **Product leader vs Lean-startup coach** (*sharpened*): Lean-startup coach concedes that a pilot is only a valid MVP if it tests a stated hypothesis. Product leader concedes a small pilot is acceptable once the problem is named.
- **Enterprise architect vs Microservices architect, Monolith advocate** (*held*): Enterprise architect keeps the additive, reversible option. Microservices architect accepts it only if REST stays the source of truth.
- **Customer-success lead vs Product-led-growth lead** (*updated*): Product-led-growth lead concedes that a new endpoint must never force a REST sunset. Customer-success lead concedes that DX can matter for adoption.
- **Observability lead vs Team-topology lead, Monolith advocate** (*updated*): Team-topology lead agrees to a pilot only with observability and one named owner. Observability lead makes observability a gate, not a nice-to-have.
- **Decision strategist vs Decision scientist** (*sharpened*): both want a pre-committed kill criterion and a named dissenter.

**Round 3.** No stance moved (`held` for everyone) and no unanswered question remained. I stopped at 3 of the 4-round cap.

## Decision matrix

| Option | Eng | Product Design | Strategy | Finance | GTM | Net |
|---|---|---|---|---|---|---|
| A. Full REST-to-GraphQL migration this quarter | Microservices architect, Refactoring architect, Monolith advocate, Team-topology lead, Security lead: no | Product leader, Discovery coach: no problem named | Strategy scholar: no crux; Decision scientist: process unexamined | Decision strategist: no kill rule | Customer-success lead: breaks integrators | **Reject** |
| B. Keep REST, do nothing | Enterprise architect: forgoes options | Discovery coach: ask first | Strategy scholar: fine if no crux | Decision strategist: fine | Product-led-growth lead: risk if DX is the bottleneck | **Default** |
| C. Additive GraphQL pilot, REST untouched | Enterprise architect, Observability lead: yes with gates | Lean-startup coach, Product leader: yes if hypothesis-driven | Decision scientist: yes with kill criteria | Decision strategist: yes with a kill rule | Product-led-growth lead: yes; Customer-success lead: yes if no sunset | **Conditional** |

**Where one team's lens overrides another's:** Engineering (cost, load, risk) and Strategy (no crux) override Growth (Product-led-growth lead) on timing. Customer success (Customer-success lead) overrides any "retire REST" instinct.

## Verdict: CONDITIONAL NO

- **Consensus:** do not migrate. Do not sunset REST.
- **Unresolved disagreement:** Product-led-growth lead and Enterprise architect would still run a pilot to find out whether DX is a growth lever. Monolith advocate and Strategy scholar would run nothing without a named problem. This did not resolve because it depends on a fact I don't have: whether integrators are complaining.
- **Named dissent:** Product-led-growth lead (GTM) and Enterprise architect (Eng) for option C even before evidence. A "ship and see" voice is not on the panel.
- **Open questions for you:**
  1. Who asked for GraphQL, and what can't they do with REST?
  2. Is the API a growth surface (PLG) or a back-office integration?
  3. Does anyone on the 10-person team already run GraphQL in production?

**Pilot criteria if you pick C:**
- Run it beside REST for one quarter, with 2-3 consenting customers and one named owner.
- Enforce query-depth and cost limits and per-query observability before launch.
- Pre-commit a kill criterion, for example: fewer than 2 customers actively using it, or more than X engineer-days of upkeep, means you shut it down.

This is advisory output from persona stances, not a substitute for knowing your actual API consumers.

**Next action (2 min):** message your two biggest API integrators and ask "what's hardest about our API today?"
