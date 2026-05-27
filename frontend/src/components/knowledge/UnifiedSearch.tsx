import { useRef, useCallback } from 'react';
import { Search, Loader2, Zap, ExternalLink, MessageSquare } from 'lucide-react';
import { useStreamingQA, type QASource } from '../../hooks/useStreamingQA';
import { cn } from '../../lib/utils';

interface UnifiedSearchProps {
  query: string;
  onQueryChange: (q: string) => void;
  onFocus: () => void;
  isActive: boolean;
  onSelectArticle?: (gid: string) => void;
}

// Question detection helper retained for future use (mode routing).
// Kept here rather than removed to make reintroduction trivial.

export function UnifiedSearch({ query, onQueryChange, onFocus, isActive, onSelectArticle }: UnifiedSearchProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const { ask, isStreaming, hasResult, hasError, answer, sources, confidence, phase, error } = useStreamingQA();

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (!q || isStreaming) return;
    ask(q, 'lightning');
  }, [query, isStreaming, ask]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && query.trim()) {
      e.preventDefault();
      const q = query.trim();
      if (!isStreaming) {
        ask(q, 'lightning');
      }
    }
  }, [query, isStreaming, ask]);

  const showResults = isActive && (hasResult || isStreaming || hasError);

  return (
    <div>
      {/* Search bar */}
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onFocus={onFocus}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything or search..."
            role="searchbox"
            aria-label="Search knowledge base"
            className="w-full pl-10 pr-20 py-2.5 bg-card border border-border rounded-lg text-sm
                       placeholder:text-muted-foreground focus:outline-none focus:ring-2
                       focus:ring-accent/20 focus:border-accent transition-colors"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {query.trim() && !isStreaming && (
              <button
                type="submit"
                className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-foreground text-background hover:bg-foreground/90 transition-colors"
              >
                <Zap className="h-3 w-3" />
                Ask
              </button>
            )}
            {isStreaming && (
              <div className="flex items-center gap-1 px-2.5 py-1 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                {phase === 'searching' ? 'Searching...' : 'Generating...'}
              </div>
            )}
          </div>
        </div>
      </form>

      {/* Inline results (only when Explore tab is active) */}
      {showResults && (
        <div className="mt-2 space-y-3">
          {/* Streaming / completed answer */}
          {(isStreaming || hasResult) && answer && (
            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare className="h-4 w-4 text-accent" />
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Answer
                </span>
                {confidence > 0 && (
                  <span className={cn(
                    'ml-auto text-xs font-mono',
                    confidence >= 0.7 ? 'text-green-600' : confidence >= 0.4 ? 'text-yellow-600' : 'text-red-500',
                  )}>
                    {Math.round(confidence * 100)}%
                  </span>
                )}
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {answer}
                {isStreaming && (
                  <span className="inline-block w-1.5 h-4 bg-accent/60 animate-pulse ml-0.5 -mb-0.5" />
                )}
              </div>
            </div>
          )}

          {/* Sources */}
          {sources.length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5 px-1">
                Sources ({sources.length})
              </h3>
              <div className="space-y-1">
                {sources.map((source: QASource) => (
                  <button
                    key={source.gid}
                    onClick={() => onSelectArticle?.(source.gid)}
                    className="flex items-start gap-2 p-2.5 w-full text-left bg-card border border-border rounded-lg
                               hover:border-accent/40 transition-colors group"
                  >
                    <ExternalLink className="h-3.5 w-3.5 text-muted-foreground mt-0.5 group-hover:text-accent shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate group-hover:text-accent">{source.title}</p>
                      <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">{source.snippet}</p>
                    </div>
                    <span className="text-xs font-mono text-muted-foreground shrink-0">
                      {Math.round(source.relevance * 100)}%
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          {hasError && (
            <div className="p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg">
              <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
