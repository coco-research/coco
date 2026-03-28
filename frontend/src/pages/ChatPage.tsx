import { useState, useRef, useEffect, useCallback } from 'react';
import { MessageSquare, Sparkles, Clock, AlertTriangle, PanelLeftClose, PanelLeft, Trash2, ChevronDown } from 'lucide-react';
import { MessageBubble, type ChatMessage } from '../components/chat/MessageBubble';
import { ChatInput } from '../components/chat/ChatInput';
import { ChatHistory } from '../components/chat/ChatHistory';
import { apiFetch, apiDelete } from '../lib/api';
import { cn } from '../lib/utils';

type Model = 'sonnet' | 'opus' | 'haiku';

const MODEL_LABELS: Record<Model, string> = {
  sonnet: 'Sonnet',
  opus: 'Opus',
  haiku: 'Haiku',
};

const SUGGESTED_PROMPTS = [
  { label: "What's new?", icon: Sparkles },
  { label: 'Catch me up', icon: Clock },
  { label: 'Show me overdue items', icon: AlertTriangle },
];

/**
 * Parse SSE text chunk into individual data payloads.
 * Handles partial lines across chunks by returning any leftover incomplete line.
 */
function parseSSEChunk(text: string, buffer: string): { events: string[]; remaining: string } {
  const raw = buffer + text;
  const lines = raw.split('\n');
  // Last element may be an incomplete line -- hold it for the next chunk
  const remaining = lines.pop() ?? '';
  const events: string[] = [];
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      events.push(line.slice(6));
    }
  }
  return { events, remaining };
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [model, setModel] = useState<Model>('sonnet');
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>();
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Auto-scroll to bottom on new messages or streaming content
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, streamingContent]);

  // Close model menu on outside click
  useEffect(() => {
    if (!modelMenuOpen) return;
    const handler = () => setModelMenuOpen(false);
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, [modelMenuOpen]);

  // Load messages when a session is selected
  const loadSessionMessages = useCallback(async (sessionId: string) => {
    try {
      const data = await apiFetch<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`);
      setMessages(data);
    } catch {
      setMessages([]);
    }
  }, []);

  const handleSelectSession = useCallback(
    (id: string) => {
      setActiveSessionId(id);
      loadSessionMessages(id);
    },
    [loadSessionMessages],
  );

  const handleSend = useCallback(
    async (content: string, contentIds?: string[]) => {
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);
      setStreamingContent('');

      const controller = new AbortController();
      abortRef.current = controller;

      // Use the current session_id, or let the backend create one
      const sessionIdForRequest = activeSessionId;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: content,
            model,
            session_id: sessionIdForRequest || null,
            ...(contentIds && contentIds.length > 0 ? { content_ids: contentIds } : {}),
          }),
          signal: controller.signal,
        });

        if (!res.ok) {
          const errText = await res.text().catch(() => 'Unknown error');
          throw new Error(errText);
        }

        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let assistantContent = '';
        let sseBuffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value, { stream: true });
          const { events, remaining } = parseSSEChunk(text, sseBuffer);
          sseBuffer = remaining;

          for (const eventData of events) {
            if (eventData === '[DONE]') continue;
            try {
              const data = JSON.parse(eventData);

              // Capture session_id from the first "session" event
              if (data.type === 'session' && data.session_id) {
                if (!activeSessionId) {
                  setActiveSessionId(data.session_id);
                }
              } else if (data.type === 'token' && data.content) {
                assistantContent += data.content;
                setStreamingContent(assistantContent);
              } else if (data.type === 'error') {
                assistantContent += `\n\nError: ${data.message ?? 'Unknown streaming error'}`;
                setStreamingContent(assistantContent);
              }
              // 'done' type -- streaming complete, handled by loop exit
            } catch {
              // Skip unparseable SSE events
            }
          }
        }

        // Finalize the assistant message
        const finalContent = assistantContent || 'No response received.';
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: finalContent,
          model,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);

        // Refresh sidebar to show updated session list
        setSidebarRefreshKey((k) => k + 1);
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        const errorMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : 'Unknown error'}`,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsStreaming(false);
        setStreamingContent('');
        abortRef.current = null;
      }
    },
    [model, activeSessionId],
  );

  const handleDeleteCurrentSession = useCallback(async () => {
    if (!activeSessionId) return;
    try {
      await apiDelete(`/chat/sessions/${activeSessionId}`);
    } catch {
      // clear locally anyway
    }
    setMessages([]);
    setStreamingContent('');
    setActiveSessionId(undefined);
    setSidebarRefreshKey((k) => k + 1);
  }, [activeSessionId]);

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setStreamingContent('');
    setActiveSessionId(undefined);
  }, []);

  const isEmpty = messages.length === 0 && !isStreaming;

  return (
    <div className="flex h-[calc(100vh-3rem)] -m-6">
      {/* Sidebar */}
      <ChatHistory
        activeId={activeSessionId}
        onSelect={handleSelectSession}
        onNew={handleNewChat}
        collapsed={!sidebarOpen}
        refreshKey={sidebarRefreshKey}
      />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header bar */}
        <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-card">
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className="p-1.5 rounded-lg hover:bg-accent/50 text-muted-foreground transition-colors"
          >
            {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeft size={18} />}
          </button>
          <div className="w-6 h-6 rounded-full bg-accent flex items-center justify-center">
            <span className="text-[10px] font-bold text-accent-foreground">C</span>
          </div>
          <span className="text-sm font-medium text-foreground">CoCo</span>

          {/* Model selector */}
          <div className="relative ml-auto">
            <button
              onClick={(e) => { e.stopPropagation(); setModelMenuOpen((o) => !o); }}
              className={cn(
                'flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium',
                'border border-border text-muted-foreground hover:bg-accent/50 transition-colors',
              )}
            >
              {MODEL_LABELS[model]}
              <ChevronDown size={12} />
            </button>
            {modelMenuOpen && (
              <div className="absolute right-0 top-full mt-1 bg-card border border-border rounded-lg shadow-lg z-10 py-1 min-w-[100px]">
                {(Object.keys(MODEL_LABELS) as Model[]).map((m) => (
                  <button
                    key={m}
                    onClick={() => { setModel(m); setModelMenuOpen(false); }}
                    className={cn(
                      'w-full text-left px-3 py-1.5 text-xs hover:bg-accent/50 transition-colors',
                      m === model ? 'text-accent font-medium' : 'text-muted-foreground',
                    )}
                  >
                    {MODEL_LABELS[m]}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Delete current session button */}
          {messages.length > 0 && activeSessionId && (
            <button
              onClick={handleDeleteCurrentSession}
              disabled={isStreaming}
              className={cn(
                'p-1.5 rounded-lg text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors',
                'disabled:opacity-40 disabled:cursor-not-allowed',
              )}
              title="Delete this session"
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>

        {/* Messages area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-background">
          {isEmpty ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-14 h-14 rounded-full bg-accent/20 flex items-center justify-center mb-4">
                <MessageSquare size={28} className="text-accent" />
              </div>
              <h2 className="text-lg font-medium text-foreground mb-1">Start a conversation</h2>
              <p className="text-sm text-muted-foreground mb-6">I'm CoCo.</p>

              <div className="flex flex-wrap gap-2 justify-center">
                {SUGGESTED_PROMPTS.map(({ label, icon: Icon }) => (
                  <button
                    key={label}
                    onClick={() => handleSend(label)}
                    disabled={isStreaming}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2 rounded-xl',
                      'border border-border bg-card text-sm text-muted-foreground',
                      'hover:bg-accent/50 hover:text-foreground transition-all shadow-sm',
                      'disabled:opacity-50',
                    )}
                  >
                    <Icon size={14} />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}

              {/* Streaming assistant message */}
              {isStreaming && streamingContent && (
                <MessageBubble
                  message={{
                    id: '__streaming__',
                    role: 'assistant',
                    content: streamingContent,
                    model,
                    created_at: new Date().toISOString(),
                  }}
                  isStreaming
                />
              )}

              {/* Typing indicator when streaming hasn't produced content yet */}
              {isStreaming && !streamingContent && (
                <div className="flex gap-3 justify-start">
                  <div className="flex-shrink-0 w-7 h-7 rounded-full bg-accent flex items-center justify-center mt-1">
                    <span className="text-xs font-bold text-accent-foreground">C</span>
                  </div>
                  <div className="bg-card border border-border rounded-2xl rounded-bl-sm px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:0ms]" />
                      <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:150ms]" />
                      <span className="w-2 h-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:300ms]" />
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Input area */}
        <ChatInput onSend={handleSend} disabled={isStreaming} streaming={isStreaming} />
      </div>
    </div>
  );
}
