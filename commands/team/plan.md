# /team plan — Planning Pipeline

> Called by team.md router when action is `plan`.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | technical-analyst, business-analyst, domain-researcher | 2-3 |
| L2 | senior-pm, (domain-dependent engineers), jira-specialist (if Jira workflow planning) | 2-3 |
| L3 | domain-accuracy, doc-quality | 2 |
| L4 | principal-pm | 1 |

## Pipeline Customization

### Layer 1: Scope Research
L1 agents assess:
- Current state of the system/project
- What's already been built vs what's needed
- Dependencies and sequencing constraints
- Risk areas that need mitigation in the plan

### Layer 2: Plan Creation
- **Mode:** `default` (creates plan documents, not source code)
- Agents produce structured plans with:
  - Phase breakdown with clear goals
  - Task decomposition within each phase
  - Dependency graph (what blocks what)
  - Effort estimates and sequencing
  - Success criteria per phase

**Toolkit integration:**
- Check team-toolkit.md for "Project Orchestration" entry
- If GSD active → create PLAN.md files compatible with GSD format (frontmatter: wave, depends_on, files_modified, autonomous, requirements, must_haves)
- If no GSD → create standalone plan documents

### GSD Integration (C4)
When `.planning/` exists:
- Read ROADMAP.md and REQUIREMENTS.md for context
- Plans follow GSD conventions
- Output: `.planning/phases/{phase_dir}/PLAN.md` files with proper frontmatter
- Compatible with `/gsd:execute-phase`

### Layer 3: Plan Validation
L3 agents check:
- Are all requirements covered?
- Is the task decomposition achievable?
- Are dependencies correctly mapped?
- Are estimates realistic?
- Are success criteria measurable?

### Layer 4: Plan Approval
Principal reviews for:
- Strategic alignment
- Resource efficiency
- Risk coverage
- Sequencing optimality
