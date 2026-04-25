#!/bin/bash

# PRD Generator Script
# Interactive workflow for generating Product Requirements Documents

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     PRD Generator - Interactive Mode    ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Check if template exists
TEMPLATE_FILE="$SKILL_DIR/references/prd_template.md"
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}✗ Error: PRD template not found at $TEMPLATE_FILE${NC}"
    exit 1
fi

# Function to prompt for input
prompt_input() {
    local prompt="$1"
    local var_name="$2"
    local required="$3"

    while true; do
        echo -e "${YELLOW}${prompt}${NC}"
        read -r input

        if [ -n "$input" ]; then
            eval "$var_name='$input'"
            break
        elif [ "$required" != "true" ]; then
            eval "$var_name=''"
            break
        else
            echo -e "${RED}This field is required. Please provide a value.${NC}"
        fi
    done
}

# Gather basic information
echo -e "${GREEN}Step 1: Basic Information${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

prompt_input "Feature/Product Name:" PRODUCT_NAME true
prompt_input "One-line Description:" DESCRIPTION true
prompt_input "Output Filename (default: ${PRODUCT_NAME// /_}_prd.md):" OUTPUT_FILE false

# Set default output file if not provided
if [ -z "$OUTPUT_FILE" ]; then
    OUTPUT_FILE="${PRODUCT_NAME// /_}_prd.md"
    OUTPUT_FILE=$(echo "$OUTPUT_FILE" | tr '[:upper:]' '[:lower:]')
fi

echo ""
echo -e "${GREEN}Step 2: Problem & Context${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

prompt_input "What problem are you solving?" PROBLEM true
prompt_input "Who are the primary users?" PRIMARY_USERS true
prompt_input "What are the key business goals?" BUSINESS_GOALS true

echo ""
echo -e "${GREEN}Step 3: Success & Scope${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

prompt_input "How will you measure success?" SUCCESS_METRICS true
prompt_input "Target launch date (or 'TBD'):" TIMELINE false
prompt_input "What's explicitly OUT of scope?" OUT_OF_SCOPE false

echo ""
echo -e "${GREEN}Step 4: PRD Type${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Select PRD type:"
echo "  1) Standard (comprehensive)"
echo "  2) Lean (streamlined)"
echo "  3) One-Pager (executive summary)"
echo ""

while true; do
    read -p "Enter choice (1-3): " prd_type
    case $prd_type in
        1) PRD_TYPE="standard"; break;;
        2) PRD_TYPE="lean"; break;;
        3) PRD_TYPE="one-pager"; break;;
        *) echo -e "${RED}Invalid choice. Please enter 1, 2, or 3.${NC}";;
    esac
done

# Generate PRD
echo ""
echo -e "${BLUE}Generating PRD...${NC}"
echo ""

# Create PRD from template
cat > "$OUTPUT_FILE" << EOF
# Product Requirements Document: $PRODUCT_NAME

**Status:** Draft
**Author:** $(whoami)
**Date:** $(date +%Y-%m-%d)
**Last Updated:** $(date +%Y-%m-%d)

---

## Executive Summary

$DESCRIPTION

This PRD outlines the requirements for $PRODUCT_NAME, addressing the need to $PROBLEM for $PRIMARY_USERS.

---

## Problem Statement

### The Problem

$PROBLEM

### Impact

Without this feature/product, users experience [describe pain points].

### Why Now?

$BUSINESS_GOALS

---

## Goals & Objectives

### Business Goals

$BUSINESS_GOALS

### User Goals

- [User goal 1]
- [User goal 2]
- [User goal 3]

### Success Criteria

$SUCCESS_METRICS

---

## User Personas

### Primary User: $PRIMARY_USERS

**Demographics:**
- [Add demographic info]

**Behaviors:**
- [Add behavioral patterns]

**Needs:**
- [Add key needs]

**Pain Points:**
- [Add pain points]

---

## User Stories & Requirements

### Core User Stories

#### Story 1: [Feature Name]

**User Story:**
\`\`\`
As a [$PRIMARY_USERS],
I want to [action],
So that [benefit].
\`\`\`

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

**Priority:** Must Have

---

#### Story 2: [Feature Name]

**User Story:**
\`\`\`
As a [user type],
I want to [action],
So that [benefit].
\`\`\`

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

**Priority:** Should Have

---

## Success Metrics

### Key Performance Indicators (KPIs)

$SUCCESS_METRICS

### Measurement Plan

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| [Metric 1] | [Current value] | [Target value] | [How to measure] |
| [Metric 2] | [Current value] | [Target value] | [How to measure] |

---

## Scope

### In Scope

- [Feature/capability 1]
- [Feature/capability 2]
- [Feature/capability 3]

### Out of Scope

$OUT_OF_SCOPE

- [Explicitly excluded item 1]
- [Explicitly excluded item 2]

### Future Considerations

- [Potential future enhancement 1]
- [Potential future enhancement 2]

---

## Technical Considerations

### Architecture

[High-level technical approach]

### Dependencies

- **External APIs:** [List APIs]
- **Services:** [List services]
- **Libraries:** [List libraries]

### Security Requirements

- [Security requirement 1]
- [Security requirement 2]

### Performance Requirements

- [Performance requirement 1]
- [Performance requirement 2]

### Data Considerations

- [Data storage needs]
- [Data migration needs]
- [Privacy considerations]

---

## Design & UX Requirements

### User Experience

[Describe key UX principles and patterns]

### Visual Design

[Reference design system, mockups, or wireframes]

### Accessibility

- WCAG 2.1 Level AA compliance required
- Keyboard navigation support
- Screen reader compatibility

### Responsive Design

- Mobile support: [Yes/No/Details]
- Tablet support: [Yes/No/Details]
- Desktop support: [Yes/No/Details]

---

## Timeline & Milestones

**Target Launch:** $TIMELINE

### Phases

| Phase | Deliverables | Target Date |
|-------|-------------|-------------|
| Discovery | Requirements finalized, designs approved | [Date] |
| Development | Core functionality complete | [Date] |
| Testing | QA complete, bugs resolved | [Date] |
| Launch | Feature live in production | $TIMELINE |

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|------------|-------------------|
| [Risk 1] | High/Med/Low | High/Med/Low | [How to mitigate] |
| [Risk 2] | High/Med/Low | High/Med/Low | [How to mitigate] |

---

## Dependencies & Assumptions

### Dependencies

- [Dependency 1]
- [Dependency 2]

### Assumptions

- [Assumption 1]
- [Assumption 2]

---

## Open Questions

- [ ] [Question 1]
- [ ] [Question 2]
- [ ] [Question 3]

---

## Stakeholder Sign-Off

| Stakeholder | Role | Status | Date |
|------------|------|--------|------|
| [Name] | Product Lead | Pending | - |
| [Name] | Engineering Lead | Pending | - |
| [Name] | Design Lead | Pending | - |

---

## Appendix

### References

- [Reference 1]
- [Reference 2]

### Change Log

| Date | Author | Changes |
|------|--------|---------|
| $(date +%Y-%m-%d) | $(whoami) | Initial draft |

EOF

echo -e "${GREEN}✓ PRD generated successfully!${NC}"
echo ""
echo -e "Output file: ${BLUE}$OUTPUT_FILE${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review and fill in the placeholder sections"
echo "  2. Add specific user stories and acceptance criteria"
echo "  3. Attach mockups/wireframes if available"
echo "  4. Share with stakeholders for review"
echo "  5. Run validation: scripts/validate_prd.sh $OUTPUT_FILE"
echo ""
echo -e "${GREEN}✓ Done!${NC}"
