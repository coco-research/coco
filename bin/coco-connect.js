'use strict';

// MCP harness connector CLI (`coco connect <tool> [--write] [--list] [--config <path>]`).
// ponytail: ceiling = declarative data/connectors.json + stdlib JSON/TOML block merger; upgrade path = full TOML/JSONC AST parser if inline JSON comments become common.

const fs = require('fs');
const os = require('os');
const path = require('path');

const TOML_START = '# coco:mcp-start';
const TOML_END = '# coco:mcp-end';

function loadCatalog() {
  const file = path.resolve(__dirname, '..', 'data', 'connectors.json');
  const data = JSON.parse(fs.readFileSync(file, 'utf8'));
  return Array.isArray(data.connectors) ? data.connectors : [];
}

function findConnector(catalog, rawTool) {
  const q = String(rawTool || '').trim().toLowerCase();
  if (!q) return null;
  return catalog.find((c) => c.id === q || (Array.isArray(c.aliases) && c.aliases.includes(q))) || null;
}

function resolveHome() {
  return (process.env.HOME && process.env.HOME.trim()) ? path.resolve(process.env.HOME) : os.homedir();
}

function appSupportDir(home, platform) {
  if (platform === 'darwin') return path.join(home, 'Library', 'Application Support');
  if (platform === 'win32') return process.env.APPDATA ? path.resolve(process.env.APPDATA) : path.join(home, 'AppData', 'Roaming');
  return process.env.XDG_CONFIG_HOME ? path.resolve(process.env.XDG_CONFIG_HOME) : path.join(home, '.config');
}

function resolveTargetPath(conn, explicitConfig) {
  if (explicitConfig) return path.resolve(explicitConfig);
  const home = resolveHome();
  const plat = process.env.COCO_CONNECT_PLATFORM || process.platform;
  const appBase = appSupportDir(home, plat);
  switch (conn.id) {
    case 'codex':
      return path.join(process.env.CODEX_HOME ? path.resolve(process.env.CODEX_HOME) : path.join(home, '.codex'), 'config.toml');
    case 'claude-code':
      return path.resolve(process.cwd(), '.mcp.json');
    case 'claude-desktop':
      return path.join(appBase, 'Claude', 'claude_desktop_config.json');
    case 'cursor':
      return path.join(process.env.CURSOR_HOME ? path.resolve(process.env.CURSOR_HOME) : path.join(home, '.cursor'), 'mcp.json');
    case 'windsurf':
      return path.join(process.env.DEVIN_CONFIG_HOME ? path.resolve(process.env.DEVIN_CONFIG_HOME) : path.join(home, '.config', 'devin'), 'mcp_config.json');
    case 'vscode':
      return path.join(appBase, 'Code', 'User', 'mcp.json');
    case 'copilot-cli':
      return path.join(process.env.COPILOT_HOME ? path.resolve(process.env.COPILOT_HOME) : path.join(home, '.copilot'), 'mcp-config.json');
    case 'gemini-cli':
      return path.join(process.env.GEMINI_CLI_HOME ? path.resolve(process.env.GEMINI_CLI_HOME) : path.join(home, '.gemini'), 'settings.json');
    case 'antigravity':
      return path.join(home, '.gemini', 'config', 'mcp_config.json');
    case 'cline':
      return path.join(process.env.CLINE_HOME ? path.resolve(process.env.CLINE_HOME) : path.join(home, '.cline', 'data', 'settings'), 'cline_mcp_settings.json');
    case 'roo-code':
      return path.join(process.env.ROO_CODE_HOME ? path.resolve(process.env.ROO_CODE_HOME) : path.join(appBase, 'Code', 'User', 'globalStorage', 'rooveterinaryinc.roo-cline', 'settings'), 'mcp_settings.json');
    case 'zed':
      return path.join(process.env.ZED_HOME ? path.resolve(process.env.ZED_HOME) : path.join(home, '.config', 'zed'), 'settings.json');
    case 'opencode':
      return path.join(home, '.config', 'opencode', 'opencode.json');
    case 'amazon-q': {
      const kiroDir = process.env.KIRO_HOME ? path.resolve(process.env.KIRO_HOME) : path.join(home, '.kiro', 'settings');
      const legacyFile = path.join(process.env.AMAZON_Q_HOME ? path.resolve(process.env.AMAZON_Q_HOME) : path.join(home, '.aws', 'amazonq'), 'mcp.json');
      if (!fs.existsSync(kiroDir) && fs.existsSync(legacyFile)) return legacyFile;
      return path.join(kiroDir, 'mcp.json');
    }
    default:
      return conn.config_path;
  }
}

function legacyPathNotes(conn, home) {
  const notes = [];
  if (conn.id === 'windsurf') {
    for (const oldRel of [['.codeium', 'mcp_config.json'], ['.codeium', 'windsurf', 'mcp_config.json']]) {
      const p = path.join(home, ...oldRel);
      if (fs.existsSync(p)) notes.push(`Note: legacy Windsurf/Codeium config also exists at ${p}`);
    }
  }
  return notes;
}

function resolveServerSpec(flags) {
  let cliPath = path.resolve(__dirname, 'coco.js');
  try { cliPath = fs.realpathSync(cliPath); } catch (_) {}
  if (flags.npx || (!flags.local && /[\\/]_npx[\\/]/.test(cliPath))) {
    return { command: 'npx', args: ['-y', 'cocosuperintelligence', 'mcp'] };
  }
  return { command: 'node', args: [cliPath, 'mcp'] };
}

function isCocoEntry(entry) {
  if (!entry || typeof entry !== 'object') return false;
  const tokens = [];
  if (typeof entry.command === 'string') tokens.push(entry.command);
  else if (Array.isArray(entry.command)) tokens.push(...entry.command.map(String));
  if (Array.isArray(entry.args)) tokens.push(...entry.args.map(String));
  return tokens.some((t) => t.includes('cocosuperintelligence') || /(?:^|[\\/])coco(?:-mcp)?\.js$/.test(t));
}

function buildJsonSpec(shape, srv) {
  switch (shape) {
    case 'copilotCli':
      return { rootKey: 'mcpServers', entry: { type: 'local', command: srv.command, args: srv.args, tools: ['*'] } };
    case 'vscodeServers':
      return { rootKey: 'servers', entry: { type: 'stdio', command: srv.command, args: srv.args } };
    case 'zedContextServers':
      return { rootKey: 'context_servers', entry: { source: 'custom', command: srv.command, args: srv.args, env: {} } };
    case 'opencodeMcp':
      return { rootKey: 'mcp', entry: { type: 'local', command: [srv.command, ...srv.args], enabled: true } };
    default:
      return { rootKey: 'mcpServers', entry: { command: srv.command, args: srv.args } };
  }
}

function buildTomlBlock(srv) {
  const argsJson = `[${srv.args.map((a) => JSON.stringify(a)).join(', ')}]`;
  return `${TOML_START}\n[mcp_servers.coco]\ncommand = ${JSON.stringify(srv.command)}\nargs = ${argsJson}\n${TOML_END}`;
}

function claudeUserScopeHint(srv) {
  return `claude mcp add --scope user coco -- ${[srv.command, ...srv.args].join(' ')}`;
}

function renderDocsSnippet(conn, srv) {
  const cmdLine = [srv.command, ...srv.args].join(' ');
  if (conn.id === 'goose') {
    return `# Add under 'extensions:' in ${conn.config_path} (${conn.source_url}):\nextensions:\n  coco:\n    type: stdio\n    cmd: ${JSON.stringify(srv.command)}\n    args: [${srv.args.map((a) => JSON.stringify(a)).join(', ')}]\n    enabled: true\n`;
  }
  if (conn.id === 'continue') {
    return `# Save as ${conn.config_path} (${conn.source_url}):\nname: coco\nversion: 1.0.0\nschema: v1\nmcpServers:\n  - name: coco\n    command: ${JSON.stringify(srv.command)}\n    args: [${srv.args.map((a) => JSON.stringify(a)).join(', ')}]\n`;
  }
  return `# ${conn.name} (${conn.level} level — ${conn.source_url})\n# Target: ${conn.config_path}\n# Install native assets with: npx cocosuperintelligence install --adapter ${conn.id}\n# Or point any MCP bridge at stdio command: ${cmdLine}\n`;
}

function renderSnippet(conn, srv) {
  if (conn.format === 'toml') return buildTomlBlock(srv) + '\n';
  if (conn.format === 'json') {
    const { rootKey, entry } = buildJsonSpec(conn.shape, srv);
    const extra = conn.id === 'claude-code' ? `# Or for user scope: ${claudeUserScopeHint(srv)}\n` : '';
    return extra + JSON.stringify({ [rootKey]: { coco: entry } }, null, 2) + '\n';
  }
  return renderDocsSnippet(conn, srv);
}

function mergeToml(prevText, srv, force) {
  const block = buildTomlBlock(srv);
  const startIdx = prevText.indexOf(TOML_START);
  const endIdx = prevText.indexOf(TOML_END);
  if (startIdx >= 0 && endIdx > startIdx) {
    const after = prevText.slice(endIdx + TOML_END.length).replace(/^\r?\n/, '');
    const before = prevText.slice(0, startIdx).replace(/[ \t]*$/, '');
    const joined = before + block + (after ? '\n' + after : '\n');
    return joined.endsWith('\n') ? joined : joined + '\n';
  }
  const secRe = /(^|\r?\n)\[mcp_servers\.coco\]\s*(?:\r?\n|$)/;
  const m = secRe.exec(prevText);
  if (m) {
    const secStart = m.index + (m[1] ? m[1].length : 0);
    const tail = prevText.slice(secStart + m[0].length - (m[1] ? m[1].length : 0));
    const nextHdr = /(^|\r?\n)\[[^\]]+\]/.exec(tail);
    const secEnd = nextHdr ? (secStart + (m[0].length - (m[1] ? m[1].length : 0)) + nextHdr.index + (nextHdr[1] ? nextHdr[1].length : 0)) : prevText.length;
    const existingSec = prevText.slice(secStart, secEnd);
    if (!/cocosuperintelligence|coco(?:-mcp)?\.js/.test(existingSec) && !force) {
      throw new Error('Refusing to overwrite existing non-Coco [mcp_servers.coco] entry (pass --force to replace).');
    }
    const prefix = prevText.slice(0, secStart).replace(/\s*$/, '');
    const suffix = prevText.slice(secEnd).replace(/^\r?\n/, '');
    return (prefix ? prefix + '\n\n' : '') + block + (suffix ? '\n\n' + suffix : '\n');
  }
  const trimmed = prevText.trimEnd();
  return (trimmed ? trimmed + '\n\n' : '') + block + '\n';
}

function mergeJson(prevText, conn, srv, force) {
  let root = {};
  if (prevText.trim()) {
    try { root = JSON.parse(prevText); }
    catch (e) { throw new Error(`Target config is not valid JSON (${e.message}); nothing was changed.`); }
    if (!root || typeof root !== 'object' || Array.isArray(root)) {
      throw new Error('Target JSON root must be an object; nothing was changed.');
    }
  }
  const { rootKey, entry } = buildJsonSpec(conn.shape, srv);
  if (root[rootKey] !== undefined && (!root[rootKey] || typeof root[rootKey] !== 'object' || Array.isArray(root[rootKey]))) {
    throw new Error(`Target JSON '${rootKey}' must be an object; nothing was changed.`);
  }
  const container = Object.assign({}, root[rootKey] || {});
  if (Object.prototype.hasOwnProperty.call(container, 'coco') && !isCocoEntry(container.coco) && !force) {
    throw new Error(`Refusing to overwrite existing non-Coco '${rootKey}.coco' entry (pass --force to replace).`);
  }
  container.coco = entry;
  root[rootKey] = container;
  return JSON.stringify(root, null, 2) + '\n';
}

function writeAtomic(filePath, buf) {
  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });
  const tmp = path.join(dir, `.${path.basename(filePath)}.coco-tmp-${process.pid}-${Date.now()}`);
  fs.writeFileSync(tmp, buf, { mode: 0o600 });
  fs.renameSync(tmp, filePath);
}

function printList(catalog) {
  const pad = (s, n) => String(s).padEnd(n, ' ');
  process.stdout.write(`${pad('TOOL', 18)}${pad('LEVEL', 10)}${pad('FORMAT', 8)}CONFIG PATH\n`);
  for (const c of catalog) {
    process.stdout.write(`${pad(c.id, 18)}${pad(c.level, 10)}${pad(c.format, 8)}${c.config_path}\n`);
  }
}

function runConnect(argv = []) {
  const catalog = loadCatalog();
  const flags = { write: false, list: false, help: false, npx: false, local: false, force: false, config: null };
  let tool = null;

  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--list' || a === '-l') flags.list = true;
    else if (a === '--write' || a === '-w') flags.write = true;
    else if (a === '--help' || a === '-h') flags.help = true;
    else if (a === '--npx') flags.npx = true;
    else if (a === '--local') flags.local = true;
    else if (a === '--force') flags.force = true;
    else if (a === '--config' && argv[i + 1]) flags.config = argv[++i];
    else if (a.startsWith('--config=')) flags.config = a.slice('--config='.length);
    else if (a.startsWith('-')) {
      process.stderr.write(`Error: unknown flag '${a}'. Run 'coco connect --help'.\n`);
      process.exit(2);
    } else if (!tool) {
      tool = a;
    }
  }

  if (flags.help || (!flags.list && !tool)) {
    process.stdout.write(
      'Usage:\n' +
      '  coco connect --list                           list supported harnesses and verification levels\n' +
      '  coco connect <tool> [--npx|--local]           print MCP config snippet (no disk writes)\n' +
      '  coco connect <tool> --write [--config <path>] merge Coco MCP server into harness config\n'
    );
    if (!flags.help && !flags.list && !tool) process.exit(2);
    return;
  }
  if (flags.list) { printList(catalog); return; }

  const conn = findConnector(catalog, tool);
  if (!conn) {
    process.stderr.write(`Error: unknown connector '${tool}'. Run 'coco connect --list' to see supported tools.\n`);
    process.exit(2);
  }

  const srv = resolveServerSpec(flags);
  if (!flags.write) {
    const target = resolveTargetPath(conn, flags.config);
    process.stdout.write(`# Target (${conn.level}): ${target}\n` + renderSnippet(conn, srv));
    return;
  }

  if (conn.format === 'docs') {
    process.stderr.write(`Error: '${conn.id}' is docs-level (${conn.config_path}) and has no automatic --write target.\n`);
    process.stdout.write(renderSnippet(conn, srv));
    process.exit(2);
  }

  const targetPath = resolveTargetPath(conn, flags.config);
  const exists = fs.existsSync(targetPath);
  const prevBuf = exists ? fs.readFileSync(targetPath) : null;
  const prevText = prevBuf ? prevBuf.toString('utf8') : '';

  let nextText;
  try {
    nextText = conn.format === 'toml' ? mergeToml(prevText, srv, flags.force) : mergeJson(prevText, conn, srv, flags.force);
  } catch (err) {
    process.stderr.write(`Error: ${err.message}\n`);
    process.exit(2);
  }

  const nextBuf = Buffer.from(nextText, 'utf8');
  const bakPath = `${targetPath}.bak`;
  if (prevBuf !== null && !fs.existsSync(bakPath)) writeAtomic(bakPath, prevBuf);
  if (!prevBuf || !prevBuf.equals(nextBuf)) writeAtomic(targetPath, nextBuf);
  process.stdout.write(`Configured ${conn.id} (${conn.level}) -> ${targetPath}\n`);
  if (conn.id === 'claude-code') {
    process.stdout.write(`User-scope alternative: ${claudeUserScopeHint(srv)}\n`);
  }
  for (const n of legacyPathNotes(conn, resolveHome())) process.stdout.write(`${n}\n`);
}

module.exports = { runConnect, loadCatalog, findConnector, resolveTargetPath, resolveServerSpec, mergeToml, mergeJson };
