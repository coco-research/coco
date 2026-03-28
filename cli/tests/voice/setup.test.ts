import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { checkVoiceDependencies } from '../../src/voice/setup.js';

// Mock child_process and fs
vi.mock('child_process', () => ({
  execSync: vi.fn(),
}));

vi.mock('fs', () => ({
  existsSync: vi.fn(),
}));

import { execSync } from 'child_process';
import { existsSync } from 'fs';

const mockExistsSync = vi.mocked(existsSync);
const mockExecSync = vi.mocked(execSync);

describe('checkVoiceDependencies', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('returns available:true when all deps present', () => {
    // whisper binary found at first candidate
    mockExistsSync.mockImplementation((p: unknown) => {
      const path = String(p);
      if (path.includes('whisper')) return true;
      if (path.includes('ggml-base.en.bin')) return true;
      return false;
    });
    // sox found in PATH
    mockExecSync.mockReturnValue('/opt/homebrew/bin/sox\n' as any);

    const result = checkVoiceDependencies();
    expect(result.available).toBe(true);
    expect(result.whisperBin).toBeTruthy();
    expect(result.modelPath).toBeTruthy();
    expect(result.soxAvailable).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('returns available:false with errors when whisper missing', () => {
    mockExistsSync.mockReturnValue(false);
    mockExecSync.mockImplementation((cmd: unknown) => {
      const command = String(cmd);
      if (command.includes('whisper')) throw new Error('not found');
      if (command.includes('sox')) throw new Error('not found');
      return '' as any;
    });

    const result = checkVoiceDependencies();
    expect(result.available).toBe(false);
    expect(result.whisperBin).toBeNull();
    expect(result.errors.length).toBeGreaterThan(0);
    expect(result.errors.some(e => e.includes('whisper'))).toBe(true);
  });

  it('checks multiple candidate paths for whisper binary', () => {
    // Only the third candidate exists
    mockExistsSync.mockImplementation((p: unknown) => {
      const path = String(p);
      if (path === '/opt/homebrew/bin/whisper-cpp-stream') return true;
      if (path.includes('ggml-base.en.bin')) return true;
      return false;
    });
    mockExecSync.mockReturnValue('/opt/homebrew/bin/sox\n' as any);

    const result = checkVoiceDependencies();
    expect(result.whisperBin).toBe('/opt/homebrew/bin/whisper-cpp-stream');
  });

  it('checks PATH via which as fallback', () => {
    mockExistsSync.mockImplementation((p: unknown) => {
      const path = String(p);
      // No binary at static paths, but model exists
      if (path.includes('ggml-base.en.bin')) return true;
      return false;
    });
    mockExecSync.mockImplementation((cmd: unknown) => {
      const command = String(cmd);
      if (command.includes('which whisper')) return '/usr/local/bin/whisper-cpp\n' as any;
      if (command.includes('which sox')) return '/opt/homebrew/bin/sox\n' as any;
      return '' as any;
    });

    const result = checkVoiceDependencies();
    expect(result.whisperBin).toBe('/usr/local/bin/whisper-cpp');
  });

  it('reports sox missing when which sox fails', () => {
    mockExistsSync.mockReturnValue(false);
    mockExecSync.mockImplementation(() => {
      throw new Error('not found');
    });

    const result = checkVoiceDependencies();
    expect(result.soxAvailable).toBe(false);
    expect(result.errors.some(e => e.includes('sox'))).toBe(true);
  });
});
