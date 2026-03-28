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
