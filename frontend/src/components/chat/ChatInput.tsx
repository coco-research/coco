import { useRef, useState, useCallback, type KeyboardEvent, type ChangeEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  streaming?: boolean;
}

export function ChatInput({ onSend, disabled = false, streaming = false }: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    // Max 5 rows (~120px)
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, []);

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    adjustHeight();
  };

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    // Reset height after clearing
    requestAnimationFrame(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    });
  }, [value, disabled, onSend]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Cmd+Enter (Mac) or Ctrl+Enter (Win) to send
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSend();
      return;
    }
    // Plain Enter also sends (Shift+Enter for newline)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-border p-4 bg-card">
      <div className="flex items-end gap-2 max-w-3xl mx-auto">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={streaming ? 'Waiting for response...' : 'Ask CoCo anything...'}
          rows={1}
          className={cn(
            'flex-1 resize-none bg-card border border-border rounded-xl px-4 py-3',
            'text-sm text-foreground placeholder:text-muted-foreground',
            'focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent',
            'transition-colors',
            disabled && 'opacity-50 cursor-not-allowed',
          )}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className={cn(
            'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center',
            'bg-accent text-accent-foreground transition-all shadow-sm',
            'hover:bg-accent/80',
            'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-accent',
          )}
        >
          {streaming ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <Send size={18} />
          )}
        </button>
      </div>
      <p className="text-xs text-muted-foreground text-center mt-2">
        {streaming ? (
          <span className="text-accent">Streaming response...</span>
        ) : (
          <>
            <kbd className="font-mono">Enter</kbd> to send &middot; <kbd className="font-mono">Shift+Enter</kbd> for newline
          </>
        )}
      </p>
    </div>
  );
}
