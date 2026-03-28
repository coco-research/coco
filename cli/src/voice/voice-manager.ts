import { EventEmitter } from 'eventemitter3';
import { checkVoiceDependencies, WhisperSetupResult } from './setup.js';
import { AudioCapture } from './audio-capture.js';
import { Listener, ListenerConfig } from './listener.js';
import { Speaker, SpeakerConfig } from './speaker.js';
import { PushToTalkController } from './hotkey.js';

export type VoiceState = 'off' | 'ready' | 'recording' | 'transcribing' | 'speaking' | 'unavailable';

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

    this.capture.on('recording-stopped', async (wavPath: string) => {
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

    this.capture.on('error', (err: Error) => {
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
