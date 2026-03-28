import { describe, it, expect, vi, beforeEach } from 'vitest';
import { EventEmitter } from 'events';

// Mock child_process.spawn
const mockSpawn = vi.fn();
vi.mock('child_process', () => ({
  spawn: (...args: unknown[]) => mockSpawn(...args),
}));

vi.mock('fs', () => ({
  existsSync: vi.fn().mockReturnValue(true),
  unlinkSync: vi.fn(),
}));

import { existsSync } from 'fs';
import { AudioCapture } from '../../src/voice/audio-capture.js';

function createMockProcess() {
  const proc = new EventEmitter() as any;
  proc.kill = vi.fn();
  proc.stderr = new EventEmitter();
  proc.stdout = new EventEmitter();
  proc.stdin = null;
  return proc;
}

describe('AudioCapture', () => {
  let capture: AudioCapture;

  beforeEach(() => {
    mockSpawn.mockReset();
    vi.mocked(existsSync).mockReturnValue(true);
    capture = new AudioCapture();
  });

  it('starts recording and emits recording-started', () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    const started = vi.fn();
    capture.on('recording-started', started);

    capture.startRecording();

    expect(capture.recording).toBe(true);
    expect(started).toHaveBeenCalled();
    expect(mockSpawn).toHaveBeenCalledWith('sox', expect.arrayContaining(['-d', '-t', 'wav', '-r', '16000', '-c', '1', '-b', '16']), expect.any(Object));
  });

  it('does not start a second recording if already recording', () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    capture.startRecording();
    capture.startRecording();

    expect(mockSpawn).toHaveBeenCalledTimes(1);
  });

  it('stops recording and calls kill with SIGINT', () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    capture.startRecording();
    (capture as any).recordStartTime = Date.now() - 1000;

    capture.stopRecording();

    expect(proc.kill).toHaveBeenCalledWith('SIGINT');
  });

  it('emits recording-stopped on exit for valid recordings', () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    capture.startRecording();
    (capture as any).recordStartTime = Date.now() - 1000;

    const stopped = vi.fn();
    capture.on('recording-stopped', stopped);

    // stopRecording registers an 'exit' listener on the mock process
    capture.stopRecording();

    // Simulate sox process exiting
    proc.emit('exit');

    expect(capture.recording).toBe(false);
    expect(stopped).toHaveBeenCalledTimes(1);
    // First arg is the wav path
    expect(stopped.mock.calls[0][0]).toContain('coco-voice-');
  });

  it('discards recordings under 500ms', () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    capture.startRecording();

    const stopped = vi.fn();
    capture.on('recording-stopped', stopped);

    // recordStartTime is very recent (< 500ms ago)
    (capture as any).recordStartTime = Date.now();

    capture.stopRecording();
    proc.emit('exit');

    expect(stopped).not.toHaveBeenCalled();
  });

  it('emits error when sox reports failure', () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    const errHandler = vi.fn();
    capture.on('error', errHandler);

    capture.startRecording();

    proc.stderr.emit('data', Buffer.from('FAIL: no audio device'));

    expect(errHandler).toHaveBeenCalled();
  });
});
