#!/usr/bin/env node
// Coco CLI — clones Coco into a target dir and runs the installer.
//
// Usage:
//   npx cocosuperintelligence               # clones to ./coco and installs (auto-detect adapter)
//   npx cocosuperintelligence install       # same as above
//   npx cocosuperintelligence install --adapter cursor
//   npx cocosuperintelligence install --systems gsd,brain,m0
//   npx cocosuperintelligence update        # checkout the pinned release tag
//   npx cocosuperintelligence uninstall     # remove symlinks + clone
//   npx cocosuperintelligence --help

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
const PINNED_TAG = 'v' + PKG_VERSION;
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
    console.log(`     Update:  node bin/coco.js update     (or: git -C <clone> pull --ff-only && bash install.sh)\n`);
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
  console.log(`cocosuperintelligence v${PKG_VERSION}`);
  checkForUpdate(true);
}

function help() {
  console.log(`Coco — open-source AI workflow framework

Usage:
  npx cocosuperintelligence                   clone + install (auto-detect)
  npx cocosuperintelligence install [flags]   clone + install with flags
  npx cocosuperintelligence update [dir]      checkout the pinned release tag
  npx cocosuperintelligence uninstall [dir]   remove symlinks + clone
  npx cocosuperintelligence version           show version + check for updates
  npx cocosuperintelligence --help            this message

Update checks contact only github.com (no telemetry); disable with COCO_NO_UPDATE_CHECK=1.

Install flags (passed to install.sh):
  --adapter <name>                      claude-code | cursor | grok | vscode |
                                        codex | generic | aider | amazon-q |
                                        cline | github-copilot-cli | hermes |
                                        pi-desktop | roo-code | vscode-continue |
                                        windsurf | zed
  --systems <list>                      gsd | brain | cognee | hyperframes | m0 |
                                        superintelligence   (comma-separated)
  --dry-run                             preview, no writes

Examples:
  npx cocosuperintelligence
  npx cocosuperintelligence install --adapter cursor
  npx cocosuperintelligence install --systems gsd,brain --adapter claude-code
  npx cocosuperintelligence update
  npx cocosuperintelligence uninstall

Repo: https://github.com/coco-research/coco
Install clones the ${PINNED_TAG} release tag, not floating main.
npx cocosuperintelligence is the published path (clones the pin, then install).
`);
}

function which(cmd) {
  const r = spawnSync('which', [cmd], { encoding: 'utf8' });
  return r.status === 0 ? r.stdout.trim() : null;
}

function run(cmd, args, opts = {}) {
  // git ignores cwd/-C when GIT_DIR is set. Git calls get gitEnv(); SSH and proxies stay.
  const r = spawnSync(cmd, args, { stdio: 'inherit', ...opts, ...(cmd === 'git' ? { env: gitEnv() } : {}) });
  if (r.status !== 0) {
    process.exit(r.status || 1);
  }
}

// Any common spelling of github.com/coco-research/coco: https/ssh/git URLs with optional
// user[:token]@ and :port, or scp form with or without user@. GitHub names are case-insensitive.
const ORIGIN_RE = /^(?:(?:https?|ssh|git):\/\/(?:[^@\/]+@)?github\.com(?::\d+)?\/|(?:[^@\/:]+@)?github\.com:)coco-research\/coco(?:\.git)?\/?$/i;

// Hooks and scripts export GIT_DIR. git -C does not override it: config and
// remote get-url then read that repo, while show-toplevel still prints -C.
// Drop only vars that redirect which repo or config git uses. Keep
// GIT_SSH_COMMAND, GIT_SSH, GIT_ASKPASS, GIT_TERMINAL_PROMPT, and proxies.
const GIT_REDIRECT = new Set([
  'GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE',
  'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_NAMESPACE',
  'GIT_CEILING_DIRECTORIES', 'GIT_DISCOVERY_ACROSS_FILESYSTEM', 'GIT_CONFIG',
  'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_SYSTEM', 'GIT_CONFIG_NOSYSTEM',
  'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT',
]);

function gitEnv() {
  const env = { ...process.env };
  for (const key of Object.keys(env)) {
    if (GIT_REDIRECT.has(key) || /^GIT_CONFIG_(?:KEY|VALUE)_\d+$/.test(key)) delete env[key];
  }
  return env;
}

function gitIn(dir, args) {
  // 1 MiB default maxBuffer raises ENOBUFS on a large status and must not look clean.
  return spawnSync('git', ['-C', dir, ...args], {
    encoding: 'utf8', env: gitEnv(), maxBuffer: 64 * 1024 * 1024,
  });
}

function sameReal(a, b) {
  try { return fs.realpathSync(a) === fs.realpathSync(b); } catch (_) { return false; }
}

function isEmptyDir(dir) {
  try { return fs.statSync(dir).isDirectory() && fs.readdirSync(dir).length === 0; } catch (_) { return false; }
}

// Null when dir is a coco-research/coco clone. Git missing or an unreadable origin fails closed.
function cloneRejection(dir) {
  if (!fs.existsSync(dir)) return 'it does not exist';
  let name = null;
  try { name = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8')).name; } catch (_) { name = null; }
  if (name !== 'cocosuperintelligence') return 'package.json name is not "cocosuperintelligence"';
  let gitSt = null;
  try { gitSt = fs.statSync(path.join(dir, '.git')); } catch (_) { gitSt = null; }
  if (!gitSt || (!gitSt.isDirectory() && !gitSt.isFile())) return 'it has no .git directory or file';
  const top = gitIn(dir, ['rev-parse', '--show-toplevel']);
  if (top.error && top.error.code === 'ENOENT') return 'its origin could not be verified; remove the directory by hand';
  // A .git file of `gitdir: <other>/.git` still reports this directory as toplevel.
  // Accept only this dir's own .git, or a linked worktree whose gitdir file points back here.
  const gitDirR = gitIn(dir, ['rev-parse', '--absolute-git-dir']);
  const gitDir = String(gitDirR.stdout || '').trim();
  let owns = gitDirR.status === 0 && sameReal(gitDir, path.join(dir, '.git'));
  if (!owns && gitDir) {
    try {
      const back = fs.readFileSync(path.join(gitDir, 'gitdir'), 'utf8').trim();
      owns = sameReal(path.resolve(gitDir, back), path.join(dir, '.git'));
    } catch (_) { owns = false; }
  }
  if (top.status !== 0 || !sameReal(String(top.stdout || '').trim(), dir) || !owns) {
    return 'its git toplevel is not this directory';
  }
  // Raw stored value. `remote get-url` applies insteadOf, so an alias can look official.
  const remote = gitIn(dir, ['config', '--local', '--get', 'remote.origin.url']);
  if ((remote.error && remote.error.code === 'ENOENT') || remote.status !== 0) {
    return 'its origin could not be verified; remove the directory by hand';
  }
  if (!ORIGIN_RE.test(String(remote.stdout || '').trim())) {
    return 'its origin must be stored as a github.com/coco-research/coco URL';
  }
  return null;
}

// Names of local work, or null when a check errored or exited non-zero (fail closed).
// untracked=false for update: ~/.coco holds untracked Coco state (knowledge/, sessions/, m0-token)
// that a plain checkout keeps.
function localWork(dir, untracked = true) {
  const gitOut = (args) => {
    const r = gitIn(dir, args);
    if (r.error || r.status !== 0) return null;
    return String(r.stdout || '').trim();
  };
  // CLI cache and the Codex adapter's generated si-commands/ are not local work.
  const status = gitOut(['status', '--porcelain', `--untracked-files=${untracked ? 'all' : 'no'}`, '--', '.', ':(exclude).update-check.json', ':(exclude)si-commands']);
  const stash = gitOut(['stash', 'list']);
  // HEAD: the install is detached at the pin, so a commit there is on no branch.
  // Release tags only: the pinned tag is not local work, but a local `git tag wip` is.
  const ahead = gitOut(['rev-list', 'HEAD', '--branches', '--not', '--remotes', '--tags=v[0-9]*']);
  if (status === null || stash === null || ahead === null) return null;
  const found = [];
  if (status) found.push('uncommitted changes');
  if (stash) found.push('a stash');
  if (ahead) found.push('unpushed commits');
  return found;
}

function refuseClone(dir, why) {
  console.error(`Not removing ${dir}: ${why}. Nothing was deleted.`);
  process.exit(2);
}

function cloneOrUpdate(dir) {
  const empty = isEmptyDir(dir);
  if (fs.existsSync(dir) && !empty) {
    const why = cloneRejection(dir);
    if (why) refuseClone(dir, why);
  }
  if (!empty && fs.existsSync(dir) && fs.existsSync(path.join(dir, '.git'))) {
    // Detached HEAD is the tagged install. A branch checkout (typical `git clone` of
    // main) must not be force-moved onto an older pin.
    const head = spawnSync('git', ['symbolic-ref', '-q', 'HEAD'], { cwd: dir, env: gitEnv() });
    if (head.status !== 0) {
      // The checkout below would strand local commits on the pinned install. Untracked state is
      // fine: without --force, git refuses to overwrite an untracked file and nothing is lost.
      const found = localWork(dir, false);
      if (found == null || found.length) {
        console.error(`Not updating ${dir}: ${found == null ? 'the local-work check could not run' : `it has ${found.join(' and ')}`}. Move that work elsewhere or remove the clone. Nothing was changed.`);
        process.exit(2);
      }
      console.log(`Coco already at ${dir} (detached). Updating to ${PINNED_TAG}...`);
      run('git', ['fetch', '--tags', '--force', '--depth', '1', 'origin', `refs/tags/${PINNED_TAG}:refs/tags/${PINNED_TAG}`], { cwd: dir });
      run('git', ['checkout', PINNED_TAG], { cwd: dir });
    } else {
      console.log(`Coco already at ${dir}. Pulling latest...`);
      run('git', ['pull', '--ff-only'], { cwd: dir });
    }
  } else {
    console.log(`Cloning Coco ${PINNED_TAG} to ${dir}...`);
    run('git', ['clone', '--branch', PINNED_TAG, '--depth', '1', REPO, dir]);
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
  console.log(`Re-install later:  npx cocosuperintelligence install\nUpdate the clone to the pinned release:  npx cocosuperintelligence update`);
}

function cmdUpdate(argv) {
  const dir = argv[0] && !argv[0].startsWith('--') ? argv[0] : DEFAULT_DIR;
  if (!isEmptyDir(dir) && !fs.existsSync(path.join(dir, '.git'))) {
    console.error(`Error: ${dir} is not a Coco clone. Run \`npx cocosuperintelligence install\` first.`);
    process.exit(1);
  }
  cloneOrUpdate(dir);
  console.log(`\nCoco updated at ${dir}. Re-run install if you want to refresh symlinks:\n  bash ${path.join(dir, 'install.sh')}`);
}

// Remove symlinks under home that point at a root or anything inside it.
// Relative link text is resolved from the link's own directory, then realpath
// when the target exists. Comparison is a plain string: a clone path is not a
// glob. The prefix is root plus a separator, so a clone named coco does not
// take links into coco-research. realpath at the start is find -H: a symlinked
// home is searched, and a symlinked directory below it is not.
function sweepLinks(home, roots) {
  if (!fs.existsSync(home)) return;
  let start;
  try { start = fs.realpathSync(home); } catch (_) { return; }
  const inside = (p) => roots.some((r) => p === r || p.startsWith(r.endsWith(path.sep) ? r : r + path.sep));
  const walk = (dir) => {
    let names;
    try { names = fs.readdirSync(dir); } catch (_) { return; }
    for (const name of names) {
      const link = path.join(dir, name);
      let st;
      try { st = fs.lstatSync(link); } catch (_) { continue; }
      if (st.isSymbolicLink()) {
        let target;
        try { target = fs.readlinkSync(link); } catch (_) { continue; }
        const abs = path.resolve(path.dirname(link), target);
        let canon = null;
        try { canon = fs.realpathSync(abs); } catch (_) { /* dangling */ }
        if (inside(abs) || (canon && inside(canon))) {
          try { fs.unlinkSync(link); } catch (e) { console.error(`Could not remove ${link}: ${e.code}`); }
        }
      } else if (st.isDirectory()) {
        walk(link);
      }
    }
  };
  walk(start);
}

// Defaults from adapters/*/install.sh. Env overrides (ZED_HOME, PI_AGENT_HOME, …)
// are not visible here; uninstall only knows the path a plain install writes.
function adapterHomes() {
  const h = os.homedir();
  const homes = [
    '.claude', '.cursor', '.grok', '.copilot', '.hermes', '.pi', '.agents',
    '.continue', '.roo-code', '.cline', '.coco',
  ].map((rel) => path.join(h, rel));
  homes.push(
    path.join(h, '.config', 'zed'),
    path.join(h, '.codeium', 'windsurf'),
    path.join(h, '.aws', 'amazon-q'),
  );
  // vscode/install.sh detect_user_dirs: prompt symlinks land in each editor User dir.
  const apps = ['Code', 'Code - Insiders', 'VSCodium', 'VSCodium - Insiders'];
  const bases = [
    path.join(h, 'Library', 'Application Support'),
    process.env.APPDATA || path.join(h, 'AppData', 'Roaming'),
    process.env.XDG_CONFIG_HOME || path.join(h, '.config'),
  ];
  for (const base of bases) {
    for (const app of apps) homes.push(path.join(base, app, 'User'));
  }
  return [...new Set(homes)];
}

// A generated file is removed only in a folder its adapter writes, and only when
// it carries that adapter's marker. Everything else in a home, ~/.coco included,
// is swept for links into the clone and nothing more.
const SI_MARKERS = [
  'Generated by `build_commands.py`',
  'Generated by `build_meta_commands.py`',
];
// The comment adapters/pi-desktop/install.sh appends to every file it writes.
const PI_MARKER = '<!-- Coco PI-Desktop adapter. Source: ';
const RULES_MARKER = '<!-- coco:rules-start -->';
const VSCODE_MARKER = 'Generated by the Coco VS Code adapter';

function isSiCommandName(name) {
  return name === 'SI.md' || (name.startsWith('SI-') && name.endsWith('.md'));
}

// Text of a regular file (never through a link), or '' when unreadable.
function readPlain(file) {
  try {
    if (!fs.lstatSync(file).isFile()) return '';
    return fs.readFileSync(file, 'utf8');
  } catch (_) { return ''; }
}

function listDir(dir) {
  try { return fs.readdirSync(dir); } catch (_) { return []; }
}

function removePath(p, opts) {
  try { fs.rmSync(p, opts); } catch (e) { console.error(`Could not remove ${p}: ${e.code}`); }
}

function hermesClaudeHomes() {
  const root = path.join(os.homedir(), '.hermes', 'profiles');
  return listDir(root).map((p) => path.join(root, p, 'home', '.claude'));
}

// Folders an adapter generates SI commands into (one level, as grok's own uninstall).
function siCommandDirs() {
  const h = os.homedir();
  return [
    path.join(h, '.claude', 'commands'),
    path.join(h, '.cursor', 'commands'),
    path.join(h, '.grok', 'commands'),
    path.join(h, '.copilot', 'coco-generated', 'si-commands'),
    path.join(h, '.pi', 'agent', 'prompts'),
    ...hermesClaudeHomes().map((c) => path.join(c, 'commands')),
  ];
}

// SI.md / SI-*.md files directly in dir that carry a generator line.
function markedSi(dir) {
  return listDir(dir).filter((n) => isSiCommandName(n)
    && SI_MARKERS.some((m) => readPlain(path.join(dir, n)).includes(m)))
    .map((n) => path.join(dir, n));
}

function sweepGenerated() {
  const h = os.homedir();
  // PI-Desktop's own --uninstall rule: a skill folder whose SKILL.md carries the
  // marker, and top-level .md files in subagents and prompts that carry it.
  const skills = path.join(h, '.agents', 'skills');
  for (const name of listDir(skills)) {
    const dir = path.join(skills, name);
    let st;
    try { st = fs.lstatSync(dir); } catch (_) { continue; }
    if (st.isDirectory() && readPlain(path.join(dir, 'SKILL.md')).includes(PI_MARKER)) {
      removePath(dir, { recursive: true, force: true });
    }
  }
  for (const dir of [path.join(h, '.agents', 'subagents'), path.join(h, '.pi', 'agent', 'prompts')]) {
    for (const name of listDir(dir)) {
      const file = path.join(dir, name);
      if (name.endsWith('.md') && readPlain(file).includes(PI_MARKER)) removePath(file);
    }
  }
  for (const dir of siCommandDirs()) markedSi(dir).forEach((f) => removePath(f));
}

// Adapters whose install leaves something this uninstall does not remove.
function leftoverAdapters(dir) {
  const h = os.homedir();
  const notes = new Set();
  if (hermesClaudeHomes().some((c) => readPlain(path.join(c, 'CLAUDE.md')).includes(RULES_MARKER))) notes.add('hermes');
  if (fs.existsSync(path.join(h, '.claude', '.coco', 'manifest.jsonl'))
    || readPlain(path.join(h, '.claude', 'CLAUDE.md')).includes(RULES_MARKER)) notes.add('claude-code');
  const instr = path.join(h, '.copilot', 'instructions');
  if (listDir(instr).some((n) => readPlain(path.join(instr, n)).includes(VSCODE_MARKER))) notes.add('vscode');
  // codex generates SI commands into ~/.coco, which is swept for links only.
  if (markedSi(path.join(h, '.coco', 'si-commands')).length) notes.add('codex');
  const copied = [
    ['zed', path.join(h, '.config', 'zed', 'rules'), path.join(dir, 'rules')],
    ['vscode-continue', path.join(h, '.continue', 'rules'), path.join(dir, 'rules')],
    ['roo-code', path.join(h, '.roo-code', 'rules'), path.join(dir, 'rules')],
    ['cline', path.join(h, '.cline', 'rules'), path.join(dir, 'rules')],
    ['amazon-q', path.join(h, '.aws', 'amazon-q', 'rules'), path.join(dir, 'rules')],
    ['windsurf', path.join(h, '.codeium', 'windsurf', 'rules'), path.join(dir, 'rules', 'cursor-mdc')],
  ];
  for (const [name, dest, src] of copied) {
    if (copiedRulesRemain(dest, src)) notes.add(name);
  }
  return notes;
}

// Copied rules have no generator marker. A byte-identical file is still the
// adapter's install, and it is not safe to delete, so the adapter is named.
function copiedRulesRemain(destDir, srcDir) {
  if (!fs.existsSync(destDir) || !fs.existsSync(srcDir)) return false;
  let names;
  try { names = fs.readdirSync(srcDir); } catch (_) { return false; }
  for (const name of names) {
    const src = path.join(srcDir, name);
    const dst = path.join(destDir, name);
    let srcSt;
    let dstSt;
    try { srcSt = fs.lstatSync(src); dstSt = fs.lstatSync(dst); } catch (_) { continue; }
    if (!srcSt.isFile() || !dstSt.isFile()) continue;
    try {
      if (fs.readFileSync(src).equals(fs.readFileSync(dst))) return true;
    } catch (_) {}
  }
  return false;
}

function cmdUninstall(argv) {
  const force = argv.includes('--force');
  const dirArg = argv.find((a) => !a.startsWith('--'));
  const dir = path.resolve(dirArg || DEFAULT_DIR);
  if (fs.existsSync(dir)) {
    const why = cloneRejection(dir);
    // Empty: no data to lose. tests/check-cli-uninstall-cleanup.sh uninstalls an empty dir.
    let entries = 1;  // not a readable directory (a file, no permission): refuse, never crash
    try { entries = fs.readdirSync(dir).length; } catch (_) {}
    if (why && entries) refuseClone(dir, why);
    if (!why && !force) {
      const found = localWork(dir);
      if (found == null) refuseClone(dir, 'the local-work check could not run; pass --force to remove it');
      if (found.length) refuseClone(dir, `it has ${found.join(' and ')}; pass --force to remove it`);
    }
  }
  // install.sh links through whichever path it ran from, so match both.
  let real = dir;
  try { real = fs.realpathSync(dir); } catch (_) { /* absent: only the given path */ }
  const roots = [...new Set([dir, real])];
  console.log(`Removing symlinks pointing into ${dir}...`);
  const homes = adapterHomes();
  for (const home of homes) sweepLinks(home, roots);
  sweepGenerated();
  const notes = leftoverAdapters(dir);
  // grok also writes generated files (SI commands, config block, hooks); its installer removes them.
  // Best-effort: an older pinned clone may not know --uninstall; never abort the uninstall over it.
  const grokInstaller = path.join(dir, 'adapters', 'grok', 'install.sh');
  if (fs.existsSync(path.join(os.homedir(), '.grok')) && fs.existsSync(grokInstaller)) {
    const r = spawnSync('bash', [grokInstaller, '--uninstall'], { stdio: 'inherit' });
    if (r.status !== 0) {
      console.log('Note: grok installer cleanup failed (possibly an older pin without --uninstall); continuing.');
    }
  }
  let isLink = false;
  try { isLink = fs.lstatSync(dir).isSymbolicLink(); } catch (_) { /* absent */ }
  if (isLink) {
    // A symlinked clone dir may point at a checkout the user keeps elsewhere: drop only the link.
    fs.rmSync(dir, { force: true });
    console.log(`Removed the link ${dir}; kept the clone it points to at ${real}. Delete that by hand if you want it gone.`);
  } else {
    console.log(`Removing clone at ${dir}...`);
    if (fs.existsSync(dir)) {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  }
  // The update notifier's cache is ours; drop it, and ~/.coco if that leaves it empty.
  fs.rmSync(UPDATE_CACHE, { force: true });
  try { fs.rmdirSync(path.dirname(UPDATE_CACHE)); } catch (_) { /* absent or holds other files */ }
  for (const name of [...notes].sort()) {
    console.log(`Note: ${name} install was not fully removed.`);
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
      // Flags pass through to install (e.g., npx cocosuperintelligence --adapter cursor).
      // A bare word is an unknown subcommand: reject it before any clone touches disk.
      if (!sub.startsWith('-')) {
        console.error(`Error: unknown command '${sub}'. Run with --help to see the commands.`);
        process.exit(2);
      }
      cmdInstall(argv);
      checkForUpdate(false);
  }
}

main();
