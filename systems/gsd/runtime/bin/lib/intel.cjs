/**
 * lib/intel.cjs -- Intel storage and query operations for GSD.
 *
 * Provides a persistent, queryable intelligence system for project metadata.
 * Intel files live in .planning/intel/ and store structured data about
 * the project's files, APIs, dependencies, architecture, and tech stack.
 *
 * All public functions gate on intel.enabled config (no-op when false).
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { platformWriteSync, platformReadSync, platformEnsureDir } = require('./shell-command-projection.cjs');

// ─── Constants ───────────────────────────────────────────────────────────────

const INTEL_DIR = '.planning/intel';

const INTEL_FILES = {
  files: 'file-roles.json',
  apis: 'api-map.json',
  deps: 'dependency-graph.json',
  arch: 'arch-decisions.json',
  stack: 'stack.json'
};

// ─── Internal helpers ────────────────────────────────────────────────────────

/**
 * Ensure the intel directory exists under the given planning dir.
 *
 * @param {string} planningDir - Path to .planning directory
 * @returns {string} Full path to .planning/intel/
 */
function ensureIntelDir(planningDir) {
  const intelPath = path.join(planningDir, 'intel');
  platformEnsureDir(intelPath);
  return intelPath;
}

/**
 * Check whether intel is enabled in the project config.
 * Reads config.json directly via fs. Returns false by default
 * (when no config, no intel key, or on error).
 *
 * @param {string} planningDir - Path to .planning directory
 * @returns {boolean}
 */
function isIntelEnabled(planningDir) {
  try {
    const configPath = path.join(planningDir, 'config.json');
    const raw = platformReadSync(configPath);
    if (raw === null) return false;
    const config = JSON.parse(raw);
    if (config && config.intel && config.intel.enabled === true) return true;
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
  return { disabled: true, message: 'Intel system disabled. Set intel.enabled=true in config.json to activate.' };
}

/**
 * Resolve full path to an intel file.
 * @param {string} planningDir
 * @param {string} filename
 * @returns {string}
 */
function intelFilePath(planningDir, filename) {
  return path.join(planningDir, 'intel', filename);
}

/**
 * Safely read and parse a JSON intel file.
 * Returns null if file doesn't exist or can't be parsed.
 *
 * @param {string} filePath
 * @returns {object|null}
 */
function safeReadJson(filePath) {
  try {
    const raw = platformReadSync(filePath);
    if (raw === null) return null;
    return JSON.parse(raw);
  } catch (_e) {
    return null;
  }
}

/**
 * Compute SHA-256 hash of a file's contents.
 * Returns null if the file doesn't exist.
 *
 * @param {string} filePath
 * @returns {string|null}
 */
function hashFile(filePath) {
  try {
    const content = platformReadSync(filePath);
    if (content === null) return null;
    return crypto.createHash('sha256').update(content).digest('hex');
  } catch (_e) {
    return null;
  }
}

/**
 * Search for a term (case-insensitive) in a JSON object's keys and string values.
 * Returns an array of matching entries.
 *
 * @param {object} data - The JSON data (expects { _meta, entries } or flat object)
 * @param {string} term - Search term
 * @returns {Array<{ key: string, value: * }>}
 */
function searchJsonEntries(data, term) {
  if (!data || typeof data !== 'object') return [];

  const entries = data.entries || data;
  if (!entries || typeof entries !== 'object') return [];

  const lowerTerm = term.toLowerCase();
  const matches = [];

  for (const [key, value] of Object.entries(entries)) {
    if (key === '_meta') continue;

    // Check key match
    if (key.toLowerCase().includes(lowerTerm)) {
      matches.push({ key, value });
      continue;
    }

    // Check string value match (recursive for objects)
    if (matchesInValue(value, lowerTerm)) {
      matches.push({ key, value });
    }
  }

  return matches;
}

/**
 * Recursively check if a term appears in any string value.
 *
 * @param {*} value
 * @param {string} lowerTerm
 * @returns {boolean}
 */
