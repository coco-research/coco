import { useState, useCallback, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { Mic, MicOff, Loader2, X, ExternalLink } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useVoiceInput } from '../../hooks/useVoiceInput';
import { getBrowserHelpUrl, getBrowserHelpLabel } from '../../lib/micPermission';

type MicState = 'idle' | 'listening' | 'processing' | 'speaking';

/**
 * Floating microphone button — fixed bottom-right on every page.
 *
 * States:
 *   idle       — static mic icon with subtle glow
 *   listening  — pulsing ring + red dot, shows live streaming transcript bubble
 *   processing — spinner replacing mic icon
 *   speaking   — waveform animation bars (TTS playback)
 *
 * Shows a provider indicator badge (Deepgram / Web Speech) while listening.
 * Live interim transcripts stream in real-time as the user speaks.
 *
 * On final transcript, dispatches `coco:voice-command` CustomEvent so
 * useVoiceCommands can route the command app-wide.
 *
 * Hidden on /jarvis (which has its own full-screen voice UI).
 * Respects `voice-enabled` in localStorage.
 */
export function FloatingMic() {
  const location = useLocation();
  const voice = useVoiceInput();
  const [micState, setMicState] = useState<MicState>('idle');
  const [response, setResponse] = useState<string | null>(null);
  const [showBubble, setShowBubble] = useState(false);
  const [permissionDismissed, setPermissionDismissed] = useState(false);
  const autoDismissRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const inactivityRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const lastTranscriptRef = useRef('');

  // Auto-dismiss transcript bubble after 5s of inactivity (no new text)
  useEffect(() => {
    if (!voice.isListening) return;

    // If transcript hasn't changed, start the 5s timer
    if (voice.transcript === lastTranscriptRef.current && voice.transcript) {
      clearTimeout(inactivityRef.current);
      inactivityRef.current = setTimeout(() => {
        voice.stop();
        setMicState('idle');
      }, 5000);
    } else {
      clearTimeout(inactivityRef.current);
    }
    lastTranscriptRef.current = voice.transcript;

    return () => clearTimeout(inactivityRef.current);
  }, [voice.transcript, voice.isListening, voice]);

  // Listen for external response events (from useVoiceCommands)
  useEffect(() => {
    function onResponse(e: Event) {
      const detail = (e as CustomEvent).detail;
      setResponse(detail.text);
      setShowBubble(true);
      setMicState(detail.speaking ? 'speaking' : 'idle');

      // Auto-dismiss after 6s
      clearTimeout(autoDismissRef.current);
      autoDismissRef.current = setTimeout(() => {
        setShowBubble(false);
        setResponse(null);
        setMicState('idle');
      }, 6000);
    }

    function onProcessing() {
      setMicState('processing');
      setShowBubble(true);
      setResponse(null);
    }

    function onSpeakEnd() {
      setMicState('idle');
    }

    window.addEventListener('coco:voice-response', onResponse);
    window.addEventListener('coco:voice-processing', onProcessing);
    window.addEventListener('coco:voice-speak-end', onSpeakEnd);
    return () => {
      window.removeEventListener('coco:voice-response', onResponse);
      window.removeEventListener('coco:voice-processing', onProcessing);
      window.removeEventListener('coco:voice-speak-end', onSpeakEnd);
      clearTimeout(autoDismissRef.current);
    };
  }, []);

  const handleResult = useCallback((text: string) => {
    if (!text.trim()) return;
    // Dispatch event for useVoiceCommands to route
    window.dispatchEvent(
      new CustomEvent('coco:voice-command', { detail: { text: text.trim() } })
    );
  }, []);

  const toggleMic = useCallback(() => {
    if (voice.isListening) {
      voice.stop();
      if (micState === 'listening') setMicState('idle');
    } else {
      setResponse(null);
      setShowBubble(false);
      setPermissionDismissed(false);
      setMicState('listening');
      lastTranscriptRef.current = '';
      voice.start(handleResult);
    }
  }, [voice, handleResult, micState]);

  const dismissBubble = useCallback(() => {
    setShowBubble(false);
    setResponse(null);
    setMicState('idle');
    clearTimeout(autoDismissRef.current);
  }, []);

  // Hide when Jarvis overlay is active — it has its own full-screen voice input
  const params = new URLSearchParams(location.search);
  if (params.get('jarvis') === 'true') return null;

  // No mic support or voice disabled — don't render
  // Use hook's `supported` which accounts for both Deepgram and Web Speech
  if (!voice.supported) return null;
  const voiceEnabled = localStorage.getItem('voice-enabled') !== 'false';
  if (!voiceEnabled) return null;

  const isListening = micState === 'listening' || voice.isListening;
  const isProcessing = micState === 'processing';
  const isSpeaking = micState === 'speaking';
  const isPermissionDenied = voice.errorKind === 'permission-denied';
  const showPermissionBubble = isPermissionDenied && !permissionDismissed;

  const providerLabel = voice.provider === 'deepgram' ? 'Deepgram' : 'Web Speech';
  const helpUrl = getBrowserHelpUrl();
  const helpLabel = getBrowserHelpLabel();

  const dismissPermissionBubble = () => setPermissionDismissed(true);

  const retryPermissionFlow = () => {
    setPermissionDismissed(true);
    voice.retryPermission();
    // Re-trigger the prompt — note this only works if the browser actually
    // allows re-prompting (some browsers persist denial until the user
    // changes the site setting manually, which is exactly why we link out).
    setResponse(null);
    setShowBubble(false);
    setMicState('listening');
    lastTranscriptRef.current = '';
    voice.start(handleResult);
  };

  return (
    <div className="fixed bottom-6 right-[5.5rem] z-40 flex flex-col items-end gap-2">
      {/* Permission-denied bubble — explicit remediation guidance with a
          browser-specific help link. Takes priority over the listening UI. */}
      {showPermissionBubble && (
        <div
          role="alert"
          className="floating-mic-bubble floating-mic-bubble-enter relative max-w-[280px] border border-destructive/40"
        >
          <button
            onClick={dismissPermissionBubble}
            className="absolute top-1.5 right-1.5 text-muted-foreground hover:text-foreground p-0.5 rounded-full hover:bg-secondary/80"
            aria-label="Dismiss microphone permission notice"
          >
            <X size={12} />
          </button>
          <div className="pr-5">
            <p className="text-sm font-medium text-foreground leading-snug">
              Microphone access denied
            </p>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              Enable in browser settings to use voice input.
            </p>
            <div className="flex items-center gap-3 mt-2">
              <a
                href={helpUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-accent hover:underline"
              >
                {helpLabel}
                <ExternalLink size={10} />
              </a>
              <button
                onClick={retryPermissionFlow}
                className="text-xs text-accent hover:underline"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Streaming transcript bubble (while listening) */}
      {isListening && (
        <div className="floating-mic-bubble floating-mic-bubble-enter">
          {voice.transcript ? (
            <p className="text-sm text-foreground leading-relaxed">
              {voice.transcript}
              <span className="floating-mic-cursor" />
            </p>
          ) : (
            <p className="text-sm text-muted-foreground animate-pulse">
              Listening...
            </p>
          )}
          {/* Provider indicator badge */}
          <span className="floating-mic-provider-badge">
            via {providerLabel}
          </span>
        </div>
      )}

      {/* Response bubble */}
      {showBubble && !isListening && (response || isProcessing) && (
        <div className="floating-mic-bubble floating-mic-bubble-enter relative">
          {isProcessing ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 size={14} className="animate-spin" />
              <span>Thinking...</span>
            </div>
          ) : (
            <>
              <button
                onClick={dismissBubble}
                className="absolute top-1.5 right-1.5 text-muted-foreground hover:text-foreground p-0.5 rounded-full hover:bg-secondary/80"
                aria-label="Dismiss"
              >
                <X size={12} />
              </button>
              <p className="text-sm text-foreground pr-5 leading-relaxed">
                {response}
              </p>
            </>
          )}
        </div>
      )}

      {/* Mic FAB with ring + state visuals */}
      <div className="relative">
        {/* Pulsing ring when listening */}
        {isListening && (
          <>
            <span className="floating-mic-ring floating-mic-ring-1" />
            <span className="floating-mic-ring floating-mic-ring-2" />
            <span className="floating-mic-ring floating-mic-ring-3" />
          </>
        )}

        {/* Subtle idle glow */}
        {!isListening && !isProcessing && !isSpeaking && (
          <span className="floating-mic-glow" />
        )}

        <button
          type="button"
          onClick={toggleMic}
          disabled={isProcessing}
          className={cn(
            'relative w-12 h-12 rounded-full flex items-center justify-center',
            'transition-all duration-200',
            'floating-mic-glass',
            isListening
              ? 'floating-mic-active'
              : isProcessing
                ? 'floating-mic-processing'
                : isSpeaking
                  ? 'floating-mic-speaking'
                  : 'floating-mic-idle',
          )}
          aria-label={isListening ? 'Stop listening' : 'Voice command'}
        >
          {isProcessing ? (
            <Loader2 size={18} className="animate-spin text-accent" />
          ) : isSpeaking ? (
            /* Waveform bars */
            <div className="flex items-center gap-[3px] h-4">
              {[0, 1, 2, 3, 4].map((i) => (
                <span
                  key={i}
                  className="floating-mic-wave-bar"
                  style={{ animationDelay: `${i * 120}ms` }}
                />
              ))}
            </div>
          ) : isListening ? (
            <div className="relative">
              <MicOff size={18} className="text-destructive" />
              {/* Red recording dot */}
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-destructive animate-pulse" />
            </div>
          ) : (
            <Mic size={18} className="text-muted-foreground group-hover:text-foreground" />
          )}
        </button>
      </div>

      {/* Voice error (generic only — permission-denied uses the rich bubble
          above so the user gets a help link and retry button). */}
      {voice.error && !isPermissionDenied && (
        <p className="text-[10px] text-destructive max-w-[200px] text-right mt-1">
          {voice.error}
        </p>
      )}
    </div>
  );
}
