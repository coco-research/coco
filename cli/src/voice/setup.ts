import { execSync } from 'child_process';
import { existsSync } from 'fs';

// Expected paths (overridable via env)
const WHISPER_BIN_DEFAULT = process.env.COCO_WHISPER_PATH
  ?? `${process.env.HOME}/.local/bin/whisper-stream`;
const WHISPER_MODEL_DEFAULT = process.env.COCO_WHISPER_MODEL_PATH
  ?? `${process.env.HOME}/.local/share/whisper/ggml-base.en.bin`;

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
    '/opt/homebrew/bin/whisper-cli',         // Homebrew v1.8+
    '/opt/homebrew/bin/whisper-cpp',         // Homebrew older formula
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
      const which = execSync('which whisper-cli 2>/dev/null || which whisper-cpp 2>/dev/null || which whisper-stream 2>/dev/null', {
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
