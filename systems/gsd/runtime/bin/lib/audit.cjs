/**
 * Open Artifact Audit — Cross-type unresolved state scanner
 *
 * Scans all .planning/ artifact categories for items with open/unresolved state.
 * Returns structured JSON for workflow consumption.
 * Called by: gsd-tools.cjs audit-open
 * Used by: /gsd:complete-milestone pre-close gate
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { toPosixPath } = require('./core.cjs');
const { platformReadSync } = require('./shell-command-projection.cjs');
const { planningDir } = require('./planning-workspace.cjs');
const { extractFrontmatter } = require('./frontmatter.cjs');
const { requireSafePath, sanitizeForDisplay } = require('./security.cjs');

/**
 * Scan .planning/debug/ for open sessions.
 * Open = status NOT in ['resolved', 'complete'].
 * Ignores the resolved/ subdirectory.
 */
function scanDebugSessions(planDir) {
  const debugDir = path.join(planDir, 'debug');
  if (!fs.existsSync(debugDir)) return [];

  const results = [];
  let files;
