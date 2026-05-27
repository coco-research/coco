import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, MicOff, Send, X, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';
import { apiPost } from '../../lib/api';
import { useJarvisAudio } from '../../hooks/useJarvisAudio';
import { useVoiceInput } from '../../hooks/useVoiceInput';
import { useScope } from '../../context/ScopeContext';
import type { CardData, CommandResponse } from '../../types/cards';
import { ActionCard } from '../jarvis/cards/ActionCard';

type OrbState = 'collapsed' | 'expanded' | 'responding';

const AUTO_COLLAPSE_MS = 5_000;

function isInputFocused(): boolean {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName.toLowerCase();
  return (
    tag === 'input' ||
    tag === 'textarea' ||
    tag === 'select' ||
    (el as HTMLElement).isContentEditable
  );
}

// --- OrbDot: collapsed state --------------------------------------------------

function OrbDot({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-11 h-11 rounded-full flex items-center justify-center',
        'bg-black/80 border border-white/10 backdrop-blur-[40px] saturate-[180%]',
        'hover:scale-110 transition-transform duration-200',
        'shadow-[0_8px_32px_rgba(0,0,0,0.5)]',
      )}
      aria-label="Open CoCo assistant"
    >
      <div className="w-3 h-3 rounded-full bg-[#0A84FF] animate-orb-pulse" />
    </button>
  );
}

// --- OrbPanel: expanded/responding state -------------------------------------

interface OrbPanelProps {
  orbState: OrbState;
  onClose: () => void;
  textInput: string;
  setTextInput: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  isProcessing: boolean;
  voice: ReturnType<typeof useVoiceInput>;
  onToggleMic: () => void;
  responseText: string;
  cards: CardData[];
}

function OrbPanel({
  onClose,
  textInput,
  setTextInput,
  onSubmit,
  isProcessing,
  voice,
  onToggleMic,
  responseText,
  cards,
}: OrbPanelProps) {
  return (
    <div
      className={cn(
        'w-[360px] animate-orb-expand',
        'bg-black/80 backdrop-blur-[40px] saturate-[180%] border border-white/10',
        'rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] overflow-hidden',
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/5">
        <span className="text-sm font-semibold text-white/80 tracking-wide">CoCo</span>
        <button
          type="button"
          onClick={onClose}
          className="text-white/40 hover:text-white/70 transition-colors p-1"
          aria-label="Close CoCo"
        >
          <X size={14} />
        </button>
      </div>

      {/* Response area */}
      {responseText && (
        <div className="px-4 py-3 border-b border-white/5">
          <p className="text-sm text-white/70 leading-relaxed">{responseText}</p>
        </div>
      )}

      {/* Cards area */}
      {cards.length > 0 && (
        <div className="px-3 py-2 max-h-[280px] overflow-y-auto scrollbar-auto-hide space-y-2">
          {cards.map((c) => (
            <ActionCard key={c.id} card={c} variant="light" />
          ))}
        </div>
      )}

      {/* Live transcript */}
      {voice.isListening && (
        <div className="px-4 py-2 border-b border-white/5">
          {voice.transcript ? (
            <p className="text-xs text-[#FF453A]/70 font-mono">"{voice.transcript}"</p>
          ) : (
            <p className="text-xs text-[#FF453A]/40 font-mono animate-pulse">Listening...</p>
          )}
        </div>
      )}

      {/* Input row */}
      <form onSubmit={onSubmit} className="flex items-center gap-2 px-3 py-2.5">
        {/* Mic button */}
        <button
          type="button"
          onClick={onToggleMic}
          disabled={isProcessing}
          className={cn(
            'shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-all',
            'border',
            voice.isListening
              ? 'bg-[#FF453A]/15 border-[#FF453A]/30 text-[#FF453A]'
              : 'bg-white/5 border-white/10 text-white/50 hover:text-white/70',
          )}
          aria-label={voice.isListening ? 'Stop listening' : 'Start voice input'}
        >
          {voice.isListening ? <MicOff size={12} /> : <Mic size={12} />}
        </button>

        {/* Text input */}
        <input
          type="text"
          value={voice.isListening ? voice.transcript : textInput}
          onChange={(e) => !voice.isListening && setTextInput(e.target.value)}
          placeholder={voice.isListening ? 'Listening...' : 'Ask CoCo...'}
          disabled={isProcessing}
          onFocus={() => voice.isListening && voice.stop()}
          className={cn(
            'flex-1 bg-white/5 border rounded-xl',
            'px-3 py-1.5 text-sm text-white/80 placeholder:text-white/25',
            'focus:outline-none transition-all font-mono',
            voice.isListening
              ? 'border-[#FF453A]/20 bg-[#FF453A]/5'
              : 'border-white/10 focus:border-[#0A84FF]/30',
          )}
        />

        {/* Send button */}
        <button
          type="submit"
          disabled={isProcessing || voice.isListening || !textInput.trim()}
          className={cn(
            'shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-all',
            'border',
            isProcessing
              ? 'bg-[#0A84FF]/15 border-[#0A84FF]/30 text-[#0A84FF]'
              : textInput.trim()
                ? 'bg-[#0A84FF]/15 border-[#0A84FF]/30 text-[#0A84FF] hover:bg-[#0A84FF]/25'
                : 'bg-white/3 border-white/8 text-white/20',
          )}
        >
          {isProcessing ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
        </button>
      </form>

      {/* Error */}
      {voice.error && (
        <p className="text-center text-[10px] text-[#FF453A]/60 font-mono px-3 pb-2">
          mic error: {voice.error}
        </p>
      )}
    </div>
  );
}

// --- CocoOrb: main component -------------------------------------------------

export function CocoOrb() {
  const navigate = useNavigate();
  const audio = useJarvisAudio();
  const voice = useVoiceInput();
  const scope = useScope();

  const [orbState, setOrbState] = useState<OrbState>('collapsed');
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [responseText, setResponseText] = useState('');
  const [cards, setCards] = useState<CardData[]>([]);

  const autoCollapseTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const resetAutoCollapse = () => {
    clearTimeout(autoCollapseTimer.current);
    if (orbState !== 'collapsed') {
      autoCollapseTimer.current = setTimeout(() => {
        setOrbState('collapsed');
        setResponseText('');
        setCards([]);
        setTextInput('');
      }, AUTO_COLLAPSE_MS);
    }
  };

  // Clean up on unmount
  useEffect(() => {
    return () => {
      clearTimeout(autoCollapseTimer.current);
    };
  }, []);

  // Reset auto-collapse timer when state changes
  useEffect(() => {
    if (orbState === 'responding') {
      // Don't auto-collapse while responding
      clearTimeout(autoCollapseTimer.current);
    } else if (orbState === 'expanded' && responseText) {
      // Auto-collapse after idle period once we have a response
      resetAutoCollapse();
    }
  }, [orbState, responseText]);

  const expand = useCallback(() => {
    setOrbState('expanded');
    setResponseText('');
    setCards([]);
    audio.blip();
  }, [audio]);

  const collapse = useCallback(() => {
    clearTimeout(autoCollapseTimer.current);
    voice.stop();
    setOrbState('collapsed');
    setResponseText('');
    setCards([]);
    setTextInput('');
  }, [voice]);

  const handleCommand = useCallback(
    async (text: string) => {
      if (!text.trim() || isProcessing) return;
      setIsProcessing(true);
      setOrbState('responding');
      setResponseText('');
      setCards([]);
      setTextInput('');

      try {
        const payload: Record<string, unknown> = { text: text.trim() };
        if (scope.selectedNode?.hub_project_id) {
          payload.project_id = scope.selectedNode.hub_project_id;
        }

        const result = await apiPost<CommandResponse>('/jarvis/command', payload);

        setResponseText(result.reply);
        if (result.cards && result.cards.length > 0) {
          setCards(result.cards);
        }

        audio.chime();
        await audio.speak(result.reply);

        if (result.action === 'navigate' && result.url) {
          setTimeout(() => navigate(result.url!), 500);
        }

        setOrbState('expanded');
      } catch {
        const fallback = 'Something went wrong. Try again.';
        setResponseText(fallback);
        setOrbState('expanded');
      } finally {
        setIsProcessing(false);
      }
    },
    [isProcessing, audio, scope.selectedNode, navigate],
  );

  const toggleMic = useCallback(() => {
    if (voice.isListening) {
      voice.stop();
    } else {
      setResponseText('');
      setCards([]);
      audio.chime();
      voice.start(handleCommand);
    }
  }, [voice, audio, handleCommand]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (textInput.trim()) handleCommand(textInput);
    },
    [textInput, handleCommand],
  );

  // Spacebar push-to-talk
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.code !== 'Space') return;
      if (isInputFocused()) return;
      e.preventDefault();

      if (orbState === 'collapsed') {
        expand();
        // Small delay to let state update, then start voice
        setTimeout(() => {
          audio.chime();
          voice.start(handleCommand);
        }, 100);
      } else {
        toggleMic();
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [orbState, expand, toggleMic, audio, voice, handleCommand]);

  return (
    <div className="fixed bottom-6 right-6 z-[70]">
      {orbState === 'collapsed' && <OrbDot onClick={expand} />}
      {orbState !== 'collapsed' && (
        <OrbPanel
          orbState={orbState}
          onClose={collapse}
          textInput={textInput}
          setTextInput={setTextInput}
          onSubmit={handleSubmit}
          isProcessing={isProcessing}
          voice={voice}
          onToggleMic={toggleMic}
          responseText={responseText}
          cards={cards}
        />
      )}
    </div>
  );
}
