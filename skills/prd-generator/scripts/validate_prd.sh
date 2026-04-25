#!/bin/bash

# PRD Validation Script
# Checks PRD completeness and quality

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
VERBOSE=false
SECTIONS="all"

# Usage function
usage() {
    echo "Usage: $0 <prd_file.md> [options]"
    echo ""
    echo "Options:"
    echo "  --verbose           Show detailed suggestions"
    echo "  --sections <list>   Check specific sections only (comma-separated)"
    echo "                      e.g., --sections user-stories,metrics"
    echo ""
    echo "Example:"
    echo "  $0 my_prd.md"
    echo "  $0 my_prd.md --verbose"
    echo "  $0 my_prd.md --sections user-stories,metrics"
    exit 1
}

# Parse arguments
if [ $# -lt 1 ]; then
    usage
fi

PRD_FILE="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --sections)
            SECTIONS="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            ;;
    esac
done

# Check if file exists
if [ ! -f "$PRD_FILE" ]; then
    echo -e "${RED}✗ Error: File not found: $PRD_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        PRD Validation Report           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "File: ${BLUE}$PRD_FILE${NC}"
echo ""

# Counters
ISSUES_FOUND=0
WARNINGS=0
CHECKS_PASSED=0

# Function to check section exists
check_section() {
    local section_name="$1"
    local section_pattern="$2"
    local required="$3"

    if grep -q "$section_pattern" "$PRD_FILE"; then
        echo -e "${GREEN}✓${NC} $section_name section found"
        ((CHECKS_PASSED++))
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗${NC} $section_name section missing (REQUIRED)"
            ((ISSUES_FOUND++))
        else
            echo -e "${YELLOW}⚠${NC} $section_name section missing (recommended)"
            ((WARNINGS++))
        fi
        return 1
    fi
}

# Function to check content quality
check_content() {
    local check_name="$1"
    local pattern="$2"
    local error_msg="$3"

    if grep -q "$pattern" "$PRD_FILE"; then
        echo -e "${YELLOW}⚠${NC} $check_name: $error_msg"
        ((WARNINGS++))
        return 1
    else
        echo -e "${GREEN}✓${NC} $check_name passed"
        ((CHECKS_PASSED++))
        return 0
    fi
}

echo -e "${BLUE}━━━ Section Completeness ━━━${NC}"
echo ""

# Required sections
check_section "Problem Statement" "##.*Problem Statement" true
check_section "Goals & Objectives" "##.*Goals.*Objectives" true
check_section "User Stories" "##.*User Stories" true
check_section "Success Metrics" "##.*Success Metrics" true
check_section "Scope" "##.*Scope" true

echo ""
echo -e "${BLUE}━━━ Recommended Sections ━━━${NC}"
echo ""

# Recommended sections
check_section "Executive Summary" "##.*Executive Summary" false
check_section "User Personas" "##.*User Personas" false
check_section "Technical Considerations" "##.*Technical Considerations" false
check_section "Design & UX Requirements" "##.*Design.*UX" false
check_section "Timeline & Milestones" "##.*Timeline.*Milestones" false
check_section "Risks & Mitigation" "##.*Risks.*Mitigation" false

echo ""
echo -e "${BLUE}━━━ Content Quality Checks ━━━${NC}"
echo ""

# Check for placeholder text
check_content "Placeholder text" "\[.*\]" "Contains placeholder brackets - fill in all placeholders"

# Check for TBD/TODO
check_content "TBD markers" "TBD\|TODO" "Contains TBD/TODO markers - resolve all open items"

# Check for empty sections
if grep -q "^##.*\n\n##" "$PRD_FILE"; then
    echo -e "${YELLOW}⚠${NC} Empty sections detected"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓${NC} No empty sections"
    ((CHECKS_PASSED++))
fi

# Check for user story format
echo ""
echo -e "${BLUE}━━━ User Story Validation ━━━${NC}"
echo ""

USER_STORY_COUNT=$(grep -c "As a.*I want.*So that" "$PRD_FILE" || true)
if [ "$USER_STORY_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Found $USER_STORY_COUNT properly formatted user stories"
    ((CHECKS_PASSED++))

    # Check for acceptance criteria
    AC_COUNT=$(grep -c "Acceptance Criteria" "$PRD_FILE" || true)
    if [ "$AC_COUNT" -ge "$USER_STORY_COUNT" ]; then
        echo -e "${GREEN}✓${NC} All user stories have acceptance criteria"
        ((CHECKS_PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} Some user stories may be missing acceptance criteria"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗${NC} No properly formatted user stories found"
    echo -e "  Expected format: 'As a [user], I want [action], So that [benefit]'"
    ((ISSUES_FOUND++))
fi

# Check for success metrics
echo ""
echo -e "${BLUE}━━━ Metrics Validation ━━━${NC}"
echo ""

if grep -q "KPI\|metric\|measure" "$PRD_FILE"; then
    echo -e "${GREEN}✓${NC} Success metrics mentioned"
    ((CHECKS_PASSED++))

    # Check for quantifiable metrics
    if grep -q "[0-9]\+%" "$PRD_FILE"; then
        echo -e "${GREEN}✓${NC} Contains quantifiable metrics (percentages found)"
        ((CHECKS_PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} Consider adding quantifiable targets (%, numbers, etc.)"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗${NC} Success metrics not clearly defined"
    ((ISSUES_FOUND++))
fi

# Check for scope definition
echo ""
echo -e "${BLUE}━━━ Scope Validation ━━━${NC}"
echo ""

IN_SCOPE=false
OUT_SCOPE=false

if grep -qi "in scope\|in-scope" "$PRD_FILE"; then
    echo -e "${GREEN}✓${NC} In-scope section defined"
    IN_SCOPE=true
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} In-scope section not clearly defined"
    ((WARNINGS++))
fi

if grep -qi "out of scope\|out-of-scope" "$PRD_FILE"; then
    echo -e "${GREEN}✓${NC} Out-of-scope section defined"
    OUT_SCOPE=true
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Out-of-scope section not defined (prevents scope creep)"
    ((WARNINGS++))
fi

# Document quality checks
echo ""
echo -e "${BLUE}━━━ Document Quality ━━━${NC}"
echo ""

# Check word count
WORD_COUNT=$(wc -w < "$PRD_FILE")
echo -e "Word count: $WORD_COUNT"

if [ "$WORD_COUNT" -lt 500 ]; then
    echo -e "${YELLOW}⚠${NC} Document seems short for a PRD (< 500 words)"
    ((WARNINGS++))
elif [ "$WORD_COUNT" -gt 5000 ]; then
    echo -e "${YELLOW}⚠${NC} Document is very long (> 5000 words) - consider splitting"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓${NC} Document length appropriate"
    ((CHECKS_PASSED++))
fi

# Check for headers hierarchy
if grep -q "^#\s" "$PRD_FILE"; then
    echo -e "${GREEN}✓${NC} Proper heading structure"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Check heading hierarchy (should start with # not ##)"
    ((WARNINGS++))
fi

# Final Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           Validation Summary           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Checks passed:  ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Warnings:       ${YELLOW}$WARNINGS${NC}"
echo -e "Issues found:   ${RED}$ISSUES_FOUND${NC}"
echo ""

# Recommendations
if [ "$VERBOSE" = true ]; then
    echo -e "${BLUE}━━━ Recommendations ━━━${NC}"
    echo ""
    echo "1. Ensure all required sections are present"
    echo "2. Fill in all placeholder text marked with [brackets]"
    echo "3. Use the user story format: 'As a [user], I want [action], So that [benefit]'"
    echo "4. Include specific, measurable success metrics"
    echo "5. Clearly define what's in and out of scope"
    echo "6. Add acceptance criteria for all user stories"
    echo "7. Review with stakeholders before finalizing"
    echo ""
fi

# Exit code
if [ "$ISSUES_FOUND" -gt 0 ]; then
    echo -e "${RED}❌ PRD validation failed${NC}"
    echo -e "   Address $ISSUES_FOUND critical issue(s) before proceeding"
    exit 1
elif [ "$WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}⚠ PRD validation passed with warnings${NC}"
    echo -e "   Consider addressing $WARNINGS warning(s) to improve quality"
    exit 0
else
    echo -e "${GREEN}✅ PRD validation passed!${NC}"
    echo -e "   Document looks ready for stakeholder review"
    exit 0
fi
