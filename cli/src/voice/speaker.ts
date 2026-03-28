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
