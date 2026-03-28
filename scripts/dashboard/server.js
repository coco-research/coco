/**
 * CoCo Dashboard Server
 *
 * Express server hosting the CoCo web dashboard at localhost:3000.
 * Endpoints:
 *   GET  /            — Chat page (static)
 *   GET  /api/events  — SSE stream tailing ~/.coco/events.jsonl
 *   POST /api/chat    — Spawn claude -p, stream response as SSE
 *   GET  /api/skills  — Skill catalog JSON (cached at startup)
 *   GET  /api/sessions — Session list JSON (last 24h)
 */

const express = require('express');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');
const matter = require('gray-matter');

const app = express();
const PORT = process.env.PORT || 3000;

const COCO_DIR = path.join(os.homedir(), '.coco');
const EVENTS_FILE = path.join(COCO_DIR, 'events.jsonl');
const PUBLIC_DIR = path.join(COCO_DIR, 'public');

// Middleware — block non-localhost origins (I-4)
app.use((req, res, next) => {
  const origin = req.get('Origin') || req.get('Referer') || '';
  if (origin && !/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/|$)/.test(origin)) {
    return res.status(403).json({ error: 'Forbidden: non-localhost origin' });
  }
  next();
});

app.use(express.json({ limit: '100kb' }));
app.use(express.static(PUBLIC_DIR));

// ---------------------------------------------------------------------------
// GET /api/events — SSE: tail events.jsonl
// ---------------------------------------------------------------------------
app.get('/api/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  // Ensure the events file exists
  if (!fs.existsSync(EVENTS_FILE)) {
    fs.writeFileSync(EVENTS_FILE, '', 'utf8');
  }

  let byteOffset = 0;

  // Send all existing events on connect
  try {
    const existing = fs.readFileSync(EVENTS_FILE, 'utf8');
    const lines = existing.split('\n').filter(Boolean);
    lines.forEach((line) => {
      res.write(`data: ${line}\n\n`);
    });
    byteOffset = Buffer.byteLength(existing, 'utf8');
  } catch (err) {
    // File might not exist yet — that is fine
  }

  // Watch for new lines appended to events.jsonl
  const onFileChange = (curr) => {
    try {
      const stat = fs.statSync(EVENTS_FILE);
      if (stat.size < byteOffset) {
        // File was rotated — reset
        byteOffset = 0;
      }
      if (stat.size <= byteOffset) return;

      const fd = fs.openSync(EVENTS_FILE, 'r');
      const newSize = stat.size - byteOffset;
      const buf = Buffer.alloc(newSize);
      fs.readSync(fd, buf, 0, newSize, byteOffset);
      fs.closeSync(fd);
      byteOffset = stat.size;

      const newContent = buf.toString('utf8');
      newContent.split('\n').filter(Boolean).forEach((line) => {
        res.write(`data: ${line}\n\n`);
      });
    } catch (err) {
      // Ignore transient read errors
    }
  };

  fs.watchFile(EVENTS_FILE, { interval: 500 }, onFileChange);

  // Heartbeat every 15s to keep connection alive
  const heartbeat = setInterval(() => {
    try { res.write(': heartbeat\n\n'); } catch (_) { /* connection closed */ }
  }, 15000);

  req.on('close', () => {
    fs.unwatchFile(EVENTS_FILE, onFileChange);
    clearInterval(heartbeat);
  });
});

// ---------------------------------------------------------------------------
// POST /api/chat — Spawn claude -p, stream response as SSE
// ---------------------------------------------------------------------------
app.post('/api/chat', (req, res) => {
  console.log('[chat] POST /api/chat body:', JSON.stringify(req.body).slice(0, 200));
  const { message } = req.body;
  if (!message) {
    return res.status(400).json({ error: 'message is required' });
  }

  // I-5: Input length validation (max 100KB)
  if (typeof message !== 'string' || Buffer.byteLength(message, 'utf8') > 100 * 1024) {
    return res.status(413).json({ error: 'message exceeds 100KB limit' });
  }

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  let proc;
  try {
    // Strip Claude Code env vars so spawned claude -p runs as a fresh instance
    const cleanEnv = { ...process.env };
    delete cleanEnv.CLAUDECODE;
    delete cleanEnv.CLAUDE_CODE_ENTRYPOINT;
    delete cleanEnv.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS;

    proc = spawn('claude', ['-p', '--output-format', 'text', message], {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: cleanEnv,
      cwd: process.env.HOME,
    });
    console.log('[chat] Spawned PID:', proc.pid, 'killed:', proc.killed);
    if (!proc.stdout) console.log('[chat] WARNING: proc.stdout is null!');
    if (!proc.pid) console.log('[chat] WARNING: proc.pid is undefined — spawn may have failed silently');
  } catch (err) {
    res.write(`data: ${JSON.stringify({ type: 'error', error: err.message })}\n\n`);
    res.write(`data: ${JSON.stringify({ type: 'done', code: 1 })}\n\n`);
    res.end();
    return;
  }

  // I-1: Kill process after 5 minutes to prevent runaway spawns
  const killTimer = setTimeout(() => {
    try { proc.kill(); } catch (_) { /* already dead */ }
    res.write(`data: ${JSON.stringify({ type: 'error', error: 'Process timed out after 5 minutes' })}\n\n`);
    res.write(`data: ${JSON.stringify({ type: 'done', code: 1 })}\n\n`);
    res.end();
  }, 5 * 60 * 1000);

  proc.stdout.on('data', (chunk) => {
    const text = chunk.toString();
    console.log("[chat] STDOUT EVENT FIRED, bytes:", chunk.toString().length, "first100:", chunk.toString().slice(0,100));
    res.write(`data: ${JSON.stringify({ type: 'text', text })}\n\n`);
  });

  let stderrBuf = '';
  proc.stderr.on('data', (chunk) => {
    stderrBuf += chunk.toString();
  });

  proc.on('close', (code) => {
    clearTimeout(killTimer);
    // No buffer to flush — text mode streams directly
    if (code !== 0 && stderrBuf) {
      res.write(`data: ${JSON.stringify({ type: 'error', error: stderrBuf.trim() })}\n\n`);
    }
    res.write(`data: ${JSON.stringify({ type: 'done', code: code || 0 })}\n\n`);
    res.end();
  });

  proc.on('error', (err) => {
    clearTimeout(killTimer);
    res.write(`data: ${JSON.stringify({ type: 'error', error: err.message })}\n\n`);
    res.write(`data: ${JSON.stringify({ type: 'done', code: 1 })}\n\n`);
    res.end();
  });

  // Kill the process if the client disconnects
  res.on('close', () => {
    clearTimeout(killTimer);
    try { proc.kill(); } catch (_) { /* already dead */ }
  });
});

// ---------------------------------------------------------------------------
// Skill Catalog — loaded at startup, cached
// ---------------------------------------------------------------------------
let skillsCache = [];

function detectFamily(id) {
  if (id.startsWith('gsd') || id.includes('/gsd/') || id.includes('gsd/')) return 'gsd';
  if (id.includes('pmstudio')) return 'pmstudio';
  if (id.startsWith('email') || id.includes('/email/')) return 'email';
  if (id.includes('team')) return 'team';
  const superpowers = [
    'brainstorming', 'executing-plans', 'writing-plans', 'systematic-debugging',
    'requesting-code-review', 'receiving-code-review', 'test-driven-development',
    'finishing-a-development-branch', 'subagent-driven-development',
    'verification-before-completion',
  ];
  if (superpowers.includes(id) || superpowers.some((s) => id.includes(s))) return 'superpowers';
  return 'standalone';
}

function loadSkills() {
  const skills = [];
  const commandsDir = path.join(os.homedir(), '.claude', 'commands');
  const skillsDir = path.join(os.homedir(), '.claude', 'skills');

  // Load commands/**/*.md
  if (fs.existsSync(commandsDir)) {
    try {
      const files = fs.readdirSync(commandsDir, { recursive: true })
        .filter((f) => f.toString().endsWith('.md'));
      for (const file of files) {
        try {
          const content = fs.readFileSync(path.join(commandsDir, file.toString()), 'utf8');
          const { data } = matter(content);
          const id = file.toString().replace(/\.md$/, '');
          skills.push({
            id,
            name: data.name || path.basename(id),
            description: data.description || '',
            family: detectFamily(id),
            source: 'commands',
          });
        } catch (_) { /* skip unreadable files */ }
      }
    } catch (_) { /* commands dir not readable */ }
  }

  // Load skills/*/SKILL.md
  if (fs.existsSync(skillsDir)) {
    try {
      const dirs = fs.readdirSync(skillsDir);
      for (const dir of dirs) {
        const skillFile = path.join(skillsDir, dir, 'SKILL.md');
        if (fs.existsSync(skillFile)) {
          try {
            const content = fs.readFileSync(skillFile, 'utf8');
            const { data } = matter(content);
            skills.push({
              id: dir,
              name: data.name || dir,
              description: data.description || '',
              family: detectFamily(dir),
              source: 'skills',
            });
          } catch (_) { /* skip unreadable */ }
        }
      }
    } catch (_) { /* skills dir not readable */ }
  }

  return skills;
}

// ---------------------------------------------------------------------------
// GET /api/skills — Skill catalog JSON
// ---------------------------------------------------------------------------
app.get('/api/skills', (_req, res) => {
  res.json(skillsCache);
});

// ---------------------------------------------------------------------------
// GET /api/sessions — Sessions from events.jsonl (last 24h)
// ---------------------------------------------------------------------------
app.get('/api/sessions', (_req, res) => {
  const sessions = groupEventsBySessions(EVENTS_FILE, 86400000);
  res.json(sessions);
});

function groupEventsBySessions(eventsPath, maxAgeMs) {
  if (!fs.existsSync(eventsPath)) return [];
  const cutoff = Date.now() - maxAgeMs;

  let lines;
  try {
    lines = fs.readFileSync(eventsPath, 'utf8').split('\n').filter(Boolean);
  } catch (_) {
    return [];
  }

  const sessionsMap = new Map();

  for (const line of lines) {
    try {
      const event = JSON.parse(line);
      if (event.ts < cutoff) continue;
      const sid = event.session;
      if (!sid) continue;
      if (!sessionsMap.has(sid)) {
        sessionsMap.set(sid, {
          id: sid,
          firstTs: event.ts,
          lastTs: event.ts,
          skill: null,
          eventCount: 0,
        });
      }
      const s = sessionsMap.get(sid);
      s.eventCount++;
      s.lastTs = Math.max(s.lastTs, event.ts);
      if (event.type === 'skill_invoked' && event.tool) s.skill = event.tool;
    } catch (_) { /* skip bad lines */ }
  }

  return Array.from(sessionsMap.values())
    .map((s) => ({
      ...s,
      status: (Date.now() - s.lastTs < 60000) ? 'active' : 'complete',
      duration: s.lastTs - s.firstTs,
    }))
    .sort((a, b) => b.lastTs - a.lastTs);
}

// ---------------------------------------------------------------------------
// Startup
// ---------------------------------------------------------------------------
// Load skills cache at startup
skillsCache = loadSkills();

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`CoCo dashboard running at http://localhost:${PORT}`);
    console.log('Chat backend: claude -p spawn (OAuth)');
    console.log(`Skills loaded: ${skillsCache.length}`);

    // Auto-open browser
    import('open').then((mod) => {
      const open = mod.default || mod;
      open(`http://localhost:${PORT}`).catch(() => {});
    }).catch(() => {});
  });
}

module.exports = app;
