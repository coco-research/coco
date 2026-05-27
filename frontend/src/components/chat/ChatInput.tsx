import { useRef, useState, useCallback, type KeyboardEvent, type ChangeEvent } from 'react';
import { Send, Loader2, Paperclip, X, FileText, Search } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';
import { cn } from '../../lib/utils';
import { apiFetch } from '../../lib/api';

export interface AttachedContent {
  id: string;
  title: string;
  source?: string;
}

interface ChatInputProps {
  onSend: (message: string, contentIds?: string[]) => void;
  disabled?: boolean;
  streaming?: boolean;
}

interface ContentSearchResult {
  id: string;
  title: string;
  summary?: string;
  source?: string;
  created_at?: string;
}

function ContentPickerDialog({
  open,
  onOpenChange,
  onAttach,
  alreadyAttached,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAttach: (item: AttachedContent) => void;
  alreadyAttached: Set<string>;
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ContentSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const data = await apiFetch<{ items: ContentSearchResult[] }>(`/content?q=${encodeURIComponent(q)}&limit=20`);
      setResults(data.items ?? []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleQueryChange = (e: ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(val), 300);
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 z-50 animate-fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg bg-card border border-border rounded-xl shadow-2xl animate-fade-in">
          <div className="p-4 border-b border-border">
            <Dialog.Title className="text-sm font-medium text-foreground mb-3">Attach Knowledge Hub content</Dialog.Title>
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={query}
                onChange={handleQueryChange}
                placeholder="Search content..."
                autoFocus
                className="w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
              />
            </div>
          </div>
          <div className="max-h-[300px] overflow-y-auto p-2">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 size={20} className="animate-spin text-muted-foreground" />
              </div>
            ) : results.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-8">
                {query.trim() ? 'No results found.' : 'Type to search Knowledge Hub content.'}
              </p>
            ) : (
              results.map(item => {
                const attached = alreadyAttached.has(item.id);
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      if (!attached) {
                        onAttach({ id: item.id, title: item.title, source: item.source });
                      }
                    }}
                    disabled={attached}
                    className={cn(
                      'w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                      attached
                        ? 'opacity-50 cursor-not-allowed bg-muted/30'
                        : 'hover:bg-accent/50 cursor-pointer',
                    )}
                  >
                    <FileText size={16} className="shrink-0 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground truncate">{item.title}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        {item.source && (
                          <span className="text-[10px] text-muted-foreground">{item.source}</span>
                        )}
                        {item.created_at && (
                          <span className="text-[10px] text-muted-foreground">
                            {new Date(item.created_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    {attached && (
                      <span className="text-[10px] text-muted-foreground">attached</span>
                    )}
                  </button>
                );
              })
            )}
          </div>
          <div className="p-3 border-t border-border flex justify-end">
            <Dialog.Close asChild>
              <button className="px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors">
                Done
              </button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export function ChatInput({ onSend, disabled = false, streaming = false }: ChatInputProps) {
  const [value, setValue] = useState('');
  const [attachments, setAttachments] = useState<AttachedContent[]>([]);
  const [pickerOpen, setPickerOpen] = useState(false);
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

  const handleAttach = useCallback((item: AttachedContent) => {
    setAttachments(prev => {
      if (prev.some(a => a.id === item.id)) return prev;
      return [...prev, item];
    });
  }, []);

  const handleRemoveAttachment = useCallback((id: string) => {
    setAttachments(prev => prev.filter(a => a.id !== id));
  }, []);

  const attachedIds = new Set(attachments.map(a => a.id));

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    const contentIds = attachments.length > 0 ? attachments.map(a => a.id) : undefined;
    onSend(trimmed, contentIds);
    setValue('');
    setAttachments([]);
    // Reset height after clearing
    requestAnimationFrame(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    });
  }, [value, disabled, onSend, attachments]);

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
      <div className="max-w-3xl mx-auto">
        {/* Attached content chips */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {attachments.map(att => (
              <span
                key={att.id}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-accent/20 text-xs text-foreground border border-accent/30"
              >
                <FileText size={12} className="text-accent shrink-0" />
                <span className="truncate max-w-[180px]">{att.title}</span>
                <button
                  onClick={() => handleRemoveAttachment(att.id)}
                  className="ml-0.5 p-0.5 rounded hover:bg-accent/30 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X size={10} />
                </button>
              </span>
            ))}
          </div>
        )}
        <div className="flex items-end gap-2">
          {/* Attach button */}
          <button
            type="button"
            onClick={() => setPickerOpen(true)}
            disabled={disabled}
            title="Attach Knowledge Hub content"
            aria-label="Attach Knowledge Hub content"
            className={cn(
              'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center',
              'border border-border text-muted-foreground transition-all',
              'hover:bg-accent/50 hover:text-foreground',
              'disabled:opacity-40 disabled:cursor-not-allowed',
              attachments.length > 0 && 'text-accent border-accent/40',
            )}
          >
            <Paperclip size={18} aria-hidden="true" />
          </button>
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
            type="button"
            onClick={handleSend}
            disabled={disabled || !value.trim()}
            aria-label={streaming ? 'Streaming response' : 'Send message'}
            className={cn(
              'flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center',
              'bg-accent text-accent-foreground transition-all shadow-sm',
              'hover:bg-accent/80',
              'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-accent',
            )}
          >
            {streaming ? (
              <Loader2 size={18} aria-hidden="true" className="animate-spin" />
            ) : (
              <Send size={18} aria-hidden="true" />
            )}
          </button>
        </div>
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

      {/* Content picker dialog */}
      <ContentPickerDialog
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        onAttach={handleAttach}
        alreadyAttached={attachedIds}
      />
    </div>
  );
}
