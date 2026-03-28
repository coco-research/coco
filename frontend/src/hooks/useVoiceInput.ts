import { useState, useRef, useCallback, useEffect } from 'react';

interface VoiceInputState {
  isListening: boolean;
  transcript: string;
  error: string | null;
}

const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

export const speechSupported = !!SpeechRecognition;

export function useVoiceInput() {
  const [state, setState] = useState<VoiceInputState>({
    isListening: false,
    transcript: '',
    error: null,
  });

  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const onResultRef = useRef<((text: string) => void) | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      recognitionRef.current?.abort();
      clearTimeout(silenceTimerRef.current);
    };
  }, []);

  const start = useCallback((onFinalResult: (text: string) => void) => {
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
    recognition.continuous = true;  // don't stop on first pause
    recognition.maxAlternatives = 1;

    let finalTranscript = '';
    let lastResultTime = Date.now();

    recognition.onstart = () => {
      setState({ isListening: true, transcript: '', error: null });
      finalTranscript = '';
      lastResultTime = Date.now();

      // Safety timeout — stop after 10s max
      silenceTimerRef.current = setTimeout(() => {
        recognition.stop();
      }, 10000);
    };

    recognition.onresult = (event: any) => {
      lastResultTime = Date.now();
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
      // 'no-speech' and 'aborted' are not real errors
      if (event.error === 'no-speech' || event.error === 'aborted') {
        setState((s) => ({ ...s, isListening: false }));
        return;
      }
      setState((s) => ({ ...s, isListening: false, error: event.error }));
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, []);

  const stop = useCallback(() => {
    clearTimeout(silenceTimerRef.current);
    recognitionRef.current?.stop();
  }, []);

  return { ...state, start, stop, supported: speechSupported };
}
