'use strict';

const fs = require('fs');
const path = require('path');
const { execTool, execGit, platformWriteSync } = require('./shell-command-projection.cjs');

// ─── Config Gate ─────────────────────────────────────────────────────────────

/**
 * Check whether graphify is enabled in the project config.
 * Reads config.json directly via fs. Returns false by default
 * (when no config, no graphify key, or on error).
 *
 * @param {string} planningDir - Path to .planning directory
 * @returns {boolean}
 */
function isGraphifyEnabled(planningDir) {
  try {
    const configPath = path.join(planningDir, 'config.json');
    if (!fs.existsSync(configPath)) return false;
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    if (config && config.graphify && config.graphify.enabled === true) return true;
    return false;
  } catch (_e) {
    return false;
  }
}

/**
 * Return the standard disabled response object.
 * @returns {{ disabled: true, message: string }}
 */
function disabledResponse() {
  return { disabled: true, message: 'graphify is not enabled. Enable with: gsd-tools config-set graphify.enabled true' };
}

// ─── Subprocess Helper ───────────────────────────────────────────────────────

/**
 * Execute graphify CLI as a subprocess with proper env and timeout handling.
 *
 * @param {string} cwd - Working directory for the subprocess
 * @param {string[]} args - Arguments to pass to graphify
