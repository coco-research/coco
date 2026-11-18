'use strict';

// MCP harness connector CLI (`coco connect <tool> [--write] [--list] [--config <path>]`).
// ponytail: ceiling = declarative data/connectors.json + stdlib JSON/TOML block merger; upgrade path = full TOML/JSONC AST parser if inline JSON comments become common.

const fs = require('fs');
const os = require('os');
const path = require('path');

const TOML_START = '# coco:mcp-start';
const TOML_END = '# coco:mcp-end';

function loadCatalog(catalogPath) {
  const file = catalogPath || path.resolve(__dirname, '..', 'data', 'connectors.json');
  let raw;
  try {
    raw = fs.readFileSync(file, 'utf8');
  } catch (err) {
    throw new Error(`Connector catalog unreadable at ${file} (${err.message}).`);
  }
  let data;
  try {
    data = JSON.parse(raw);
  } catch (err) {
    throw new Error(`Connector catalog is not valid JSON (${err.message}).`);
  }
  if (!data || !Array.isArray(data.connectors)) {
    throw new Error('Connector catalog is missing a connectors array.');
  }
  return data.connectors;
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

function expandCatalogPath(rawPath, home, appBase) {
  const macAppPrefix = '~/Library/Application Support/';
  if (rawPath.startsWith(macAppPrefix)) {
    return path.join(appBase, ...rawPath.slice(macAppPrefix.length).split('/'));
  }
  if (rawPath.startsWith('~/')) {
    return path.join(home, ...rawPath.slice(2).split('/'));
  }
  return path.resolve(process.cwd(), rawPath);
}

function resolveFromEnvOrCatalog(envVar, envRel, rawPath, home, appBase) {
  if (envVar && process.env[envVar]) {
    return path.join(path.resolve(process.env[envVar]), ...String(envRel || '').split('/'));
  }
  return expandCatalogPath(rawPath, home, appBase);
}

function resolveTargetPath(conn, explicitConfig) {
  if (explicitConfig) return path.resolve(explicitConfig);
  if (conn.format === 'docs') return conn.config_path;
  const home = resolveHome();
  const plat = process.env.COCO_CONNECT_PLATFORM || process.platform;
  const appBase = appSupportDir(home, plat);
  const primary = resolveFromEnvOrCatalog(conn.env_home, conn.env_rel, conn.config_path, home, appBase);
  if (conn.legacy_path) {
    const legacy = resolveFromEnvOrCatalog(conn.legacy_env_home, conn.legacy_rel, conn.legacy_path, home, appBase);
    if (!fs.existsSync(path.dirname(primary)) && fs.existsSync(legacy)) return legacy;
  }
  return primary;
}

function legacyPathNotes(conn, home) {
  const notes = [];
  if (Array.isArray(conn.legacy_notes)) {
    for (const rel of conn.legacy_notes) {
      const p = path.join(home, ...rel.split('/'));
      if (fs.existsSync(p)) notes.push(`Note: legacy ${conn.name} config also exists at ${p}`);
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
    const before = prevText.slice(0, startIdx);
    const joined = before + block + (after ? '\n' + after : '\n');
    return joined.endsWith('\n') ? joined : joined + '\n';
  }
  const rawLines = prevText.split(/\r?\n/);
  const targetHdrRe = /^[ \t]*(\[\[?[ \t]*mcp_servers\.coco[ \t]*\]\]?)[ \t]*(?:#.*)?$/;
  const anyHdrRe = /^[ \t]*\[/;
  const matchedRanges = [];
  for (let i = 0; i < rawLines.length; i++) {
    const m = targetHdrRe.exec(rawLines[i]);
    if (!m) continue;
    const isArrayTable = m[1].startsWith('[[');
    let endLine = rawLines.length;
    for (let j = i + 1; j < rawLines.length; j++) {
      if (anyHdrRe.test(rawLines[j])) { endLine = j; break; }
    }
    matchedRanges.push({ start: i, end: endLine, isArrayTable, text: rawLines.slice(i, endLine).join('\n') });
    i = endLine - 1;
  }
  if (matchedRanges.length > 0) {
    const hasArrayTable = matchedRanges.some((r) => r.isArrayTable);
    if (hasArrayTable && !force) {
      throw new Error('Refusing to overwrite existing [[mcp_servers.coco]] array-of-tables entry (pass --force to replace).');
    }
    const allCocoOwned = !hasArrayTable && matchedRanges.length === 1 &&
      /cocosuperintelligence|coco(?:-mcp)?\.js/.test(matchedRanges[0].text);
    if (!allCocoOwned && !force) {
      throw new Error('Refusing to overwrite existing non-Coco [mcp_servers.coco] entry (pass --force to replace).');
    }
    const kept = [];
    let inserted = false;
    let cursor = 0;
    for (const r of matchedRanges) {
      if (r.start > cursor) kept.push(...rawLines.slice(cursor, r.start));
      if (!inserted) {
        while (kept.length > 0 && kept[kept.length - 1].trim() === '') kept.pop();
        if (kept.length > 0) kept.push('');
        kept.push(...block.split('\n'));
        inserted = true;
      }
      cursor = r.end;
    }
    if (cursor < rawLines.length) {
      const rest = rawLines.slice(cursor);
      while (rest.length > 0 && rest[0].trim() === '') rest.shift();
      if (rest.length > 0) kept.push('', ...rest);
    }
    while (kept.length > 0 && kept[kept.length - 1].trim() === '') kept.pop();
    return kept.join('\n') + '\n';
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
  let catalog;
  try {
    catalog = loadCatalog();
  } catch (err) {
    process.stderr.write(`Error: ${err.message}\n`);
    process.exit(2);
  }
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
    else if (a === '--config') {
      const next = argv[i + 1];
      if (!next || next.startsWith('-')) {
        process.stderr.write("Error: missing file path after '--config'.\n");
        process.exit(2);
      }
      flags.config = next;
      i++;
    } else if (a.startsWith('--config=')) {
      const val = a.slice('--config='.length);
      if (!val || val.startsWith('-')) {
        process.stderr.write("Error: missing file path after '--config='.\n");
        process.exit(2);
      }
      flags.config = val;
    } else if (a.startsWith('-')) {
      process.stderr.write(`Error: unknown flag '${a}'. Run 'coco connect --help'.\n`);
      process.exit(2);
    } else if (!tool) {
      tool = a;
    } else {
      process.stderr.write(`Error: unexpected extra argument '${a}'.\n`);
      process.exit(2);
    }
  }

  if (flags.help || (!flags.list && !tool)) {
    process.stdout.write(
      'Usage:\n' +
      '  coco connect --list                           list supported harnesses and verification levels\n' +
      '  coco connect <tool> [--npx|--local]           print MCP config snippet (no disk writes)\n' +
      '  coco connect <tool> --write [--config <path>] merge Coco MCP server into harness config\n'
    );
    if (!flags.help) process.exit(2);
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
