'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {
  validateInstallerMigrationActions,
  validateInstallerMigrationRecord,
} = require('./installer-migration-authoring.cjs');
const { platformWriteSync } = require('./shell-command-projection.cjs');

const MANIFEST_NAME = 'gsd-file-manifest.json';
const INSTALL_STATE_NAME = 'gsd-install-state.json';
const INSTALL_MIGRATION_LOCK_NAME = 'gsd-install-migration.lock';
const DEFAULT_MIGRATIONS_DIR = path.join(__dirname, 'installer-migrations');
const DEFAULT_LOCK_TIMEOUT_MS = 30_000;
const STRICT_JSON = Symbol('strict-json');

function sha256File(filePath) {
  const hash = crypto.createHash('sha256');
  const buffer = Buffer.allocUnsafe(1024 * 1024);
  const fd = fs.openSync(filePath, 'r');
  try {
    while (true) {
      const bytesRead = fs.readSync(fd, buffer, 0, buffer.length, null);
      if (bytesRead === 0) break;
      hash.update(buffer.subarray(0, bytesRead));
    }
  } finally {
    fs.closeSync(fd);
  }
  return hash.digest('hex');
}

function sha256Text(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function readJsonIfPresent(filePath, fallback) {
  if (!fs.existsSync(filePath)) return fallback;
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (error) {
    if (fallback === STRICT_JSON) {
      throw new Error(`invalid installer migration state JSON: ${filePath}: ${error.message}`);
    }
    return fallback;
  }
}

function readInstallManifest(configDir) {
  const manifest = readJsonIfPresent(path.join(configDir, MANIFEST_NAME), null);
  if (!manifest || typeof manifest !== 'object') {
    return { version: null, timestamp: null, mode: null, files: {} };
  }
  return {
    version: manifest.version || null,
    timestamp: manifest.timestamp || null,
    mode: manifest.mode || null,
    files: manifest.files && typeof manifest.files === 'object' ? manifest.files : {},
  };
}

function readInstallState(configDir) {
  const state = readJsonIfPresent(path.join(configDir, INSTALL_STATE_NAME), STRICT_JSON);
  if (!state || typeof state !== 'object') {
    return { schemaVersion: 1, appliedMigrations: [] };
  }
  return {
    schemaVersion: state.schemaVersion || 1,
    appliedMigrations: Array.isArray(state.appliedMigrations) ? state.appliedMigrations : [],
  };
}

// Strict atomic write for the install state: must never be left half-written.
// Bypasses the seam because platformWriteSync falls back to a direct write on
// rename failure, which would silently violate this invariant.
function atomicWriteInstallState(configDir, content) {
  fs.mkdirSync(configDir, { recursive: true });
  const filePath = path.join(configDir, INSTALL_STATE_NAME);
  const tmpPath = `${filePath}.tmp-${process.pid}-${Date.now()}`;
  try {
    fs.writeFileSync(tmpPath, content, 'utf8');
    fs.renameSync(tmpPath, filePath);
  } catch (error) {
    try { fs.rmSync(tmpPath, { force: true }); } catch { /* best-effort */ }
    throw error;
  }
}

function writeInstallState(configDir, state) {
  atomicWriteInstallState(configDir, JSON.stringify(state, null, 2) + '\n');
  return state;
}

function readJson(configDir, relPath) {
  const { fullPath } = ensureInsideConfig(configDir, relPath);
  if (!fs.existsSync(fullPath)) {
    return { exists: false, value: null, error: null };
  }
  try {
    return { exists: true, value: JSON.parse(fs.readFileSync(fullPath, 'utf8')), error: null };
  } catch (error) {
    return { exists: true, value: null, error };
  }
}

function normalizeRelPath(relPath) {
  if (typeof relPath !== 'string' || relPath.trim() === '') {
    throw new Error('migration action relPath must be a non-empty string');
  }
  const normalized = relPath.replace(/\\/g, '/');
  if (path.isAbsolute(normalized) || path.win32.isAbsolute(normalized)) {
    throw new Error(`migration action relPath must stay inside configDir: ${relPath}`);
  }
  const segments = normalized.split('/');
  if (segments.some((segment) => segment === '' || segment === '.' || segment === '..')) {
    throw new Error(`migration action relPath must stay inside configDir: ${relPath}`);
  }
  return segments.join('/');
}

function classifyArtifact(configDir, relPath, manifest) {
  const normalized = normalizeRelPath(relPath);
  const originalHash = manifest.files[normalized] || null;
  const fullPath = path.join(configDir, normalized);
  if (!fs.existsSync(fullPath)) {
    return { classification: originalHash ? 'managed-missing' : 'missing', originalHash, currentHash: null };
  }
  const currentHash = sha256File(fullPath);
  if (!originalHash) {
    return { classification: 'unknown', originalHash: null, currentHash };
  }
  if (currentHash === originalHash) {
    return { classification: 'managed-pristine', originalHash, currentHash };
  }
  return { classification: 'managed-modified', originalHash, currentHash };
}

function appliedMigrationIds(state) {
  return new Set(
    state.appliedMigrations
      .filter((entry) => entry && typeof entry.id === 'string')
      .map((entry) => entry.id)
  );
