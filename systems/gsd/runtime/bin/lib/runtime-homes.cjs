'use strict';

/**
 * runtime-homes.cjs — canonical runtime → global config/skills directory mapping.
 *
 * Single source of truth for resolving the global config base directory and
 * the correct global skills directory for every GSD-supported runtime.
 *
 * Mirrors the logic in bin/install.js getGlobalDir() but as a pure,
 * side-effect-free module safe to require() at any point without triggering
 * the installer. bin/install.js is the authoritative source — keep in sync.
 *
 * Runtime-specific notes:
 *   hermes  — GSD skills nest under skills/gsd/<skillName>/ (not the flat
 *             skills/<skillName>/ layout used by all other runtimes). This
 *             collapses 86 skill entries into one category in Hermes' system
 *             prompt (#2841).
 *   cline   — Rules-based; commands are embedded in .clinerules. Cline does
 *             not use a skills/ directory. getGlobalSkillDir() returns null
 *             for cline so the caller can emit an appropriate warning.
 */

const os = require('os');
const path = require('path');

/**
 * Expand a leading ~ to os.homedir().
 * @param {string} p
 * @returns {string}
 */
function expandTilde(p) {
  if (!p) return p;
  if (p.startsWith('~/') || p === '~') return path.join(os.homedir(), p.slice(1));
  return p;
}

/**
 * Return the global config base directory for the given runtime.
 * Respects the same env-var overrides as bin/install.js getGlobalDir().
 *
 * @param {string} runtime
 * @returns {string} Absolute path to the runtime's global config directory
 */
function getGlobalConfigDir(runtime) {
  const home = os.homedir();
  const env = process.env;

