import { useState, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { Mic, MicOff, Loader2, X } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useVoiceInput, speechSupported } from '../../hooks/useVoiceInput';
import { apiPost } from '../../lib/api';

interface CommandResult {
  reply: string;
  action?: string;
  url?: string;
}

/**
 * Floating microphone button — fixed bottom-right.
 * Uses Web Speech API to capture voice, sends transcript to `/api/jarvis/command`,
 * and shows a response bubble. Hidden on the /jarvis page (which has its own input).
 */
export function FloatingMic() {
  const location = useLocation();
  const voice = useVoiceInput();
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState<string | null>(null);
  const [showBubble, setShowBubble] = useState(false);

  // Hide on /jarvis page — it has its own full-screen voice input
  if (location.pathname === '/jarvis') return null;

  // No mic support — don't render
  if (!speechSupported) return null;

  const handleResult = useCallback(async (text: string) => {
    if (!text.trim()) return;
    setIsProcessing(true);
    setShowBubble(true);
    setResponse(null);

    try {
      const result = await apiPost<CommandResult>('/jarvis/command', { text: text.trim() });
      setResponse(result.reply);
    } catch {
      setResponse('Something went wrong. Try again.');
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const toggleMic = useCallback(() => {
    if (voice.isListening) {
      voice.stop();
    } else {
      setResponse(null);
      setShowBubble(false);
      voice.start(handleResult);
    }
  }, [voice, handleResult]);

  const dismissBubble = useCallback(() => {
    setShowBubble(false);
    setResponse(null);
  }, []);

  return (
    <div className="fixed bottom-6 right-20 z-[60] flex flex-col items-end gap-2">
      {/* Transcript bubble (while listening) */}
      {voice.isListening && (
        <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-lg max-w-xs animate-in fade-in slide-in-from-bottom-2 duration-200">
          {voice.transcript ? (
            <p className="text-sm text-foreground">&ldquo;{voice.transcript}&rdquo;</p>
          ) : (
            <p className="text-sm text-muted-foreground animate-pulse">Listening...</p>
          )}
        </div>
      )}

      {/* Response bubble */}
      {showBubble && !voice.isListening && (response || isProcessing) && (
        <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-lg max-w-xs animate-in fade-in slide-in-from-bottom-2 duration-200 relative">
          {isProcessing ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 size={14} className="animate-spin" />
              <span>Thinking...</span>
            </div>
          ) : (
            <>
              <button
                onClick={dismissBubble}
                className="absolute top-1 right-1 text-muted-foreground hover:text-foreground p-0.5"
                aria-label="Dismiss"
              >
                <X size={12} />
              </button>
              <p className="text-sm text-foreground pr-4">{response}</p>
            </>
          )}
        </div>
      )}

      {/* Mic FAB */}
      <button
        type="button"
        onClick={toggleMic}
        disabled={isProcessing}
        className={cn(
          'w-11 h-11 rounded-full flex items-center justify-center transition-all duration-200 shadow-lg',
          'border',
          voice.isListening
            ? 'bg-destructive/15 border-destructive/30 text-destructive hover:bg-destructive/25'
            : isProcessing
              ? 'bg-accent/15 border-accent/30 text-accent cursor-wait'
              : 'bg-card border-border text-muted-foreground hover:text-foreground hover:border-accent/50',
        )}
        aria-label={voice.isListening ? 'Stop listening' : 'Voice command'}
      >
        {isProcessing ? (
          <Loader2 size={16} className="animate-spin" />
        ) : voice.isListening ? (
          <MicOff size={16} />
        ) : (
          <Mic size={16} />
        )}
      </button>

      {/* Voice error */}
      {voice.error && (
        <p className="text-[10px] text-destructive max-w-[200px] text-right">
          Mic error: {voice.error}
        </p>
      )}
    </div>
  );
}
