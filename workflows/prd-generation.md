# PRD Generation Workflow

> From a brief conversation to a comprehensive Product Requirements Document in under a minute.

## Overview

This workflow transforms a product idea into a structured, actionable PRD through two phases: a discovery conversation that extracts the right information, and a parallel generation step that produces all 13 sections simultaneously.

---

## Phase 1: The Discovery Conversation

Before generating anything, the AI must understand the problem space. The discovery conversation covers five areas:

### 1. Problem Definition
- What problem are we solving?
- Who experiences this problem? How often?
- What do people do today without this solution?
- What is the cost of the status quo (time, money, frustration)?

### 2. Users and Personas
- Who are the primary users? Secondary users?
- What are their roles, technical skill levels, and daily workflows?
- What motivates them? What frustrates them?
- Are there anti-personas (people this product is explicitly not for)?

### 3. Goals and Constraints
- What does success look like in 30/60/90 days?
- What are the hard constraints (budget, timeline, compliance, technology)?
- What is the MVP scope vs. the full vision?
- Are there dependencies on other teams or systems?

### 4. Existing Context
- Is there an existing system being replaced or extended?
- Are there meeting notes, research findings, or prior PRDs to reference?
- What has been tried before? What failed and why?

### 5. Stakeholders
- Who approves this?
- Who needs to be consulted?
- Who will be informed?
- What governance or review processes apply?

**Tip:** If you have raw meeting notes, paste them directly. The AI can extract discovery answers from unstructured notes rather than asking you to re-state what you already discussed.

---

## Phase 2: The 13-Section PRD Structure

Once discovery is complete, the PRD is generated with these sections:

### Section 1: Overview
A one-paragraph executive summary: what the product is, who it serves, and why it matters now. This section should be understandable by anyone in the organization without technical background.

### Section 2: Problem Statement
The problem in detail — who is affected, how severely, and what the measurable impact is. Include data points where available. A strong problem statement makes the rest of the PRD feel inevitable.

### Section 3: Goals and Success Metrics
Concrete, measurable goals tied to business outcomes. Each goal has a metric, a target value, and a measurement method. See the Success Metrics Frameworks section below for structured approaches.

### Section 4: User Personas
2-4 personas with names, roles, goals, pain points, and technical proficiency. Each persona should map to specific user stories later in the document.

### Section 5: User Stories
Structured as: "As a [persona], I want [action] so that [benefit]." Each story includes acceptance criteria using Given/When/Then format. Stories are prioritized as P0 (launch blocker), P1 (launch), P2 (fast follow), or P3 (future).

### Section 6: Functional Requirements
What the system must do, organized by feature area. Each requirement is testable and traceable to a user story. Use "The system shall..." language for clarity.

### Section 7: Non-Functional Requirements
Performance targets (response time, throughput), availability (uptime SLA), scalability (concurrent users, data volume), security (authentication, authorization, encryption), and accessibility (WCAG level).

### Section 8: Technical Architecture
High-level architecture: components, their responsibilities, and how they communicate. Include technology choices with rationale. Reference the project's existing stack if applicable.

### Section 9: Data Model
Key entities, their attributes, and relationships. Include data flow — where data originates, how it transforms, and where it is stored. Note any data retention or privacy requirements.

### Section 10: API Design
Endpoints, methods, request/response schemas, authentication, and error handling. For internal APIs, include versioning strategy. For external integrations, document rate limits and fallback behavior.

### Section 11: UI/UX Requirements
Key screens or views, navigation flow, interaction patterns, and accessibility requirements. Reference design system components where applicable. Include wireframe descriptions or references.

### Section 12: Timeline and Milestones
Phased delivery plan with dates, deliverables, and dependencies. Include MVP scope (Phase 1), fast-follow features (Phase 2), and future vision (Phase 3+). Flag external dependencies that could block progress.

### Section 13: Risks and Mitigations
Technical, business, and operational risks. Each risk has a likelihood (High/Medium/Low), impact (High/Medium/Low), and a specific mitigation strategy. Include contingency plans for high-impact risks.

---

## User Stories: Format and Examples

### Format
```
**US-[ID]: [Title]**
As a [persona], I want [action] so that [benefit].

Priority: P[0-3]
Acceptance Criteria:
- Given [context], when [action], then [expected result]
- Given [context], when [action], then [expected result]
```

### Example
```
**US-001: Search for a city's weather**
As a commuter, I want to search for any city's current weather
so that I can plan my route before leaving.

Priority: P0
Acceptance Criteria:
- Given I am on the dashboard, when I type a city name, then I see
  autocomplete suggestions after 2+ characters
- Given I select a city from suggestions, when the page loads, then
  I see current temperature, conditions, and a 5-day forecast
- Given the API is unavailable, when I search, then I see a friendly
  error message with the last cached result (if available)
```

---

## Success Metrics Frameworks

Choose the framework that best fits your product's maturity and goals.

### AARRR (Pirate Metrics)
Best for growth-stage products where acquisition and retention are primary concerns.

| Stage | Question | Example Metric |
|-------|----------|---------------|
| **Acquisition** | How do users find us? | Sign-ups per week, landing page conversion |
| **Activation** | Do users have a good first experience? | % completing onboarding, time to first value |
| **Retention** | Do users come back? | DAU/MAU ratio, 7-day retention rate |
| **Revenue** | How do we make money? | ARPU, conversion to paid, LTV |
| **Referral** | Do users tell others? | NPS, referral rate, viral coefficient |

### HEART (Google's UX Framework)
Best for products where user experience quality is the primary differentiator.

| Dimension | Question | Example Metric |
|-----------|----------|---------------|
| **Happiness** | Are users satisfied? | CSAT score, NPS, qualitative feedback |
| **Engagement** | How deeply do users interact? | Session duration, features used per session |
| **Adoption** | Are new users adopting key features? | % using feature X within first week |
| **Retention** | Do users keep using the product? | Churn rate, repeat usage frequency |
| **Task success** | Can users accomplish their goals? | Task completion rate, error rate, time on task |

### OKR (Objectives and Key Results)
Best for aligning product goals with organizational strategy.

```
Objective: [Qualitative, aspirational goal]
  KR1: [Quantitative result] from [baseline] to [target] by [date]
  KR2: [Quantitative result] from [baseline] to [target] by [date]
  KR3: [Quantitative result] from [baseline] to [target] by [date]
```

**Example:**
```
Objective: Make weather planning effortless for daily commuters
  KR1: Increase daily active users from 0 to 500 by end of Q1
  KR2: Achieve 60% 7-day retention rate by end of Q1
  KR3: Reduce average time-to-forecast from 45s to under 5s by end of Q1
```

---

## Validation Checklist

Before finalizing, validate the PRD against these criteria:

### Completeness
- [ ] All 13 sections are present and substantive (not placeholder text)
- [ ] Every user story has acceptance criteria
- [ ] Every goal has a measurable metric with a target value
- [ ] Technical architecture covers all major components
- [ ] Risks section includes at least 3 risks with mitigations

### Consistency
- [ ] User stories trace back to personas
- [ ] Functional requirements trace back to user stories
- [ ] API design matches the data model
- [ ] Timeline accounts for all P0 and P1 user stories
- [ ] Non-functional requirements are achievable with the proposed architecture

### Feasibility
- [ ] Technical choices are compatible with the existing stack
- [ ] Timeline is realistic given team size and dependencies
- [ ] Non-functional targets are achievable (not aspirational fiction)
- [ ] External dependencies have been confirmed with owning teams

### Testability
- [ ] Every functional requirement can be verified with a specific test
- [ ] Acceptance criteria use Given/When/Then format (unambiguous)
- [ ] Non-functional requirements have specific thresholds (not "fast" or "scalable")
- [ ] Edge cases are documented (empty states, error states, boundary conditions)
