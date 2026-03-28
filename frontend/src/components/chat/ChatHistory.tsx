import { useState, useEffect, useCallback } from 'react';
import { MessageSquarePlus, MessageSquare, X, Loader2 } from 'lucide-react';
import { apiFetch, apiPost, apiDelete } from '../../lib/api';
import { cn } from '../../lib/utils';

export interface ChatSession {
  id: string;
  title: string | null;
  model: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

interface ChatHistoryProps {
  activeId?: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  collapsed?: boolean;
  refreshKey?: number; // bump to trigger a refetch
}

/** Format a date string into a relative group label. */
function dateLabel(isoStr: string): string {
  const d = new Date(isoStr + (isoStr.endsWith('Z') ? '' : 'Z'));
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/** Format time ago from ISO string. */
function timeAgo(isoStr: string): string {
  const d = new Date(isoStr + (isoStr.endsWith('Z') ? '' : 'Z'));
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const mins = Math.floor(diffMs / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

/** Group sessions by date label. */
function groupByDate(sessions: ChatSession[]): Record<string, ChatSession[]> {
  const groups: Record<string, ChatSession[]> = {};
  for (const s of sessions) {
    const label = dateLabel(s.updated_at);
    (groups[label] ??= []).push(s);
  }
  return groups;
}

export function ChatHistory({ activeId, onSelect, onNew, collapsed = false, refreshKey = 0 }: ChatHistoryProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    try {
      const data = await apiFetch<ChatSession[]>('/chat/sessions');
      setSessions(data);
    } catch {
      // API may not be available yet
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions, refreshKey]);

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    try {
      await apiDelete(`/chat/sessions/${sessionId}`);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeId === sessionId) {
        onNew();
      }
    } catch {
      // ignore
    }
  };

  if (collapsed) return null;

  const groups = groupByDate(sessions);

  return (
    <aside className="w-64 flex-shrink-0 border-r border-border bg-card flex flex-col h-full">
      {/* New chat button */}
      <div className="p-3 border-b border-border">
        <button
          onClick={onNew}
          className={cn(
            'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm',
            'bg-card border border-border text-foreground hover:bg-accent/50 transition-all',
          )}
        >
          <MessageSquarePlus size={16} />
          New Chat
        </button>
      </div>

      {/* Sessions list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-3">
        {loading && (
          <div className="flex justify-center py-6">
            <Loader2 size={18} className="animate-spin text-muted-foreground" />
          </div>
        )}
        {!loading && sessions.length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-6">No conversations yet</p>
        )}
        {!loading &&
          Object.entries(groups).map(([date, items]) => (
            <div key={date}>
              <p className="text-xs text-muted-foreground font-medium px-2 mb-1">{date}</p>
              <div className="space-y-0.5">
                {items.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => onSelect(s.id)}
                    onMouseEnter={() => setHoveredId(s.id)}
                    onMouseLeave={() => setHoveredId(null)}
                    className={cn(
                      'w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm group',
                      'hover:bg-accent/50 transition-colors',
                      s.id === activeId ? 'bg-accent/20 text-accent' : 'text-muted-foreground',
                    )}
                  >
                    <MessageSquare size={14} className="flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="truncate block">{s.title || 'New Chat'}</span>
                      <span className="text-[10px] text-muted-foreground/60">
                        {s.message_count} msg{s.message_count !== 1 ? 's' : ''} &middot; {timeAgo(s.updated_at)}
                      </span>
                    </div>
                    {hoveredId === s.id && (
                      <button
                        onClick={(e) => handleDelete(e, s.id)}
                        className="flex-shrink-0 p-0.5 rounded hover:bg-destructive/20 hover:text-destructive transition-colors"
                        title="Delete session"
                      >
                        <X size={12} />
                      </button>
                    )}
                  </button>
                ))}
              </div>
            </div>
          ))}
      </div>
    </aside>
  );
}
