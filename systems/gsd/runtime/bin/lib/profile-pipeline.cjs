/**
 * Profile Pipeline — session scanning, message extraction, and sampling
 *
 * Reads Claude Code session history (read-only) to extract user messages
 * for behavioral profiling. Three commands:
 *   - scan-sessions: list all projects and sessions
 *   - extract-messages: extract user messages from a specific project
 *   - profile-sample: multi-project sampling with recency weighting
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');
const { output, error, reapStaleTempFiles } = require('./core.cjs');

// ─── Session I/O Helpers ──────────────────────────────────────────────────────

function getSessionsDir(overridePath) {
  const dir = overridePath || path.join(os.homedir(), '.claude', 'projects');
  if (!fs.existsSync(dir)) return null;
  return dir;
}

function scanProjectDir(projectDirPath) {
  const entries = fs.readdirSync(projectDirPath);
  const sessions = [];

  for (const entry of entries) {
    if (!entry.endsWith('.jsonl')) continue;
    const sessionId = entry.replace('.jsonl', '');
    const filePath = path.join(projectDirPath, entry);
    const stat = fs.statSync(filePath);

    sessions.push({
      sessionId,
      filePath,
      size: stat.size,
      modified: stat.mtime,
    });
  }

  sessions.sort((a, b) => b.modified - a.modified);
  return sessions;
}

function readSessionIndex(projectDirPath) {
  try {
    const indexPath = path.join(projectDirPath, 'sessions-index.json');
    const raw = fs.readFileSync(indexPath, 'utf-8');
    const parsed = JSON.parse(raw);
    const entries = new Map();
    for (const entry of (parsed.entries || [])) {
      if (entry.sessionId) {
        entries.set(entry.sessionId, entry);
      }
    }
    return { originalPath: parsed.originalPath || null, entries };
  } catch {
    return { originalPath: null, entries: new Map() };
  }
}

function getProjectName(projectDirName, indexData, firstRecordCwd) {
  if (indexData && indexData.originalPath) {
    return path.basename(indexData.originalPath);
  }
  if (firstRecordCwd) {
    return path.basename(firstRecordCwd);
  }
  return projectDirName;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
  return `${(bytes / 1073741824).toFixed(1)} GB`;
}

function formatProjectTable(projects) {
  let out = '';
  out += 'Project'.padEnd(35) + 'Sessions'.padEnd(10) + 'Size'.padEnd(10) + 'Last Active\n';
  out += '-'.repeat(75) + '\n';
  for (const p of projects) {
    const name = p.name.length > 33 ? p.name.substring(0, 30) + '...' : p.name;
    out += name.padEnd(35) + String(p.sessionCount).padEnd(10) +
           p.totalSizeHuman.padEnd(10) + p.lastActive + '\n';
  }
  return out;
}

function formatSessionTable(sessions) {
  let out = '';
  out += '  Session ID'.padEnd(42) + 'Size'.padEnd(10) + 'Modified\n';
  out += '  ' + '-'.repeat(70) + '\n';
  for (const s of sessions) {
    const id = s.sessionId.length > 38 ? s.sessionId.substring(0, 35) + '...' : s.sessionId;
    out += '  ' + id.padEnd(40) + formatBytes(s.size).padEnd(10) +
           new Date(s.modified).toISOString().replace('T', ' ').substring(0, 19) + '\n';
  }
  return out;
}

// ─── Message Extraction Helpers ───────────────────────────────────────────────

function isGenuineUserMessage(record) {
  if (record.type !== 'user') return false;
  if (record.userType !== 'external') return false;
  if (record.isMeta === true) return false;
  if (record.isSidechain === true) return false;
  const content = record.message?.content;
  if (typeof content !== 'string') return false;
  if (content.length === 0) return false;
  if (content.startsWith('<local-command')) return false;
  if (content.startsWith('<command-')) return false;
  if (content.startsWith('<task-notification')) return false;
  if (content.startsWith('<local-command-stdout')) return false;
  return true;
}

function truncateContent(content, maxLen = 2000) {
  if (content.length <= maxLen) return content;
  return content.substring(0, maxLen) + '... [truncated]';
}

async function streamExtractMessages(filePath, filterFn, maxMessages = 300) {
  const rl = readline.createInterface({
    input: fs.createReadStream(filePath),
    crlfDelay: Infinity,
    terminal: false,
  });

  const messages = [];
  const sessionId = path.basename(filePath, '.jsonl');

  for await (const line of rl) {
    if (messages.length >= maxMessages) break;
    let record;
    try {
      record = JSON.parse(line);
    } catch {
      continue;
    }
    if (!filterFn(record)) continue;
    messages.push({
      sessionId,
      projectPath: record.cwd || null,
