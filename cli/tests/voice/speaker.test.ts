import { describe, it, expect, vi, beforeEach } from 'vitest';
import { EventEmitter } from 'events';

const mockSpawn = vi.fn();
vi.mock('child_process', () => ({
  spawn: (...args: unknown[]) => mockSpawn(...args),
  execSync: vi.fn(() => 'Alex                en_US    # Most people\nSamantha            en_US    # A calm voice\nAva                 en_US    # A modern voice\nTom                 en_US    # A natural voice\n'),
}));

import { Speaker } from '../../src/voice/speaker.js';

function createMockProcess() {
  const proc = new EventEmitter() as any;
  proc.kill = vi.fn();
  proc.stdin = null;
  proc.stdout = new EventEmitter();
  proc.stderr = new EventEmitter();
  return proc;
}

describe('Speaker', () => {
  let speaker: Speaker;

  beforeEach(() => {
    vi.resetAllMocks();
    speaker = new Speaker({ voice: 'Samantha', rate: 200, enabled: true });
  });

  it('spawns say with correct voice and rate', async () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    const speakPromise = speaker.speak('Hello world');

    expect(mockSpawn).toHaveBeenCalledWith('say', ['-v', 'Samantha', '-r', '200', 'Hello world'], { stdio: 'ignore' });

    proc.emit('exit');
    await speakPromise;
  });

  it('does nothing when enabled:false', async () => {
    speaker.updateConfig({ enabled: false });

    await speaker.speak('Hello');
    expect(mockSpawn).not.toHaveBeenCalled();
  });

  it('does nothing for empty text', async () => {
    await speaker.speak('   ');
    expect(mockSpawn).not.toHaveBeenCalled();
  });

  it('stop() kills active speech process', () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    speaker.speak('Long text here');
    expect(speaker.speaking).toBe(true);

    speaker.stop();
    expect(proc.kill).toHaveBeenCalledWith('SIGTERM');
    expect(speaker.speaking).toBe(false);
  });

  it('speakSummary extracts first sentence only', async () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    const speakPromise = speaker.speakSummary('This is the summary. This should not be spoken. More text.');

    // speak() is called, which calls spawn. The text arg is the last element in the args array.
    expect(mockSpawn).toHaveBeenCalled();
    const callArgs = mockSpawn.mock.calls[0][1]; // ['- v', 'Samantha', '-r', '200', text]
    const spokenText = callArgs[callArgs.length - 1];
    expect(spokenText).toBe('This is the summary.');

    proc.emit('exit');
    await speakPromise;
  });

  it('strips markdown from summary', async () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    const speakPromise = speaker.speakSummary('## Done\n\nBuilt the auth service.\n```code block```\nMore details...');

    const callArgs = mockSpawn.mock.calls[0][1];
    const spokenText = callArgs[callArgs.length - 1];
    expect(spokenText).not.toContain('```');
    expect(spokenText).not.toContain('##');
    expect(spokenText).toContain('Built the auth service.');

    proc.emit('exit');
    await speakPromise;
  });

  it('truncates long text to 200 chars', async () => {
    const proc = createMockProcess();
    mockSpawn.mockReturnValue(proc);

    const longText = 'A'.repeat(300);
    const speakPromise = speaker.speakSummary(longText);

    const callArgs = mockSpawn.mock.calls[0][1];
    const spokenText = callArgs[callArgs.length - 1];
    expect(spokenText.length).toBeLessThanOrEqual(204); // 200 + "..."

    proc.emit('exit');
    await speakPromise;
  });

  it('does not speak trivially short text', async () => {
    await speaker.speakSummary('Hi');
    expect(mockSpawn).not.toHaveBeenCalled();
  });

  it('listVoices returns English voices', () => {
    const voices = Speaker.listVoices();
    expect(voices).toContain('Alex');
    expect(voices).toContain('Samantha');
    expect(voices.length).toBeGreaterThanOrEqual(4);
  });
});
