# Phase 3: Voice I/O — Implementation Plan

**Date:** 2026-03-19
**Owner:** Rijul Kalra
**Status:** Planning
**Effort:** 2-3 days
**Depends on:** Phase 2 (parallel sessions, session-manager, updated orchestrator)
**Spec refs:** TECH-SPEC.md §4.1-4.2, ROADMAP.md Phase 3, RESEARCH.md voice findings

---

## Goal

Add push-to-talk voice input (whisper.cpp) and text-to-speech output (macOS `say`) to CoCo, making it hands-free capable. Fully offline. Graceful degradation when whisper.cpp is unavailable.

---

## Task Breakdown

### Task 1: whisper.cpp Installation and Setup Script

**File:** `src/voice/setup.ts`

**Purpose:** Detect, validate, and optionally install whisper.cpp and the base.en model on Apple Silicon.

```typescript
import { execSync, execFileSync } from 'child_process';
import { existsSync } from 'fs';
import path from 'path';

// Expected paths (overridable via env)
const WHISPER_BIN_DEFAULT = process.env.COCO_WHISPER_PATH
  ?? `${process.env.HOME}/.local/bin/whisper-stream`;
const WHISPER_MODEL_DEFAULT = process.env.COCO_WHISPER_MODEL_PATH
  ?? `${process.env.HOME}/.local/share/whisper/ggml-base.en.bin`;
const SOX_BIN = '/opt/homebrew/bin/sox';  // Apple Silicon Homebrew path

export interface WhisperSetupResult {
  available: boolean;
  whisperBin: string | null;
  modelPath: string | null;
  soxAvailable: boolean;
  errors: string[];
}

/**
 * Check all voice dependencies. Does NOT install anything —
 * returns a diagnostic so the caller can decide.
 */
export function checkVoiceDependencies(): WhisperSetupResult {
  const errors: string[] = [];

  // 1. Check whisper binary
  let whisperBin: string | null = null;
  const candidates = [
    WHISPER_BIN_DEFAULT,
    '/opt/homebrew/bin/whisper-cpp',        // Homebrew formula
    '/opt/homebrew/bin/whisper-cpp-stream',  // Homebrew stream variant
    '/usr/local/bin/whisper-stream',         // Intel Mac fallback
  ];
  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      whisperBin = candidate;
      break;
    }
  }
  // Also check PATH
  if (!whisperBin) {
    try {
      const which = execSync('which whisper-cpp 2>/dev/null || which whisper-stream 2>/dev/null', {
        encoding: 'utf-8',
      }).trim();
      if (which) whisperBin = which;
    } catch { /* not found */ }
  }
  if (!whisperBin) {
    errors.push(
      'whisper.cpp binary not found. Install via: brew install whisper-cpp ' +
      'or build from source (see Task 1 instructions below).'
    );
  }

  // 2. Check model file
  let modelPath: string | null = null;
  const modelCandidates = [
    WHISPER_MODEL_DEFAULT,
    `${process.env.HOME}/.local/share/whisper/ggml-base.en.bin`,
    '/opt/homebrew/share/whisper-cpp/models/ggml-base.en.bin',  // Homebrew model location
  ];
  for (const candidate of modelCandidates) {
    if (existsSync(candidate)) {
      modelPath = candidate;
      break;
    }
  }
  if (!modelPath) {
    errors.push(
      'Whisper base.en model not found. Download via:\n' +
      '  mkdir -p ~/.local/share/whisper && \\\n' +
      '  curl -L -o ~/.local/share/whisper/ggml-base.en.bin \\\n' +
      '    https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin'
    );
  }

  // 3. Check sox (for audio capture)
  let soxAvailable = false;
  try {
    execSync('which sox', { encoding: 'utf-8' });
    soxAvailable = true;
  } catch {
    errors.push('sox not found. Install via: brew install sox');
  }

  return {
    available: whisperBin !== null && modelPath !== null && soxAvailable,
    whisperBin,
    modelPath,
    soxAvailable,
    errors,
  };
}

/**
 * Convenience: print setup instructions to stderr and return availability.
 */
export function ensureVoiceReady(): boolean {
  const result = checkVoiceDependencies();
  if (!result.available) {
    console.error('[CoCo Voice] Dependencies missing:');
    for (const err of result.errors) {
      console.error(`  - ${err}`);
    }
    console.error('[CoCo Voice] Voice commands will be disabled. Use /voice status to retry.');
  }
  return result.available;
}
```

**Manual setup steps (for the plan, not code):**

```bash
# 1. Install whisper.cpp via Homebrew (Apple Silicon)
brew install whisper-cpp

# 2. Download the base.en model (~150MB, English-only, fastest)
mkdir -p ~/.local/share/whisper
curl -L -o ~/.local/share/whisper/ggml-base.en.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin

# 3. Install sox for audio capture
brew install sox

# 4. Verify
whisper-cpp --help          # should print usage
sox --version               # should print version
ls ~/.local/share/whisper/  # should show ggml-base.en.bin
```

**Alternative: build from source (if Homebrew formula is outdated):**

```bash
git clone https://github.com/ggerganov/whisper.cpp.git ~/src/whisper.cpp
cd ~/src/whisper.cpp
# Apple Silicon optimized build with CoreML + Metal acceleration
cmake -B build -DWHISPER_COREML=ON -DWHISPER_METAL=ON
cmake --build build --config Release -j$(sysctl -n hw.ncpu)
cp build/bin/whisper-stream ~/.local/bin/whisper-stream
```

**Verification:**
- [ ] `checkVoiceDependencies()` returns `{ available: true }` with all paths populated
- [ ] `whisper-cpp --help` exits cleanly
- [ ] Model file exists and is ~150MB
- [ ] `sox -d -t wav -r 16000 -c 1 -b 16 /tmp/test.wav trim 0 2` records 2 seconds of audio

---

### Task 2: Audio Capture Module

**File:** `src/voice/audio-capture.ts`

**Purpose:** Record microphone audio to a temporary WAV file using `sox`. Manages the record-on-press / stop-on-release lifecycle.

```typescript
import { ChildProcess, spawn } from 'child_process';
import { tmpdir } from 'os';
import { join } from 'path';
import { unlinkSync, existsSync } from 'fs';
import { EventEmitter } from 'eventemitter3';

interface AudioCaptureEvents {
  'recording-started': () => void;
  'recording-stopped': (wavPath: string, durationMs: number) => void;
  'error': (err: Error) => void;
}

export class AudioCapture extends EventEmitter<AudioCaptureEvents> {
  private soxProcess: ChildProcess | null = null;
  private currentWavPath: string | null = null;
  private recordStartTime: number = 0;
  private isRecording = false;

  /**
   * Start recording microphone audio to a temp WAV file.
   * Format: 16kHz, mono, 16-bit signed — what whisper.cpp expects.
   */
  startRecording(): void {
    if (this.isRecording) return;

    const wavPath = join(tmpdir(), `coco-voice-${Date.now()}.wav`);
    this.currentWavPath = wavPath;
    this.recordStartTime = Date.now();

    // sox -d = default audio device (microphone)
    // -t wav = output format
    // -r 16000 = 16kHz sample rate (whisper.cpp requirement)
    // -c 1 = mono
    // -b 16 = 16-bit
    this.soxProcess = spawn('sox', [
      '-d',               // default input device (microphone)
      '-t', 'wav',        // output format
      '-r', '16000',      // sample rate
      '-c', '1',          // mono
      '-b', '16',         // bit depth
      wavPath,            // output file
    ], {
      stdio: ['ignore', 'ignore', 'pipe'],  // capture stderr for errors
    });

    this.soxProcess.stderr?.on('data', (data: Buffer) => {
      const msg = data.toString();
      // sox prints "Input File" info to stderr on start — ignore that
      if (msg.includes('FAIL') || msg.includes('error')) {
        this.emit('error', new Error(`sox recording error: ${msg}`));
      }
    });

    this.soxProcess.on('error', (err) => {
      this.emit('error', new Error(`Failed to start sox: ${err.message}`));
      this.isRecording = false;
    });

    this.isRecording = true;
    this.emit('recording-started');
  }

  /**
   * Stop recording. Returns the path to the recorded WAV file.
   * Sends SIGINT to sox for clean shutdown (writes WAV header correctly).
   */
  stopRecording(): void {
    if (!this.isRecording || !this.soxProcess) return;

    const wavPath = this.currentWavPath!;
    const durationMs = Date.now() - this.recordStartTime;

    // SIGINT causes sox to finalize the WAV header and exit cleanly
    this.soxProcess.kill('SIGINT');

    this.soxProcess.on('exit', () => {
      this.isRecording = false;
      this.soxProcess = null;

      // Discard recordings shorter than 500ms (accidental key taps)
      if (durationMs < 500) {
        this.cleanup(wavPath);
        return;
      }

      if (existsSync(wavPath)) {
        this.emit('recording-stopped', wavPath, durationMs);
      } else {
        this.emit('error', new Error('Recording file not created'));
      }
    });
  }

  /** Clean up a temporary WAV file */
  cleanup(wavPath: string): void {
    try {
      if (existsSync(wavPath)) unlinkSync(wavPath);
    } catch { /* best effort */ }
  }

  /** Is currently recording? */
  get recording(): boolean {
    return this.isRecording;
  }
}
```

**Verification:**
- [ ] `startRecording()` spawns sox, `recording` returns `true`
- [ ] `stopRecording()` kills sox cleanly, emits `recording-stopped` with a valid WAV path
- [ ] WAV file plays correctly: `afplay /tmp/coco-voice-*.wav`
- [ ] Recordings under 500ms are discarded (no event emitted)
- [ ] Microphone permission prompt appears on first run (macOS system dialog)

---

### Task 3: Listener — whisper.cpp Transcription

**File:** `src/voice/listener.ts`

**Purpose:** Accept a WAV file from AudioCapture, run whisper.cpp on it, return transcribed text. Includes a technical-term post-processing dictionary.

```typescript
import { execFile } from 'child_process';
import { existsSync } from 'node:fs';
import { promisify } from 'util';
import { EventEmitter } from 'eventemitter3';
import { checkVoiceDependencies, WhisperSetupResult } from './setup.js';

const execFileAsync = promisify(execFile);

interface ListenerEvents {
  'transcription': (text: string, durationMs: number) => void;
  'error': (err: Error) => void;
  'status': (msg: string) => void;
}

export interface ListenerConfig {
  whisperBin: string;
  modelPath: string;
  language: string;       // "en"
  threads: number;        // CPU threads for inference (default: 4)
}

/**
 * Post-processing dictionary for commonly misheard technical terms.
 * whisper.cpp struggles with CLI/code vocabulary — this fixes the top offenders.
 */
const TECH_CORRECTIONS: Array<[RegExp, string]> = [
  [/\bcube\s*cut(?:tle|le)\b/gi, 'kubectl'],
  [/\bcube\s*c?t?l?\b/gi, 'kubectl'],
  [/\bdocker\s*file\b/gi, 'Dockerfile'],
  [/\bnpm\b/gi, 'npm'],
  [/\bpip\s*install\b/gi, 'pip install'],
  [/\bgit\s*hub\b/gi, 'GitHub'],
  [/\btype\s*script\b/gi, 'TypeScript'],
  [/\bjava\s*script\b/gi, 'JavaScript'],
  [/\bnode\s*j\.?s\.?\b/gi, 'Node.js'],
  [/\breact\s*j\.?s\.?\b/gi, 'React'],
  [/\bnext\s*j\.?s\.?\b/gi, 'Next.js'],
  [/\bpost\s*gres\b/gi, 'Postgres'],
  [/\bmysql\b/gi, 'MySQL'],
  [/\bmongo\s*d\.?b\.?\b/gi, 'MongoDB'],
  [/\bdynamo\s*d\.?b\.?\b/gi, 'DynamoDB'],
  [/\blambda\b/gi, 'Lambda'],
  [/\ba\.?p\.?i\.?\s*gateway\b/gi, 'API Gateway'],
  [/\be\.?k\.?s\.?\b/gi, 'EKS'],
  [/\bcloud\s*watch\b/gi, 'CloudWatch'],
  [/\bslash\s*team\b/gi, '/team'],
  [/\bslash\s*g\.?s\.?d\.?\b/gi, '/gsd'],
  [/\bslash\s*voice\b/gi, '/voice'],
  [/\bcoco\b/gi, 'CoCo'],
  [/\bink\b/gi, 'Ink'],
];

function applyTechCorrections(text: string): string {
  let corrected = text;
  for (const [pattern, replacement] of TECH_CORRECTIONS) {
    corrected = corrected.replace(pattern, replacement);
  }
  return corrected.trim();
}

export class Listener extends EventEmitter<ListenerEvents> {
  private config: ListenerConfig;
  private busy = false;

  constructor(config: ListenerConfig) {
    super();
    this.config = config;
  }

  /**
   * Transcribe a WAV file using whisper.cpp.
   * Returns the transcribed text after post-processing.
   *
   * whisper.cpp CLI usage:
   *   whisper-cpp -m <model> -f <wav> -t <threads> -l en --no-timestamps --no-prints
   *
   * Flags:
   *   -m  model path
   *   -f  input WAV file (16kHz, mono, 16-bit)
   *   -t  threads
   *   -l  language
   *   --no-timestamps  omit [00:00.000 --> 00:05.000] prefixes
   *   --no-prints  no-prints (suppress progress output, only emit text)
   */
  async transcribe(wavPath: string): Promise<string | null> {
    if (this.busy) {
      this.emit('status', 'Transcription already in progress, skipping.');
      return null;
    }

    this.busy = true;
    const startTime = Date.now();

    try {
      this.emit('status', 'Transcribing...');

      const { stdout, stderr } = await execFileAsync(this.config.whisperBin, [
        '-m', this.config.modelPath,
        '-f', wavPath,
        '-t', String(this.config.threads),
        '-l', this.config.language,
        '--no-timestamps',
        '--no-prints',  // no progress prints
      ], {
        timeout: 30_000,  // 30s max — if it takes longer, something is wrong
      });

      const durationMs = Date.now() - startTime;
      const rawText = stdout.trim();

      if (!rawText) {
        this.emit('status', 'No speech detected.');
        return null;
      }

      const correctedText = applyTechCorrections(rawText);

      this.emit('transcription', correctedText, durationMs);
      this.emit('status', `Transcribed in ${durationMs}ms: "${correctedText}"`);

      return correctedText;
    } catch (err: any) {
      const error = new Error(`Transcription failed: ${err.message}`);
      this.emit('error', error);
      return null;
    } finally {
      this.busy = false;
    }
  }

  /** Create a Listener from auto-detected dependencies */
  static fromAutoDetect(): Listener | null {
    const deps = checkVoiceDependencies();
    if (!deps.available || !deps.whisperBin || !deps.modelPath) {
      return null;
    }
    return new Listener({
      whisperBin: deps.whisperBin,
      modelPath: deps.modelPath,
      language: 'en',
      threads: 4,
    });
  }
}
```

**Verification:**
- [ ] Record a 5-second test: `sox -d -t wav -r 16000 -c 1 -b 16 /tmp/test.wav trim 0 5`
- [ ] Transcribe: `whisper-cpp -m ~/.local/share/whisper/ggml-base.en.bin -f /tmp/test.wav --no-timestamps --no-prints`
- [ ] Output matches spoken words with >90% accuracy on plain English
- [ ] `applyTechCorrections("cube cuttle get pods")` returns `"kubectl get pods"`
- [ ] Transcription latency <2s for a 10-second recording on M-series Mac

---

### Task 4: Speaker — Text-to-Speech via macOS `say`

**File:** `src/voice/speaker.ts`

**Purpose:** Speak CoCo's response headlines using macOS `say`. Non-blocking, interruptible, with voice and rate selection.

```typescript
import { ChildProcess, spawn, execSync } from 'child_process';

export interface SpeakerConfig {
  voice: string;    // macOS voice name: "Samantha", "Alex", "Ava", "Tom"
  rate: number;     // words per minute (default: 200, range: 100-400)
  enabled: boolean;
}

export class Speaker {
  private config: SpeakerConfig;
  private currentProcess: ChildProcess | null = null;

  constructor(config: SpeakerConfig) {
    this.config = config;
  }

  /**
   * Speak text using macOS `say` command.
   * Non-blocking — fires and forgets. Call stop() to interrupt.
   *
   * Usage: say -v Samantha -r 200 "text"
   */
  async speak(text: string): Promise<void> {
    if (!this.config.enabled) return;
    if (!text.trim()) return;

    // Stop any current speech first
    this.stop();

    return new Promise<void>((resolve) => {
      this.currentProcess = spawn('say', [
        '-v', this.config.voice,
        '-r', String(this.config.rate),
        text,
      ], {
        stdio: 'ignore',
      });

      this.currentProcess.on('exit', () => {
        this.currentProcess = null;
        resolve();
      });

      this.currentProcess.on('error', () => {
        this.currentProcess = null;
        resolve();  // don't throw — TTS failure is non-critical
      });
    });
  }

  /**
   * Speak only the summary of a response:
   * - First sentence (up to first period, question mark, or exclamation)
   * - Truncated to 200 chars max
   * - Never reads code blocks, file paths, or raw output
   */
  async speakSummary(text: string): Promise<void> {
    if (!this.config.enabled) return;

    // Strip markdown formatting
    let clean = text
      .replace(/```[\s\S]*?```/g, '')   // remove code blocks
      .replace(/`[^`]+`/g, '')           // remove inline code
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')  // [text](url) -> text
      .replace(/[#*_~>]/g, '')           // remove markdown symbols
      .replace(/\n+/g, ' ')             // collapse newlines
      .trim();

    // Extract first sentence
    const sentenceEnd = clean.search(/[.!?]/);
    if (sentenceEnd > 0 && sentenceEnd < 200) {
      clean = clean.slice(0, sentenceEnd + 1);
    } else if (clean.length > 200) {
      clean = clean.slice(0, 200) + '...';
    }

    if (clean.length > 5) {  // don't speak trivially short text
      await this.speak(clean);
    }
  }

  /** Interrupt current speech immediately */
  stop(): void {
    if (this.currentProcess) {
      this.currentProcess.kill('SIGTERM');
      this.currentProcess = null;
    }
  }

  /** Update configuration at runtime */
  updateConfig(partial: Partial<SpeakerConfig>): void {
    Object.assign(this.config, partial);
  }

  /** Is currently speaking? */
  get speaking(): boolean {
    return this.currentProcess !== null;
  }

  /** List available macOS voices (for /voice config) */
  static listVoices(): string[] {
    try {
      const output = execSync('say -v ?', { encoding: 'utf-8' });
      // Parse: "Alex   en_US  # Most people ..."
      return output
        .split('\n')
        .filter((line: string) => line.includes('en_'))  // English voices only
        .map((line: string) => line.split(/\s+/)[0])
        .filter(Boolean);
    } catch {
      return ['Samantha', 'Alex', 'Ava', 'Tom'];  // fallback defaults
    }
  }
}
```

**Verification:**
- [ ] `new Speaker({ voice: 'Samantha', rate: 200, enabled: true }).speak("CoCo ready.")` speaks audibly
- [ ] `speakSummary("## Done\n\nBuilt the auth service.\n```code block```\nMore details...")` speaks only "Built the auth service."
- [ ] `stop()` silences speech immediately mid-sentence
- [ ] `Speaker.listVoices()` returns at least 4 English voice names
- [ ] TTS failure (e.g., invalid voice name) does NOT crash CoCo — silently degrades

---

### Task 5: Push-to-Talk Hotkey Binding

**File:** `src/voice/hotkey.ts`

**Purpose:** Bind a push-to-talk key (F5 by default) so that holding the key records, releasing transcribes, and the result feeds into the orchestrator.

```typescript
import { EventEmitter } from 'eventemitter3';

interface HotkeyEvents {
  'ptt-start': () => void;
  'ptt-stop': () => void;
}

/**
 * Push-to-talk controller.
 *
 * Works with Ink's useInput hook. The App component calls
 * handleKeyPress on every raw keypress. This module tracks
 * whether the PTT key is held down.
 *
 * Key binding: F5 (default), configurable via state context.
 *
 * Ink key mapping for F5: key.escape sequence "\x1b[15~"
 * (or use a simpler key like Ctrl+Space for terminals that
 * don't pass F-keys reliably).
 */
/**
 * Push-to-talk mode:
 * - 'hold': Hold key to record, release to stop (uses key-repeat detection).
 *   NOTE: Hold-to-record relies on terminal key-repeat and may not work on
 *   all terminals. If your terminal does not send key-repeat events,
 *   use 'toggle' mode instead.
 * - 'toggle': First press starts recording, second press stops.
 *   More reliable across terminals since it does not depend on key-repeat.
 */
type PTTMode = 'hold' | 'toggle';

export class PushToTalkController extends EventEmitter<HotkeyEvents> {
  private pttKey: string;
  private isHeld = false;
  private mode: PTTMode;

  constructor(pttKey: string = 'f5', mode: PTTMode = 'hold') {
    super();
    this.pttKey = pttKey;
    this.mode = mode;
  }

  /**
   * Called from Ink's useInput or raw stdin handler.
   *
   * For Ink's useInput(input, key):
   *   - key.escape, key.return, key.tab, etc. are booleans
   *   - F-keys come through as raw escape sequences
   *
   * Strategy: In App.tsx, set stdin to raw mode and listen for
   * the F5 escape sequence directly.
   *
   * F5 = ESC [ 1 5 ~  = "\x1b[15~"
   * Ctrl+Space = "\x00"
   *
   * Supports two modes:
   * - 'hold': keydown starts, keyup (detected via repeat timeout) stops
   * - 'toggle': first press starts, second press stops
   */
  handleRawData(data: Buffer): boolean {
    const str = data.toString();

    // F5 escape sequence
    const isF5 = str === '\x1b[15~';
    // Ctrl+Space
    const isCtrlSpace = str === '\x00';

    const isPTTKey = (this.pttKey === 'f5' && isF5)
      || (this.pttKey === 'ctrl+space' && isCtrlSpace);

    if (!isPTTKey) return false;  // not our key, don't consume

    if (this.mode === 'toggle') {
      return this.handleToggle();
    }
    return this.handleHold();
  }

  private handleToggle(): boolean {
    if (!this.isHeld) {
      // First press — start recording
      this.isHeld = true;
      this.emit('ptt-start');
    } else {
      // Second press — stop recording
      this.isHeld = false;
      if (this.releaseTimer) clearTimeout(this.releaseTimer);
      this.emit('ptt-stop');
    }
    return true;
  }

  private handleHold(): boolean {
    if (!this.isHeld) {
      // Key just pressed — start recording
      this.isHeld = true;
      this.emit('ptt-start');

      // Set a timer: if we don't see the key again within 150ms,
      // treat it as "released". Terminals don't have keyup events,
      // so we use key-repeat detection.
      this.startReleaseDetection();
    } else {
      // Key is being held (auto-repeat) — reset release timer
      this.resetReleaseTimer();
    }

    return true;  // consumed the key event
  }

  private releaseTimer: ReturnType<typeof setTimeout> | null = null;

  private startReleaseDetection(): void {
    this.releaseTimer = setTimeout(() => {
      // No repeat received within window — key was released
      this.isHeld = false;
      this.emit('ptt-stop');
    }, 200);  // 200ms — generous for key repeat interval
  }

  private resetReleaseTimer(): void {
    if (this.releaseTimer) clearTimeout(this.releaseTimer);
    this.startReleaseDetection();
  }

  /** Switch between hold and toggle mode at runtime */
  setMode(mode: PTTMode): void {
    this.mode = mode;
  }

  /** Force stop (e.g., when voice is toggled off) */
  forceRelease(): void {
    if (this.isHeld) {
      this.isHeld = false;
      if (this.releaseTimer) clearTimeout(this.releaseTimer);
      this.emit('ptt-stop');
    }
  }

  get held(): boolean {
    return this.isHeld;
  }

  /** Update the PTT key binding */
  setKey(key: string): void {
    this.pttKey = key;
  }
}
```

**Integration point in App.tsx:**

```tsx
// In App.tsx, inside the component:

import { useStdin } from 'ink';
import { PushToTalkController } from '../voice/hotkey.js';
import { AudioCapture } from '../voice/audio-capture.js';
import { Listener } from '../voice/listener.js';

// Inside component body:
const { stdin, setRawMode } = useStdin();
const pttRef = useRef(new PushToTalkController());
const captureRef = useRef(new AudioCapture());
const listenerRef = useRef(Listener.fromAutoDetect());

useEffect(() => {
  if (!voiceEnabled || !listenerRef.current) return;

  setRawMode(true);

  const ptt = pttRef.current;
  const capture = captureRef.current;
  const listener = listenerRef.current;

  // Wire PTT -> AudioCapture -> Listener -> Orchestrator
  ptt.on('ptt-start', () => {
    capture.startRecording();
    setStatusMessage('Recording...');
  });

  ptt.on('ptt-stop', () => {
    capture.stopRecording();
    setStatusMessage('Transcribing...');
  });

  capture.on('recording-stopped', async (wavPath, durationMs) => {
    const text = await listener.transcribe(wavPath);
    capture.cleanup(wavPath);
    if (text) {
      // Feed transcribed text into the SAME pipeline as typed text
      orchestrator.handleInput(text);
      setStatusMessage('');
    }
  });

  // Listen for raw key data
  const onData = (data: Buffer) => ptt.handleRawData(data);
  stdin?.on('data', onData);

  return () => {
    stdin?.off('data', onData);
    ptt.removeAllListeners();
    capture.removeAllListeners();
  };
}, [voiceEnabled]);
```

**Verification:**
- [ ] Hold mode: Pressing F5 emits `ptt-start` and begins recording
- [ ] Hold mode: Releasing F5 (no repeat within 200ms) emits `ptt-stop` and starts transcription
- [ ] Toggle mode: First F5 press emits `ptt-start`, second press emits `ptt-stop`
- [ ] Toggle mode: Works on terminals that don't send key-repeat events
- [ ] Transcribed text appears in orchestrator as if the user typed it
- [ ] Short taps (<500ms) are discarded by AudioCapture
- [ ] `forceRelease()` cleanly stops recording if voice is toggled off mid-record
- [ ] `setMode('toggle')` switches to toggle mode at runtime

---

### Task 6: Voice Manager — Orchestration Layer

**File:** `src/voice/voice-manager.ts`

**Purpose:** Single entry point that owns the full voice pipeline (setup, capture, listener, speaker, hotkey). Handles `/voice on|off|status` commands and graceful degradation.

```typescript
import { EventEmitter } from 'eventemitter3';
import { checkVoiceDependencies, WhisperSetupResult } from './setup.js';
import { AudioCapture } from './audio-capture.js';
import { Listener, ListenerConfig } from './listener.js';
import { Speaker, SpeakerConfig } from './speaker.js';
import { PushToTalkController } from './hotkey.js';

type VoiceState = 'off' | 'ready' | 'recording' | 'transcribing' | 'speaking' | 'unavailable';

interface VoiceManagerEvents {
  'state-change': (state: VoiceState) => void;
  'transcription': (text: string) => void;
  'error': (err: Error) => void;
}

export interface VoiceManagerConfig {
  pttKey: string;
  speakerVoice: string;
  speakerRate: number;
  whisperThreads: number;
}

const DEFAULTS: VoiceManagerConfig = {
  pttKey: 'f5',
  speakerVoice: 'Samantha',
  speakerRate: 200,
  whisperThreads: 4,
};

export class VoiceManager extends EventEmitter<VoiceManagerEvents> {
  private state: VoiceState = 'off';
  private deps: WhisperSetupResult;
  private capture: AudioCapture;
  private listener: Listener | null = null;
  private speaker: Speaker;
  private ptt: PushToTalkController;
  private config: VoiceManagerConfig;

  constructor(config: Partial<VoiceManagerConfig> = {}) {
    super();
    this.config = { ...DEFAULTS, ...config };

    // Check dependencies on construction
    this.deps = checkVoiceDependencies();

    // Always create speaker (macOS `say` has no dependencies)
    this.speaker = new Speaker({
      voice: this.config.speakerVoice,
      rate: this.config.speakerRate,
      enabled: false,  // starts disabled, enabled via /voice on
    });

    // Create capture and PTT controller
    this.capture = new AudioCapture();
    this.ptt = new PushToTalkController(this.config.pttKey);

    // Create listener only if whisper.cpp is available
    if (this.deps.available && this.deps.whisperBin && this.deps.modelPath) {
      this.listener = new Listener({
        whisperBin: this.deps.whisperBin,
        modelPath: this.deps.modelPath,
        language: 'en',
        threads: this.config.whisperThreads,
      });
    }

    this.wireEvents();
  }

  private wireEvents(): void {
    this.ptt.on('ptt-start', () => {
      if (this.state !== 'ready') return;
      this.setState('recording');
      this.capture.startRecording();
    });

    this.ptt.on('ptt-stop', () => {
      if (this.state !== 'recording') return;
      this.capture.stopRecording();
      this.setState('transcribing');
    });

    this.capture.on('recording-stopped', async (wavPath) => {
      if (!this.listener) {
        this.setState('ready');
        return;
      }
      const text = await this.listener.transcribe(wavPath);
      this.capture.cleanup(wavPath);

      if (text) {
        this.emit('transcription', text);
      }
      this.setState('ready');
    });

    this.capture.on('error', (err) => {
      this.emit('error', err);
      this.setState('ready');
    });
  }

  private setState(newState: VoiceState): void {
    this.state = newState;
    this.emit('state-change', newState);
  }

  // --- Public API for /voice commands ---

  /**
   * /voice on — Enable voice input and output.
   * Returns a status message for the UI.
   */
  turnOn(): string {
    // Re-check dependencies so re-installing whisper.cpp takes effect
    // without restarting CoCo
    this.deps = checkVoiceDependencies();

    // Enable TTS first — macOS `say` has no external dependencies
    // and should work even when whisper.cpp/sox are missing
    this.speaker.updateConfig({ enabled: true });

    if (!this.deps.available) {
      // Recreate listener in case deps were just installed
      this.listener = null;
      this.setState('unavailable');
      const missing = this.deps.errors.join('\n  ');
      return `Voice partially enabled (TTS only). Missing STT dependencies:\n  ${missing}`;
    }

    // Recreate listener with fresh deps
    if (this.deps.whisperBin && this.deps.modelPath) {
      this.listener = new Listener({
        whisperBin: this.deps.whisperBin,
        modelPath: this.deps.modelPath,
        language: 'en',
        threads: this.config.whisperThreads,
      });
    }

    this.setState('ready');
    return `Voice enabled. Hold ${this.config.pttKey.toUpperCase()} to talk. Say "/voice off" to disable.`;
  }

  /**
   * /voice off — Disable voice input and output.
   */
  turnOff(): string {
    this.ptt.forceRelease();
    this.speaker.stop();
    this.speaker.updateConfig({ enabled: false });
    this.setState('off');
    return 'Voice disabled.';
  }

  /**
   * /voice status — Show current voice state and configuration.
   */
  status(): string {
    const lines = [
      `Voice state: ${this.state}`,
      `STT (whisper.cpp): ${this.deps.whisperBin ?? 'NOT FOUND'}`,
      `Model: ${this.deps.modelPath ?? 'NOT FOUND'}`,
      `sox: ${this.deps.soxAvailable ? 'available' : 'NOT FOUND'}`,
      `TTS voice: ${this.config.speakerVoice} @ ${this.config.speakerRate} wpm`,
      `Push-to-talk key: ${this.config.pttKey.toUpperCase()}`,
      `All dependencies met: ${this.deps.available ? 'YES' : 'NO'}`,
    ];
    if (!this.deps.available) {
      lines.push('', 'Missing:');
      for (const err of this.deps.errors) {
        lines.push(`  - ${err}`);
      }
    }
    return lines.join('\n');
  }

  /**
   * Speak a response summary (called by orchestrator on session completion).
   */
  async speakResponse(text: string): Promise<void> {
    await this.speaker.speakSummary(text);
  }

  /** Expose PTT controller for raw stdin wiring in App.tsx */
  get pttController(): PushToTalkController {
    return this.ptt;
  }

  /** Current voice state */
  get currentState(): VoiceState {
    return this.state;
  }
}
```

**Verification:**
- [ ] `new VoiceManager().turnOn()` returns success message when deps are present
- [ ] `new VoiceManager().turnOn()` returns degradation message listing missing deps when they are absent
- [ ] Full pipeline: hold F5 -> speak -> release F5 -> transcription appears -> text sent to orchestrator
- [ ] `/voice off` mid-recording stops recording cleanly
- [ ] `/voice status` prints all dependency paths and current config

---

### Task 7: Orchestrator Integration — /voice Commands

**File:** `src/core/orchestrator.ts` (modify existing)

**Purpose:** Add `/voice on|off|status` as meta-commands in the orchestrator. Wire voice transcription events into `handleInput()`. Wire session completion into TTS.

```typescript
// Add to orchestrator.ts constructor:

import { VoiceManager } from '../voice/voice-manager.js';

/**
 * Events emitted by the Orchestrator.
 * Includes voice-related events added in Phase 3.
 */
interface OrchestratorEvents {
  // --- Phase 1/2 events ---
  // (existing events defined in earlier phases)

  // --- Phase 3: Voice events ---
  voice_input: (data: { text: string }) => void;
  system_message: (data: { text: string }) => void;
  session_complete: (data: { summary: string }) => void;
}

/**
 * Options-object constructor pattern (cross-phase alignment).
 * All dependencies injected via a single object.
 */
interface OrchestratorDeps {
  state: StateManager;
  skills: SkillRegistry;
  sessionManager?: SessionManager;
  taskQueue?: TaskQueue;
  voiceManager?: VoiceManager;
}

class Orchestrator extends EventEmitter<OrchestratorEvents> {
  private voiceManager: VoiceManager;

  constructor(deps: OrchestratorDeps) {
    super();
    const { state, skills, sessionManager, taskQueue } = deps;
    // ... existing init ...

    // Initialize voice (loads config from state)
    const voiceConfig = {
      pttKey: state.getContext('push_to_talk_key') ?? 'f5',
      speakerVoice: state.getContext('voice_name') ?? 'Samantha',
      speakerRate: parseInt(state.getContext('voice_rate') ?? '200', 10),
      whisperThreads: 4,
    };
    this.voiceManager = new VoiceManager(voiceConfig);

    // When voice transcribes text, feed it into the same input pipeline
    this.voiceManager.on('transcription', (text: string) => {
      this.emit('voice_input', { text });
      this.handleInput(text);  // same pipeline as typed text
    });

    // When a session completes, speak the summary
    this.on('session_complete', (event: { summary: string }) => {
      this.voiceManager.speakResponse(event.summary);
    });
  }

  // Add to the meta-command handler inside handleInput():
  async handleInput(text: string): Promise<void> {
    const trimmed = text.trim();

    // --- Meta-command handling (add these cases) ---

    if (trimmed === '/voice on') {
      const msg = this.voiceManager.turnOn();
      this.emit('system_message', { text: msg });
      this.state.setContext('voice_enabled', 'true');
      return;
    }

    if (trimmed === '/voice off') {
      const msg = this.voiceManager.turnOff();
      this.emit('system_message', { text: msg });
      this.state.setContext('voice_enabled', 'false');
      return;
    }

    if (trimmed === '/voice status') {
      const msg = this.voiceManager.status();
      this.emit('system_message', { text: msg });
      return;
    }

    // /voice config <key> <value> — e.g., /voice config voice Alex
    const voiceConfigMatch = trimmed.match(/^\/voice\s+config\s+(\w+)\s+(.+)$/);
    if (voiceConfigMatch) {
      const [, key, value] = voiceConfigMatch;
      const validKeys: Record<string, string> = {
        voice: 'voice_name',
        rate: 'voice_rate',
        key: 'push_to_talk_key',
      };
      if (validKeys[key]) {
        this.state.setContext(validKeys[key], value);
        this.emit('system_message', {
          text: `Voice config updated: ${key} = ${value}. Restart voice to apply.`,
        });
      } else {
        this.emit('system_message', {
          text: `Unknown voice config key: ${key}. Valid keys: voice, rate, key`,
        });
      }
      return;
    }

    // --- Existing meta-command handling continues below ---
    // /status, /halt, /queue, /history, etc.
    // ... (unchanged) ...

    // --- Intent classification and dispatch ---
    // ... (unchanged) ...
  }

  // Expose voice manager for App.tsx to wire PTT
  get voice(): VoiceManager {
    return this.voiceManager;
  }

  // Add to startup():
  async startup(): Promise<void> {
    // ... existing startup logic ...

    // Auto-enable voice if it was on in the last session
    if (this.state.getContext('voice_enabled') === 'true') {
      const msg = this.voiceManager.turnOn();
      this.emit('system_message', { text: msg });
    }
  }
}
```

**Verification:**
- [ ] Typing `/voice on` enables voice, persists `voice_enabled=true` in SQLite context
- [ ] Typing `/voice off` disables voice, persists `voice_enabled=false`
- [ ] Typing `/voice status` prints dependency info and config
- [ ] Voice transcription goes through the exact same `handleInput()` path as typed text
- [ ] Session completion triggers `speakSummary()` on the response
- [ ] Restarting CoCo auto-enables voice if it was on in the last session
- [ ] `/voice config voice Alex` updates the stored voice name

---

### Task 8: StatusBar Voice Indicator

**File:** `src/ui/StatusBar.tsx` (modify existing)

**Purpose:** Show microphone state in the status bar.

```tsx
// Add voiceState prop to StatusBar:

interface StatusBarProps {
  project: string;
  branch: string;
  activeSessions: number;
  queueDepth: number;
  voiceState: 'off' | 'ready' | 'recording' | 'transcribing' | 'speaking' | 'unavailable';
  clock: string;
}

// In the render, add a voice indicator segment:

function voiceIndicator(state: StatusBarProps['voiceState']): string {
  switch (state) {
    case 'off':           return '';            // don't show when off
    case 'ready':         return 'mic:on';      // idle, ready to record
    case 'recording':     return 'mic:REC';     // actively recording (could use red color)
    case 'transcribing':  return 'mic:...';     // processing
    case 'speaking':      return 'mic:TTS';     // speaking response
    case 'unavailable':   return 'mic:N/A';     // deps missing
  }
}

// Render line:
// CoCo | how-i-pm-with-ai (main) | 2 active | Q:3 | mic:REC | 14:32
```

**Color coding (Ink `<Text>` with `color` prop):**
- `mic:on` — green
- `mic:REC` — red, bold
- `mic:...` — yellow
- `mic:TTS` — cyan
- `mic:N/A` — dim gray

**Verification:**
- [ ] Status bar shows no mic indicator when voice is off
- [ ] Status bar shows `mic:on` (green) when voice is enabled and idle
- [ ] Status bar shows `mic:REC` (red) when recording
- [ ] Status bar shows `mic:...` (yellow) when transcribing

---

### Task 9: Graceful Degradation

**File:** Spread across `voice-manager.ts`, `orchestrator.ts`, `setup.ts`

**Purpose:** If whisper.cpp is not installed, voice commands do not crash CoCo. They print helpful setup instructions and disable only the STT portion. TTS (macOS `say`) still works independently.

**Degradation matrix:**

| Missing Dependency | STT (record+transcribe) | TTS (say) | /voice on | /voice status |
|---|---|---|---|---|
| Nothing missing | Works | Works | Enables both | Shows all green |
| whisper.cpp binary | Disabled | Works | Enables TTS only, prints whisper install instructions | Shows whisper as missing |
| whisper model file | Disabled | Works | Enables TTS only, prints model download instructions | Shows model as missing |
| sox | Disabled | Works | Enables TTS only, prints sox install instructions | Shows sox as missing |
| All three missing | Disabled | Works | Enables TTS only, prints full setup guide | Shows all missing |

**Implementation — handled in VoiceManager.turnOn():**

When `turnOn()` is called it:
1. Re-checks dependencies via `this.deps = checkVoiceDependencies()` (so re-installing whisper.cpp takes effect without restarting CoCo)
2. Enables TTS *first* (`speaker.updateConfig({ enabled: true })`) — before the dependency check — so macOS `say` always works regardless of STT availability
3. If `deps.available === false`, returns a "partially enabled (TTS only)" message with setup instructions
4. If `deps.available === true`, recreates the Listener with fresh paths and enters `ready` state
- The PTT controller simply does not start recording when state is `unavailable`
- Speaker is always available since macOS `say` is a system binary

**Additional safeguard in listener.ts:**

```typescript
// In Listener.transcribe(), if the binary doesn't exist at runtime
// (e.g., user uninstalled whisper.cpp while CoCo was running):
async transcribe(wavPath: string): Promise<string | null> {
  if (!existsSync(this.config.whisperBin)) {
    this.emit('error', new Error(
      'whisper.cpp binary no longer found. Run /voice status for setup instructions.'
    ));
    return null;
  }
  // ... rest of transcription
}
```

**Verification:**
- [ ] Uninstall whisper.cpp, run `/voice on` — get helpful message, TTS still works
- [ ] Delete model file, run `/voice on` — get model download instructions
- [ ] Remove sox, run `/voice on` — get sox install instructions
- [ ] All three missing — get complete setup guide, `say` still speaks responses
- [ ] Re-install whisper.cpp, run `/voice on` — STT works again (deps re-checked on every turnOn call, no restart needed)

---

### Task 10: Tests

**File:** `tests/voice/`

**Test files and what they cover:**

```
tests/voice/
├── setup.test.ts          # dependency detection (mock fs.existsSync, execSync)
├── audio-capture.test.ts  # sox spawn/kill lifecycle (mock child_process)
├── listener.test.ts       # transcription + tech corrections (mock execFile)
├── speaker.test.ts        # say command + summary extraction (mock spawn)
├── hotkey.test.ts         # PTT key detection + release timer
└── voice-manager.test.ts  # full pipeline integration (mock all subprocess calls)
```

**Key test cases:**

```typescript
// setup.test.ts
describe('checkVoiceDependencies', () => {
  it('returns available:true when all deps present', ...);
  it('returns available:false with errors when whisper missing', ...);
  it('checks multiple candidate paths for whisper binary', ...);
  it('checks PATH via which as fallback', ...);
});

// listener.test.ts
describe('Listener', () => {
  it('transcribes WAV and returns text', ...);
  it('applies tech corrections to output', ...);
  it('returns null for empty transcription', ...);
  it('respects 30s timeout', ...);
  it('rejects concurrent transcriptions', ...);
});

// speaker.test.ts
describe('Speaker', () => {
  it('spawns say with correct voice and rate', ...);
  it('speakSummary extracts first sentence only', ...);
  it('strips markdown from summary', ...);
  it('stop() kills active speech process', ...);
  it('does nothing when enabled:false', ...);
});

// hotkey.test.ts
describe('PushToTalkController', () => {
  it('emits ptt-start on first F5 keypress (hold mode)', ...);
  it('emits ptt-stop after 200ms without repeat (hold mode)', ...);
  it('does not emit ptt-stop during key repeat (hold mode)', ...);
  it('toggle mode: first press starts, second press stops', ...);
  it('toggle mode: does not use release timer', ...);
  it('forceRelease cancels active recording', ...);
  it('handles Ctrl+Space as alternative PTT key', ...);
  it('setMode switches between hold and toggle at runtime', ...);
});

// voice-manager.test.ts
describe('VoiceManager', () => {
  it('turnOn returns success when deps available', ...);
  it('turnOn returns degradation message when deps missing but enables TTS', ...);
  it('turnOn re-checks dependencies (picks up newly installed whisper.cpp)', ...);
  it('full pipeline: ptt-start -> record -> ptt-stop -> transcribe -> emit', ...);
  it('turnOff mid-recording stops cleanly', ...);
  it('status() lists all dependency states', ...);
});
```

**Verification:**
- [ ] `npm test -- tests/voice/` passes all tests
- [ ] Tests run without requiring actual whisper.cpp, sox, or microphone (all mocked)
- [ ] Coverage >80% on all voice modules

---

## File Summary

| # | File | Action | Purpose |
|---|------|--------|---------|
| 1 | `src/voice/setup.ts` | Create | Dependency detection and setup instructions |
| 2 | `src/voice/audio-capture.ts` | Create | sox-based microphone recording |
| 3 | `src/voice/listener.ts` | Create | whisper.cpp transcription + tech corrections |
| 4 | `src/voice/speaker.ts` | Create | macOS `say` TTS with summary extraction |
| 5 | `src/voice/hotkey.ts` | Create | Push-to-talk key binding (F5 / Ctrl+Space) |
| 6 | `src/voice/voice-manager.ts` | Create | Pipeline orchestration, /voice commands |
| 7 | `src/core/orchestrator.ts` | Modify | Add /voice meta-commands, wire transcription to handleInput |
| 8 | `src/ui/App.tsx` | Modify | Wire PTT raw stdin handler, pass voiceState to StatusBar |
| 9 | `src/ui/StatusBar.tsx` | Modify | Add mic state indicator with color coding |
| 10 | `tests/voice/*.test.ts` | Create | Unit and integration tests for all voice modules |

---

## Execution Order

```
Day 1 (Foundation)
  Task 1: setup.ts          — dependency detection
  Task 2: audio-capture.ts  — sox recording
  Task 3: listener.ts       — whisper.cpp transcription
  Task 4: speaker.ts        — macOS say TTS
  [ Checkpoint: each module works standalone via manual test ]

Day 2 (Integration)
  Task 5: hotkey.ts          — push-to-talk binding
  Task 6: voice-manager.ts   — pipeline orchestration
  Task 7: orchestrator.ts    — /voice commands + input wiring
  Task 8: StatusBar.tsx       — mic indicator
  Task 9: degradation         — verify all failure modes
  [ Checkpoint: full voice pipeline works end-to-end ]

Day 3 (Polish)
  Task 10: tests              — unit + integration tests
  Tech corrections dictionary — expand based on real usage
  Performance tuning          — verify <2s transcription latency
  [ Checkpoint: all tests pass, demo recording ]
```

---

## Open Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Terminal doesn't pass F5 key | Medium | PTT unusable | Support Ctrl+Space as fallback; `/voice config key ctrl+space`; toggle mode (`setMode('toggle')`) for terminals without key-repeat |
| Microphone permission denied on macOS | High (first run) | No recording | Detect permission error from sox stderr, print "System Preferences > Privacy > Microphone" instructions |
| whisper.cpp ARM build fails via Homebrew | Low | No STT | Fall back to source build with CoreML+Metal flags (documented in Task 1) |
| Key-repeat rate varies across terminals | Medium | Missed release events | 200ms release window is generous; configurable via `COCO_PTT_RELEASE_MS` env var |
| Transcription of code/CLI terms is poor | High | Wrong commands dispatched | Tech corrections dictionary (Task 3); expand over time with user feedback |
| sox not available on non-Homebrew systems | Low | No recording | Document `apt install sox` for Linux; macOS Homebrew is primary target |

---

## Success Criteria (from ROADMAP.md)

- [ ] Push-to-talk (F5 or configurable key) captures audio and transcribes via whisper.cpp
- [ ] Transcription accuracy >90% on technical speech
- [ ] Transcription latency <2 seconds for a 10-second utterance
- [ ] TTS reads back CoCo's response headline (first sentence only)
- [ ] Voice toggled on/off without restarting (`/voice on`, `/voice off`)
- [ ] Works fully offline — no cloud API calls for voice
