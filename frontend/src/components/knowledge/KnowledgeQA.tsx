import { useState, useRef, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Search, Loader2, ExternalLink, MessageSquare, AlertCircle } from 'lucide-react';
import { apiPost } from '../../lib/api';
import { cn } from '../../lib/utils';

interface QASource {
  gid: string;
  title: string;
  snippet: string;
  relevance: number;
}

interface QAResponse {
  answer: string;
  sources: QASource[];
  confidence: number;
  model: string;
  input_tokens: number;
  output_tokens: number;
}

interface KnowledgeQAProps {
  onSelectArticle?: (gid: string) => void;
}

export function KnowledgeQA({ onSelectArticle }: KnowledgeQAProps) {
  const [question, setQuestion] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const qa = useMutation({
    mutationFn: (q: string) =>
      apiPost<QAResponse>('/knowledge/ask', { question: q, max_sources: 5 }),
  });

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (qa.isPending) return;
      const q = question.trim();
      if (!q) return;
      qa.mutate(q);
    },
    [question, qa],
  );

  const confidenceColor = (c: number) => {
    if (c >= 0.7) return 'text-green-600';
    if (c >= 0.4) return 'text-yellow-600';
    return 'text-red-500';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Search bar */}
      <form onSubmit={handleSubmit} className="px-4 py-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            ref={inputRef}
            id="qa-question"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your knowledge base..."
            aria-label="Ask a question about your knowledge base"
            className="w-full pl-10 pr-24 py-3 bg-card border border-border rounded-lg text-sm
                       placeholder:text-muted-foreground focus:outline-none focus:ring-2
                       focus:ring-accent/20 focus:border-accent transition-colors"
          />
          <button
            type="submit"
            disabled={qa.isPending || !question.trim()}
            aria-label={qa.isPending ? 'Searching...' : 'Ask question'}
            className={cn(
              'absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 rounded-md text-sm font-medium transition-colors',
              qa.isPending || !question.trim()
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-foreground text-background hover:bg-foreground/90',
            )}
          >
            {qa.isPending ? (
              <><Loader2 className="h-4 w-4 animate-spin" /><span className="sr-only">Searching</span></>
            ) : (
              'Ask'
            )}
          </button>
        </div>
      </form>

      {/* Results area */}
      <div className="flex-1 overflow-auto px-4 pb-4" role="status" aria-live="polite">
        {/* Loading state */}
        {qa.isPending && (
          <div className="flex items-center gap-3 p-4 bg-card border border-border rounded-lg">
            <Loader2 className="h-5 w-5 animate-spin text-accent" />
            <div>
              <p className="text-sm font-medium">Searching knowledge base...</p>
              <p className="text-xs text-muted-foreground">
                Finding relevant articles and synthesizing an answer
              </p>
            </div>
          </div>
        )}

        {/* Error state */}
        {qa.isError && (
          <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg">
            <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-700 dark:text-red-400">
                Failed to get answer
              </p>
              <p className="text-xs text-red-600 dark:text-red-500 mt-1">
                {(qa.error as Error)?.message || 'Unknown error'}
              </p>
            </div>
          </div>
        )}

        {/* Answer */}
        {qa.data && (
          <div className="space-y-4">
            {/* Answer card */}
            <div className="bg-card border border-border rounded-lg p-5">
              <div className="flex items-center gap-2 mb-3">
                <MessageSquare className="h-4 w-4 text-accent" />
                <span className="text-sm font-medium">Answer</span>
                <span
                  className={cn(
                    'ml-auto text-xs font-mono',
                    confidenceColor(qa.data.confidence),
                  )}
                >
                  {Math.round(qa.data.confidence * 100)}% confidence
                </span>
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {qa.data.answer}
              </div>
              {qa.data.model && (
                <p className="mt-3 text-xs text-muted-foreground">
                  {qa.data.model} &middot; {qa.data.input_tokens + qa.data.output_tokens} tokens
                </p>
              )}
            </div>

            {/* Sources */}
            {qa.data.sources.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Sources ({qa.data.sources.length})
                </h3>
                <div className="space-y-2">
                  {qa.data.sources.map((source) => (
                    <button
                      key={source.gid}
                      onClick={() => onSelectArticle?.(source.gid)}
                      className="flex items-start gap-3 p-3 w-full text-left bg-card border border-border rounded-lg
                                 hover:border-accent/40 transition-colors group"
                    >
                      <ExternalLink className="h-4 w-4 text-muted-foreground mt-0.5 group-hover:text-accent" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate group-hover:text-accent">
                          {source.title}
                        </p>
                        <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
                          {source.snippet}
                        </p>
                      </div>
                      <span className="text-xs font-mono text-muted-foreground">
                        {Math.round(source.relevance * 100)}%
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {!qa.data && !qa.isPending && !qa.isError && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <MessageSquare className="h-10 w-10 text-muted-foreground/40 mb-3" />
            <p className="text-sm text-muted-foreground">
              Ask a question to get answers from your knowledge base
            </p>
            <div className="mt-4 space-y-1.5">
              {[
                'Who is responsible for this project?',
                'What are the most important recent decisions?',
                'What systems are involved in this workflow?',
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => {
                    setQuestion(example);
                    qa.mutate(example);
                  }}
                  className="block w-full text-left px-3 py-2 text-xs text-muted-foreground
                             bg-muted/50 rounded-md hover:bg-muted hover:text-foreground transition-colors"
                >
                  &ldquo;{example}&rdquo;
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
