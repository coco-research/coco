#!/usr/bin/env bash
# Hermetic verification for `coco mcp` (compatible with bash 3.2 and bash 5).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="$ROOT/bin/coco.js"

T="$(mktemp -d)"
cleanup() { rm -rf "$T"; }
trap cleanup EXIT

USER_HOME="$T/userdir"
EMPTY_DIR="$T/empty-coco"
mkdir -p "$USER_HOME" "$EMPTY_DIR"

cat > "$T/net-guard.js" <<'EOF'
'use strict';
const fs = require('fs');
let calls = 0;
const block = (api) => function blocked() { calls += 1; throw new Error('Blocked network call: ' + api); };
for (const m of ['http', 'https']) { const mod = require(m); mod.request = block(m + '.request'); mod.get = block(m + '.get'); }
require('net').Socket.prototype.connect = block('net.connect');
require('tls').connect = block('tls.connect');
require('dns').lookup = block('dns.lookup');
require('dgram').Socket.prototype.send = block('dgram.send');
if (typeof globalThis.fetch === 'function') globalThis.fetch = block('fetch');
process.on('exit', () => {
  if (process.env.COCO_MCP_NET_LOG) {
    try { fs.writeFileSync(process.env.COCO_MCP_NET_LOG, String(calls), 'utf8'); } catch (_) {}
  }
});
EOF

SUMMARY="$(HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node - "$CLI" "$T" "$USER_HOME" "$EMPTY_DIR" "$ROOT" <<'NODE'
'use strict';
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const [cli, tmp, userHome, emptyDir, repoRoot] = process.argv.slice(2);
const guard = path.join(tmp, 'net-guard.js');
const assert = (cond, msg) => { if (!cond) { process.stderr.write('FAIL: ' + msg + '\n'); process.exit(1); } };

function startLineServer(tag, extraEnv) {
  const netLog = path.join(tmp, 'net-' + tag + '.count');
  const env = Object.assign({}, process.env, {
    HOME: userHome, COCO_NO_UPDATE_CHECK: '1', COCO_MCP_NET_LOG: netLog, NODE_OPTIONS: '--require ' + JSON.stringify(guard),
  }, extraEnv || {});
  if (!extraEnv || !Object.prototype.hasOwnProperty.call(extraEnv, 'COCO_DIR')) delete env.COCO_DIR;
  const proc = spawn(process.execPath, [cli, 'mcp'], { env, stdio: ['pipe', 'pipe', 'pipe'] });
  let stderr = '', buf = Buffer.alloc(0);
  const pending = new Map();
  const parseErrors = [];
  const strayMessages = [];
  proc.stderr.on('data', (d) => { stderr += d.toString('utf8'); });
  proc.stdout.on('data', (chunk) => {
    buf = Buffer.concat([buf, chunk]);
    for (;;) {
      const nl = buf.indexOf(0x0a);
      if (nl < 0) break;
      const rawLine = buf.subarray(0, nl).toString('utf8').replace(/\r$/, '');
      const byteLen = Buffer.byteLength(rawLine, 'utf8');
      buf = buf.subarray(nl + 1);
      if (!rawLine.trim()) continue;
      const msg = JSON.parse(rawLine);
      if (msg.id === null && msg.error && msg.error.code === -32700 && parseErrors.length > 0) {
        parseErrors.shift()({ msg, byteLen });
      } else if (pending.has(msg.id)) {
        const cb = pending.get(msg.id);
        pending.delete(msg.id);
        cb({ msg, byteLen });
      } else {
        strayMessages.push(msg);
      }
    }
  });
  return {
    request: (id, method, params) => new Promise((res) => { pending.set(id, res); proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n'); }),
    notify: (method, params) => proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', method, params }) + '\n'),
    sendMalformed: (raw) => new Promise((res) => { parseErrors.push(res); proc.stdin.write(raw + '\n'); }),
    strayCount: () => strayMessages.length,
    close: () => new Promise((res) => { proc.on('close', (code) => res({ code, stderr, netCalls: parseInt(fs.readFileSync(netLog, 'utf8').trim(), 10) })); proc.stdin.end(); }),
  };
}

function runContentLengthAndSymlinkProbe() {
  return new Promise((resolve, reject) => {
    const netLog = path.join(tmp, 'net-cl.count');
    const outside = path.join(tmp, 'outside.md');
    fs.writeFileSync(outside, '---\nname: escape\ndescription: nope\n---\noutside\n', 'utf8');
    const custom = path.join(tmp, 'custom-coco');
    fs.mkdirSync(path.join(custom, 'skills', 'safe-skill'), { recursive: true });
    fs.mkdirSync(path.join(custom, 'skills', 'escape'), { recursive: true });
    fs.writeFileSync(path.join(custom, 'skills', 'safe-skill', 'SKILL.md'), '---\nname: safe-skill\ndescription: fixture\n---\n' + 'x'.repeat(5000) + '\n', 'utf8');
    fs.symlinkSync(outside, path.join(custom, 'skills', 'escape', 'SKILL.md'));

    const env = Object.assign({}, process.env, {
      HOME: userHome, COCO_DIR: custom, COCO_MCP_MAX_BYTES: '2048', COCO_MCP_NET_LOG: netLog, NODE_OPTIONS: '--require ' + JSON.stringify(guard),
    });
    const proc = spawn(process.execPath, [cli, 'mcp'], { env, stdio: ['pipe', 'pipe', 'pipe'] });
    let out = Buffer.alloc(0);
    proc.stdout.on('data', (c) => { out = Buffer.concat([out, c]); });
    proc.on('error', reject);
    const sendCL = (o) => { const s = JSON.stringify(o); proc.stdin.write('Content-Length: ' + Buffer.byteLength(s, 'utf8') + '\r\n\r\n' + s); };
    sendCL({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'probe', version: '1.0' } } });
    sendCL({ jsonrpc: '2.0', id: 2, method: 'tools/call', params: { name: 'coco_skill', arguments: { name: 'escape' } } });
    sendCL({ jsonrpc: '2.0', id: 3, method: 'tools/call', params: { name: 'coco_skill', arguments: { name: 'safe-skill' } } });
    proc.stdin.end();
    proc.on('close', (code) => {
      assert(code === 0, 'Content-Length probe exited ' + code);
      const frames = [];
      let cur = out;
      while (cur.length > 0) {
        const sep = cur.indexOf('\r\n\r\n');
        assert(sep > 0, 'missing Content-Length separator');
        const len = parseInt(/Content-Length:\s*(\d+)/i.exec(cur.subarray(0, sep).toString('ascii'))[1], 10);
        frames.push({ len, msg: JSON.parse(cur.subarray(sep + 4, sep + 4 + len).toString('utf8')) });
        cur = cur.subarray(sep + 4 + len);
      }
      assert(frames.length === 3 && frames[0].msg.result.protocolVersion === '2024-11-05', '2024-11-05 negotiation failed');
      assert(frames[1].msg.result.isError === true, 'symlink escape was not refused');
      assert(frames[2].len <= 2048 && frames[2].msg.result.content[0].text.includes('truncated'), '2048 cap failed');
      resolve(parseInt(fs.readFileSync(netLog, 'utf8').trim(), 10));
    });
  });
}

(async () => {
  const s = startLineServer('main');
  const init = await s.request(1, 'initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'check-coco-mcp', version: '1.0.0' } });
  const proto = init.msg.result && init.msg.result.protocolVersion;
  assert(init.msg.id === 1 && proto === '2025-06-18' && init.msg.result.serverInfo.name === 'coco', 'handshake failed');
  s.notify('notifications/initialized', {});
  const pong = await s.request(2, 'ping', {});
  assert(pong.msg.id === 2 && pong.msg.result && typeof pong.msg.result === 'object', 'ping failed');

  const tools = (await s.request(3, 'tools/list', {})).msg.result.tools || [];
  const names = tools.map((t) => t.name);
  assert(names.includes('coco_search') && names.includes('coco_skill'), 'missing base tools');
  assert(tools.every((t) => t.annotations && t.annotations.readOnlyHint === true), 'missing readOnlyHint');

  const searchHumanizer = await s.request(4, 'tools/call', { name: 'coco_search', arguments: { query: 'humanizer', limit: 5 } });
  assert(searchHumanizer.msg.result.content[0].text.includes('humanizer'), 'coco_search missed humanizer');
  const searchCmd = await s.request(5, 'tools/call', { name: 'coco_search', arguments: { query: 'plan', kind: 'command', limit: 5 } });
  assert(searchCmd.msg.result.content[0].text.includes('[command]'), 'coco_search kind=command failed');
  const searchAgent = await s.request(6, 'tools/call', { name: 'coco_search', arguments: { query: 'reviewer', kind: 'agent', limit: 5 } });
  assert(searchAgent.msg.result.content[0].text.includes('[agent]'), 'coco_search kind=agent failed');

  const skillRes = await s.request(7, 'tools/call', { name: 'coco_skill', arguments: { name: 'prd-generator' } });
  assert(!skillRes.msg.result.isError, 'coco_skill(prd-generator) failed');
  const prdText = skillRes.msg.result.content[0].text;
  const expectedSkillBytes = fs.readFileSync(path.join(repoRoot, 'skills', 'prd-generator', 'SKILL.md'));
  assert(Buffer.from(prdText, 'utf8').equals(expectedSkillBytes), 'coco_skill(prd-generator) bytes do not match skills/prd-generator/SKILL.md');
  const prdKb = (expectedSkillBytes.length / 1024).toFixed(1);

  const tmpl = await s.request(8, 'resources/templates/list', {});
  assert(tmpl.msg.result.resourceTemplates[0].uriTemplate === 'coco://skill/{name}', 'missing template');
  const rList = await s.request(9, 'resources/list', {});
  assert(Array.isArray(rList.msg.result.resources) && rList.msg.result.resources.length > 0, 'empty resources');
  const rRead = await s.request(10, 'resources/read', { uri: 'coco://skill/prd-generator' });
  assert(Buffer.from(rRead.msg.result.contents[0].text, 'utf8').equals(expectedSkillBytes), 'resources/read bytes do not match SKILL.md');

  assert((await s.request(11, 'tools/call', { name: 'coco_skill', arguments: { name: '../etc' } })).msg.result.isError === true, '../etc tool not refused');
  assert((await s.request(111, 'tools/call', { name: 'coco_skill', arguments: { name: 'foo..bar' } })).msg.result.isError === true, 'foo..bar tool not refused');
  assert((await s.request(12, 'tools/call', { name: 'coco_skill', arguments: { name: '../etc/passwd' } })).msg.result.isError === true, '../etc/passwd not refused');
  assert((await s.request(13, 'tools/call', { name: 'coco_skill', arguments: { name: '/etc/passwd' } })).msg.result.isError === true, '/etc/passwd not refused');
  assert((await s.request(14, 'resources/read', { uri: 'coco://skill/../etc' })).msg.error.code === -32602, '../etc resource not refused');
  assert((await s.request(15, 'tools/call', { name: 'coco_skill', arguments: { name: 'nonexistent-skill-xyz' } })).msg.result.isError === true, 'unknown tool not refused');
  assert((await s.request(16, 'resources/read', { uri: 'coco://skill/nonexistent-skill-xyz' })).msg.error.code === -32002, 'unknown resource not refused');

  const unkMethod = await s.request(17, 'unknown/method', {});
  assert(unkMethod.msg.error && unkMethod.msg.error.code === -32601, 'unknown method did not return -32601');
  const badJson = await s.sendMalformed('{not-valid-json');
  assert(badJson.msg.error && badJson.msg.error.code === -32700, 'malformed JSON did not return -32700');

  const capRes = await s.request(18, 'tools/call', { name: 'coco_skill', arguments: { name: 'design-taste-frontend' } });
  assert(!capRes.msg.result.isError && capRes.byteLen <= 32768 && capRes.msg.result.content[0].text.includes('truncated at'), '32 KiB cap failed');
  assert(s.strayCount() === 0, 'notification produced an unexpected reply');

  const closedMain = await s.close();
  assert(closedMain.code === 0, 'server exited ' + closedMain.code + ': ' + closedMain.stderr);

  const emptySrv = startLineServer('empty', { COCO_DIR: emptyDir });
  await emptySrv.request(1, 'initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'empty', version: '1.0' } });
  const missingHint = await emptySrv.request(2, 'tools/call', { name: 'coco_skill', arguments: { name: 'humanizer' } });
  assert(missingHint.msg.result.isError === true && missingHint.msg.result.content[0].text.includes('npx cocosuperintelligence install'), 'missing install hint on empty COCO_DIR');
  const closedEmpty = await emptySrv.close();
  assert(closedEmpty.code === 0, 'empty server exited ' + closedEmpty.code);

  const totalNet = closedMain.netCalls + closedEmpty.netCalls + (await runContentLengthAndSymlinkProbe());
  assert(totalNet === 0, 'expected 0 network calls, saw ' + totalNet);

  process.stdout.write(
    'handshake ok (protocol ' + proto + ') · tools: coco_search, coco_skill · coco_skill(prd-generator) ' +
    prdKb + ' KB · ../etc refused · unknown refused · reply cap held · network calls ' + totalNet + '\n'
  );
})().catch((err) => { process.stderr.write((err && err.stack ? err.stack : String(err)) + '\n'); process.exit(1); });
NODE
)"

if [ -e "$USER_HOME/.coco" ]; then
  echo "FAIL: server touched ~/.coco in isolated HOME" >&2
  exit 1
fi

printf '%s\n' "$SUMMARY"
