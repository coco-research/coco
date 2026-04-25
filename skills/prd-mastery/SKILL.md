---
name: "PRD Mastery: Context-Aware, Expert-Driven, and Token-Efficient Refinement"
description: "A skill that blends the wisdom of top industry experts, ensures token-efficient PRDs, and organizes outputs in a clear folder structure."
version: "1.0"
author: "Callum Bir"
keywords: ["PRD", "product requirements", "business analysis", "product management", "documentation", "Cagan", "Torres", "Biddle"]
---

# PRD Mastery Skills

**Status:** Production Ready  
**Package Manager:** pnpm  
**Key Focus:** Context-aware PRD creation, token efficiency, expert-driven guidance  
**Official References:**
- Marty Cagan - "Inspired: How to Create Tech Products Customers Love"
- Teresa Torres - "Continuous Discovery Habits"
- George Biddle - Product Management Best Practices

---

## Table of Contents

1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Workflow Steps](#workflow-steps)
4. [Expert-Driven Questioning Techniques](#expert-driven-questioning-techniques)
5. [Token Efficiency Guidelines](#token-efficiency-guidelines)
6. [PRD Organization Structure](#prd-organization-structure)
7. [Code Examples](#code-examples)
8. [Best Practices](#best-practices)
9. [Templates & Resources](#templates--resources)

---

## Overview

The PRD Mastery skill helps AI agents create high-quality, context-aware Product Requirements Documents (PRDs) that are:

- **Context-Aware**: Adapts to whether the project is new or existing, understanding the current tech stack and architecture
- **Expert-Driven**: Uses questioning techniques from industry leaders like Marty Cagan, Teresa Torres, and George Biddle
- **Token-Efficient**: Optimized for AI readability and minimal token usage while maintaining clarity and completeness
- **Well-Organized**: Maintains a clear folder structure for managing multiple PRDs and related artifacts

### Key Features

✅ Automated repository reconnaissance to understand project context  
✅ Adaptive questioning based on project stage  
✅ Expert-guided user interviews to extract requirements  
✅ Token-optimized output format  
✅ Structured organization system for PRD management  
✅ Reusable templates and examples  

---

## Installation & Setup

### Prerequisites

```bash
# Node.js 20.9+ for running reconnaissance scripts
node --version

# pnpm (recommended)
pnpm --version
```

### Quick Start

1. **Run Repository Reconnaissance**
   ```bash
   node .claude/skills/ba-prd-skills/repo_scan.js
   ```

2. **Review Preliminary Findings**
   ```bash
   cat prelim_summary.md
   ```

3. **Create Your First PRD**
   Follow the workflow steps below to guide the PRD creation process.

---

## Workflow Steps

### Step 1: Initial Reconnaissance

**Goal**: Automatically determine if the project is new or existing, identify tech stack, and document context.

**Process**:
1. Run `repo_scan.js` to analyze:
   - Existing codebase structure
   - Technology stack (frameworks, languages, tools)
   - Architecture patterns (monorepo, microservices, etc.)
   - Dependencies and integrations
   - Documentation state

2. Output is saved to `prelim_summary.md` with:
   - Project type (new/existing)
   - Tech stack summary
   - Architecture overview
   - Key observations
   - Recommended next steps

**Example Output**:
```markdown
# Preliminary Project Summary

**Project Type**: Existing
**Tech Stack**: Next.js 16, React, TypeScript, Prisma ORM
**Architecture**: App Router with server components
**Key Observations**: 
- Well-structured authentication system using Auth.js
- Vector database integration with Upstash
- MCP server pattern implementation
```

---

### Step 2: Identify Project Stage and Tech Context

**Goal**: Understand where the project is in its lifecycle and whether architecture changes are needed.

**Context-Aware Questions**:

For **New Projects**:
- What problem are you solving?
- Who are your target users?
- What are the core user outcomes you want to enable?
- What technical constraints do you have? (team skills, budget, timeline)
- What are your scalability expectations?

For **Existing Projects**:
- What are you trying to improve or add?
- Are there pain points with the current architecture?
- Should we maintain the existing tech stack or consider changes?
- What are the key integration points we need to preserve?
- What are the migration constraints?

**Adaptive Follow-ups**:
- If user provides technical details → Validate against current stack, identify gaps
- If user is non-technical → Translate to technical requirements, suggest options
- If requirements are vague → Use expert questioning to narrow scope

---

### Step 3: Guide the User (Expert-Driven Approach)

**Goal**: Use proven questioning techniques to move from broad ideas to specific, outcome-focused PRDs.

#### Marty Cagan's Outcome-Focused Questions

Inspired by "Inspired", focus on outcomes over features:

1. **Problem Definition**
   - What customer problem are we solving?
   - How do we know this is a real problem?
   - What does success look like for the user?

2. **Discovery Validation**
   - Have we validated this problem with real users?
   - What evidence do we have that this solution will work?
   - What are the risks?

3. **Value Proposition**
   - Why will customers choose this?
   - What makes this solution compelling?
   - How does this align with business objectives?

#### Teresa Torres' Continuous Discovery

Based on "Continuous Discovery Habits":

1. **Opportunity Mapping**
   - What opportunities have we identified?
   - Which opportunity has the biggest impact?
   - How does this connect to the desired outcome?

2. **Assumption Testing**
   - What assumptions are we making?
   - Which assumptions are riskiest?
   - How can we test these quickly?

3. **Customer Interviews**
   - Who should we talk to?
   - What do we need to learn?
   - How will we capture and synthesize insights?

#### George Biddle's Structured Approach

Focus on clarity and completeness:

1. **Stakeholder Alignment**
   - Who needs to approve this?
   - What concerns might stakeholders have?
   - How do we measure success?

2. **Technical Feasibility**
   - Is this technically possible with our stack?
   - What are the technical risks?
   - What dependencies exist?

3. **Implementation Plan**
   - What's the MVP scope?
   - How do we break this into phases?
   - What's the timeline?

---

### Step 4: Apply Best Practices and Organize Output

**Goal**: Create a token-efficient PRD and organize it in a clear folder structure.

#### Folder Structure

```
prds/
├── README.md                          # Index of all PRDs
├── prd-001-user-authentication/
│   ├── prd.md                        # Main PRD document
│   ├── research.md                   # User research findings
│   ├── technical-specs.md            # Technical specifications
│   ├── mockups/                      # Design mockups
│   └── decisions.md                  # Architecture decisions
├── prd-002-vector-search/
│   ├── prd.md
│   ├── research.md
│   ├── technical-specs.md
│   └── decisions.md
└── templates/
    └── prd-template.md               # Template for new PRDs
```

#### PRD Document Structure

Each PRD follows a token-efficient format:

```markdown
# [Feature Name] - PRD

**ID**: PRD-XXX
**Status**: Draft | In Review | Approved | Implemented
**Owner**: [Name]
**Created**: YYYY-MM-DD
**Last Updated**: YYYY-MM-DD

## Summary
[2-3 sentence overview optimized for AI parsing]

## Problem Statement
- User need: [Specific user problem]
- Business goal: [Why this matters]
- Success metric: [How we measure success]

## Target Users
- Primary: [Who benefits most]
- Secondary: [Additional users]

## Key Outcomes
1. [Outcome 1 - user benefit]
2. [Outcome 2 - business benefit]
3. [Outcome 3 - technical benefit]

## Requirements
### Must Have
- [ ] Requirement 1
- [ ] Requirement 2

### Should Have
- [ ] Requirement 3

### Could Have
- [ ] Requirement 4

## Technical Approach
- Stack: [Tech stack]
- Architecture: [High-level approach]
- Integration points: [Key integrations]

## Risks & Assumptions
- Risk: [Risk] | Mitigation: [Plan]
- Assumption: [Assumption] | Validation: [How to test]

## Success Criteria
- Metric 1: [Target]
- Metric 2: [Target]

## Implementation Plan
1. Phase 1: [Scope] - [Timeline]
2. Phase 2: [Scope] - [Timeline]

## Resources
- Design: [Link]
- Research: [Link]
- Technical specs: [Link]
```

---

## Expert-Driven Questioning Techniques

### The Discovery Framework

Combine expert approaches into a cohesive discovery process:

#### Phase 1: Problem Discovery (Cagan)
**Questions to Ask**:
1. What problem are we solving?
2. For whom?
3. Why now?
4. What happens if we don't solve it?

**Output**: Clear problem statement

#### Phase 2: Opportunity Assessment (Torres)
**Questions to Ask**:
1. What opportunities exist?
2. Which has the most impact?
3. What assumptions are we making?
4. How can we test these quickly?

**Output**: Prioritized opportunities with testable assumptions

#### Phase 3: Solution Definition (Biddle)
**Questions to Ask**:
1. What's the minimal viable solution?
2. What are the technical constraints?
3. Who needs to approve this?
4. How do we measure success?

**Output**: Scoped solution with clear success metrics

---

## Token Efficiency Guidelines

### Optimization Principles

1. **Use Structured Lists Over Paragraphs**
   ❌ Avoid: "The authentication system needs to support multiple providers including Google OAuth, GitHub, and email/password authentication. It should also handle session management and provide secure token storage."
   
   ✅ Prefer:
   ```markdown
   **Authentication Requirements**:
   - Providers: Google OAuth, GitHub, email/password
   - Session management: Required
   - Token storage: Secure, encrypted
   ```

2. **Frontload Key Information**
   - Summary at the top
   - Outcomes before implementation details
   - Critical paths before edge cases

3. **Use Semantic Markers**
   - `**Must Have**`: Critical requirements
   - `**Should Have**`: Important but not blocking
   - `**Could Have**`: Nice to have
   - `**Won't Have**`: Out of scope

4. **Eliminate Redundancy**
   - Link to external docs instead of copying
   - Reference technical specs instead of duplicating
   - Use acronyms consistently (define once)

5. **Optimize for Scanning**
   - Use headers for navigation
   - Bullet points for quick reading
   - Tables for comparisons
   - Code blocks for examples

### Token Count Targets

- **Summary**: 50-100 tokens
- **Problem Statement**: 100-200 tokens
- **Requirements**: 200-400 tokens
- **Technical Approach**: 150-300 tokens
- **Total PRD**: 600-1200 tokens (excluding appendices)

### AI-Friendly Formatting

```markdown
## Requirements

**Auth**: Multi-provider (Google, GitHub, email)
**Session**: JWT, 24h expiry, refresh tokens
**Security**: HTTPS only, CSRF protection, rate limiting
**UX**: Social login buttons, password reset flow
```

This format is:
- Easy to parse
- Quick to scan
- Clear hierarchy
- No redundant words

---

## PRD Organization Structure

### Repository Setup

Create a dedicated PRD management system:

```bash
# Create PRD directory structure
mkdir -p prds/templates
mkdir -p prds/archive

# Initialize README
cat > prds/README.md << 'EOF'
# Product Requirements Documents

## Active PRDs
- [PRD-001: User Authentication](./prd-001-user-authentication/prd.md)
- [PRD-002: Vector Search](./prd-002-vector-search/prd.md)

## Status Legend
- 🟡 Draft
- 🔵 In Review
- 🟢 Approved
- ✅ Implemented
- 📦 Archived
EOF
```

### PRD Naming Convention

- `prd-NNN-kebab-case-name/`
- Sequential numbering (001, 002, 003)
- Descriptive kebab-case names
- Consistent structure across all PRDs

### Version Control

Each PRD should be:
- Tracked in git
- Reviewed via pull requests
- Updated with clear change logs
- Archived when superseded

---

## Code Examples

### Repository Reconnaissance Script

See `repo_scan.js` for the full implementation. Key features:

```javascript
// Detect project type
const isNewProject = !fs.existsSync('package.json');

// Identify tech stack
const techStack = {
  framework: detectFramework(),
  language: detectLanguage(),
  database: detectDatabase(),
  deployment: detectDeployment()
};

// Analyze architecture
const architecture = {
  pattern: detectPattern(),
  structure: analyzeStructure(),
  integrations: findIntegrations()
};
```

### Creating a New PRD

```bash
# Use the helper script
node .claude/skills/ba-prd-skills/create_prd.js "User Authentication"

# Or manually
mkdir prds/prd-001-user-authentication
cp prds/templates/prd-template.md prds/prd-001-user-authentication/prd.md
```

---

## Best Practices

### 1. Always Start with Context

- Run reconnaissance before asking questions
- Review existing documentation
- Understand current architecture
- Identify constraints early

### 2. Focus on Outcomes, Not Outputs

- "Users can complete checkout in < 30s" (outcome)
- Not "Add a checkout button" (output)

### 3. Validate Assumptions Early

- Don't assume user needs
- Test risky assumptions first
- Gather evidence before committing

### 4. Keep PRDs Living Documents

- Update as you learn
- Track decisions and changes
- Archive when no longer relevant

### 5. Optimize for AI and Humans

- Humans need context and narrative
- AI needs structure and clarity
- Use both, but prioritize structure

### 6. Maintain Traceability

- Link PRDs to implementation
- Reference research and decisions
- Track metrics and outcomes

### 7. Use Templates Consistently

- Reduces cognitive load
- Ensures completeness
- Enables automation

---

## Templates & Resources

### Available Templates

1. **PRD Template** (`templates/prd-template.md`)
   - Standard PRD structure
   - Token-optimized format
   - Ready to use

2. **Research Template** (`templates/research-template.md`)
   - User interview guide
   - Findings synthesis
   - Insight extraction

3. **Technical Specs Template** (`templates/technical-specs-template.md`)
   - Architecture decisions
   - API specifications
   - Data models

### Expert Resources

**Marty Cagan**:
- Book: "Inspired: How to Create Tech Products Customers Love"
- Focus: Product discovery and validation
- Key takeaway: Fall in love with the problem, not the solution

**Teresa Torres**:
- Book: "Continuous Discovery Habits"
- Focus: Weekly user touchpoints and opportunity solution trees
- Key takeaway: Continuous discovery enables better decisions

**George Biddle**:
- Focus: Structured product management frameworks
- Key takeaway: Clear structure enables team alignment

### Additional Reading

- "The Lean Product Playbook" by Dan Olsen
- "User Story Mapping" by Jeff Patton
- "Continuous Discovery Habits" by Teresa Torres
- "Escaping the Build Trap" by Melissa Perri

---

## Token Efficiency Cheat Sheet

### Before (Verbose)
```markdown
The authentication system will need to support multiple authentication 
providers to give users flexibility in how they log in. We should support 
Google OAuth because many users have Google accounts, GitHub OAuth for 
developers, and also traditional email and password authentication for 
users who prefer not to use third-party providers.
```

**Token count**: ~60 tokens

### After (Optimized)
```markdown
**Auth Providers**:
- Google OAuth (most users have accounts)
- GitHub OAuth (developer audience)
- Email/password (privacy-conscious users)
```

**Token count**: ~25 tokens

**Savings**: ~58% reduction while maintaining clarity

---

## Quick Start Checklist

When creating a new PRD:

- [ ] Run repository reconnaissance (`repo_scan.js`)
- [ ] Review preliminary findings (`prelim_summary.md`)
- [ ] Identify project stage (new vs existing)
- [ ] Choose appropriate questioning framework
- [ ] Interview stakeholders and users
- [ ] Document problem statement and outcomes
- [ ] Define requirements using MoSCoW method
- [ ] Specify technical approach and risks
- [ ] Create PRD folder structure
- [ ] Fill in PRD template
- [ ] Optimize for token efficiency
- [ ] Link to research and specs
- [ ] Get stakeholder review
- [ ] Track in PRD index

---

## Example PRD

See `examples/prd-example.md` for a complete example of a token-efficient, expert-driven PRD following this framework.

---

## Version History

- **1.0** (December 2024) - Initial release
  - Repository reconnaissance
  - Expert-driven questioning
  - Token efficiency optimization
  - Folder structure organization

---

**Built with ❤️ by Callum Bir**

Inspired by the product wisdom of Marty Cagan, Teresa Torres, and George Biddle
