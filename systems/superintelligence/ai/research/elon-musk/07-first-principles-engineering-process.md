# Musk's first-principles engineering doctrine

Sources:
- https://everydayastronaut.com/starbase-tour-and-interview-with-elon-musk/
- https://modelthinkers.com/mental-model/musks-5-step-design-process
- https://oodaloop.com/analysis/archive/the-everyday-astronaut-elon-musk-and-his-five-step-engineering-process/
- https://www.youtube.com/watch?v=zAfGk-SK1Es

Retrieved: 2026-05-28

## The 5-step process (canonical ordering — order matters)

Articulated at Starbase, Boca Chica, Texas during Everyday Astronaut tour (2021), reiterated in numerous interviews since.

### Step 1 — Make the requirements less dumb

> "The requirements are definitely dumb; it does not matter who gave them to you."

Particularly dangerous when smart people give you requirements — you stop questioning them. Tagged in his frame as the most common error.

### Step 2 — Delete the part or process

> "If parts are not being added back into the design at least 10% of the time, not enough parts are being deleted."

The 10% rule: if you never need to add a part back, you weren't deleting aggressively enough. Deletion is the correct default; restoration is the correction signal.

### Step 3 — Simplify and optimize the design

> "The most common error of a smart engineer is to optimize something that should not exist."

Cannot be done before Steps 1 and 2. Optimizing a thing that shouldn't exist is the canonical waste pattern.

### Step 4 — Accelerate cycle time

> "You're moving too slowly, go faster! But don't go faster until you've worked on the other three things first."

Cycle-time acceleration only after the design is right. Otherwise you're accelerating the wrong thing.

### Step 5 — Automate

Automation is the LAST step, not the first. Counterintuitive Tesla manufacturing lesson — Tesla famously over-automated the Model 3 line in 2018 and had to manually back out. Musk: "humans are underrated."

Includes removing in-process testing once acceptance rates are high enough.

## First-principles reasoning frame

Musk's broader doctrine — articulated repeatedly on Lex Fridman, Joe Rogan, Tim Dodd interviews:

- "Reason from the underlying physics, not by analogy."
- Boil any problem down to fundamental constraints (conservation laws, mass, energy, cost of raw materials) and rebuild upward.
- Famous application: SpaceX vs traditional aerospace launch cost. "Look at the raw materials cost of a rocket. Aluminum, copper, carbon fiber. Maybe 2% of the rocket's price. Where did the other 98% go?"
- Same frame applied to: Tesla battery costs (raw lithium + nickel + cobalt + cathode chemistry), Optimus body cost target, Cybercab purchase price target.

## Why this matters for the persona

- Musk does not deliver opinions in alignment / safety / interpretability vocabulary
- He delivers them in cost-physics + manufacturing-cycle vocabulary
- A persona summoned for an AI-architecture decision will reframe it as: what is the requirements waste? what can be deleted? what's the actual cycle time? what's the automation premature?
- This is the cell_role = lead-driver signature: he does not validate; he reframes the problem.
