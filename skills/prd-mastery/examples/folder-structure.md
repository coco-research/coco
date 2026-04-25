# PRD Folder Structure Guide

This guide explains how to organize multiple PRDs and related artifacts in your repository using the PRD Mastery skill's recommended structure.

---

## Overview

The PRD folder structure is designed to:
- Keep all product documentation organized and discoverable
- Maintain clear separation between different features/initiatives
- Support easy navigation and cross-referencing
- Scale from single PRD to hundreds of PRDs
- Enable automated tooling and analysis

---

## Recommended Structure

```
prds/
├── README.md                              # Index of all PRDs
├── templates/                             # Reusable templates
│   ├── prd-template.md
│   ├── research-template.md
│   └── technical-specs-template.md
├── archive/                               # Completed/deprecated PRDs
│   └── 2023/
│       └── prd-001-old-feature/
├── prd-001-ai-code-review/               # Individual PRD folder
│   ├── prd.md                            # Main PRD document
│   ├── research.md                       # User research findings
│   ├── technical-specs.md                # Technical specifications
│   ├── decisions.md                      # Architecture decisions
│   ├── mockups/                          # Design mockups
│   │   ├── dashboard.png
│   │   └── comment-template.png
│   └── metrics.md                        # Success metrics tracking
├── prd-002-vector-search/
│   ├── prd.md
│   ├── research.md
│   ├── technical-specs.md
│   └── adrs/                             # Architecture Decision Records
│       ├── 001-embedding-model.md
│       └── 002-vector-database.md
└── prd-003-user-authentication/
    ├── prd.md
    ├── research.md
    ├── technical-specs.md
    └── security-review.md
```

---

## File Naming Conventions

### PRD Folders
- Format: `prd-NNN-kebab-case-name/`
- Sequential numbering: `001`, `002`, `003`, etc.
- Descriptive names: Clearly indicate the feature
- Examples:
  - ✅ `prd-001-ai-code-review/`
  - ✅ `prd-042-payment-integration/`
  - ❌ `prd-1/` (no leading zeros)
  - ❌ `PRD_001_ai_review/` (wrong case/separator)

### Core Files
- `prd.md` - Main PRD document (always required)
- `research.md` - User research (optional but recommended)
- `technical-specs.md` - Technical details (optional but recommended)
- `decisions.md` or `adrs/` - Architecture decisions (optional)
- `metrics.md` - Tracking post-launch metrics (optional)

---

## Root README.md

The `prds/README.md` serves as the index for all PRDs. Keep it updated:

```markdown
# Product Requirements Documents

## Active PRDs

| ID | Feature | Owner | Status | Created | Updated |
|----|---------|-------|--------|---------|---------|
| [PRD-001](./prd-001-ai-code-review/prd.md) | AI Code Review | Jane | 🟢 Approved | 2024-12-01 | 2024-12-15 |
| [PRD-002](./prd-002-vector-search/prd.md) | Vector Search | Bob | 🔵 In Review | 2024-12-10 | 2024-12-18 |
| [PRD-003](./prd-003-user-auth/prd.md) | User Auth | Alice | 🟡 Draft | 2024-12-20 | 2024-12-22 |

## Status Legend
- 🟡 **Draft** - Work in progress
- 🔵 **In Review** - Awaiting stakeholder approval
- 🟢 **Approved** - Ready for implementation
- ✅ **Implemented** - Live in production
- 📦 **Archived** - Completed or superseded

## By Category

### AI & Agents
- PRD-001: AI Code Review
- PRD-002: Vector Search

### Infrastructure
- PRD-003: User Authentication

## Quick Links
- [Templates](./templates/)
- [Archive](./archive/)
```

---

## Individual PRD Folder Structure

Each PRD folder should contain:

### Required Files

1. **prd.md** - The main PRD document
   - Use the template from `templates/prd-template.md`
   - Keep token-efficient and well-structured
   - Update as the feature evolves

### Recommended Files

2. **research.md** - User research findings
   - Interview notes and insights
   - User personas
   - Validated assumptions
   - Opportunity mapping

3. **technical-specs.md** - Detailed technical specifications
   - Architecture diagrams
   - API specifications
   - Data models
   - Security considerations
   - Performance requirements

4. **decisions.md** or **adrs/** - Architecture Decision Records
   - Document why decisions were made
   - Include context, options considered, and rationale
   - Link to relevant discussions

### Optional Files

5. **metrics.md** - Post-launch metrics tracking
   - Baseline measurements
   - Current metrics
   - Analysis and insights

6. **mockups/** - Design mockups and wireframes
   - UI designs
   - User flows
   - Prototypes

7. **experiments/** - A/B test plans and results
   - Hypothesis
   - Test design
   - Results and learnings

---

## Archive Structure

Move completed or deprecated PRDs to `archive/`:

```
archive/
├── 2023/
│   ├── prd-001-old-feature/
│   └── prd-002-deprecated-feature/
└── 2024/
    └── prd-042-completed-feature/
```

**When to Archive**:
- Feature is fully implemented and stable (3+ months)
- PRD is superseded by a new version
- Feature is deprecated or removed

**Archive Process**:
1. Add "Archived" status to PRD
2. Move entire folder to appropriate year
3. Update main README.md
4. Keep reference for historical context

---

## Cross-References

### Linking Between PRDs

Use relative links to reference related PRDs:

```markdown
## Related PRDs
- [PRD-001: AI Code Review](../prd-001-ai-code-review/prd.md)
- [PRD-005: Test Automation](../prd-005-test-automation/prd.md)
```

### Linking to Implementation

Link PRDs to actual implementation:

```markdown
## Implementation
- **Code**: [src/features/code-review](../../src/features/code-review)
- **Tests**: [tests/code-review](../../tests/code-review)
- **Docs**: [docs/code-review.md](../../docs/code-review.md)
```

---

## Version Control Best Practices

### Git Workflow

1. **New PRDs**: Create on feature branch
   ```bash
   git checkout -b prd/001-ai-code-review
   mkdir prds/prd-001-ai-code-review
   cp prds/templates/prd-template.md prds/prd-001-ai-code-review/prd.md
   # Edit the PRD
   git add prds/prd-001-ai-code-review/
   git commit -m "Add PRD-001: AI Code Review"
   ```

2. **Updates**: Use pull requests for changes
   ```bash
   git checkout -b prd/001-update-scope
   # Update PRD files
   git commit -m "PRD-001: Update scope based on stakeholder feedback"
   ```

3. **Approvals**: Tag approved versions
   ```bash
   git tag prd-001-v1.0
   git push origin prd-001-v1.0
   ```

### Commit Messages

Follow conventional commits for PRD changes:
- `prd: Add PRD-042: Payment Integration`
- `prd: Update PRD-001 success metrics`
- `prd: Archive PRD-007: Legacy feature`

---

## Automation Opportunities

### Scripts to Create

1. **Create New PRD**
   ```bash
   ./scripts/create-prd.sh "AI Code Review"
   # Creates folder, copies template, assigns next ID
   ```

2. **Update Index**
   ```bash
   ./scripts/update-prd-index.sh
   # Scans all PRDs, regenerates README.md
   ```

3. **Archive PRD**
   ```bash
   ./scripts/archive-prd.sh 001
   # Moves PRD to archive, updates README
   ```

### CI/CD Integration

- Validate PRD structure on PR
- Check all links are valid
- Ensure README.md is up to date
- Generate metrics reports

---

## Maintenance

### Regular Reviews

**Monthly**:
- [ ] Update PRD statuses in README.md
- [ ] Archive completed PRDs (3+ months old)
- [ ] Review and close open questions
- [ ] Update metrics for active features

**Quarterly**:
- [ ] Clean up orphaned files
- [ ] Update templates based on learnings
- [ ] Review and improve structure
- [ ] Archive year-old PRDs

---

## Example Folder Structures

### Simple Project (1-10 PRDs)
```
prds/
├── README.md
├── templates/
├── prd-001-feature-a/
├── prd-002-feature-b/
└── prd-003-feature-c/
```

### Medium Project (10-50 PRDs)
```
prds/
├── README.md
├── templates/
├── archive/
│   └── 2023/
├── prd-001-feature-a/
├── prd-002-feature-b/
├── ...
└── prd-042-feature-z/
```

### Large Project (50+ PRDs)
```
prds/
├── README.md
├── templates/
├── archive/
│   ├── 2022/
│   ├── 2023/
│   └── 2024/
├── active/
│   ├── prd-100-feature-a/
│   └── prd-101-feature-b/
├── approved/
│   ├── prd-095-feature-x/
│   └── prd-098-feature-y/
└── draft/
    └── prd-102-feature-z/
```

---

## Tips for Success

1. **Start Simple**: Don't over-engineer - begin with basic structure
2. **Be Consistent**: Use templates and naming conventions
3. **Keep Updated**: Update README.md when PRDs change status
4. **Link Everything**: Cross-reference PRDs, code, docs
5. **Archive Regularly**: Don't let old PRDs clutter active list
6. **Document Decisions**: Capture the "why" not just the "what"
7. **Make Discoverable**: Good naming and clear index
8. **Version Control**: Track all changes with meaningful commits

---

## Getting Started Checklist

Starting a new PRD repository:

- [ ] Create `prds/` directory
- [ ] Copy templates from PRD Mastery skill
- [ ] Create README.md with status legend
- [ ] Set up folder structure (basic or advanced)
- [ ] Add `.gitkeep` files for empty directories
- [ ] Document your conventions (this file!)
- [ ] Create first PRD using template
- [ ] Set up automation scripts (optional)
- [ ] Configure CI checks (optional)
- [ ] Train team on structure and process

---

*This folder structure guide is part of the PRD Mastery skill*
