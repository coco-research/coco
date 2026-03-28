import { useRef, useCallback, useEffect, useState, useMemo } from 'react';

type SpeakingListener = (speaking: boolean) => void;

class JarvisAudioEngine {
  private ctx: AudioContext | null = null;
  private ambientStop: (() => void) | null = null;
  private currentAudio: HTMLAudioElement | null = null;
  private _isSpeaking = false;
  private _listeners = new Set<SpeakingListener>();

  private ensureContext() {
    if (!this.ctx) this.ctx = new AudioContext();
    if (this.ctx.state === 'suspended') this.ctx.resume();
    return this.ctx;
  }

  private setSpeaking(v: boolean) {
    if (this._isSpeaking === v) return;
    this._isSpeaking = v;
    this._listeners.forEach((cb) => cb(v));
  }

  onSpeakingChange(cb: SpeakingListener): () => void {
    this._listeners.add(cb);
    return () => { this._listeners.delete(cb); };
  }

  /** Short notification blip */
  blip() {
    const ctx = this.ensureContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1320, ctx.currentTime + 0.08);
    gain.gain.setValueAtTime(0.1, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.15);
  }

  /** Section reveal chime */
  chime() {
    const ctx = this.ensureContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(523, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(784, ctx.currentTime + 0.15);
    gain.gain.setValueAtTime(0.06, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.4);
  }

  /** Two-tone success */
  success() {
    const ctx = this.ensureContext();
    [660, 880].forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.08, ctx.currentTime + i * 0.12);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.12 + 0.3);
      osc.connect(gain).connect(ctx.destination);
      osc.start(ctx.currentTime + i * 0.12);
      osc.stop(ctx.currentTime + i * 0.12 + 0.3);
    });
  }

  /** Cinematic ambient atmosphere — layered synth pad like Jarvis workshop */
  startAmbient() {
    if (this.ambientStop) return;
    const ctx = this.ensureContext();
    const masterGain = ctx.createGain();
    masterGain.gain.value = 0;
    masterGain.gain.linearRampToValueAtTime(1, ctx.currentTime + 3);
    masterGain.connect(ctx.destination);

    const nodes: OscillatorNode[] = [];

    // Layer 1: Deep sub bass — the "reactor hum"
    const sub = ctx.createOscillator();
    const subGain = ctx.createGain();
    const subFilter = ctx.createBiquadFilter();
    sub.type = 'sine';
    sub.frequency.value = 55;
    subFilter.type = 'lowpass';
    subFilter.frequency.value = 100;
    subGain.gain.value = 0.025;
    sub.connect(subFilter).connect(subGain).connect(masterGain);
    sub.start();
    nodes.push(sub);

    // Layer 2: Warm pad — two detuned oscillators for width
    const padL = ctx.createOscillator();
    const padR = ctx.createOscillator();
    const padGain = ctx.createGain();
    const padFilter = ctx.createBiquadFilter();
    padL.type = 'triangle';
    padR.type = 'triangle';
    padL.frequency.value = 110;
    padR.frequency.value = 110.5; // slight detune = width
    padFilter.type = 'lowpass';
    padFilter.frequency.value = 300;
    padGain.gain.value = 0.012;
    padL.connect(padFilter);
    padR.connect(padFilter);
    padFilter.connect(padGain).connect(masterGain);
    padL.start();
    padR.start();
    nodes.push(padL, padR);

    // Layer 3: High shimmer — very quiet, adds "air"
    const shimmer = ctx.createOscillator();
    const shimmerGain = ctx.createGain();
    const shimmerFilter = ctx.createBiquadFilter();
    shimmer.type = 'sine';
    shimmer.frequency.value = 880;
    shimmerFilter.type = 'bandpass';
    shimmerFilter.frequency.value = 900;
    shimmerFilter.Q.value = 10;
    shimmerGain.gain.value = 0.004;
    // Slow LFO on shimmer volume for breathing effect
    const lfo = ctx.createOscillator();
    const lfoGain = ctx.createGain();
    lfo.type = 'sine';
    lfo.frequency.value = 0.15; // very slow breathing
    lfoGain.gain.value = 0.002;
    lfo.connect(lfoGain).connect(shimmerGain.gain);
    lfo.start();
    shimmer.connect(shimmerFilter).connect(shimmerGain).connect(masterGain);
    shimmer.start();
    nodes.push(shimmer, lfo);

    this.ambientStop = () => {
      masterGain.gain.linearRampToValueAtTime(0.001, ctx.currentTime + 2);
      setTimeout(() => {
        nodes.forEach((n) => { try { n.stop(); } catch {} });
      }, 2200);
      this.ambientStop = null;
    };
  }

  stopAmbient() {
    this.ambientStop?.();
  }

  private prefetchedUrl: string | null = null;
  private prefetchedAudio: HTMLAudioElement | null = null;

  /** Pre-fetch TTS audio so it's ready to play instantly */
  async prefetch(text: string): Promise<void> {
    if (!text) return;
    try {
      const resp = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: 'andrew', speed: '-5%' }),
      });
      if (!resp.ok) return;
      const blob = await resp.blob();
      this.prefetchedUrl = URL.createObjectURL(blob);
      this.prefetchedAudio = new Audio(this.prefetchedUrl);
      this.prefetchedAudio.volume = 0.9;
      // Pre-load the audio data so play() is instant
      this.prefetchedAudio.preload = 'auto';
    } catch {
      // Prefetch failed — speak() will fall back
    }
  }

  /** Play pre-fetched audio or fetch+play if not pre-fetched */
  async speak(text: string): Promise<void> {
    if (!text) return;

    // Use pre-fetched audio if available
    if (this.prefetchedAudio) {
      this.currentAudio = this.prefetchedAudio;
      const url = this.prefetchedUrl!;
      this.prefetchedAudio = null;
      this.prefetchedUrl = null;
      this.setSpeaking(true);
      try {
        await this.currentAudio.play();
        await new Promise<void>((resolve) => {
          this.currentAudio!.onended = () => { URL.revokeObjectURL(url); this.setSpeaking(false); resolve(); };
          this.currentAudio!.onerror = () => { URL.revokeObjectURL(url); this.setSpeaking(false); resolve(); };
        });
        return;
      } catch {
        this.setSpeaking(false);
      }
    }

    // No prefetch — fetch and play now (fallback path)
    try {
      const resp = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: 'andrew', speed: '-5%' }),
      });
      if (!resp.ok) {
        this.speakFallback(text);
        return;
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      this.currentAudio = new Audio(url);
      this.currentAudio.volume = 0.9;
      this.setSpeaking(true);
      await this.currentAudio.play();
      await new Promise<void>((resolve) => {
        this.currentAudio!.onended = () => { URL.revokeObjectURL(url); this.setSpeaking(false); resolve(); };
        this.currentAudio!.onerror = () => { URL.revokeObjectURL(url); this.setSpeaking(false); resolve(); };
      });
    } catch {
      this.setSpeaking(false);
      this.speakFallback(text);
    }
  }

  /** Fallback: Web Speech API */
  private speakFallback(text: string) {
    if (!('speechSynthesis' in window)) return;
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 0.95;
    utter.pitch = 0.8;
    const voices = speechSynthesis.getVoices();
    const preferred = voices.find(
      (v) => v.name.includes('Daniel') && v.lang.startsWith('en')
    ) ?? voices.find((v) => v.lang.startsWith('en'));
    if (preferred) utter.voice = preferred;
    this.setSpeaking(true);
    utter.onend = () => this.setSpeaking(false);
    utter.onerror = () => this.setSpeaking(false);
    speechSynthesis.speak(utter);
  }

  cancelSpeak() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    if ('speechSynthesis' in window) speechSynthesis.cancel();
    this.setSpeaking(false);
  }

  /** Clean up all audio resources */
  destroy() {
    this.cancelSpeak();
    this.stopAmbient();
    // Revoke any prefetched blob URLs
    if (this.prefetchedUrl) {
      URL.revokeObjectURL(this.prefetchedUrl);
      this.prefetchedUrl = null;
      this.prefetchedAudio = null;
    }
    // Close audio context
    if (this.ctx && this.ctx.state !== 'closed') {
      this.ctx.close().catch(() => {});
    }
    this.ctx = null;
  }
}

const engine = new JarvisAudioEngine();

export function useJarvisAudio() {
  const audioUnlocked = useRef(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    return engine.onSpeakingChange(setIsSpeaking);
  }, []);

  const unlock = useCallback(() => {
    if (audioUnlocked.current) return;
    audioUnlocked.current = true;
    try {
      // Use the engine's AudioContext instead of creating a duplicate
      engine.blip(); // triggers ensureContext() + resume() + plays a brief sound
    } catch {}
  }, []);

  useEffect(() => {
    document.addEventListener('click', unlock, { once: true });
    document.addEventListener('keydown', unlock, { once: true });
    return () => {
      document.removeEventListener('click', unlock);
      document.removeEventListener('keydown', unlock);
      engine.destroy();
    };
  }, [unlock]);

  return useMemo(() => ({
    prefetch: (t: string) => engine.prefetch(t),
    speak: (t: string) => engine.speak(t),
    chime: () => engine.chime(),
    blip: () => engine.blip(),
    success: () => engine.success(),
    startAmbient: () => engine.startAmbient(),
    stopAmbient: () => engine.stopAmbient(),
    cancelSpeak: () => engine.cancelSpeak(),
    isSpeaking,
  }), [isSpeaking]);
}
