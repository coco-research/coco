import { describe, it, expect, vi, beforeEach } from 'vitest';

// Control the availability flag
let depsAvailable = true;

vi.mock('../../src/voice/setup.js', () => ({
  checkVoiceDependencies: vi.fn(() => ({
    available: depsAvailable,
    whisperBin: depsAvailable ? '/usr/local/bin/whisper-cpp' : null,
    modelPath: depsAvailable ? '/tmp/model.bin' : null,
    soxAvailable: depsAvailable,
    errors: depsAvailable ? [] : ['whisper.cpp binary not found.', 'sox not found.'],
  })),
}));

vi.mock('../../src/voice/audio-capture.js', () => {
  const { EventEmitter } = require('eventemitter3');
  class MockAudioCapture extends EventEmitter {
    recording = false;
    startRecording = vi.fn(() => { this.recording = true; });
    stopRecording = vi.fn(() => { this.recording = false; });
    cleanup = vi.fn();
  }
  return { AudioCapture: MockAudioCapture };
});

vi.mock('../../src/voice/listener.js', () => {
  const { EventEmitter } = require('eventemitter3');
  class MockListener extends EventEmitter {
    transcribe = vi.fn(async () => 'hello world');
  }
  return {
    Listener: MockListener,
  };
});

vi.mock('../../src/voice/speaker.js', () => {
  class MockSpeaker {
    config: any;
    constructor(config: any) { this.config = config; }
    speak = vi.fn();
    speakSummary = vi.fn();
    stop = vi.fn();
    updateConfig = vi.fn((partial: any) => Object.assign(this.config, partial));
    get speaking() { return false; }
  }
  return { Speaker: MockSpeaker };
});

vi.mock('../../src/voice/hotkey.js', () => {
  const { EventEmitter } = require('eventemitter3');
  class MockPTT extends EventEmitter {
    forceRelease = vi.fn();
    handleRawData = vi.fn();
    setMode = vi.fn();
    setKey = vi.fn();
    held = false;
  }
  return { PushToTalkController: MockPTT };
});

import { VoiceManager } from '../../src/voice/voice-manager.js';
import { checkVoiceDependencies } from '../../src/voice/setup.js';

describe('VoiceManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    depsAvailable = true;
  });

  it('turnOn returns success when deps available', () => {
    const vm = new VoiceManager();
    const msg = vm.turnOn();
    expect(msg).toContain('Voice enabled');
    expect(vm.currentState).toBe('ready');
  });

  it('turnOn returns degradation message when deps missing but enables TTS', () => {
    depsAvailable = false;
    const vm = new VoiceManager();
    const msg = vm.turnOn();
    expect(msg).toContain('TTS only');
    expect(msg).toContain('Missing STT dependencies');
    expect(vm.currentState).toBe('unavailable');
  });

  it('turnOn re-checks dependencies', () => {
    const vm = new VoiceManager();
    vm.turnOn();
    // checkVoiceDependencies called in constructor AND in turnOn
    expect(checkVoiceDependencies).toHaveBeenCalledTimes(2);
  });

  it('turnOff stops cleanly', () => {
    const vm = new VoiceManager();
    vm.turnOn();
    const msg = vm.turnOff();
    expect(msg).toBe('Voice disabled.');
    expect(vm.currentState).toBe('off');
  });

  it('status() lists all dependency states', () => {
    const vm = new VoiceManager();
    const status = vm.status();
    expect(status).toContain('Voice state:');
    expect(status).toContain('STT (whisper.cpp):');
    expect(status).toContain('TTS voice:');
    expect(status).toContain('Push-to-talk key:');
  });

  it('status() shows missing deps when unavailable', () => {
    depsAvailable = false;
    const vm = new VoiceManager();
    vm.turnOn();
    const status = vm.status();
    expect(status).toContain('Missing:');
    expect(status).toContain('NOT FOUND');
  });

  it('emits transcription events', async () => {
    const vm = new VoiceManager();
    vm.turnOn();

    const transcriptionHandler = vi.fn();
    vm.on('transcription', transcriptionHandler);

    // Simulate: capture emits recording-stopped -> listener transcribes -> vm emits transcription
    const capture = (vm as any).capture;
    capture.emit('recording-stopped', '/tmp/test.wav', 2000);

    // Wait for async listener.transcribe
    await new Promise(resolve => setTimeout(resolve, 20));
    expect(transcriptionHandler).toHaveBeenCalledWith('hello world');
  });

  it('exposes pttController', () => {
    const vm = new VoiceManager();
    expect(vm.pttController).toBeDefined();
  });
});
