---
name: ultra-think
description: "Deep, multi-dimensional analysis and problem solving. Activates systematic reasoning across technical, business, user, and system perspectives. Generates multiple solutions with trade-offs, then synthesizes into a clear recommendation."
domain: foundational
supports: [claude-code, cursor, codex, generic]
version: 0.1.0
---

# Ultra Think — Deep Analysis Mode

Deep, multi-dimensional analysis and problem solving. Activates systematic reasoning across technical, business, user, and system perspectives. Generates multiple solutions with trade-offs, then synthesizes into a clear recommendation.

**Use when**: facing architectural decisions, complex trade-offs, strategic technology choices, system design problems, scaling challenges, migration decisions, or any question that deserves more than a quick answer. Attach this skill when you want rigorous, first-principles thinking.

---

## When This Skill Is Activated

Do NOT jump to a solution. Follow every step below in order. Think deeply at each stage before moving on.

---

## Step 1: Parse the Problem

Before analyzing, make sure you understand what's actually being asked.

- Extract the core challenge from the user's message
- Identify all stakeholders and constraints (stated and implied)
- Surface hidden complexities and implicit requirements
- Question assumptions — what is the user taking for granted?
- Name the unknowns explicitly

---

## Step 2: Multi-Dimensional Analysis

Analyze the problem from four perspectives. Do not skip any.

### Technical Perspective
- Feasibility and constraints
- Scalability, performance, maintainability
- Security implications
- Technical debt and future-proofing
- Integration complexity

### Business Perspective
- Business value and ROI
- Time-to-market pressure
- Competitive advantage
- Risk vs. reward trade-offs
- Cost (development, operational, opportunity)

### User Perspective
- User needs and pain points
- Usability and accessibility
- Edge cases and failure states from the user's point of view
- User journeys affected

### System Perspective
- System-wide impacts and ripple effects
- Integration points and coupling
- Dependencies (upstream and downstream)
- Emergent behaviors and unintended interactions

---

## Step 3: Generate Multiple Solutions

Brainstorm **at least 3 distinct approaches** — not variations of the same idea.

For each approach, evaluate:
- Pros and cons
- Implementation complexity (T-shirt size: S/M/L/XL)
- Resource requirements (people, time, money)
- Key risks
- Long-term implications (what does this look like in 2 years?)

Include at least one unconventional or creative solution. Consider hybrid approaches that combine strengths of different options.

---

## Step 4: Deep Dive on Top Candidates

For the 1–2 most promising solutions:

- Sketch a detailed implementation plan (phases, milestones)
- Identify pitfalls and mitigation strategies
- Consider a phased approach or MVP path
- Analyze **second-order effects** — what changes because of this change?
- Think through failure modes — what happens when this breaks?
- Estimate reversibility — how hard is it to undo if wrong?

---

## Step 5: Cross-Domain Thinking

Look beyond the immediate domain for insight:

- Are there parallels from other industries? (e.g., how did logistics solve this? Healthcare? Finance?)
- Do design patterns from other contexts apply? (e.g., circuit breakers from electrical engineering → software resilience)
- Are there natural system analogies? (e.g., biological redundancy, evolutionary pressure)
- Can existing solutions be combined in a novel way?

---

## Step 6: Challenge and Stress-Test

Play devil's advocate against every solution, including the one you favor.

- What's the strongest argument against each option?
- What blind spots might you have?
- Run "what if" scenarios (what if traffic is 10x? what if the team halves? what if requirements change?)
- Stress-test assumptions — which ones, if wrong, would invalidate the whole approach?
- Look for unintended consequences

---

## Step 7: Synthesize and Recommend

Combine all insights into a structured deliverable. Use this exact format:

```
## Problem Analysis
- **Core challenge**: [one sentence]
- **Key constraints**: [list]
- **Critical success factors**: [what must be true for any solution to work]
- **Assumptions**: [what we're taking as given]

## Solution Options

### Option 1: [Name]
- **Description**: [2-3 sentences]
- **Pros**: [list]
- **Cons**: [list]
- **Complexity**: [S/M/L/XL]
- **Risk level**: [Low/Medium/High]
- **Best when**: [conditions that make this the right choice]

### Option 2: [Name]
[Same structure]

### Option 3: [Name]
[Same structure]

## Recommendation
- **Recommended approach**: [which option and why]
- **Rationale**: [the decisive factors]
- **Implementation roadmap**: [phases with rough timelines]
- **Success metrics**: [how we'll know it's working]
- **Risk mitigation**: [top 3 risks and their mitigations]
- **Reversibility**: [how hard to undo if wrong]

## Contrarian View
- **The case against this recommendation**: [strongest counterargument]
- **What would change our mind**: [signals that we chose wrong]
- **Areas of uncertainty**: [what we don't know yet]

## Confidence Assessment
- **Overall confidence**: [High/Medium/Low] — [why]
- **What would increase confidence**: [additional research, prototyping, data needed]
```

---

## Step 8: Meta-Reflection

End with a brief reflection:

- Where is the analysis weakest?
- What biases might be influencing the recommendation?
- What additional expertise or data would improve the analysis?
- What's the one thing most likely to be wrong?

---

## Thinking Principles

Apply these mental models throughout the analysis:

| Principle | Application |
|-----------|-------------|
| **First Principles** | Break down to fundamental truths, don't reason by analogy alone |
| **Systems Thinking** | Consider interconnections, feedback loops, emergent behavior |
| **Probabilistic Thinking** | Work with ranges and likelihoods, not certainties |
| **Inversion** | Ask "what should we avoid?" not just "what should we do?" |
| **Second-Order Effects** | Consider the consequences of consequences |
| **Reversibility** | Prefer reversible decisions; be extra careful with irreversible ones |
| **Occam's Razor** | Among equally valid solutions, prefer the simpler one |

---

## Output Expectations

- Comprehensive analysis (typically 2–4 pages of insight)
- Multiple viable solutions with honest trade-offs
- Clear reasoning chains — show your work
- Explicit acknowledgment of uncertainties
- Actionable recommendation with next steps
- At least one novel insight or non-obvious perspective
