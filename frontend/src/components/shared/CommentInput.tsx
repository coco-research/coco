import { useState, useRef, useEffect, useCallback } from 'react';
import { Send } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { MentionOption } from '../../types/comments';

interface CommentInputProps {
  mentionOptions: MentionOption[];
  onSubmit: (body: string, mentions: string[]) => void;
  placeholder?: string;
  autoFocus?: boolean;
  isPending?: boolean;
}

export function CommentInput({
  mentionOptions,
  onSubmit,
  placeholder = 'Add a comment...',
  autoFocus = false,
  isPending = false,
}: CommentInputProps) {
  const [text, setText] = useState('');
  const [showMentions, setShowMentions] = useState(false);
  const [mentionFilter, setMentionFilter] = useState('');
  const [mentionIndex, setMentionIndex] = useState(0);
  const [cursorPos, setCursorPos] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredOptions = mentionOptions.filter((opt) =>
    opt.label.toLowerCase().includes(mentionFilter.toLowerCase()),
  );

  // Reset mention index when filter changes
  useEffect(() => {
    setMentionIndex(0);
  }, [mentionFilter]);

  const insertMention = useCallback(
    (option: MentionOption) => {
      // Find the @ that triggered this mention
      const beforeCursor = text.slice(0, cursorPos);
      const atIndex = beforeCursor.lastIndexOf('@');
      if (atIndex === -1) return;

      const before = text.slice(0, atIndex);
      const after = text.slice(cursorPos);
      const newText = `${before}@${option.label} ${after}`;
      setText(newText);
      setShowMentions(false);
      setMentionFilter('');

      // Restore focus
      requestAnimationFrame(() => {
        const ta = textareaRef.current;
        if (ta) {
          const newPos = atIndex + option.label.length + 2; // @label + space
          ta.focus();
          ta.setSelectionRange(newPos, newPos);
        }
      });
    },
    [text, cursorPos],
  );

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    const val = e.target.value;
    const pos = e.target.selectionStart ?? val.length;
    setText(val);
    setCursorPos(pos);

    // Check if we're in a mention context
    const beforeCursor = val.slice(0, pos);
    const atIndex = beforeCursor.lastIndexOf('@');
    if (atIndex !== -1) {
      const fragment = beforeCursor.slice(atIndex + 1);
      // Only show if no space in the fragment (still typing the mention)
      if (!fragment.includes(' ') && !fragment.includes('\n')) {
        setMentionFilter(fragment);
        setShowMentions(true);
        return;
      }
    }
    setShowMentions(false);
    setMentionFilter('');
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (showMentions && filteredOptions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setMentionIndex((prev) => (prev + 1) % filteredOptions.length);
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setMentionIndex((prev) => (prev - 1 + filteredOptions.length) % filteredOptions.length);
        return;
      }
      if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        insertMention(filteredOptions[mentionIndex]);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setShowMentions(false);
        return;
      }
    }

    // Cmd+Enter or Ctrl+Enter to submit
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function extractMentions(body: string): string[] {
    const re = /@([\w\s-]+?)(?=\s@|\s[^@]|$)/g;
    const found: string[] = [];
    let match: RegExpExecArray | null;
    while ((match = re.exec(body)) !== null) {
      const name = match[1].trim();
      const opt = mentionOptions.find(
        (o) => o.label.toLowerCase() === name.toLowerCase(),
      );
      if (opt) found.push(opt.id);
    }
    return [...new Set(found)];
  }

  function handleSubmit() {
    const trimmed = text.trim();
    if (!trimmed || isPending) return;
    const mentions = extractMentions(trimmed);
    onSubmit(trimmed, mentions);
    setText('');
    setShowMentions(false);
  }

  return (
    <div className="relative">
      {/* Mention dropdown */}
      {showMentions && filteredOptions.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute bottom-full left-0 mb-1 w-56 max-h-40 overflow-y-auto bg-card border border-border rounded-lg shadow-lg z-10"
        >
          {filteredOptions.map((opt, i) => (
            <button
              key={opt.id}
              onClick={() => insertMention(opt)}
              className={cn(
                'w-full text-left px-3 py-1.5 text-sm flex items-center gap-2 transition-colors',
                i === mentionIndex
                  ? 'bg-accent/50 text-foreground'
                  : 'text-muted-foreground hover:bg-accent/30 hover:text-foreground',
              )}
            >
              <span
                className={cn(
                  'inline-block w-5 h-5 rounded-full text-[10px] font-medium flex items-center justify-center shrink-0',
                  opt.type === 'agent'
                    ? 'bg-accent/30 text-accent'
                    : 'bg-info/20 text-info',
                )}
              >
                {opt.label[0]?.toUpperCase()}
              </span>
              <span className="truncate">{opt.label}</span>
              <span className="text-[10px] text-muted-foreground ml-auto capitalize">
                {opt.type}
              </span>
            </button>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          autoFocus={autoFocus}
          rows={1}
          className="flex-1 bg-transparent border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/30 focus:border-accent/50 resize-none transition-colors min-h-[36px] max-h-24"
          style={{ fieldSizing: 'content' } as React.CSSProperties}
        />
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || isPending}
          className={cn(
            'p-2 rounded-lg transition-colors shrink-0',
            text.trim() && !isPending
              ? 'text-accent hover:bg-accent/20'
              : 'text-muted-foreground/40 cursor-not-allowed',
          )}
          title="Send (Cmd+Enter)"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
      <p className="text-[10px] text-muted-foreground/60 mt-1">
        Type @ to mention. Cmd+Enter to send.
      </p>
    </div>
  );
}
