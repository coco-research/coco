'use strict';

const fs = require('fs');
const path = require('path');

const BASELINE_MIGRATION_ID = '2026-05-11-first-time-baseline-scan';

// Runtime install surfaces must stay aligned with:
// - docs/installer-migrations.md#runtime-configuration-contract-registry
// - docs/ARCHITECTURE.md#runtime-install-contract-matrix
//
// The registry rows are based on each runtime's upstream loader docs where
// available. Source-limited rows are intentionally conservative: scan generated
// files GSD materializes, but do not infer ownership of undocumented host config.
const RUNTIME_SURFACES = {
  claude: ['get-shit-done', 'commands/gsd', 'skills', 'agents', 'hooks', 'settings.json'],
  codex: ['get-shit-done', 'skills', 'agents', 'hooks', 'config.toml', 'hooks.json'],
  gemini: ['get-shit-done', 'commands/gsd', 'hooks'],
  opencode: ['get-shit-done', 'command', 'skills', 'agents'],
  kilo: ['get-shit-done', 'command', 'skills', 'agents'],
  copilot: ['get-shit-done', 'skills', 'agents'],
  antigravity: ['get-shit-done', 'skills', 'agents'],
  cursor: ['get-shit-done', 'skills', 'agents'],
  windsurf: ['get-shit-done', 'skills', 'agents', 'rules'],
  augment: ['get-shit-done', 'skills', 'agents'],
  trae: ['get-shit-done', 'skills', 'agents', 'rules'],
  qwen: ['get-shit-done', 'skills', 'agents'],
  hermes: ['get-shit-done', 'skills/gsd', 'agents'],
  cline: ['get-shit-done', 'skills', 'agents'],
  codebuddy: ['get-shit-done', 'skills', 'agents'],
};

const COMMON_SURFACES = ['get-shit-done', 'skills', 'agents', 'hooks'];
const INTERNAL_TOP_LEVEL_NAMES = new Set([
  'gsd-file-manifest.json',
  'gsd-install-state.json',
  'gsd-migration-backups',
  'gsd-migration-journal',
]);
const USER_OWNED_PATHS = new Set([
  'get-shit-done/USER-PROFILE.md',
  'commands/gsd/dev-preferences.md',
  'skills/gsd-dev-preferences/SKILL.md',
]);
let knownGeneratedAgentNames = null;

function normalizeRelPath(relPath) {
  return relPath.replace(/\\/g, '/').replace(/^\/+/, '');
}

function baselineInstallSurfaces(runtime) {
  if (runtime && RUNTIME_SURFACES[runtime]) return RUNTIME_SURFACES[runtime];
  return COMMON_SURFACES;
}

function walkFiles(root, relDir, files) {
  const dir = path.join(root, relDir);
  if (!fs.existsSync(dir)) return;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const relPath = path.posix.join(relDir, entry.name);
    if (relDir === '' && INTERNAL_TOP_LEVEL_NAMES.has(entry.name)) continue;
    const fullPath = path.join(root, relPath);
    if (entry.isDirectory()) {
      walkFiles(root, relPath, files);
    } else if (entry.isFile()) {
      files.add(normalizeRelPath(relPath));
    }
  }
