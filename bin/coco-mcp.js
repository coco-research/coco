'use strict';

// Read-only stdio MCP server (JSON-RPC 2.0, zero external dependencies, zero network).
// ponytail: ceiling = in-memory lexical index built once per stdio process (~5k files); upgrade path = prebuilt SQLite FTS5 index.

const fs = require('fs');
const os = require('os');
const path = require('path');
const si = require('./coco-mcp-si');

const SUPPORTED_PROTOCOLS = ['2025-06-18', '2025-03-26', '2024-11-05'];
const DEFAULT_PROTOCOL = '2025-06-18';
const DEFAULT_MAX_REPLY_BYTES = 32768;
const MAX_INPUT_FRAME_BYTES = 1024 * 1024;
const SKILL_NAME_RE = /^[a-z0-9][a-z0-9:._-]{0,127}$/i;
const MISSING_CHECKOUT_MSG = 'Coco content checkout not found. Run `npx cocosuperintelligence install` or set `COCO_DIR` to a Coco clone.';

function readPkgVersion(cocoDir) {
  const candidates = [cocoDir, path.resolve(__dirname, '..')].filter(Boolean);
  for (const base of candidates) {
    try {
      const v = JSON.parse(fs.readFileSync(path.join(base, 'package.json'), 'utf8')).version;
      if (v) return String(v);
    } catch (_) {}
  }
  return '0.0.0';
}

function resolveMaxBytes() {
  const n = parseInt(process.env.COCO_MCP_MAX_BYTES || '', 10);
  if (!Number.isFinite(n)) return DEFAULT_MAX_REPLY_BYTES;
  return Math.min(262144, Math.max(1024, n));
}

function hasDir(p) {
  try { return fs.statSync(p).isDirectory(); } catch (_) { return false; }
}

function hasFile(p) {
  try { return fs.statSync(p).isFile(); } catch (_) { return false; }
}

// Checkout resolution order:
// 1. $COCO_DIR (or --coco-dir); 2. package parent if skills/INDEX.md exists; 3. ~/.coco/src; 4. ./coco.
// Returns realpath string when skills/ exists, or null so tool calls emit the install hint as isError.
function resolveCocoDir(argv = []) {
  let cliDir = null;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--coco-dir' && argv[i + 1]) cliDir = argv[++i];
    else if (a.startsWith('--coco-dir=')) cliDir = a.slice('--coco-dir='.length);
  }
  const explicit = cliDir !== null ? cliDir : (Object.prototype.hasOwnProperty.call(process.env, 'COCO_DIR') ? process.env.COCO_DIR : null);
  if (explicit !== null) {
    if (!explicit) return null;
    try {
      const real = fs.realpathSync(explicit);
      return hasDir(path.join(real, 'skills')) ? real : null;
    } catch (_) { return null; }
  }
  const pkgRoot = path.resolve(__dirname, '..');
  if (hasFile(path.join(pkgRoot, 'skills', 'INDEX.md')) || hasDir(path.join(pkgRoot, 'skills'))) {
    try { return fs.realpathSync(pkgRoot); } catch (_) {}
  }
  const home = (process.env.HOME && process.env.HOME.trim()) ? process.env.HOME : os.homedir();
  for (const fallback of [path.join(home, '.coco', 'src'), path.resolve(process.cwd(), 'coco')]) {
    if (hasDir(path.join(fallback, 'skills'))) {
      try { return fs.realpathSync(fallback); } catch (_) {}
    }
  }
  return null;
}

function isInsideRoot(realRoot, targetPath) {
  const prefix = realRoot.endsWith(path.sep) ? realRoot : realRoot + path.sep;
  return targetPath === realRoot || targetPath.startsWith(prefix);
}

function parseFrontmatter(text) {
  if (!text.startsWith('---')) return {};
  const end = text.indexOf('\n---', 3);
  if (end < 0) return {};
  const out = {};
  for (const line of text.slice(3, end).split(/\r?\n/)) {
    const m = /^([a-zA-Z0-9_-]+)\s*:\s*(.*)$/.exec(line);
    if (!m) continue;
    let v = m[2].trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
    if (v && v !== '|' && v !== '>') out[m[1]] = v;
  }
  return out;
}

function firstParagraph(text) {
  let body = text;
  if (body.startsWith('---')) {
    const end = body.indexOf('\n---', 3);
    if (end >= 0) body = body.slice(end + 4);
  }
  for (const raw of body.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || line.startsWith('```') || line.startsWith('<!--')) continue;
    return line.replace(/^>\s*/, '').slice(0, 200);
  }
  return '';
}

function safeListDir(dir) {
  try { return fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)); }
  catch (_) { return []; }
}

function walkSkillFiles(dir, maxDepth, out) {
  if (maxDepth < 0) return;
  for (const ent of safeListDir(dir)) {
    if (ent.name.startsWith('.')) continue;
    const full = path.join(dir, ent.name);
    if (ent.isFile() && ent.name === 'SKILL.md') out.push(full);
    else if (ent.isDirectory() && maxDepth > 0) walkSkillFiles(full, maxDepth - 1, out);
  }
}

function validLookupKey(raw) {
  if (typeof raw !== 'string') return false;
  const s = raw.trim();
  if (!s || s.length > 128 || s.includes('..') || s.includes('/') || s.includes('\\') || s.includes('\0')) return false;
  return SKILL_NAME_RE.test(s);
}

function buildSkillIndex(cocoDir) {
  if (!cocoDir) return { realCocoDir: null, byName: new Map(), list: [], searchItems: [] };
  const realCocoDir = fs.realpathSync(cocoDir);
  const byName = new Map();
  const candidates = [];

  const core = [];
  walkSkillFiles(path.join(realCocoDir, 'skills'), 2, core);
  for (const file of core) candidates.push({ file, source: 'core', priority: 4 });

  for (const sysEnt of safeListDir(path.join(realCocoDir, 'systems'))) {
    if (!sysEnt.isDirectory() || sysEnt.name.startsWith('.')) continue;
    const bundleDir = path.join(realCocoDir, 'systems', sysEnt.name);
    const bundleSkills = [];
    walkSkillFiles(path.join(bundleDir, 'skills'), 3, bundleSkills);
    for (const file of bundleSkills) candidates.push({ file, source: `system:${sysEnt.name}`, priority: 3 });
    if (sysEnt.name === 'superintelligence') {
      for (const teamEnt of safeListDir(bundleDir)) {
        if (!teamEnt.isDirectory() || teamEnt.name.startsWith('.')) continue;
        const ts = path.join(bundleDir, teamEnt.name, 'SKILL.md');
        if (fs.existsSync(ts)) candidates.push({ file: ts, slugOverride: `si-${teamEnt.name}`, source: 'system:superintelligence', priority: 2 });
      }
    }
  }

  for (const adEnt of safeListDir(path.join(realCocoDir, 'adapters'))) {
    if (!adEnt.isDirectory() || adEnt.name.startsWith('.')) continue;
    const adSkills = [];
    walkSkillFiles(path.join(realCocoDir, 'adapters', adEnt.name, 'skills'), 2, adSkills);
    for (const file of adSkills) candidates.push({ file, source: `adapter:${adEnt.name}`, priority: 2 });
  }

  for (const item of candidates) {
    let realPath;
    try {
      realPath = fs.realpathSync(item.file);
      if (!fs.statSync(realPath).isFile() || !isInsideRoot(realCocoDir, realPath)) continue;
    } catch (_) { continue; }
    let text;
    try { text = fs.readFileSync(realPath, 'utf8'); } catch (_) { continue; }
    const fm = parseFrontmatter(text);
    const dirSlug = item.slugOverride || path.basename(path.dirname(realPath));
    const name = (fm.name && validLookupKey(fm.name)) ? fm.name.trim() : dirSlug;
    if (!validLookupKey(name)) continue;
    const entry = {
      name,
      slug: dirSlug,
      kind: 'skill',
      description: (fm.description || firstParagraph(text) || `Coco ${item.source} skill`).replace(/\s+/g, ' ').slice(0, 240),
      domain: fm.domain || '',
      source: item.source,
      priority: item.priority,
      relPath: path.relative(realCocoDir, realPath).split(path.sep).join('/'),
      realPath,
    };
    const key = name.toLowerCase();
    const prev = byName.get(key);
    if (!prev || entry.priority > prev.priority) byName.set(key, entry);
    if (validLookupKey(dirSlug) && !byName.has(dirSlug.toLowerCase())) byName.set(dirSlug.toLowerCase(), entry);
  }

  const unique = new Map();
  for (const e of byName.values()) if (!unique.has(e.realPath)) unique.set(e.realPath, e);
  const list = [...unique.values()].sort((a, b) => a.name.localeCompare(b.name));
  const searchItems = list.slice();

  // Index shipped commands and specialist agents for coco_search({ kind }).
  for (const nsEnt of safeListDir(path.join(realCocoDir, 'commands'))) {
    if (!nsEnt.isDirectory() || nsEnt.name.startsWith('.')) continue;
    for (const fEnt of safeListDir(path.join(realCocoDir, 'commands', nsEnt.name))) {
      if (!fEnt.isFile() || !fEnt.name.endsWith('.md')) continue;
      const stem = fEnt.name.slice(0, -3);
      if (/^[A-Z0-9_-]+$/.test(stem) || stem.startsWith('_')) continue;
      try {
        const rp = fs.realpathSync(path.join(realCocoDir, 'commands', nsEnt.name, fEnt.name));
        if (!isInsideRoot(realCocoDir, rp)) continue;
        const text = fs.readFileSync(rp, 'utf8');
        const fm = parseFrontmatter(text);
        const cmdName = `${nsEnt.name}:${stem}`;
        searchItems.push({
          name: cmdName, slug: stem, kind: 'command', priority: 3, domain: nsEnt.name,
          description: (fm.description || firstParagraph(text) || `Coco /${cmdName} command`).replace(/\s+/g, ' ').slice(0, 240),
        });
      } catch (_) {}
    }
  }

  for (const aEnt of safeListDir(path.join(realCocoDir, 'agents'))) {
    if (!aEnt.isFile() || !aEnt.name.endsWith('.md')) continue;
    const stem = aEnt.name.slice(0, -3);
    if (/^[A-Z0-9_-]+$/.test(stem)) continue;
    try {
      const rp = fs.realpathSync(path.join(realCocoDir, 'agents', aEnt.name));
      if (!isInsideRoot(realCocoDir, rp)) continue;
      const text = fs.readFileSync(rp, 'utf8');
      const fm = parseFrontmatter(text);
      const agName = (fm.name && validLookupKey(fm.name)) ? fm.name.trim() : stem;
      searchItems.push({
        name: agName, slug: stem, kind: 'agent', priority: 3, domain: fm.domain || 'engineering',
        description: (fm.description || firstParagraph(text) || `Coco ${agName} agent`).replace(/\s+/g, ' ').slice(0, 240),
      });
    } catch (_) {}
  }

  return { realCocoDir, byName, list, searchItems };
}

function capUtf8(text, maxBytes) {
  const full = Buffer.from(String(text), 'utf8');
  if (full.length <= maxBytes) return String(text);
  const suffix = `\n\n...[truncated at ${maxBytes} bytes]`;
  const sBuf = Buffer.from(suffix, 'utf8');
  if (sBuf.length >= maxBytes) return full.subarray(0, Math.max(0, maxBytes)).toString('utf8');
  let keep = maxBytes - sBuf.length;
  while (keep > 0 && (full[keep] & 0xc0) === 0x80) keep--;
  return full.subarray(0, keep).toString('utf8') + suffix;
}

function fitEnvelopeText(rawText, maxFrameBytes, buildMsg) {
  let budget = Math.max(128, maxFrameBytes - 256);
  for (let i = 0; i < 6; i++) {
    const candidate = capUtf8(rawText, budget);
    const actual = Buffer.byteLength(JSON.stringify(buildMsg(candidate)), 'utf8');
    if (actual <= maxFrameBytes) return candidate;
    budget = Math.max(64, budget - (actual - maxFrameBytes) - 64);
  }
  return capUtf8(rawText, 64);
}

function searchCatalog(index, rawQuery, rawKind, rawLimit) {
  const limit = Math.min(50, Math.max(1, parseInt(rawLimit, 10) || 10));
  const kind = rawKind ? String(rawKind).trim().toLowerCase() : '';
  const pool = kind ? index.searchItems.filter((it) => it.kind === kind) : index.searchItems;
  const q = String(rawQuery || '').trim().toLowerCase();
  if (!q) return pool.slice().sort((a, b) => (b.priority - a.priority) || a.name.localeCompare(b.name)).slice(0, limit);
  const terms = q.split(/[^a-z0-9:._-]+/).filter(Boolean);
  const scored = [];
  for (const entry of pool) {
    const nL = entry.name.toLowerCase(), sL = entry.slug.toLowerCase(), dL = entry.description.toLowerCase(), domL = (entry.domain || '').toLowerCase();
    let score = (nL === q || sL === q) ? 60 : (nL.startsWith(q) || sL.startsWith(q)) ? 30 : (nL.includes(q) || sL.includes(q)) ? 18 : 0;
    if (dL.includes(q)) score += 10;
    for (const t of terms) {
      if (nL === t || sL === t) score += 20;
      else if (nL.includes(t) || sL.includes(t)) score += 10;
      if (domL === t) score += 8;
      if (dL.includes(t)) score += 5;
    }
    if (score > 0) scored.push({ entry, score });
  }
  scored.sort((a, b) => (b.score - a.score) || (b.entry.priority - a.entry.priority) || a.entry.name.localeCompare(b.entry.name));
  return scored.slice(0, limit).map((s) => s.entry);
}

function lookupSkill(index, rawName) {
  if (!validLookupKey(rawName) || String(rawName).includes(':')) {
    return { ok: false, kind: 'invalid', message: 'Refused skill lookup: invalid name or path traversal.' };
  }
  const entry = index.byName.get(rawName.trim().toLowerCase());
  if (!entry) return { ok: false, kind: 'unknown', message: `Refused skill lookup: unknown skill '${rawName.trim()}'.` };
  if (!isInsideRoot(index.realCocoDir, entry.realPath)) return { ok: false, kind: 'invalid', message: 'Refused skill lookup: outside package root.' };
  try { return { ok: true, entry, content: fs.readFileSync(entry.realPath, 'utf8') }; }
  catch (_) { return { ok: false, kind: 'unknown', message: `Refused skill lookup: unreadable skill '${entry.name}'.` }; }
}

const READ_ONLY_ANNOTATIONS = { readOnlyHint: true, destructiveHint: false, openWorldHint: false };

const BASE_TOOLS = [
  {
    name: 'coco_search',
    description: 'Search Coco skills, commands, and agents by keyword (read-only, local index).',
    annotations: READ_ONLY_ANNOTATIONS,
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Case-insensitive search query across names and descriptions.' },
        kind: { type: 'string', enum: ['skill', 'command', 'agent'], description: 'Optional asset kind filter.' },
        limit: { type: 'integer', minimum: 1, maximum: 50, description: 'Maximum results to return (default 10, max 50).' },
      },
      additionalProperties: false,
    },
  },
  {
    name: 'coco_skill',
    description: 'Fetch a Coco skill SKILL.md document by exact allowlisted name (read-only, size-capped).',
    annotations: READ_ONLY_ANNOTATIONS,
    inputSchema: {
      type: 'object',
      properties: { name: { type: 'string', description: 'Allowlisted skill name from coco_search.' } },
      required: ['name'],
      additionalProperties: false,
    },
  },
];

const ALL_TOOLS = BASE_TOOLS.concat(si.siTools(READ_ONLY_ANNOTATIONS));
const SI_HELPERS = { validLookupKey, isInsideRoot, parseFrontmatter, safeListDir };

function createServerState(rawCocoDir) {
  let cocoDir = null;
  if (rawCocoDir) {
    try {
      const rp = fs.realpathSync(rawCocoDir);
      if (hasDir(path.join(rp, 'skills'))) cocoDir = rp;
    } catch (_) { cocoDir = null; }
  }
  let skillIndex = null, siIndex = null, promptIndex = null;
  const maxBytes = resolveMaxBytes();
  const pkgVersion = readPkgVersion(cocoDir);
  const getIndex = () => (skillIndex || (skillIndex = buildSkillIndex(cocoDir)));
  const getSi = () => (siIndex || (siIndex = si.buildSiIndex(cocoDir, SI_HELPERS)));
  const getPrompts = () => (promptIndex || (promptIndex = si.buildPromptIndex(cocoDir, getIndex(), getSi(), SI_HELPERS)));
  return { cocoDir, maxBytes, pkgVersion, getIndex, getSi, getPrompts };
}

function handleRpc(state, req) {
  if (!req || typeof req !== 'object' || Array.isArray(req) || req.jsonrpc !== '2.0' || typeof req.method !== 'string') {
    return { jsonrpc: '2.0', id: (req && req.id !== undefined) ? req.id : null, error: { code: -32600, message: 'Invalid Request' } };
  }
  if (!Object.prototype.hasOwnProperty.call(req, 'id')) return null;
  const id = req.id;
  const params = (req.params && typeof req.params === 'object' && !Array.isArray(req.params)) ? req.params : {};
  const maxBytes = state.maxBytes;

  switch (req.method) {
    case 'initialize': {
      const reqProto = typeof params.protocolVersion === 'string' ? params.protocolVersion : '';
      return {
        jsonrpc: '2.0',
        id,
        result: {
          protocolVersion: SUPPORTED_PROTOCOLS.includes(reqProto) ? reqProto : DEFAULT_PROTOCOL,
          capabilities: {
            tools: { listChanged: false },
            resources: { subscribe: false, listChanged: false },
            prompts: { listChanged: false },
          },
          serverInfo: { name: 'coco', title: 'Coco Super Intelligence', version: state.pkgVersion },
        },
      };
    }
    case 'ping':
      return { jsonrpc: '2.0', id, result: {} };
    case 'tools/list':
      return { jsonrpc: '2.0', id, result: { tools: ALL_TOOLS } };
    case 'tools/call': {
      const toolName = params.name;
      const args = (params.arguments && typeof params.arguments === 'object' && !Array.isArray(params.arguments)) ? params.arguments : {};
      if (!ALL_TOOLS.some((t) => t.name === toolName)) {
        return { jsonrpc: '2.0', id, error: { code: -32602, message: `Unknown tool: ${String(toolName || '')}` } };
      }
      if (!state.cocoDir) {
        return { jsonrpc: '2.0', id, result: { isError: true, content: [{ type: 'text', text: MISSING_CHECKOUT_MSG }] } };
      }
      if (toolName === 'coco_search') {
        if (args.kind !== undefined && !['skill', 'command', 'agent'].includes(String(args.kind))) {
          return { jsonrpc: '2.0', id, result: { isError: true, content: [{ type: 'text', text: "Invalid kind: expected 'skill', 'command', or 'agent'." }] } };
        }
        const hits = searchCatalog(state.getIndex(), args.query, args.kind, args.limit);
        const lines = hits.length ? hits.map((h) => `- ${h.name} [${h.kind}]: ${h.description}`) : ['No matching Coco entries found.'];
        const raw = `Coco matches (${hits.length}):\n${lines.join('\n')}`;
        const build = (t) => ({ jsonrpc: '2.0', id, result: { content: [{ type: 'text', text: t }] } });
        return build(fitEnvelopeText(raw, maxBytes, build));
      }
      if (toolName === 'coco_skill') {
        const res = lookupSkill(state.getIndex(), args.name);
        if (!res.ok) return { jsonrpc: '2.0', id, result: { isError: true, content: [{ type: 'text', text: res.message }] } };
        const build = (t) => ({ jsonrpc: '2.0', id, result: { content: [{ type: 'text', text: t }] } });
        return build(fitEnvelopeText(res.content, maxBytes, build));
      }
      if (toolName === 'coco_persona') {
        const res = si.callPersona(state.getSi(), args, SI_HELPERS);
        if (!res.ok) return { jsonrpc: '2.0', id, result: { isError: true, content: [{ type: 'text', text: res.message }] } };
        const build = (t) => ({ jsonrpc: '2.0', id, result: { content: [{ type: 'text', text: t }] } });
        return build(fitEnvelopeText(res.text, maxBytes, build));
      }
      const res = si.callBoard(state.getSi(), args, SI_HELPERS);
      if (!res.ok) return { jsonrpc: '2.0', id, result: { isError: true, content: [{ type: 'text', text: res.message }] } };
      const build = (t) => ({
        jsonrpc: '2.0',
        id,
        result: maxBytes >= 16384
          ? { content: [{ type: 'text', text: t }], structuredContent: res.structured }
          : { content: [{ type: 'text', text: t }] },
      });
      return build(fitEnvelopeText(res.text, maxBytes, build));
    }
    case 'prompts/list': {
      if (!state.cocoDir) return { jsonrpc: '2.0', id, result: { prompts: [] } };
      const pIdx = state.getPrompts();
      const start = Math.max(0, parseInt(params.cursor, 10) || 0);
      const page = 120;
      const prompts = pIdx.list.slice(start, start + page).map((p) => ({
        name: p.name, description: p.description, arguments: p.arguments,
      }));
      const result = { prompts };
      if (start + page < pIdx.list.length) result.nextCursor = String(start + page);
      return { jsonrpc: '2.0', id, result };
    }
    case 'prompts/get': {
      if (!state.cocoDir) return { jsonrpc: '2.0', id, error: { code: -32002, message: MISSING_CHECKOUT_MSG } };
      const res = si.getPrompt(state.getPrompts(), state.cocoDir, params.name, params.arguments, SI_HELPERS);
      if (!res.ok) return { jsonrpc: '2.0', id, error: { code: res.code, message: res.message } };
      const build = (t) => ({
        jsonrpc: '2.0',
        id,
        result: { description: res.entry.description, messages: [{ role: 'user', content: { type: 'text', text: t } }] },
      });
      return build(fitEnvelopeText(res.text, maxBytes, build));
    }
    case 'resources/templates/list':
      return {
        jsonrpc: '2.0',
        id,
        result: {
          resourceTemplates: [
            { uriTemplate: 'coco://skill/{name}', name: 'Coco Skill', description: 'Read an allowlisted Coco skill or engineering guide by name.', mimeType: 'text/markdown' },
            { uriTemplate: 'coco://persona/{department}/{name}', name: 'Coco Persona', description: 'Read an allowlisted Super Intelligence persona card by department and slug.', mimeType: 'text/markdown' },
          ],
        },
      };
    case 'resources/list': {
      if (!state.cocoDir) return { jsonrpc: '2.0', id, result: { resources: [] } };
      const idx = state.getIndex();
      const start = Math.max(0, parseInt(params.cursor, 10) || 0);
      const page = 50;
      const resources = idx.list.slice(start, start + page).map((s) => ({
        uri: `coco://skill/${s.name}`, name: s.name, description: s.description, mimeType: 'text/markdown',
      }));
      const result = { resources };
      if (start + page < idx.list.length) result.nextCursor = String(start + page);
      return { jsonrpc: '2.0', id, result };
    }
    case 'resources/read': {
      const uri = typeof params.uri === 'string' ? params.uri : '';
      if (uri.startsWith('coco://persona/')) {
        if (!state.cocoDir) return { jsonrpc: '2.0', id, error: { code: -32002, message: MISSING_CHECKOUT_MSG } };
        const rest = uri.slice('coco://persona/'.length);
        const slash = rest.indexOf('/');
        if (slash <= 0 || rest.indexOf('/', slash + 1) >= 0) {
          return { jsonrpc: '2.0', id, error: { code: -32602, message: 'Refused resource URI: expected coco://persona/<department>/<name>.' } };
        }
        const pRes = si.readPersonaResource(state.getSi(), rest.slice(0, slash), rest.slice(slash + 1), SI_HELPERS);
        if (!pRes.ok) return { jsonrpc: '2.0', id, error: { code: pRes.code, message: pRes.message } };
        const build = (t) => ({ jsonrpc: '2.0', id, result: { contents: [{ uri: pRes.uri, mimeType: 'text/markdown', text: t }] } });
        return build(fitEnvelopeText(pRes.text, maxBytes, build));
      }
      if (!uri.startsWith('coco://skill/')) {
        return { jsonrpc: '2.0', id, error: { code: -32602, message: 'Refused resource URI: expected coco://skill/<name> or coco://persona/<department>/<name>.' } };
      }
      if (!state.cocoDir) return { jsonrpc: '2.0', id, error: { code: -32002, message: MISSING_CHECKOUT_MSG } };
      const res = lookupSkill(state.getIndex(), uri.slice('coco://skill/'.length));
      if (!res.ok) return { jsonrpc: '2.0', id, error: { code: res.kind === 'invalid' ? -32602 : -32002, message: res.message } };
      const build = (t) => ({ jsonrpc: '2.0', id, result: { contents: [{ uri: `coco://skill/${res.entry.name}`, mimeType: 'text/markdown', text: t }] } });
      return build(fitEnvelopeText(res.content, maxBytes, build));
    }
    default:
      return { jsonrpc: '2.0', id, error: { code: -32601, message: `Method not found: ${req.method}` } };
  }
}

function sendFrame(msg, framing) {
  const payload = JSON.stringify(msg);
  if (framing === 'content-length') process.stdout.write(`Content-Length: ${Buffer.byteLength(payload, 'utf8')}\r\n\r\n${payload}`);
  else process.stdout.write(payload + '\n');
}

function dispatchRaw(state, rawJson, framing) {
  let parsed;
  try { parsed = JSON.parse(rawJson); }
  catch (_) { sendFrame({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } }, framing); return; }
  const reply = handleRpc(state, parsed);
  if (reply) sendFrame(reply, framing);
}

function runMcp(argv = []) {
  if (argv.includes('--help') || argv.includes('-h')) {
    process.stdout.write(
      'Usage: coco mcp [--coco-dir <dir>]\n\nStarts the read-only Coco MCP server over stdio (JSON-RPC 2.0).\n' +
      'Environment:\n  COCO_DIR            Content root (defaults to checkout or ~/.coco/src)\n' +
      '  COCO_MCP_MAX_BYTES  Maximum JSON-RPC reply size in bytes (default 32768)\n'
    );
    return;
  }
  const state = createServerState(resolveCocoDir(argv));
  let buf = Buffer.alloc(0);

  const drain = () => {
    while (buf.length > 0) {
      let lead = 0;
      while (lead < buf.length && (buf[lead] === 0x0d || buf[lead] === 0x0a)) lead++;
      if (lead > 0) { buf = buf.subarray(lead); if (!buf.length) break; }

      if (/^content-length\s*:/i.test(buf.subarray(0, Math.min(buf.length, 32)).toString('ascii'))) {
        let sepIdx = buf.indexOf('\r\n\r\n'), sepLen = 4;
        const lfIdx = buf.indexOf('\n\n');
        if (lfIdx >= 0 && (sepIdx < 0 || lfIdx < sepIdx)) { sepIdx = lfIdx; sepLen = 2; }
        if (sepIdx < 0) {
          if (buf.length > 4096) { buf = Buffer.alloc(0); sendFrame({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Header too large' } }, 'content-length'); }
          break;
        }
        const m = /content-length\s*:\s*(\d+)/i.exec(buf.subarray(0, sepIdx).toString('ascii'));
        if (!m) { buf = buf.subarray(sepIdx + sepLen); sendFrame({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Invalid Content-Length' } }, 'content-length'); continue; }
        const bodyLen = parseInt(m[1], 10);
        if (bodyLen > MAX_INPUT_FRAME_BYTES) { buf = Buffer.alloc(0); sendFrame({ jsonrpc: '2.0', id: null, error: { code: -32600, message: 'Frame exceeds maximum input size' } }, 'content-length'); break; }
        if (buf.length < sepIdx + sepLen + bodyLen) break;
        const rawJson = buf.subarray(sepIdx + sepLen, sepIdx + sepLen + bodyLen).toString('utf8');
        buf = buf.subarray(sepIdx + sepLen + bodyLen);
        dispatchRaw(state, rawJson, 'content-length');
      } else {
        const nl = buf.indexOf(0x0a);
        if (nl < 0) {
          if (buf.length > MAX_INPUT_FRAME_BYTES) { buf = Buffer.alloc(0); sendFrame({ jsonrpc: '2.0', id: null, error: { code: -32600, message: 'Line exceeds maximum input size' } }, 'line'); }
          break;
        }
        let lineBuf = buf.subarray(0, nl);
        buf = buf.subarray(nl + 1);
        if (lineBuf.length && lineBuf[lineBuf.length - 1] === 0x0d) lineBuf = lineBuf.subarray(0, lineBuf.length - 1);
        const rawJson = lineBuf.toString('utf8').trim();
        if (rawJson) dispatchRaw(state, rawJson, 'line');
      }
    }
  };

  process.stdin.on('data', (chunk) => { buf = buf.length ? Buffer.concat([buf, chunk]) : chunk; drain(); });
  process.stdin.on('end', drain);
}

module.exports = {
  runMcp, createServerState, handleRpc, resolveCocoDir, buildSkillIndex, capUtf8, fitEnvelopeText, validLookupKey, isInsideRoot, parseFrontmatter, safeListDir, READ_ONLY_ANNOTATIONS, MISSING_CHECKOUT_MSG,
};
