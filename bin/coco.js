#!/usr/bin/env node
// Coco CLI — clones Coco into a target dir and runs the installer.
//
// Usage:
//   npx coco-cli                      # clones to ./coco and installs (auto-detect adapter)
//   npx coco-cli install              # same as above
//   npx coco-cli install --adapter cursor
//   npx coco-cli install --systems gsd,brain,team
//   npx coco-cli update               # pull latest in existing clone
//   npx coco-cli uninstall            # remove symlinks + clone
//   npx coco-cli --help

'use strict';

const { execSync, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const REPO = 'https://github.com/rijulkalra2000/coco.git';
const DEFAULT_DIR = path.join(process.cwd(), 'coco');

function help() {
  console.log(`Coco — open-source AI workflow framework

Usage:
  npx coco-cli                          clone + install (auto-detect)
  npx coco-cli install [flags]          clone + install with flags
  npx coco-cli update [dir]             pull latest in existing clone
  npx coco-cli uninstall [dir]          remove symlinks + clone
  npx coco-cli --help                   this message

Install flags (passed to install.sh):
  --adapter <name>                      claude-code | cursor | codex | generic
  --systems <list>                      e.g., gsd,brain,team
  --dry-run                             preview, no writes

Examples:
  npx coco-cli
  npx coco-cli install --adapter cursor
  npx coco-cli install --systems gsd,brain --adapter claude-code
  npx coco-cli update
  npx coco-cli uninstall

Repo: https://github.com/rijulkalra2000/coco
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
  console.log(`Re-run install / update later with:\n  npx coco-cli update`);
}

function cmdUpdate(argv) {
  const dir = argv[0] && !argv[0].startsWith('--') ? argv[0] : DEFAULT_DIR;
  if (!fs.existsSync(path.join(dir, '.git'))) {
    console.error(`Error: ${dir} is not a Coco clone. Run \`npx coco-cli install\` first.`);
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
      break;
    case 'install':
      cmdInstall(rest);
      break;
    case 'update':
      cmdUpdate(rest);
      break;
    case 'uninstall':
      cmdUninstall(rest);
      break;
    default:
      // any unknown subcommand → pass through to install (e.g., npx coco-cli --adapter cursor)
      cmdInstall(argv);
  }
}

main();
