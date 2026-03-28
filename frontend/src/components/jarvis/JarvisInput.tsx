import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, MicOff, Send, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useVoiceInput } from '../../hooks/useVoiceInput';
import { useTypewriter } from '../../hooks/useTypewriter';
import { apiPost } from '../../lib/api';
import type { CommandResponse } from '../../types/cards';

interface HistoryEntry {
  query: string;
  reply: string;
}

interface Props {
  onCommand?: (text: string) => Promise<CommandResponse>;
  onSpeak: (text: string) => Promise<void>;
  onChime: () => void;
  onInteract?: () => void;
  delay?: number;
}

function ResponseBubble({ text, visible }: { text: string; visible: boolean }) {
  const { displayed, isDone } = useTypewriter(text, 22, { enabled: visible });
  if (!visible || !text) return null;
  return (
    <div className="max-w-xl mx-auto mt-4 mb-2">
      <p className="text-sm text-white/70 leading-relaxed text-center">
        {displayed}
        {!isDone && <span className="inline-block w-0.5 h-3.5 bg-white/40 ml-0.5 animate-pulse" />}
      </p>
    </div>
  );
}

export function JarvisInput({ onCommand, onSpeak, onChime, onInteract, delay = 0 }: Props) {
  const navigate = useNavigate();
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState('');
  const [userQuery, setUserQuery] = useState('');
  const [suggestChat, setSuggestChat] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const voice = useVoiceInput();

  const handleCommand = useCallback(async (input: string) => {
    if (!input.trim() || isProcessing) return;
    setIsProcessing(true);
    setResponse('');
    setSuggestChat(false);
    setUserQuery(input.trim());
    setTextInput('');
    onInteract?.();

    try {
      const result = onCommand
        ? await onCommand(input.trim())
        : await apiPost<CommandResponse>('/jarvis/command', { text: input.trim(), context: history });
      setResponse(result.reply);
      // Track in session history (keep last 5)
      setHistory((prev) => [...prev.slice(-4), { query: input.trim(), reply: result.reply }]);
      onChime();

      // Speak the response and wait for it to finish
      await onSpeak(result.reply);

      // Navigate after speech finishes (only allow internal paths)
      if (result.action === 'navigate' && result.url?.startsWith('/')) {
        setTimeout(() => navigate(result.url!), 500);
      }
      // For complex queries, show "Continue in Chat" hint
      if (result.action === 'suggest_chat') {
        setSuggestChat(true);
      }
    } catch {
      const fallback = "Something went wrong. Try again.";
      setResponse(fallback);
      await onSpeak(fallback);
    } finally {
      setIsProcessing(false);
    }
  }, [isProcessing, onSpeak, onChime, onInteract, navigate]);

  const toggleMic = () => {
    if (voice.isListening) {
      voice.stop();
    } else {
      setResponse('');
      setUserQuery('');
      onChime(); // audio feedback: "I'm listening"
      voice.start(handleCommand);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) handleCommand(textInput);
  };

  return (
    <div
      className="jarvis-reveal max-w-xl mx-auto"
      style={{ '--reveal-delay': `${delay}ms` } as React.CSSProperties}
    >
      {/* Session history — last few command-response pairs */}
      {history.length > 0 && (
        <div className="max-w-xl mx-auto space-y-2 mb-4">
          {history.slice(-5).map((h, i) => (
            <div key={i} className="text-xs text-white/40">
              <span className="font-mono text-sky-400/60">&gt; {h.query}</span>
              <p className="ml-4 text-white/25">{h.reply.slice(0, 100)}{h.reply.length > 100 ? '...' : ''}</p>
            </div>
          ))}
        </div>
      )}

      {/* User's spoken/typed query */}
      {userQuery && (
        <p className="text-center text-xs text-white/30 mb-2">
          &gt; {userQuery}
        </p>
      )}

      {/* Response */}
      <ResponseBubble text={response} visible={!!response} />

      {/* Continue in Chat — shown when Jarvis suggests full chat for complex queries */}
      {suggestChat && response && (
        <div className="text-center mt-2">
          <button
            onClick={() => navigate('/chat')}
            className="text-[11px] font-mono text-sky-400/60 hover:text-sky-400 transition-colors border border-sky-400/20 hover:border-sky-400/40 rounded-lg px-3 py-1.5"
          >
            Continue in Chat →
          </button>
        </div>
      )}

      {/* Live transcript while listening */}
      {voice.isListening && (
        <div className="text-center mb-3">
          {voice.transcript ? (
            <p className="text-sm text-white/60">
              "{voice.transcript}"
            </p>
          ) : (
            <p className="text-sm text-white/30 animate-pulse">
              Listening...
            </p>
          )}
        </div>
      )}

      {/* Input bar */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2 mt-4">
        {/* Mic button */}
        <button
          type="button"
          onClick={toggleMic}
          disabled={isProcessing}
          className={cn(
            'shrink-0 w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300',
            'border backdrop-blur-sm',
            voice.isListening
              ? 'bg-[#FF453A]/15 border-[#FF453A]/30 text-[#FF453A]'
              : 'bg-white/5 border-white/10 text-white/50 hover:text-white/80 hover:border-white/20',
          )}
        >
          {voice.isListening ? (
            <MicOff size={16} />
          ) : (
            <Mic size={16} />
          )}
        </button>

        {/* Text input */}
        <input
          ref={inputRef}
          type="text"
          value={voice.isListening ? voice.transcript : textInput}
          onChange={(e) => !voice.isListening && setTextInput(e.target.value)}
          placeholder={voice.isListening ? 'Listening...' : 'Ask CoCo anything...'}
          disabled={isProcessing}
          onFocus={() => voice.isListening && voice.stop()}
          className={cn(
            'flex-1 bg-white/5 backdrop-blur-sm border rounded-xl',
            'px-4 py-2.5 text-sm text-white/80 placeholder:text-white/25',
            'focus:outline-none transition-all',
            voice.isListening
              ? 'border-[#FF453A]/20 bg-[#FF453A]/5'
              : 'border-white/10 focus:border-white/20',
          )}
        />

        {/* Send button */}
        <button
          type="submit"
          disabled={isProcessing || voice.isListening || !textInput.trim()}
          className={cn(
            'shrink-0 w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300',
            'border backdrop-blur-sm',
            isProcessing
              ? 'bg-[#0A84FF]/15 border-[#0A84FF]/30 text-[#0A84FF]'
              : textInput.trim()
                ? 'bg-[#0A84FF]/15 border-[#0A84FF]/30 text-[#0A84FF]'
                : 'bg-white/3 border-white/8 text-white/20',
          )}
        >
          {isProcessing ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </form>

      {/* Hints */}
      {!response && !voice.isListening && (
        <p className="text-center text-[10px] text-white/20 mt-2.5 tracking-wider">
          try: "process" · "briefing" · "overdue" · "decide" · "todos" · "health" · "costs" · "search" · or ask anything
        </p>
      )}

      {/* Error */}
      {voice.error && (
        <p className="text-center text-[10px] text-[#FF453A]/60 mt-1">
          mic error: {voice.error}
        </p>
      )}
    </div>
  );
}
