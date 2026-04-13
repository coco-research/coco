import { useState, useRef, useCallback, useMemo } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Search, Loader2, ExternalLink, MessageSquare, AlertCircle, Zap, Brain, ChevronDown, ChevronRight } from 'lucide-react';
import { apiPost } from '../../lib/api';
import { cn } from '../../lib/utils';

type Mode = 'lightning' | 'ultrathink';

interface QASource {
  gid: string;
  title: string;
  snippet: string;
  relevance: number;
}

interface ToolCall {
  tool: string;
  input: Record<string, unknown>;
  elapsed_s: number;
  round: number;
}

interface QAResponse {
  answer: string;
  sources: QASource[];
  confidence: number;
  model: string;
  input_tokens: number;
  output_tokens: number;
  mode: string;
  thinking: string | null;
  tool_calls: ToolCall[] | null;
  rounds: number;
}

interface KnowledgeQAProps {
  onSelectArticle?: (gid: string) => void;
}

const COMPLEX_PATTERNS = [
  /\bhow does .+ (?:affect|connect|relate|impact)\b/i,
  /\bcompare\b/i,
  /\brelationship between\b/i,
  /\bhistory of\b/i,
  /\bwhat connects\b/i,
  /\bwho (?:works with|reports to|owns)\b/i,
  /\btrace\b/i,
  /\bevolution of\b/i,
];

function detectComplexity(q: string): boolean {
  return COMPLEX_PATTERNS.some((p) => p.test(q));
}

const TOOL_ICONS: Record<string, string> = {
  search_articles: 'Search',
  get_entity_details: 'Entity',
  traverse_connections: 'Graph',
  get_article: 'Read',
};

export function KnowledgeQA({ onSelectArticle }: KnowledgeQAProps) {
  const [question, setQuestion] = useState('');
  const [mode, setMode] = useState<Mode>('lightning');
  const [showThinking, setShowThinking] = useState(false);
  const [showToolCalls, setShowToolCalls] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const suggestUltrathink = useMemo(() => detectComplexity(question), [question]);

  const qa = useMutation({
    mutationFn: ({ q, m }: { q: string; m: Mode }) =>
      apiPost<QAResponse>('/knowledge/ask', { question: q, max_sources: 5, mode: m }),
  });

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (qa.isPending) return;
      const q = question.trim();
      if (!q) return;
      qa.mutate({ q, m: mode });
    },
    [question, mode, qa],
  );

  const confidenceLabel = (c: number) => {
    if (c >= 0.7) return { text: 'High', cls: 'text-green-600' };
    if (c >= 0.4) return { text: 'Medium', cls: 'text-yellow-600' };
    return { text: 'Low', cls: 'text-red-500' };
  };

  const isUltrathink = qa.data?.mode === 'ultrathink';

  return (
    <div className="flex flex-col h-full">
      {/* Search bar */}
      <form onSubmit={handleSubmit} className="px-4 py-4 space-y-2">
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

        {/* Mode toggle */}
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-muted rounded-lg p-0.5" role="radiogroup" aria-label="Answer mode">
            <button
              type="button"
              role="radio"
              aria-checked={mode === 'lightning'}
              onClick={() => setMode('lightning')}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
                mode === 'lightning'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              <Zap className="h-3 w-3" />
              Lightning
            </button>
            <button
              type="button"
              role="radio"
              aria-checked={mode === 'ultrathink'}
              onClick={() => setMode('ultrathink')}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
                mode === 'ultrathink'
                  ? 'bg-purple-100 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 shadow-sm'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              <Brain className="h-3 w-3" />
              Ultrathink
            </button>
          </div>
          <span className="text-xs text-muted-foreground">
            {mode === 'lightning' ? 'Fast answers (~2s)' : 'Deep analysis with graph traversal (~15-30s)'}
          </span>
          {suggestUltrathink && mode === 'lightning' && (
            <button
              type="button"
              onClick={() => setMode('ultrathink')}
              className="text-xs text-purple-600 dark:text-purple-400 hover:underline"
            >
              Complex question detected — try Ultrathink?
            </button>
          )}
        </div>
      </form>

      {/* Results area */}
      <div className="flex-1 overflow-auto px-4 pb-4" role="status" aria-live="polite">
        {/* Loading state */}
        {qa.isPending && (
          <div className="flex items-center gap-3 p-4 bg-card border border-border rounded-lg">
            <Loader2 className="h-5 w-5 animate-spin text-accent" />
            <div>
              <p className="text-sm font-medium">
                {mode === 'ultrathink' ? 'Deep analysis in progress...' : 'Searching knowledge base...'}
              </p>
              <p className="text-xs text-muted-foreground">
                {mode === 'ultrathink'
                  ? 'Searching, traversing connections, and reasoning across multiple sources'
                  : 'Finding relevant articles and synthesizing an answer'}
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
            {/* Ultrathink: Thinking process (collapsible) */}
            {isUltrathink && qa.data.thinking && (
              <div className="bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-900 rounded-lg">
                <button
                  onClick={() => setShowThinking(!showThinking)}
                  className="flex items-center gap-2 w-full px-4 py-3 text-left"
                >
                  {showThinking ? <ChevronDown className="h-4 w-4 text-purple-500" /> : <ChevronRight className="h-4 w-4 text-purple-500" />}
                  <Brain className="h-4 w-4 text-purple-500" />
                  <span className="text-xs font-medium text-purple-700 dark:text-purple-300">
                    Reasoning ({qa.data.rounds} round{qa.data.rounds !== 1 ? 's' : ''})
                  </span>
                </button>
                {showThinking && (
                  <div className="px-4 pb-3">
                    <pre className="text-xs text-purple-800 dark:text-purple-200 whitespace-pre-wrap leading-relaxed max-h-60 overflow-auto">
                      {qa.data.thinking}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Ultrathink: Tool call chain (collapsible) */}
            {isUltrathink && qa.data.tool_calls && qa.data.tool_calls.length > 0 && (
              <div className="bg-card border border-border rounded-lg">
                <button
                  onClick={() => setShowToolCalls(!showToolCalls)}
                  className="flex items-center gap-2 w-full px-4 py-3 text-left"
                >
                  {showToolCalls ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  <span className="text-xs font-medium text-muted-foreground">
                    Research chain ({qa.data.tool_calls.length} tool call{qa.data.tool_calls.length !== 1 ? 's' : ''})
                  </span>
                </button>
                {showToolCalls && (
                  <div className="px-4 pb-3 space-y-1.5">
                    {qa.data.tool_calls.map((tc, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        <span className="w-5 h-5 rounded-full bg-muted flex items-center justify-center text-[10px] font-mono">
                          {tc.round}
                        </span>
                        <span className="font-medium text-foreground">
                          {TOOL_ICONS[tc.tool] || tc.tool}
                        </span>
                        <span className="text-muted-foreground truncate flex-1">
                          {JSON.stringify(tc.input).slice(0, 80)}
                        </span>
                        <span className="text-muted-foreground font-mono">
                          {tc.elapsed_s}s
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Answer card */}
            <div className={cn(
              'bg-card border rounded-lg p-5',
              isUltrathink ? 'border-purple-200 dark:border-purple-900' : 'border-border',
            )}>
              <div className="flex items-center gap-2 mb-3">
                {isUltrathink ? (
                  <Brain className="h-4 w-4 text-purple-500" />
                ) : (
                  <Zap className="h-4 w-4 text-accent" />
                )}
                <span className="text-sm font-medium">
                  {isUltrathink ? 'Deep Analysis' : 'Answer'}
                </span>
                {(() => {
                  const c = confidenceLabel(qa.data.confidence);
                  return (
                    <span className={cn('ml-auto text-xs font-mono', c.cls)}>
                      {c.text} — {Math.round(qa.data.confidence * 100)}%
                    </span>
                  );
                })()}
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {qa.data.answer}
              </div>
              {qa.data.model && (
                <p className="mt-3 text-xs text-muted-foreground">
                  {qa.data.model} &middot; {qa.data.input_tokens + qa.data.output_tokens} tokens
                  {isUltrathink && ` · ${qa.data.rounds} round${qa.data.rounds !== 1 ? 's' : ''}`}
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
                { q: 'Who is responsible for this project?', mode: 'lightning' as Mode },
                { q: 'What are the most important recent decisions?', mode: 'lightning' as Mode },
                { q: 'How do the programs connect to each other?', mode: 'ultrathink' as Mode },
              ].map(({ q, mode: exMode }) => (
                <button
                  key={q}
                  onClick={() => {
                    setQuestion(q);
                    setMode(exMode);
                    qa.mutate({ q, m: exMode });
                  }}
                  className="flex items-center gap-2 w-full text-left px-3 py-2 text-xs text-muted-foreground
                             bg-muted/50 rounded-md hover:bg-muted hover:text-foreground transition-colors"
                >
                  {exMode === 'ultrathink' ? (
                    <Brain className="h-3 w-3 text-purple-500 shrink-0" />
                  ) : (
                    <Zap className="h-3 w-3 text-muted-foreground shrink-0" />
                  )}
                  &ldquo;{q}&rdquo;
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
