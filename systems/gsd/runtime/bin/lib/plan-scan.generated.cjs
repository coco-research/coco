'use strict';

/**
 * GENERATED FILE — DO NOT EDIT.
 *
 * Source: sdk/src/query/plan-scan.ts
 * Regenerate: cd sdk && npm run gen:plan-scan
 *
 * Plan Scan Module — detects plan and summary files in a phase directory.
 * Supports both flat (pre-#3139) and nested (post-#3139) layouts.
 */

const { existsSync, readdirSync } = require('node:fs');
const { join } = require('node:path');

// Excluded derivative files
const PLAN_OUTLINE_RE = /-OUTLINE\.md$/i;
const PLAN_PRE_BOUNCE_RE = /\.pre-bounce\.md$/i;

function isRootPlanFile(fileName) {
    if (PLAN_OUTLINE_RE.test(fileName))
        return false;
    if (PLAN_PRE_BOUNCE_RE.test(fileName))
        return false;
    if (fileName.endsWith('-PLAN.md') || fileName === 'PLAN.md')
        return true;
    return /\.md$/i.test(fileName) && /PLAN/i.test(fileName);
}

function isNestedPlanFile(fileName) {
    if (PLAN_OUTLINE_RE.test(fileName))
        return false;
    if (PLAN_PRE_BOUNCE_RE.test(fileName))
        return false;
    return /^PLAN-\d+.*\.md$/i.test(fileName) || /-PLAN-\d+.*\.md$/i.test(fileName);
}

function isRootSummaryFile(fileName) {
    return fileName.endsWith('-SUMMARY.md') || fileName === 'SUMMARY.md';
}
