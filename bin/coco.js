#!/usr/bin/env node
// Coco CLI — clones Coco into a target dir and runs the installer.
//
// Usage:
//   npx @coco-research/coco-cli               # clones to ./coco and installs (auto-detect adapter)
//   npx @coco-research/coco-cli install       # same as above
//   npx @coco-research/coco-cli install --adapter cursor
//   npx @coco-research/coco-cli install --systems gsd,brain,team
//   npx @coco-research/coco-cli update        # pull latest in existing clone
//   npx @coco-research/coco-cli uninstall     # remove symlinks + clone
//   npx @coco-research/coco-cli --help

'use strict';

const { execSync, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const https = require('https');

const REPO = 'https://github.com/coco-research/coco.git';
const DEFAULT_DIR = path.join(process.cwd(), 'coco');

// ── Update notifier ─────────────────────────────────────────────────────────
// Privacy: contacts only github.com (the source), no analytics/telemetry. Result
// is cached for 24h in ~/.coco/.update-check.json. Disable with COCO_NO_UPDATE_CHECK=1.
const PKG_VERSION = (() => {
  try { return require('../package.json').version || '0.0.0'; } catch (_) { return '0.0.0'; }
})();
const UPDATE_CACHE = path.join(os.homedir(), '.coco', '.update-check.json');
const LATEST_URL = 'https://raw.githubusercontent.com/coco-research/coco/main/package.json';

function semverGt(a, b) {
  const pa = String(a).split('.').map(n => parseInt(n, 10) || 0);
  const pb = String(b).split('.').map(n => parseInt(n, 10) || 0);
  for (let i = 0; i < 3; i++) { if ((pa[i] || 0) > (pb[i] || 0)) return true; if ((pa[i] || 0) < (pb[i] || 0)) return false; }
  return false;
}

function readCache() {
  try { return JSON.parse(fs.readFileSync(UPDATE_CACHE, 'utf8')); } catch (_) { return null; }
}
function writeCache(latest) {
  try {
    fs.mkdirSync(path.dirname(UPDATE_CACHE), { recursive: true });
    fs.writeFileSync(UPDATE_CACHE, JSON.stringify({ checkedAt: Date.now(), latest }));
  } catch (_) { /* best-effort */ }
}

function fetchLatestVersion(cb) {
  let done = false;
  const finish = (v) => { if (!done) { done = true; cb(v); } };
  try {
    const req = https.get(LATEST_URL, { headers: { 'User-Agent': 'coco-cli' } }, (res) => {
      if (res.statusCode !== 200) { res.resume(); return finish(null); }
      let body = '';
      res.on('data', (d) => { body += d; });
      res.on('end', () => { try { finish(JSON.parse(body).version || null); } catch (_) { finish(null); } });
    });
    req.setTimeout(2500, () => { req.destroy(); finish(null); });
    req.on('error', () => finish(null));
  } catch (_) { finish(null); }
}

function banner(latest) {
  if (latest && semverGt(latest, PKG_VERSION)) {
    console.log(`\n  ⬆  Coco ${latest} is available (you have ${PKG_VERSION}).`);
    console.log(`     Update:  npx @coco-research/coco-cli update     (or: git -C <clone> pull --ff-only && bash install.sh)\n`);
  }
}

// Non-blocking: prints a one-line banner if a newer version exists. Silent on
// offline/error. `force` bypasses the 24h cache (used by the `version` command).
function checkForUpdate(force) {
  if (process.env.COCO_NO_UPDATE_CHECK) return;
  const cache = readCache();
  const fresh = cache && (Date.now() - (cache.checkedAt || 0) < 24 * 3600 * 1000);
  if (fresh && !force) { banner(cache.latest); return; }
  fetchLatestVersion((latest) => {
    if (latest) { writeCache(latest); banner(latest); }
    else if (cache) { banner(cache.latest); }
  });
}

function cmdVersion() {
  console.log(`@coco-research/coco-cli v${PKG_VERSION}`);
  checkForUpdate(true);
}

function help() {
  console.log(`Coco — open-source AI workflow framework

Usage:
  npx @coco-research/coco-cli                   clone + install (auto-detect)
  npx @coco-research/coco-cli install [flags]   clone + install with flags
  npx @coco-research/coco-cli update [dir]      pull latest in existing clone
  npx @coco-research/coco-cli uninstall [dir]   remove symlinks + clone
  npx @coco-research/coco-cli version           show version + check for updates
  npx @coco-research/coco-cli --help            this message

Update checks contact only github.com (no telemetry); disable with COCO_NO_UPDATE_CHECK=1.

Install flags (passed to install.sh):
  --adapter <name>                      claude-code | cursor | codex | generic
  --systems <list>                      e.g., gsd,brain,team
  --dry-run                             preview, no writes

Examples:
  npx @coco-research/coco-cli
  npx @coco-research/coco-cli install --adapter cursor
  npx @coco-research/coco-cli install --systems gsd,brain --adapter claude-code
  npx @coco-research/coco-cli update
  npx @coco-research/coco-cli uninstall

Repo: https://github.com/coco-research/coco
`);
}

function which(cmd) {
  const r = spawnSync('which', [cmd], { encoding: 'utf8' });
  return r.status === 0 ? r.stdout.trim() : null;
}

function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { stdio: 'inherit', ...opts });
  if (r.status !== 0) {
    process.exit(r.status || 1);
  }
}

function cloneOrUpdate(dir) {
  if (fs.existsSync(dir) && fs.existsSync(path.join(dir, '.git'))) {
    console.log(`Coco already at ${dir}. Pulling latest...`);
    run('git', ['pull', '--ff-only'], { cwd: dir });
  } else {
    if (fs.existsSync(dir)) {
      console.error(`Error: ${dir} exists but is not a git repo. Move it or pick a different location.`);
      process.exit(1);
    }
    console.log(`Cloning Coco to ${dir}...`);
    run('git', ['clone', REPO, dir]);
  }
}

function cmdInstall(argv) {
  if (!which('git')) {
    console.error('Error: git is required. Install git first.');
    process.exit(1);
  }
  if (!which('bash')) {
    console.error('Error: bash is required. Install bash first.');
    process.exit(1);
  }

  const dir = DEFAULT_DIR;
  cloneOrUpdate(dir);

  const installScript = path.join(dir, 'install.sh');
  if (!fs.existsSync(installScript)) {
    console.error(`Error: ${installScript} not found.`);
    process.exit(1);
  }

  console.log(`Running ${installScript}...`);
  run('bash', [installScript, ...argv]);

  console.log(`\nDone. Coco installed at ${dir}.`);
  console.log(`Re-run install / update later with:\n  npx @coco-research/coco-cli update`);
}

function cmdUpdate(argv) {
  const dir = argv[0] && !argv[0].startsWith('--') ? argv[0] : DEFAULT_DIR;
  if (!fs.existsSync(path.join(dir, '.git'))) {
    console.error(`Error: ${dir} is not a Coco clone. Run \`npx @coco-research/coco-cli install\` first.`);
    process.exit(1);
  }
  cloneOrUpdate(dir);
  console.log(`\nCoco updated at ${dir}. Re-run install if you want to refresh symlinks:\n  bash ${path.join(dir, 'install.sh')}`);
}

function cmdUninstall(argv) {
  const dir = argv[0] && !argv[0].startsWith('--') ? argv[0] : DEFAULT_DIR;
  console.log(`Removing symlinks pointing into ${dir}...`);
  const homes = [path.join(os.homedir(), '.claude'), path.join(os.homedir(), '.cursor')];
  for (const home of homes) {
    if (!fs.existsSync(home)) continue;
    run('find', [home, '-type', 'l', '-lname', `*${dir}*`, '-delete']);
  }
  console.log(`Removing clone at ${dir}...`);
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
  console.log('Uninstalled.');
}

function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 0) {
    cmdInstall([]);
    return;
  }

  const sub = argv[0];
  const rest = argv.slice(1);

  switch (sub) {
    case '--help':
    case '-h':
    case 'help':
      help();
      checkForUpdate(false);
      break;
    case 'version':
    case '--version':
    case '-v':
      cmdVersion();
      break;
    case 'install':
      cmdInstall(rest);
      checkForUpdate(false);
      break;
    case 'update':
      cmdUpdate(rest);
      break;
    case 'uninstall':
      cmdUninstall(rest);
      break;
    default:
      // any unknown subcommand → pass through to install (e.g., npx @coco-research/coco-cli --adapter cursor)
      cmdInstall(argv);
      checkForUpdate(false);
  }
}

main();
