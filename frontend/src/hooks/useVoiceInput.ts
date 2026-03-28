import { useState, useRef, useCallback, useEffect } from 'react';
import { DeepgramClient } from '../lib/deepgram';

interface VoiceInputState {
  isListening: boolean;
  transcript: string;
  error: string | null;
}

type SttProvider = 'deepgram' | 'webspeech' | 'none';

const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

export const speechSupported = !!SpeechRecognition;

// ─── Error mapping: technical → user-friendly ─────────────────────────────

const FRIENDLY_ERRORS: Record<string, string> = {
  'NotAllowedError': 'Microphone access denied. Check your browser settings.',
  'not-allowed': 'Microphone access denied. Check your browser settings.',
  'NotFoundError': 'No microphone detected.',
  'not-found': 'No microphone detected.',
  'audio-capture': 'Microphone is in use by another app. Close other apps using the mic and try again.',
  'network': 'Voice service unavailable. Using offline mode.',
  'service-not-allowed': 'Speech recognition service not available. Try using Chrome.',
  'no-speech': '',  // silent — not an error
  'aborted': '',     // silent — user-initiated
};

function mapError(error: string): string {
  const mapped = FRIENDLY_ERRORS[error];
  if (mapped !== undefined) return mapped;
  // Network/connection errors
  if (/network|fetch|connect|timeout|socket/i.test(error)) {
    return 'Voice service unavailable. Using offline mode.';
  }
  if (/permission|denied|block/i.test(error)) {
    return 'Microphone access denied. Check your browser settings.';
  }
  if (/not.?found|no.?mic/i.test(error)) {
    return 'No microphone detected.';
  }
  return `Voice input error: ${error}`;
}

// ─── Transcription timeout (15s with no result) ──────────────────────────
const TRANSCRIPTION_TIMEOUT_MS = 15_000;

export function useVoiceInput() {
  const [state, setState] = useState<VoiceInputState>({
    isListening: false,
    transcript: '',
    error: null,
  });

  const [provider, setProvider] = useState<SttProvider>('none');
  const recognitionRef = useRef<any>(null);
  const deepgramRef = useRef<DeepgramClient | null>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const transcriptionTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const onResultRef = useRef<((text: string) => void) | null>(null);
  const retryCountRef = useRef(0);
  const lastCommandArgsRef = useRef<{ onFinalResult: ((text: string) => void) } | null>(null);

  // Check Deepgram availability on mount, fall back to Web Speech API
  useEffect(() => {
    let cancelled = false;
    const client = new DeepgramClient();
    client.isAvailable().then((available) => {
      if (cancelled) return;
      if (available) {
        deepgramRef.current = client;
        setProvider('deepgram');
      } else if (SpeechRecognition) {
        setProvider('webspeech');
      } else {
        setProvider('none');
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      deepgramRef.current?.stop();
      clearTimeout(silenceTimerRef.current);
      clearTimeout(transcriptionTimeoutRef.current);
    };
  }, []);

  // ─── Helper: start transcription timeout ───────────────────────────────
  const startTranscriptionTimeout = useCallback((stopFn: () => void) => {
    clearTimeout(transcriptionTimeoutRef.current);
    transcriptionTimeoutRef.current = setTimeout(() => {
      stopFn();
      setState((s) => ({
        ...s,
        isListening: false,
        error: "Didn't catch that. Try again.",
      }));
    }, TRANSCRIPTION_TIMEOUT_MS);
  }, []);

  const clearTranscriptionTimeout = useCallback(() => {
    clearTimeout(transcriptionTimeoutRef.current);
  }, []);

  // ─── Fallback to Web Speech API when Deepgram fails ──────────────────
  const fallbackToWebSpeech = useCallback((onFinalResult: (text: string) => void) => {
    if (!SpeechRecognition) {
      setState((s) => ({
        ...s,
        isListening: false,
        error: 'Voice input unavailable. Try typing instead.',
      }));
      return;
    }
    // Switch provider and start Web Speech
    setProvider('webspeech');
    deepgramRef.current = null;
    // Will be called via startWebSpeech below
    startWebSpeechImpl(onFinalResult);
  }, []);

  // ---------- Deepgram path ----------
  const startDeepgram = useCallback((onFinalResult: (text: string) => void) => {
    const client = deepgramRef.current;
    if (!client) {
      fallbackToWebSpeech(onFinalResult);
      return;
    }

    onResultRef.current = onFinalResult;
    lastCommandArgsRef.current = { onFinalResult };
    retryCountRef.current = 0;
    let accumulated = '';
    let gotResult = false;

    setState({ isListening: true, transcript: '', error: null });

    // Start transcription timeout
    const stopDeepgram = () => {
      client.stop();
      clearTimeout(silenceTimerRef.current);
    };
    startTranscriptionTimeout(stopDeepgram);

    client
      .start((text, isFinal) => {
        gotResult = true;
        // Clear and reset transcription timeout on any result
        clearTranscriptionTimeout();

        if (isFinal) {
          accumulated += (accumulated ? ' ' : '') + text;
          setState((s) => ({ ...s, transcript: accumulated }));

          // Auto-stop after 1.5s of silence following final text
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = setTimeout(() => {
            client.stop();
            setState((s) => ({ ...s, isListening: false }));
            if (accumulated.trim()) {
              onResultRef.current?.(accumulated.trim());
            }
            accumulated = '';
          }, 1500);
        } else {
          // Show interim text
          setState((s) => ({ ...s, transcript: accumulated + (accumulated ? ' ' : '') + text }));
          // Reset transcription timeout on interim results too
          startTranscriptionTimeout(stopDeepgram);
        }
      })
      .catch((err: Error) => {
        clearTranscriptionTimeout();
        const errMsg = err.message || 'Failed to start Deepgram STT';

        // If Deepgram fails, try retry once, then fall back to Web Speech
        if (retryCountRef.current < 1 && !gotResult) {
          retryCountRef.current++;
          setTimeout(() => startDeepgram(onFinalResult), 500);
          return;
        }

        // Fall back to Web Speech API
        setState((s) => ({ ...s, isListening: false }));
        fallbackToWebSpeech(onFinalResult);
      });

    // Safety timeout - stop after 10s
    silenceTimerRef.current = setTimeout(() => {
      client.stop();
      clearTranscriptionTimeout();
      setState((s) => ({ ...s, isListening: false }));
      if (accumulated.trim()) {
        onResultRef.current?.(accumulated.trim());
      }
    }, 10000);
  }, [startTranscriptionTimeout, clearTranscriptionTimeout, fallbackToWebSpeech]);

  // ---------- Web Speech API path (impl) ----------
  const startWebSpeechImpl = useCallback((onFinalResult: (text: string) => void) => {
    if (!SpeechRecognition) {
      setState((s) => ({
        ...s,
        isListening: false,
        error: 'Voice input unavailable. Try typing instead.',
      }));
      return;
    }

    // Stop any existing recognition
    recognitionRef.current?.abort();
    clearTimeout(silenceTimerRef.current);

    onResultRef.current = onFinalResult;
    lastCommandArgsRef.current = { onFinalResult };
    retryCountRef.current = 0;

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;

    let finalTranscript = '';
    let gotResult = false;

    recognition.onstart = () => {
      setState({ isListening: true, transcript: '', error: null });
      finalTranscript = '';

      // Start transcription timeout (15s with no result)
      startTranscriptionTimeout(() => recognition.stop());

      // Safety timeout -- stop after 10s max
      silenceTimerRef.current = setTimeout(() => {
        recognition.stop();
      }, 10000);
    };

    recognition.onresult = (event: any) => {
      gotResult = true;
      clearTranscriptionTimeout();

      let interim = '';
      finalTranscript = '';

      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        } else {
          interim += result[0].transcript;
        }
      }

      setState((s) => ({ ...s, transcript: finalTranscript || interim }));

      // Auto-stop after 1.5s of silence following a final result
      if (finalTranscript) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = setTimeout(() => {
          recognition.stop();
        }, 1500);
      } else {
        // Reset transcription timeout on interim
        startTranscriptionTimeout(() => recognition.stop());
      }
    };

    recognition.onend = () => {
      clearTimeout(silenceTimerRef.current);
      clearTranscriptionTimeout();
      const text = finalTranscript.trim();
      setState((s) => ({ ...s, isListening: false }));

      if (text) {
        onResultRef.current?.(text);
      }
    };

    recognition.onerror = (event: any) => {
      clearTimeout(silenceTimerRef.current);
      clearTranscriptionTimeout();

      const errorCode = event.error;

      // Silent errors
      if (errorCode === 'no-speech' || errorCode === 'aborted') {
        setState((s) => ({ ...s, isListening: false }));
        return;
      }

      // Network errors: retry once before giving up
      if ((errorCode === 'network' || errorCode === 'audio-capture') && retryCountRef.current < 1 && !gotResult) {
        retryCountRef.current++;
        setState((s) => ({ ...s, isListening: false }));
        setTimeout(() => startWebSpeechImpl(onFinalResult), 500);
        return;
      }

      const msg = mapError(errorCode);
      setState((s) => ({ ...s, isListening: false, error: msg || undefined }));
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [startTranscriptionTimeout, clearTranscriptionTimeout]);

  // ---------- Web Speech API path (public) ----------
  const startWebSpeech = useCallback((onFinalResult: (text: string) => void) => {
    startWebSpeechImpl(onFinalResult);
  }, [startWebSpeechImpl]);

  // ---------- Unified start / stop ----------
  const start = useCallback(
    (onFinalResult: (text: string) => void) => {
      // Clear any previous error
      setState((s) => ({ ...s, error: null }));

      if (provider === 'deepgram') {
        startDeepgram(onFinalResult);
      } else if (provider === 'webspeech') {
        startWebSpeech(onFinalResult);
      } else {
        setState((s) => ({
          ...s,
          error: 'Voice input unavailable. Try typing instead.',
        }));
      }
    },
    [provider, startDeepgram, startWebSpeech],
  );

  const stop = useCallback(() => {
    clearTimeout(silenceTimerRef.current);
    clearTimeout(transcriptionTimeoutRef.current);
    if (provider === 'deepgram') {
      deepgramRef.current?.stop();
      setState((s) => ({ ...s, isListening: false }));
    } else {
      recognitionRef.current?.stop();
    }
  }, [provider]);

  return {
    ...state,
    start,
    stop,
    supported: provider !== 'none',
    provider,
  };
}
