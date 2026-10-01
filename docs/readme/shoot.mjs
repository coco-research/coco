#!/usr/bin/env node
// Shoot docs/readme/si-decide-{light,dark}.png from the terminal template.
// Node >= 22. Built-in fetch and WebSocket only. No Playwright, no Puppeteer, no npm deps.
//
// Reads docs/readme/terminal/si-decide-run.txt and sets #out.textContent to that
// exact string, then calls styleTranscript() in the page. Words are not rewritten here.

import { spawn } from 'node:child_process'
import { mkdtempSync, rmSync, readFileSync, writeFileSync, existsSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

// CHROME_PATH wins. Otherwise the usual binary for this platform.
function chromeCandidates() {
  if (process.env.CHROME_PATH) return [process.env.CHROME_PATH]
  if (process.platform === 'darwin') {
    return ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome']
  }
  if (process.platform === 'linux') {
    return ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser']
  }
  if (process.platform === 'win32') {
    const programFiles = process.env.ProgramFiles || 'C:\\Program Files'
    return [path.join(programFiles, 'Google', 'Chrome', 'Application', 'chrome.exe')]
  }
  return []
}

const candidates = chromeCandidates()
const CHROME = candidates.find((p) => existsSync(p))
const here = path.dirname(fileURLToPath(import.meta.url))
const htmlPath = path.join(here, 'terminal', 'si-decide.html')
const runPath = path.join(here, 'terminal', 'si-decide-run.txt')

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

if (!CHROME) {
  const looked = candidates.length ? candidates.join(', ') : process.platform
  console.error('Chrome not found. Set CHROME_PATH to the browser binary. Looked for: ' + looked)
  process.exit(1)
}
if (!existsSync(htmlPath)) {
  console.error('Missing ' + htmlPath)
  process.exit(1)
}
if (!existsSync(runPath)) {
  console.error('Missing ' + runPath + ' (the real transcript). Refusing to invent one.')
  process.exit(1)
}

const transcript = readFileSync(runPath, 'utf8')
const fileUrl = pathToFileURL(htmlPath).href

let chrome
let userDataDir
let chromeLog = ''
let cleaned = false
function stopChrome(signal) {
  try { if (chrome) chrome.kill(signal) } catch { /* already gone */ }
}
function cleanup() {
  if (cleaned) return
  cleaned = true
  stopChrome('SIGKILL')
  if (!userDataDir) return
  try { rmSync(userDataDir, { recursive: true, force: true }) } catch { /* temp dir already gone */ }
}
process.on('exit', cleanup)
process.on('SIGINT', () => { cleanup(); process.exit(1) })
process.on('SIGTERM', () => { cleanup(); process.exit(1) })

let id = 0
const wait = new Map()

function cdp(sock, method, params = {}) {
  return new Promise((resolve, reject) => {
    const msgId = ++id
    const timer = setTimeout(() => {
      wait.delete(msgId)
      reject(new Error('CDP timeout: ' + method))
    }, 15000)
    wait.set(msgId, {
      resolve: (value) => { clearTimeout(timer); resolve(value) },
      reject: (err) => { clearTimeout(timer); reject(err) },
    })
    sock.send(JSON.stringify({ id: msgId, method, params }))
  })
}

async function evaluate(sock, expression, awaitPromise = false) {
  const res = await cdp(sock, 'Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise,
  })
  if (res.exceptionDetails) {
    const details = res.exceptionDetails
    const text = details.exception?.description || details.text || 'evaluate failed'
    throw new Error(text + '\n' + expression.slice(0, 200))
  }
  return res.result ? res.result.value : undefined
}

async function measureTerm(sock) {
  return evaluate(sock, `(() => {
    const r = document.getElementById('term').getBoundingClientRect();
    return { x: r.x, y: r.y, width: r.width, height: r.height };
  })()`)
}

// Chrome writes the chosen port to DevToolsActivePort when --remote-debugging-port=0.
async function debugPort() {
  const file = path.join(userDataDir, 'DevToolsActivePort')
  const deadline = Date.now() + 10000
  while (Date.now() < deadline) {
    try {
      const line = readFileSync(file, 'utf8').split(/\r?\n/, 1)[0].trim()
      if (/^\d+$/.test(line) && line !== '0') return line
    } catch {
      /* file not written yet */
    }
    if (chrome.exitCode !== null) break
    await sleep(100)
  }
  const why = chrome.exitCode !== null ? ' Chrome exited ' + chrome.exitCode + '.' : ''
  throw new Error('Chrome did not write DevToolsActivePort within 10s.' + why + (chromeLog ? '\n' + chromeLog : ''))
}

try {
  userDataDir = mkdtempSync(path.join(tmpdir(), 'coco-readme-shoot-'))
  // Node's built-in WebSocket sends no Origin header, so Chrome's CDP origin
  // check does not apply and --remote-allow-origins is omitted. A rejected
  // socket means this Chrome started requiring an Origin on debugger clients.
  chrome = spawn(CHROME, [
    '--headless=new',
    '--remote-debugging-port=0',
    '--user-data-dir=' + userDataDir,
    '--no-first-run',
    '--hide-scrollbars',
    'about:blank',
  ], { stdio: ['ignore', 'ignore', 'pipe'] })
  chrome.stderr.on('data', (buf) => {
    chromeLog = (chromeLog + buf.toString()).slice(-2000)
  })

  const port = await debugPort()
  let ws
  for (let i = 0; i < 40 && !ws; i++) {
    if (chrome.exitCode !== null) break
    try {
      const list = await (await fetch('http://127.0.0.1:' + port + '/json/list')).json()
      const page = list.find((x) => x.type === 'page' && x.webSocketDebuggerUrl)
      ws = page && page.webSocketDebuggerUrl
    } catch {
      /* debugger not up yet */
    }
    if (!ws) await sleep(250)
  }
  if (!ws) {
    const why = chrome.exitCode !== null ? ' Chrome exited ' + chrome.exitCode + '.' : ''
    throw new Error('Chrome debugger did not open on port ' + port + '.' + why + (chromeLog ? '\n' + chromeLog : ''))
  }

  const sock = new WebSocket(ws)
  sock.onmessage = (m) => {
    const d = JSON.parse(m.data)
    if (d.id && wait.has(d.id)) {
      const pending = wait.get(d.id)
      wait.delete(d.id)
      if (d.error) pending.reject(new Error(d.error.message || JSON.stringify(d.error)))
      else pending.resolve(d.result || {})
    }
  }
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('WebSocket did not open within 10s')), 10000)
    sock.onopen = () => { clearTimeout(timer); resolve() }
    sock.onerror = () => { clearTimeout(timer); reject(new Error('WebSocket failed')) }
  })

  await cdp(sock, 'Page.enable')
  await cdp(sock, 'Runtime.enable')
  await cdp(sock, 'Page.navigate', { url: fileUrl })
  // Navigation destroys the execution context. A rejected evaluate is a retry, not a fatal error.
  let ready = false
  let lastNavErr
  for (let i = 0; i < 50; i++) {
    try {
      const state = await evaluate(sock, 'document.readyState')
      if (state === 'complete' && await evaluate(sock, '!!document.getElementById("term")')) {
        ready = true
        break
      }
    } catch (err) {
      lastNavErr = err
    }
    await sleep(100)
  }
  if (!ready) throw lastNavErr || new Error('Page did not finish loading')

  // Exact transcript. textContent, so the page does not parse it as HTML.
  await evaluate(sock, 'document.getElementById("out").textContent = ' + JSON.stringify(transcript))
  await evaluate(sock, 'styleTranscript()')

  for (const theme of ['light', 'dark']) {
    await cdp(sock, 'Emulation.setEmulatedMedia', {
      features: [{ name: 'prefers-color-scheme', value: theme }],
    })
    await evaluate(sock, 'document.fonts.ready.then(() => true)', true)
    await evaluate(sock, 'new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))', true)

    const box = await measureTerm(sock)
    if (!box || !box.width || !box.height) throw new Error('No #term box for ' + theme)

    const width = Math.ceil(box.width)
    const height = Math.ceil(box.height)
    await cdp(sock, 'Emulation.setDeviceMetricsOverride', {
      width: Math.max(width, 1100),
      height: height + 2,
      deviceScaleFactor: 2,
      mobile: false,
    })
    await evaluate(sock, 'document.fonts.ready.then(() => true)', true)
    await evaluate(sock, 'new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))', true)

    const box2 = await measureTerm(sock)
    // scale 1: deviceScaleFactor 2 already produces a 2x PNG. clip.scale would multiply it.
    const clip = {
      x: Math.max(0, box2.x),
      y: Math.max(0, box2.y),
      width: Math.ceil(box2.width),
      height: Math.ceil(box2.height),
      scale: 1,
    }
    const shot = await cdp(sock, 'Page.captureScreenshot', {
      format: 'png',
      clip,
      captureBeyondViewport: true,
    })
    if (!shot.data) throw new Error('Empty screenshot for ' + theme)
    const out = path.join(here, 'si-decide-' + theme + '.png')
    writeFileSync(out, Buffer.from(shot.data, 'base64'))
    console.log(out + ' ' + clip.width + 'x' + clip.height)
  }

  sock.close()
} catch (err) {
  console.error(err && err.stack ? err.stack : err)
  process.exitCode = 1
} finally {
  // Stop Chrome before deleting its profile, or the dir comes back mid-unlink.
  stopChrome('SIGTERM')
  await sleep(400)
  cleanup()
}
