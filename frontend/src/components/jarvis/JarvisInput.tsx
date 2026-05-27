import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, MicOff, Send, Loader2, Clock, Trash2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useVoiceInput } from '../../hooks/useVoiceInput';
import { useTypewriter } from '../../hooks/useTypewriter';
import { apiFetch, apiPost } from '../../lib/api';
import { useJarvisStore } from '../../stores/jarvisStore';
import type { CommandResponse } from '../../types/cards';

interface JarvisHistoryItem {
  id: number;
  command: string;
  response_summary: string | null;
  cards_json: string | null;
  created_at: string;
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
  const messages = useJarvisStore((s) => s.messages);
  const addExchange = useJarvisStore((s) => s.addExchange);
  const clearJarvis = useJarvisStore((s) => s.clear);
  // Render as command/response pairs (user followed by assistant).
  const history = useMemo(() => {
    const pairs: { query: string; reply: string }[] = [];
    for (let i = 0; i < messages.length; i++) {
      const m = messages[i];
      if (m.role === 'user') {
        const next = messages[i + 1];
        pairs.push({
          query: m.text,
          reply: next && next.role === 'assistant' ? next.text : '',
        });
        if (next && next.role === 'assistant') i++;
      }
    }
    return pairs;
  }, [messages]);
  const [recentCommands, setRecentCommands] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const voice = useVoiceInput();

  // Fetch recent Jarvis history on mount
  useEffect(() => {
    apiFetch<JarvisHistoryItem[]>('/jarvis/history?limit=5')
      .then((items) => {
        // Deduplicate commands and keep only unique ones
        const seen = new Set<string>();
        const cmds: string[] = [];
        for (const item of items) {
          const cmd = item.command.trim();
          const lower = cmd.toLowerCase();
          if (!seen.has(lower) && cmds.length < 5) {
            seen.add(lower);
            cmds.push(cmd);
          }
        }
        setRecentCommands(cmds);
      })
      .catch(() => {
        // Silently ignore — history is optional
      });
  }, []);

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
      // Persist exchange to Jarvis store (survives navigations + reloads)
      addExchange(input.trim(), result.reply);
      // Update recent commands for suggestions
      setRecentCommands((prev) => {
        const lower = input.trim().toLowerCase();
        const filtered = prev.filter((c) => c.toLowerCase() !== lower);
        return [input.trim(), ...filtered].slice(0, 5);
      });
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
  }, [isProcessing, onSpeak, onChime, onInteract, navigate, addExchange]);

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
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-widest text-white/30">
              Session ({history.length})
            </span>
            <button
              type="button"
              onClick={() => {
                clearJarvis();
                setResponse('');
                setUserQuery('');
                setSuggestChat(false);
              }}
              className="flex items-center gap-1 text-[10px] font-mono text-white/30 hover:text-[#FF453A]/80 transition-colors"
              aria-label="Clear Jarvis session"
            >
              <Trash2 size={10} />
              Clear
            </button>
          </div>
          {history.slice(-5).map((h, i) => (
            <div key={i} className="text-xs text-white/40">
              <span className="font-mono text-sky-400/60">&gt; {h.query}</span>
              {h.reply && (
                <p className="ml-4 text-white/25">{h.reply.slice(0, 100)}{h.reply.length > 100 ? '...' : ''}</p>
              )}
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

      {/* Recent commands as clickable suggestions */}
      {!response && !voice.isListening && recentCommands.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
          <Clock size={10} className="text-white/20" />
          {recentCommands.map((cmd, i) => (
            <button
              key={i}
              onClick={() => handleCommand(cmd)}
              disabled={isProcessing}
              className="text-[10px] font-mono text-white/25 hover:text-sky-400/70 transition-colors
                         border border-white/8 hover:border-sky-400/30 rounded-md px-2 py-0.5
                         disabled:opacity-30 disabled:cursor-not-allowed"
            >
              {cmd.length > 30 ? cmd.slice(0, 30) + '...' : cmd}
            </button>
          ))}
        </div>
      )}

      {/* Hints */}
      {!response && !voice.isListening && recentCommands.length === 0 && (
        <p className="text-center text-[10px] text-white/20 mt-2.5 tracking-wider">
          try: "process" · "briefing" · "overdue" · "decide" · "todos" · "health" · "costs" · "search" · or ask anything
        </p>
      )}

      {/* Error */}
      {voice.error && (
        <p className="text-center text-[10px] text-[#FF453A]/60 mt-1">
          {voice.error}
        </p>
      )}
    </div>
  );
}
