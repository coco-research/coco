'use strict';

const path = require('path');
const fs = require('fs');
// Use non-destructured access so test-time mock.method(childProcess, 'spawnSync')
// can intercept calls from this seam — destructured imports capture references
// at load time and become un-mockable.
const childProcess = require('child_process');

/**
 * Shell Command Projection Module
 *
 * Tracer-bullet seam for runtime-aware projection of serialized command text
 * that GSD writes into runtime config or prints for copy/paste. This module
 * does NOT execute commands; it only renders command text for external shells
 * and runtimes.
 */

/**
 * Return true when a managed hook command must be prefixed with PowerShell's
 * call operator so a quoted executable token is invokable by the target
 * runtime/shell combination.
 *
 * Current evidence-backed policy:
 * - Gemini on Windows requires `& ` for quoted node/bash runners.
 * - Claude Code on Windows does NOT: its hook commands execute under bash/Git
 *   Bash and `& ` breaks there (#3413).
 *
 * Keep the policy conservative until another runtime has a verified need.
 */
function hookCommandNeedsPowerShellCallOperator(opts = {}) {
  const platform = opts.platform || process.platform;
  const runtime = opts.runtime || 'generic';
  return platform === 'win32' && runtime === 'gemini';
}

/**
 * Project a fully-assembled hook command string for the target runtime.
 */
function formatHookCommandForRuntime(command, opts = {}) {
  return hookCommandNeedsPowerShellCallOperator(opts) ? `& ${command}` : command;
}

/**
 * Project a managed hook script path token for serialized shell commands.
 * Windows managed hook commands normalize to forward slashes so the same path
 * survives JSON/TOML/config surfaces consistently.
 */
function formatManagedHookScriptToken(scriptPath, opts = {}) {
  const platform = opts.platform || process.platform;
  if (platform !== 'win32') return null;
  return JSON.stringify(scriptPath.replace(/\\/g, '/'));
}

function projectLocalHookPrefix({ runtime = 'claude', dirName }) {
  if (!dirName) return dirName;
  return (runtime === 'gemini' || runtime === 'antigravity')
    ? dirName
    : `"$CLAUDE_PROJECT_DIR"/${dirName}`;
}

function projectPortableHookBaseDir({ configDir, homeDir }) {
  const normalizedConfigDir = String(configDir || '').replace(/\\/g, '/');
  const normalizedHome = String(homeDir || '').replace(/\\/g, '/');
  if (!normalizedConfigDir || !normalizedHome) return normalizedConfigDir;
  return normalizedConfigDir.startsWith(normalizedHome)
    ? '$HOME' + normalizedConfigDir.slice(normalizedHome.length)
    : normalizedConfigDir;
}

function projectShellCommandText({
  runnerToken,
  argTokens = [],
  runtime = 'generic',
  platform = process.platform,
}) {
  if (!runnerToken) return null;
  const parts = [runnerToken, ...argTokens.filter(Boolean)];
  return formatHookCommandForRuntime(parts.join(' '), { platform, runtime });
}

function projectManagedHookCommand({ absoluteRunner, scriptPath, runtime = 'generic', platform = process.platform }) {
  if (!absoluteRunner || !scriptPath) return null;
  const normalizedScriptPath = platform === 'win32' ? scriptPath.replace(/\\/g, '/') : scriptPath;
  return projectShellCommandText({
    runnerToken: absoluteRunner,
    argTokens: [JSON.stringify(normalizedScriptPath)],
    runtime,
    platform,
  });
}

const MANAGED_HOOK_BASENAMES_BY_SURFACE = {
  'settings-json': new Set([
    'gsd-check-update.js',
    'gsd-statusline.js',
    'gsd-context-monitor.js',
    'gsd-prompt-guard.js',
    'gsd-read-guard.js',
    'gsd-read-injection-scanner.js',
    'gsd-update-banner.js',
    'gsd-workflow-guard.js',
  ]),
  'codex-toml': new Set([
    'gsd-check-update.js',
  ]),
};

