import { useState, useRef, useCallback, useMemo, useEffect } from 'react';
import {
  Search,
  Loader2,
  ExternalLink,
  MessageSquare,
  AlertCircle,
  Zap,
  Brain,
  ChevronDown,
  ChevronRight,
  Clock,
  Send,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useStreamingQA, type QASource, type ToolCall, type QAMode } from '../../hooks/useStreamingQA';

type Mode = QAMode;

interface HistoryEntry {
  id: string;
  question: string;
  mode: Mode;
  answer: string;
  sources: QASource[];
  confidence: number;
  model: string;
  input_tokens: number;
  output_tokens: number;
  thinking: string | null;
  tool_calls: ToolCall[] | null;
  rounds: number;
  timestamp: number;
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

const MAX_HISTORY = 5;

export function KnowledgeQA({ onSelectArticle }: KnowledgeQAProps) {
  const [question, setQuestion] = useState('');
  const [mode, setMode] = useState<Mode>('lightning');
  const [showThinking, setShowThinking] = useState(false);
  const [showToolCalls, setShowToolCalls] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const answerRef = useRef<HTMLDivElement>(null);
  // History
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  // Streaming via shared hook
  const {
    phase,
    answer,
    sources,
    confidence,
    model,
    tokens,
    thinking,
    toolCalls,
    rounds,
    error,
    isStreaming: hookIsStreaming,
    hasResult: hookHasResult,
    hasError: hookHasError,
    ask,
    abort,
    reset,
  } = useStreamingQA();

  // When a history entry is replayed, it overrides the live hook state for display
  const [historyOverride, setHistoryOverride] = useState<HistoryEntry | null>(null);

  // Display state — history override takes precedence over live hook state
  const streamPhase = historyOverride ? ('done' as const) : phase;
  const streamAnswer = historyOverride?.answer ?? answer;
  const streamSources = historyOverride?.sources ?? sources;
  const streamConfidence = historyOverride?.confidence ?? confidence;
  const streamModel = historyOverride?.model ?? model;
  const streamTokens = historyOverride
    ? { input: historyOverride.input_tokens, output: historyOverride.output_tokens }
    : tokens;
  const streamThinking = historyOverride?.thinking ?? thinking;
  const streamToolCalls = historyOverride ? (historyOverride.tool_calls ?? []) : toolCalls;
  const streamRounds = historyOverride?.rounds ?? rounds;
  const streamError = historyOverride ? null : error;
  const isStreaming = !historyOverride && hookIsStreaming;
  const hasResult = historyOverride ? !!historyOverride.answer : hookHasResult;
  const hasError = !historyOverride && hookHasError;

  const suggestUltrathink = useMemo(() => detectComplexity(question), [question]);

  const addToHistory = useCallback(
    (q: string, m: Mode, data: { answer: string; sources: QASource[]; confidence: number; model?: string; input_tokens?: number; output_tokens?: number; thinking?: string | null; tool_calls?: ToolCall[] | null; rounds?: number }) => {
      setHistory((prev) => {
        const entry: HistoryEntry = {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          question: q,
          mode: m,
          answer: data.answer,
          sources: data.sources,
          confidence: data.confidence,
          model: data.model ?? '',
          input_tokens: data.input_tokens ?? 0,
          output_tokens: data.output_tokens ?? 0,
          thinking: data.thinking ?? null,
          tool_calls: data.tool_calls ?? null,
          rounds: data.rounds ?? 1,
          timestamp: Date.now(),
        };
        return [entry, ...prev].slice(0, MAX_HISTORY);
      });
    },
    [],
  );

  const handleAsk = useCallback((q: string, m: Mode) => {
    setHistoryOverride(null);
    ask(q, m).then((result) => {
      if (result) addToHistory(q, m, result);
    }).catch(() => {
      // hook sets error state internally; this prevents unhandled rejection warnings
    });
  }, [ask, addToHistory]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (isStreaming) return;
      const q = question.trim();
      if (!q) return;
      handleAsk(q, mode);
    },
    [question, mode, isStreaming, handleAsk],
  );

  const loadFromHistory = useCallback((entry: HistoryEntry) => {
    reset();
    setQuestion(entry.question);
    setMode(entry.mode);
    setHistoryOverride(entry);
    setShowHistory(false);
  }, [reset]);

  // Auto-scroll answer area during streaming
  useEffect(() => {
    if (phase === 'generating' && answerRef.current) {
      answerRef.current.scrollTop = answerRef.current.scrollHeight;
    }
  }, [answer, phase]);

  // Cleanup on unmount
  useEffect(() => {
    return () => { abort(); };
  }, [abort]);

  const isUltrathink = mode === 'ultrathink';

  const confidenceLabel = (c: number) => {
    if (c >= 0.7) return { text: 'High', cls: 'text-green-600' };
    if (c >= 0.4) return { text: 'Medium', cls: 'text-yellow-600' };
    return { text: 'Low', cls: 'text-red-500' };
  };

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
            placeholder="Ask anything about your knowledge base..."
            aria-label="Ask anything about your knowledge base"
            className="w-full pl-10 pr-28 py-3 bg-card border border-border rounded-lg text-sm
                       placeholder:text-muted-foreground focus:outline-none focus:ring-2
                       focus:ring-accent/20 focus:border-accent transition-colors"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {history.length > 0 && (
              <button
                type="button"
                onClick={() => setShowHistory(!showHistory)}
                className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                title="Recent questions"
                aria-label="Show recent questions"
              >
                <Clock className="h-4 w-4" />
              </button>
            )}
            <button
              type="submit"
              disabled={isStreaming || !question.trim()}
              aria-label={isStreaming ? 'Searching...' : 'Ask question'}
              className={cn(
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5',
                isStreaming || !question.trim()
                  ? 'bg-muted text-muted-foreground cursor-not-allowed'
                  : 'bg-foreground text-background hover:bg-foreground/90',
              )}
            >
              {isStreaming ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  Ask
                </>
              )}
            </button>
          </div>
        </div>

        {/* History dropdown */}
        {showHistory && history.length > 0 && (
          <div className="bg-card border border-border rounded-lg shadow-lg overflow-hidden">
            <div className="px-3 py-2 border-b border-border">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Recent ({history.length})
              </span>
            </div>
            {history.map((entry) => (
              <button
                key={entry.id}
                onClick={() => loadFromHistory(entry)}
                className="flex items-center gap-2 w-full text-left px-3 py-2.5 text-sm
                           hover:bg-muted/50 transition-colors border-b border-border last:border-0"
              >
                {entry.mode === 'ultrathink' ? (
                  <Brain className="h-3.5 w-3.5 text-purple-500 shrink-0" />
                ) : (
                  <Zap className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                )}
                <span className="truncate flex-1">{entry.question}</span>
                <span className={cn('text-xs font-mono shrink-0', confidenceLabel(entry.confidence).cls)}>
                  {Math.round(entry.confidence * 100)}%
                </span>
              </button>
            ))}
          </div>
        )}

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
      <div ref={answerRef} className="flex-1 overflow-auto px-4 pb-4" role="status" aria-live="polite">
        {/* Loading: searching phase */}
        {streamPhase === 'searching' && (
          <div className="flex items-center gap-3 p-4 bg-card border border-border rounded-lg">
            <Loader2 className="h-5 w-5 animate-spin text-accent" />
            <div>
              <p className="text-sm font-medium">Searching knowledge base...</p>
              <p className="text-xs text-muted-foreground">
                {isUltrathink
                  ? 'Preparing deep analysis — searching, traversing connections, and reasoning across multiple sources'
                  : 'Finding relevant articles across your knowledge base'}
              </p>
            </div>
          </div>
        )}

        {/* Loading: generating phase (show sources + streaming answer) */}
        {streamPhase === 'generating' && (
          <div className="space-y-4">
            {/* Sources (already received) */}
            {streamSources.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Sources ({streamSources.length})
                </h3>
                <div className="space-y-2">
                  {streamSources.map((source) => (
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

            {/* Streaming answer */}
            <div className={cn(
              'bg-card border rounded-lg p-5',
              isUltrathink ? 'border-purple-200 dark:border-purple-900' : 'border-border',
            )}>
              <div className="flex items-center gap-2 mb-3">
                <Loader2 className="h-4 w-4 animate-spin text-accent" />
                <span className="text-sm font-medium">Generating answer...</span>
              </div>
              {streamAnswer && (
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {streamAnswer}
                  <span className="inline-block w-1.5 h-4 bg-accent/60 animate-pulse ml-0.5 -mb-0.5" />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error state */}
        {hasError && (
          <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-lg">
            <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-700 dark:text-red-400">
                Failed to get answer
              </p>
              <p className="text-xs text-red-600 dark:text-red-500 mt-1">
                {streamError || 'Unknown error'}
              </p>
            </div>
          </div>
        )}

        {/* Completed answer */}
        {hasResult && (
          <div className="space-y-4">
            {/* Ultrathink: Thinking process (collapsible) */}
            {isUltrathink && streamThinking && (
              <div className="bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-900 rounded-lg">
                <button
                  onClick={() => setShowThinking(!showThinking)}
                  className="flex items-center gap-2 w-full px-4 py-3 text-left"
                >
                  {showThinking ? <ChevronDown className="h-4 w-4 text-purple-500" /> : <ChevronRight className="h-4 w-4 text-purple-500" />}
                  <Brain className="h-4 w-4 text-purple-500" />
                  <span className="text-xs font-medium text-purple-700 dark:text-purple-300">
                    Reasoning ({streamRounds} round{streamRounds !== 1 ? 's' : ''})
                  </span>
                </button>
                {showThinking && (
                  <div className="px-4 pb-3">
                    <pre className="text-xs text-purple-800 dark:text-purple-200 whitespace-pre-wrap leading-relaxed max-h-60 overflow-auto">
                      {streamThinking}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Ultrathink: Tool call chain (collapsible) */}
            {isUltrathink && streamToolCalls.length > 0 && (
              <div className="bg-card border border-border rounded-lg">
                <button
                  onClick={() => setShowToolCalls(!showToolCalls)}
                  className="flex items-center gap-2 w-full px-4 py-3 text-left"
                >
                  {showToolCalls ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  <span className="text-xs font-medium text-muted-foreground">
                    Research chain ({streamToolCalls.length} tool call{streamToolCalls.length !== 1 ? 's' : ''})
                  </span>
                </button>
                {showToolCalls && (
                  <div className="px-4 pb-3 space-y-1.5">
                    {streamToolCalls.map((tc, i) => (
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
                {streamConfidence > 0 && (() => {
                  const c = confidenceLabel(streamConfidence);
                  return (
                    <span className={cn('ml-auto text-xs font-mono', c.cls)}>
                      {c.text} — {Math.round(streamConfidence * 100)}%
                    </span>
                  );
                })()}
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {streamAnswer}
              </div>
              {streamModel && (
                <p className="mt-3 text-xs text-muted-foreground">
                  {streamModel}
                  {(streamTokens.input + streamTokens.output > 0) && (
                    <> &middot; {streamTokens.input + streamTokens.output} tokens</>
                  )}
                  {isUltrathink && ` · ${streamRounds} round${streamRounds !== 1 ? 's' : ''}`}
                </p>
              )}
            </div>

            {/* Sources */}
            {streamSources.length > 0 && (
              <div>
                <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Sources ({streamSources.length})
                </h3>
                <div className="space-y-2">
                  {streamSources.map((source) => (
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
        {streamPhase === 'idle' && (
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
                    handleAsk(q, exMode);
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
