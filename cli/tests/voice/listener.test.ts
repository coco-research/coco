import { describe, it, expect, vi, beforeEach } from 'vitest';

// Use vi.hoisted so the mock fn is available inside vi.mock factory
const { mockExecFileAsync } = vi.hoisted(() => ({
  mockExecFileAsync: vi.fn(),
}));

vi.mock('child_process', () => ({
  execFile: vi.fn(),
}));

vi.mock('node:fs', () => ({
  existsSync: vi.fn().mockReturnValue(true),
}));

vi.mock('util', () => ({
  promisify: () => mockExecFileAsync,
}));

vi.mock('../../src/voice/setup.js', () => ({
  checkVoiceDependencies: () => ({
    available: true,
    whisperBin: '/usr/local/bin/whisper-cpp',
    modelPath: '/tmp/model.bin',
    soxAvailable: true,
    errors: [],
  }),
}));

import { existsSync } from 'node:fs';
import { Listener, applyTechCorrections } from '../../src/voice/listener.js';

describe('applyTechCorrections', () => {
  it('corrects "cube cuttle" to "kubectl"', () => {
    expect(applyTechCorrections('cube cuttle get pods')).toBe('kubectl get pods');
  });

  it('corrects "docker file" to "Dockerfile"', () => {
    expect(applyTechCorrections('create a docker file')).toBe('create a Dockerfile');
  });

  it('corrects "type script" to "TypeScript"', () => {
    expect(applyTechCorrections('use type script for this')).toBe('use TypeScript for this');
  });

  it('corrects "java script" to "JavaScript"', () => {
    expect(applyTechCorrections('java script is great')).toBe('JavaScript is great');
  });

  it('corrects "git hub" to "GitHub"', () => {
    expect(applyTechCorrections('push to git hub')).toBe('push to GitHub');
  });

  it('corrects "slash voice" to "/voice"', () => {
    expect(applyTechCorrections('type slash voice on')).toBe('type /voice on');
  });

  it('corrects "coco" to "CoCo"', () => {
    expect(applyTechCorrections('open coco')).toBe('open CoCo');
  });

  it('handles multiple corrections in one string', () => {
    const result = applyTechCorrections('use type script with node js');
    expect(result).toBe('use TypeScript with Node.js');
  });
});

describe('Listener', () => {
  let listener: Listener;

  beforeEach(() => {
    mockExecFileAsync.mockReset();
    // Ensure existsSync returns true for runtime binary check
    vi.mocked(existsSync).mockReturnValue(true);
    listener = new Listener({
      whisperBin: '/usr/local/bin/whisper-cpp',
      modelPath: '/tmp/model.bin',
      language: 'en',
      threads: 4,
    });
  });

  it('transcribes WAV and returns corrected text', async () => {
    mockExecFileAsync.mockResolvedValue({ stdout: '  hello world  \n', stderr: '' });

    const result = await listener.transcribe('/tmp/test.wav');
    expect(result).toBe('hello world');
  });

  it('applies tech corrections to output', async () => {
    mockExecFileAsync.mockResolvedValue({ stdout: 'use type script\n', stderr: '' });

    const result = await listener.transcribe('/tmp/test.wav');
    expect(result).toBe('use TypeScript');
  });

  it('returns null for empty transcription', async () => {
    mockExecFileAsync.mockResolvedValue({ stdout: '  \n', stderr: '' });

    const result = await listener.transcribe('/tmp/test.wav');
    expect(result).toBeNull();
  });

  it('returns null and emits error on failure', async () => {
    mockExecFileAsync.mockRejectedValue(new Error('timeout'));

    const errorHandler = vi.fn();
    listener.on('error', errorHandler);

    const result = await listener.transcribe('/tmp/test.wav');
    expect(result).toBeNull();
    expect(errorHandler).toHaveBeenCalled();
  });

  it('returns null when binary not found at runtime', async () => {
    vi.mocked(existsSync).mockReturnValue(false);

    const errorHandler = vi.fn();
    listener.on('error', errorHandler);

    const result = await listener.transcribe('/tmp/test.wav');
    expect(result).toBeNull();
    expect(errorHandler).toHaveBeenCalled();
  });

  it('rejects concurrent transcriptions', async () => {
    let resolveFirst: (v: any) => void;
    mockExecFileAsync.mockImplementation(() => new Promise(resolve => { resolveFirst = resolve; }));

    const statusHandler = vi.fn();
    listener.on('status', statusHandler);

    const p1 = listener.transcribe('/tmp/test1.wav');
    const p2 = listener.transcribe('/tmp/test2.wav');

    expect(await p2).toBeNull();
    expect(statusHandler).toHaveBeenCalledWith(expect.stringContaining('already in progress'));

    // Resolve first
    resolveFirst!({ stdout: 'text', stderr: '' });
    await p1;
  });

  it('creates listener from auto-detect', () => {
    const auto = Listener.fromAutoDetect();
    expect(auto).toBeInstanceOf(Listener);
  });

  it('respects 30-second timeout on transcription', async () => {
    // Simulate a timeout error from execFileAsync (which is what happens
    // when the {timeout: 30_000} option triggers in the real execFile call)
    const timeoutError = new Error('Command timed out after 30000ms');
    timeoutError.name = 'Error';
    (timeoutError as any).killed = true;
    (timeoutError as any).signal = 'SIGTERM';
    mockExecFileAsync.mockRejectedValue(timeoutError);

    const errorHandler = vi.fn();
    listener.on('error', errorHandler);

    const result = await listener.transcribe('/tmp/slow.wav');
    expect(result).toBeNull();
    expect(errorHandler).toHaveBeenCalledTimes(1);
    expect(errorHandler.mock.calls[0][0].message).toContain('Transcription failed');
    expect(errorHandler.mock.calls[0][0].message).toContain('timed out');
  });

  it('resets busy flag after timeout so next transcription can proceed', async () => {
    mockExecFileAsync.mockRejectedValueOnce(new Error('Command timed out'));
    await listener.transcribe('/tmp/slow.wav');

    // Should be able to transcribe again (not stuck as busy)
    mockExecFileAsync.mockResolvedValueOnce({ stdout: 'recovered text\n', stderr: '' });
    const result = await listener.transcribe('/tmp/next.wav');
    expect(result).toBe('recovered text');
  });
});
