import { execFile } from 'child_process';
import { existsSync } from 'node:fs';
import { promisify } from 'util';
import { EventEmitter } from 'eventemitter3';
import { checkVoiceDependencies } from './setup.js';

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

export function applyTechCorrections(text: string): string {
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
   */
  async transcribe(wavPath: string): Promise<string | null> {
    if (this.busy) {
      this.emit('status', 'Transcription already in progress, skipping.');
      return null;
    }

    // Runtime check: binary may have been removed while CoCo was running
    if (!existsSync(this.config.whisperBin)) {
      this.emit('error', new Error(
        'whisper.cpp binary no longer found. Run /voice status for setup instructions.'
      ));
      return null;
    }

    this.busy = true;
    const startTime = Date.now();

    try {
      this.emit('status', 'Transcribing...');

      const { stdout } = await execFileAsync(this.config.whisperBin, [
        '-m', this.config.modelPath,
        '-f', wavPath,
        '-t', String(this.config.threads),
        '-l', this.config.language,
        '--no-timestamps',
        '--no-prints',  // suppress progress output, only emit text
      ], {
        timeout: 30_000,  // 30s max
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
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      const error = new Error(`Transcription failed: ${message}`);
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
