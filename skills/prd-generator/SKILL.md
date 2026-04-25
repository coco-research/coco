---
name: prd-generator
description: Generate comprehensive Product Requirements Documents (PRDs) for product managers. Use this skill when users ask to "create a PRD", "write product requirements", "document a feature", or need help structuring product specifications.
---

# PRD Generator

## Overview

Generate comprehensive, well-structured Product Requirements Documents (PRDs) that follow industry best practices. This skill helps product managers create clear, actionable requirements documents that align stakeholders and guide development teams.

## Core Workflow

When a user requests to create a PRD (e.g., "create a PRD for a user authentication feature"), follow this workflow:

### Step 1: Gather Context

Before generating the PRD, collect essential information through a discovery conversation:

**Required Information:**
- **Feature/Product Name**: What are we building?
- **Problem Statement**: What problem does this solve?
- **Target Users**: Who is this for?
- **Business Goals**: What are we trying to achieve?
- **Success Metrics**: How will we measure success?
- **Timeline/Constraints**: Any deadlines or limitations?

**Discovery Questions to Ask:**

```
1. What problem are you trying to solve?
2. Who is the primary user/audience for this feature?
3. What are the key business objectives?
4. Are there any technical constraints we should be aware of?
5. What does success look like? How will you measure it?
6. What's the timeline for this feature?
7. What's explicitly out of scope?
```

**Note:** If the user provides a detailed brief or requirements upfront, you can skip some questions. Always ask for clarification on missing critical information.

### Step 2: Generate PRD Structure

Use the standard PRD template from `references/prd_template.md` to create a well-structured document. The PRD should include:

1. **Executive Summary** - High-level overview (2-3 paragraphs)
2. **Problem Statement** - Clear articulation of the problem
3. **Goals & Objectives** - What we're trying to achieve
4. **User Personas** - Who we're building for
5. **User Stories & Requirements** - Detailed functional requirements
6. **Success Metrics** - KPIs and measurement criteria
7. **Scope** - What's in and out of scope
8. **Technical Considerations** - Architecture, dependencies, constraints
9. **Design & UX Requirements** - UI/UX considerations
10. **Timeline & Milestones** - Key dates and phases
11. **Risks & Mitigation** - Potential issues and solutions
12. **Dependencies & Assumptions** - What we're relying on
13. **Open Questions** - Unresolved items

### Step 3: Create User Stories

For each major requirement, generate user stories using the standard format:

```
As a [user type],
I want to [action],
So that [benefit/value].

Acceptance Criteria:
- [Specific, testable criterion 1]
- [Specific, testable criterion 2]
- [Specific, testable criterion 3]
```

Reference `references/user_story_examples.md` for common patterns and best practices.

### Step 4: Define Success Metrics

Use appropriate metrics frameworks based on the product type:

- **AARRR (Pirate Metrics)**: Acquisition, Activation, Retention, Revenue, Referral
- **HEART Framework**: Happiness, Engagement, Adoption, Retention, Task Success
- **North Star Metric**: Single key metric that represents core value
- **OKRs**: Objectives and Key Results

Consult `references/metrics_frameworks.md` for detailed guidance on each framework.

### Step 5: Validate & Review

Optionally run the validation script to ensure PRD completeness:

```bash
scripts/validate_prd.sh <prd_file.md>
```

This checks for:
- All required sections present
- User stories follow proper format
- Success metrics are defined
- Scope is clearly articulated
- No placeholder text remains

## Usage Patterns

### Pattern 1: New Feature PRD

**User Request:** "Create a PRD for adding dark mode to our mobile app"

**Execution:**

1. Ask discovery questions about dark mode requirements
2. Generate PRD using template
3. Create user stories for:
   - Theme switching
   - Preference persistence
   - System-level sync
   - Design token updates
4. Define success metrics (adoption rate, user satisfaction)
5. Identify technical dependencies (design system, platform APIs)

### Pattern 2: Product Enhancement PRD

**User Request:** "Write requirements for improving our search functionality"

**Execution:**

1. Gather context on current search limitations
2. Identify user pain points and desired improvements
3. Generate PRD with focus on:
   - Current state analysis
   - Proposed enhancements
   - Impact assessment
4. Create prioritized user stories
5. Define before/after metrics

### Pattern 3: New Product PRD

**User Request:** "I need a PRD for a new analytics dashboard product"

**Execution:**

1. Comprehensive discovery (market analysis, user research)
2. Generate full PRD with:
   - Market opportunity
   - Competitive analysis
   - Product vision
   - MVP scope
   - Go-to-market considerations
3. Detailed user stories for core features
4. Phased rollout plan
5. Success metrics aligned with business goals

### Pattern 4: Quick PRD / One-Pager

**User Request:** "Create a lightweight PRD for a small bug fix feature"

**Execution:**

1. Generate simplified PRD focusing on:
   - Problem statement
   - Solution approach
   - Acceptance criteria
   - Success metrics
2. Skip sections not relevant for small scope
3. Keep document concise (1-2 pages)

## PRD Best Practices

### Writing Quality Requirements

**Good Requirements Are:**
- **Specific**: Clear and unambiguous
- **Measurable**: Can be verified/tested
- **Achievable**: Technically feasible
- **Relevant**: Tied to user/business value
- **Time-bound**: Has clear timeline

**Avoid:**
- Vague language ("fast", "easy", "intuitive")
- Implementation details (let engineers decide how)
- Feature creep (stick to core requirements)
- Assumptions without validation

### User Story Best Practices

**DO:**
- Focus on user value, not features
- Write from user perspective
- Include clear acceptance criteria
- Keep stories independent and small
- Use consistent format

**DON'T:**
- Write technical implementation details
- Create dependencies between stories
- Make stories too large (epics)
- Use internal jargon
- Skip acceptance criteria

### Scope Management

**In-Scope Section:**
- List specific features/capabilities included
- Be explicit and detailed
- Link to user stories

**Out-of-Scope Section:**
- Explicitly state what's NOT included
- Prevents scope creep
- Manages stakeholder expectations
- Can include "future considerations"

### Success Metrics Guidelines

**Choose Metrics That:**
- Align with business objectives
- Are measurable and trackable
- Have clear targets/thresholds
- Include both leading and lagging indicators
- Consider user and business value

**Typical Metric Categories:**
- **Adoption**: How many users use the feature?
- **Engagement**: How often do they use it?
- **Satisfaction**: Do users like it?
- **Performance**: Does it work well?
- **Business Impact**: Does it drive business goals?

## Advanced Features

### PRD Templates for Different Contexts

The skill supports different PRD formats:

**Standard PRD** - Full comprehensive document
**Lean PRD** - Streamlined for agile teams
**One-Pager** - Executive summary format
**Technical PRD** - Engineering-focused requirements
**Design PRD** - UX/UI-focused requirements

Specify the format when requesting: "Create a lean PRD for..." or "Generate a technical PRD for..."

### Integration with Design

**Design Requirements Section Should Include:**
- Visual design requirements
- Interaction patterns
- Accessibility requirements (WCAG compliance)
- Responsive design considerations
- Design system components to use
- User flow diagrams
- Wireframe/mockup references

### Technical Considerations Section

**Should Address:**
- **Architecture**: High-level technical approach
- **Dependencies**: External services, libraries, APIs
- **Security**: Authentication, authorization, data protection
- **Performance**: Load times, scalability requirements
- **Compatibility**: Browser, device, platform support
- **Data**: Storage, migration, privacy considerations
- **Integration**: How it fits with existing systems

### Stakeholder Alignment

**PRD Should Help:**
- Align cross-functional teams
- Set clear expectations
- Enable parallel work streams
- Facilitate decision-making
- Provide single source of truth

**Distribution Checklist:**
- [ ] Engineering reviewed technical feasibility
- [ ] Design reviewed UX requirements
- [ ] Product leadership approved scope
- [ ] Stakeholders understand timeline
- [ ] Success metrics agreed upon

## Common PRD Scenarios

### Scenario 1: Feature Request from Customer

When creating a PRD based on customer feedback:

1. Document the customer request verbatim
2. Analyze the underlying problem
3. Generalize the solution for all users
4. Validate with product strategy
5. Scope appropriately (might be smaller or larger than request)

### Scenario 2: Strategic Initiative

When creating a PRD for a strategic company initiative:

1. Link to company OKRs/goals
2. Include market analysis
3. Consider competitive landscape
4. Think multi-phase rollout
5. Include success criteria aligned with strategy

### Scenario 3: Technical Debt / Infrastructure

When creating a PRD for technical improvements:

1. Explain user impact (even if indirect)
2. Document current limitations
3. Articulate benefits (speed, reliability, maintainability)
4. Include engineering input heavily
5. Define measurable improvements

### Scenario 4: Compliance / Regulatory

When creating a PRD for compliance requirements:

1. Reference specific regulations (GDPR, HIPAA, etc.)
2. Include legal/compliance review
3. Deadline is usually non-negotiable
4. Focus on minimum viable compliance
5. Document audit trail requirements

## Validation & Quality Checks

### Self-Review Checklist

Before finalizing the PRD, verify:

- [ ] **Problem is clear**: Anyone can understand what we're solving
- [ ] **Users are identified**: We know who this is for
- [ ] **Success is measurable**: We can determine if it worked
- [ ] **Scope is bounded**: Clear what's in and out
- [ ] **Requirements are testable**: QA can verify completion
- [ ] **Timeline is realistic**: Estimates validated with engineering
- [ ] **Risks are identified**: We've thought through what could go wrong
- [ ] **Stakeholders aligned**: Key people have reviewed and approved

### Using the Validation Script

```bash
# Basic validation
scripts/validate_prd.sh my_prd.md

# Verbose output with suggestions
scripts/validate_prd.sh my_prd.md --verbose

# Check specific sections only
scripts/validate_prd.sh my_prd.md --sections "user-stories,metrics"
```

## Resources

This skill includes bundled resources:

### scripts/

- **generate_prd.sh** - Interactive PRD generation workflow
- **validate_prd.sh** - Validates PRD completeness and quality

### references/

- **prd_template.md** - Standard PRD template structure
- **user_story_examples.md** - User story patterns and examples
- **metrics_frameworks.md** - Guide to PM metrics (AARRR, HEART, OKRs)

## Tips for Product Managers

### Before Writing the PRD

1. **Do your research**: User interviews, data analysis, competitive analysis
2. **Validate the problem**: Ensure it's worth solving
3. **Check strategic alignment**: Does this fit our roadmap?
4. **Estimate effort**: Rough t-shirt size with engineering
5. **Consider alternatives**: Is this the best solution?

### During PRD Creation

1. **Be clear, not clever**: Simple language wins
2. **Show, don't tell**: Use examples, mockups, diagrams
3. **Think edge cases**: What could go wrong?
4. **Prioritize ruthlessly**: What's MVP vs. nice-to-have?
5. **Collaborate early**: Don't work in isolation

### After PRD Completion

1. **Review with stakeholders**: Get feedback early
2. **Iterate based on input**: PRDs are living documents
3. **Present, don't just share**: Walk through the PRD
4. **Get formal sign-off**: Ensure commitment
5. **Keep it updated**: Adjust as understanding evolves

## Examples

### Example 1: Mobile Feature PRD

```bash
# User: "Create a PRD for adding biometric authentication to our iOS app"

# Assistant will:
# 1. Ask discovery questions about security requirements, user personas, existing auth
# 2. Generate PRD covering:
#    - Problem: Password friction, security concerns
#    - Solution: Face ID / Touch ID integration
#    - User stories: Enable biometric, fallback to password, settings management
#    - Metrics: Adoption rate, login success rate, support tickets
#    - Technical: iOS Keychain, LocalAuthentication framework
#    - Risks: Device compatibility, user privacy concerns
# 3. Output formatted markdown PRD
```

### Example 2: Web Platform Enhancement

```bash
# User: "Write requirements for improving our checkout flow conversion"

# Assistant will:
# 1. Gather data on current conversion rates and drop-off points
# 2. Generate PRD including:
#    - Current state analysis with metrics
#    - Proposed improvements (guest checkout, saved payment, progress indicator)
#    - A/B test plan
#    - Success metrics: Conversion rate increase, time to checkout
#    - User stories for each improvement
# 3. Include phased rollout approach
```

### Example 3: B2B Product PRD

```bash
# User: "I need a PRD for an admin dashboard for enterprise customers"

# Assistant will:
# 1. Identify B2B-specific requirements (multi-tenancy, permissions, reporting)
# 2. Generate comprehensive PRD with:
#    - Enterprise user personas (admin, manager, analyst)
#    - Role-based access control requirements
#    - Reporting and analytics needs
#    - Integration requirements (SSO, SCIM)
#    - Success metrics: Customer adoption, admin efficiency
# 3. Include enterprise-specific considerations (compliance, SLAs)
```

## Troubleshooting

**Issue: PRD is too long/detailed**

Solution: Create a "Lean PRD" focusing on problem, solution, acceptance criteria, and metrics. Reserve full PRD for major initiatives.

**Issue: Requirements are too vague**

Solution: Add specific examples, use concrete numbers, include visual references. Replace "fast" with "loads in under 2 seconds."

**Issue: Stakeholders not aligned**

Solution: Share PRD early as draft, incorporate feedback, present in person, get explicit sign-off before development starts.

**Issue: Scope keeps expanding**

Solution: Use "Out of Scope" section aggressively, create separate PRDs for future phases, tie scope to timeline constraints.

**Issue: Engineers say it's not feasible**

Solution: Involve engineering earlier in process, be flexible on solution approach, focus on problem not implementation.

## Best Practices Summary

1. **Start with the problem, not the solution**
2. **Write for your audience** (execs need summary, engineers need details)
3. **Be specific and measurable** (avoid vague language)
4. **Include visuals** (mockups, diagrams, flows)
5. **Define success upfront** (metrics, not features)
6. **Scope aggressively** (MVP mentality)
7. **Collaborate, don't dictate** (get input from all functions)
8. **Keep it updated** (PRD is a living document)
9. **Focus on "why" and "what", not "how"** (let engineers solve "how")
10. **Make it skimmable** (headers, bullets, summaries)
