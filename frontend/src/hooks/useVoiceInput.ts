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
  const onResultRef = useRef<((text: string) => void) | null>(null);

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
    };
  }, []);

  // ---------- Deepgram path ----------
  const startDeepgram = useCallback((onFinalResult: (text: string) => void) => {
    const client = deepgramRef.current;
    if (!client) return;

    onResultRef.current = onFinalResult;
    let accumulated = '';

    setState({ isListening: true, transcript: '', error: null });

    client
      .start((text, isFinal) => {
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
        }
      })
      .catch((err: Error) => {
        setState((s) => ({
          ...s,
          isListening: false,
          error: err.message || 'Failed to start Deepgram STT',
        }));
      });

    // Safety timeout - stop after 10s
    silenceTimerRef.current = setTimeout(() => {
      client.stop();
      setState((s) => ({ ...s, isListening: false }));
      if (accumulated.trim()) {
        onResultRef.current?.(accumulated.trim());
      }
    }, 10000);
  }, []);

  // ---------- Web Speech API path ----------
  const startWebSpeech = useCallback((onFinalResult: (text: string) => void) => {
    if (!SpeechRecognition) {
      setState((s) => ({ ...s, error: 'Speech recognition not supported. Use Chrome.' }));
      return;
    }

    // Stop any existing recognition
    recognitionRef.current?.abort();
    clearTimeout(silenceTimerRef.current);

    onResultRef.current = onFinalResult;

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;

    let finalTranscript = '';

    recognition.onstart = () => {
      setState({ isListening: true, transcript: '', error: null });
      finalTranscript = '';

      // Safety timeout -- stop after 10s max
      silenceTimerRef.current = setTimeout(() => {
        recognition.stop();
      }, 10000);
    };

    recognition.onresult = (event: any) => {
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
      }
    };

    recognition.onend = () => {
      clearTimeout(silenceTimerRef.current);
      const text = finalTranscript.trim();
      setState((s) => ({ ...s, isListening: false }));

      if (text) {
        onResultRef.current?.(text);
      }
    };

    recognition.onerror = (event: any) => {
      clearTimeout(silenceTimerRef.current);
      if (event.error === 'no-speech' || event.error === 'aborted') {
        setState((s) => ({ ...s, isListening: false }));
        return;
      }
      const friendlyErrors: Record<string, string> = {
        'not-allowed': 'Microphone access denied. Please allow mic permission in your browser settings.',
        'NotAllowedError': 'Microphone access denied. Please allow mic permission in your browser settings.',
        'not-found': 'No microphone found. Please connect a mic and try again.',
        'NotFoundError': 'No microphone found. Please connect a mic and try again.',
        'audio-capture': 'Microphone is in use by another app. Close other apps using the mic and try again.',
        'network': 'Network error during speech recognition. Check your connection.',
        'service-not-allowed': 'Speech recognition service not available. Try using Chrome.',
      };
      const msg = friendlyErrors[event.error] || `Voice input error: ${event.error}`;
      setState((s) => ({ ...s, isListening: false, error: msg }));
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, []);

  // ---------- Unified start / stop ----------
  const start = useCallback(
    (onFinalResult: (text: string) => void) => {
      if (provider === 'deepgram') {
        startDeepgram(onFinalResult);
      } else if (provider === 'webspeech') {
        startWebSpeech(onFinalResult);
      } else {
        setState((s) => ({ ...s, error: 'No speech recognition available.' }));
      }
    },
    [provider, startDeepgram, startWebSpeech],
  );

  const stop = useCallback(() => {
    clearTimeout(silenceTimerRef.current);
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
