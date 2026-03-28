import { useState, useRef, useEffect, useCallback } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { useScope } from '../context/ScopeContext';
import { apiPost, apiFetch } from '../lib/api';
import {
  Inbox, AlertTriangle, FileCheck, FolderOpen, Activity, Check, X, Eye, EyeOff, ChevronRight, Clock, Mic
} from 'lucide-react';
import { cn } from '../lib/utils';
import { useInViewport } from '../hooks/useInViewport';
import { useToast } from '../components/shared/Toast';
import { useListNavigation } from '../hooks/useListNavigation';
import { VoiceDecisionCard, type VoiceDecisionItem } from '../components/inbox/VoiceDecisionCard';

type ReadState = 'unread' | 'seen' | 'dismissed';
type InboxTab = 'all' | 'urgent' | 'drafts' | 'classify' | 'health';

interface InboxItem {
  id: string;
  type: 'urgent' | 'draft_approval' | 'classify' | 'health' | 'overdue';
  title: string;
  subtitle: string;
  project?: string;
  source?: string;
  timeAgo: string;
  sourceId?: string;
}

interface Project {
  id: string;
  name: string;
}

const TAB_CONFIG: { key: InboxTab; label: string; icon: React.ElementType }[] = [
  { key: 'all', label: 'All', icon: Inbox },
  { key: 'urgent', label: 'Urgent', icon: AlertTriangle },
  { key: 'drafts', label: 'Drafts', icon: FileCheck },
  { key: 'classify', label: 'Classify', icon: FolderOpen },
  { key: 'health', label: 'Health', icon: Activity },
];

function typeIcon(type: InboxItem['type']) {
  switch (type) {
    case 'urgent': return <AlertTriangle size={14} className="text-destructive" />;
    case 'draft_approval': return <FileCheck size={14} className="text-info" />;
    case 'classify': return <FolderOpen size={14} className="text-warning" />;
    case 'health': return <Activity size={14} className="text-destructive" />;
    case 'overdue': return <Clock size={14} className="text-warning" />;
  }
}

function ProjectPicker({
  onSelect,
  onCancel,
}: {
  onSelect: (projectId: string) => void;
  onCancel: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiFetch<Project[]>('/projects'),
  });

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onCancel();
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [onCancel]);

  return (
    <div ref={ref} className="absolute right-0 top-full mt-1 z-50 bg-popover border border-border rounded-lg shadow-lg overflow-hidden animate-fade-in min-w-[180px]">
      <div className="max-h-[200px] overflow-y-auto py-1">
        {(!projects || projects.length === 0) ? (
          <p className="text-xs text-muted-foreground px-3 py-2">No projects found</p>
        ) : (
          projects.map((p) => (
            <button
              key={p.id}
              onClick={() => onSelect(p.id)}
              className="w-full text-left px-3 py-1.5 text-sm hover:bg-accent/50 transition-colors truncate"
            >
              {p.name}
            </button>
          ))
        )}
      </div>
    </div>
  );
}

function InboxItemRow({
  item,
  readState,
  onMarkSeen,
  onDismiss,
  onApprove,
  onReject,
  onClassify,
}: {
  item: InboxItem;
  readState: ReadState;
  onMarkSeen: (id: string) => void;
  onDismiss: (id: string) => void;
  onApprove: (sourceId: string) => void;
  onReject: (sourceId: string) => void;
  onClassify: (sourceId: string, projectId: string) => void;
}) {
  const [showPicker, setShowPicker] = useState(false);
  const [viewRef, hasBeenVisible] = useInViewport(2000);

  // Auto-transition: unread -> seen after 2s in viewport
  useEffect(() => {
    if (hasBeenVisible && readState === 'unread') {
      onMarkSeen(item.id);
    }
  }, [hasBeenVisible, readState, item.id, onMarkSeen]);

  const stateClassName = readState === 'unread'
    ? 'notif-unread'
    : readState === 'seen'
      ? 'notif-seen'
      : 'notif-dismissed';

  return (
    <div
      ref={viewRef}
      className={cn(
        'group flex items-center gap-3 px-4 py-3 hover:bg-accent/50 transition-all cursor-pointer relative',
        stateClassName,
      )}
    >
      {/* Unread indicator dot */}
      <div className="shrink-0 relative">
        {typeIcon(item.type)}
        {readState === 'unread' && (
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-primary rounded-full animate-pulse-dot" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className={cn(
          'text-sm truncate transition-all duration-300',
          readState === 'unread' ? 'font-medium text-foreground' : 'font-normal text-muted-foreground',
        )}>
          {item.title}
        </p>
        <p className="text-xs text-muted-foreground truncate">{item.subtitle}</p>
      </div>
      {item.project && (
        <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded shrink-0">
          {item.project}
        </span>
      )}
      <span className="text-[10px] text-muted-foreground shrink-0 tabular-nums">{item.timeAgo}</span>
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
        {item.type === 'draft_approval' && item.sourceId && (
          <>
            <button
              className="p-1 rounded hover:bg-success/20 text-success"
              title="Approve"
              onClick={() => onApprove(item.sourceId!)}
            >
              <Check size={14} />
            </button>
            <button
              className="p-1 rounded hover:bg-destructive/20 text-destructive"
              title="Reject"
              onClick={() => onReject(item.sourceId!)}
            >
              <X size={14} />
            </button>
            <button className="p-1 rounded hover:bg-accent text-muted-foreground" title="Preview">
              <Eye size={14} />
            </button>
          </>
        )}
        {item.type === 'classify' && item.sourceId && (
          <div className="relative">
            <button
              className="p-1 rounded hover:bg-accent text-muted-foreground"
              title="Assign project"
              onClick={() => setShowPicker(!showPicker)}
            >
              <ChevronRight size={14} />
            </button>
            {showPicker && (
              <ProjectPicker
                onSelect={(projectId) => {
                  onClassify(item.sourceId!, projectId);
                  setShowPicker(false);
                }}
                onCancel={() => setShowPicker(false)}
              />
            )}
          </div>
        )}
        {(item.type === 'urgent' || item.type === 'overdue' || item.type === 'health') && readState !== 'dismissed' && (
          <button
            className="p-1 rounded hover:bg-accent text-muted-foreground"
            title="Dismiss"
            onClick={() => onDismiss(item.id)}
          >
            <X size={14} />
          </button>
        )}
      </div>
    </div>
  );
}

export default function InboxPage() {
  const [activeTab, setActiveTab] = useState<InboxTab>('all');
  const { selectedNodeId, scopeProjectIds } = useScope();
  const [readStates, setReadStates] = useState<Record<string, ReadState>>({});
  const [showDismissed, setShowDismissed] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const [voiceItem, setVoiceItem] = useState<VoiceDecisionItem | null>(null);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // ─── Helpers for read state ──────────────────────────────────────

  const getReadState = useCallback(
    (id: string): ReadState => readStates[id] ?? 'unread',
    [readStates],
  );

  const handleMarkSeen = useCallback((id: string) => {
    setReadStates((prev) => {
      if (prev[id] === 'seen' || prev[id] === 'dismissed') return prev;
      return { ...prev, [id]: 'seen' };
    });
  }, []);

  const handleDismiss = useCallback((id: string) => {
    setReadStates((prev) => ({ ...prev, [id]: 'dismissed' }));
  }, []);

  // ─── Queries ──────────────────────────────────────────────────────

  const { data: queueData } = useQuery({
    queryKey: ['queue'],
    queryFn: async () => {
      const res = await fetch('/api/queue');
      if (!res.ok) return { items: [] };
      return res.json();
    },
    staleTime: 10_000,
  });

  const { data: draftsData } = useQuery({
    queryKey: ['drafts', selectedNodeId, scopeProjectIds],
    queryFn: async () => {
      const url = scopeProjectIds.length === 1
        ? `/api/drafts?project_id=${scopeProjectIds[0]}`
        : scopeProjectIds.length > 1
          ? `/api/drafts?project_ids=${scopeProjectIds.join(',')}`
          : '/api/drafts';
      const res = await fetch(url);
      if (!res.ok) return [];
      return res.json();
    },
    staleTime: 10_000,
  });

  const { data: healthData } = useQuery({
    queryKey: ['dashboard-health'],
    queryFn: async () => {
      const res = await fetch('/api/dashboard');
      if (!res.ok) return [];
      const data = await res.json();
      return data.health ?? [];
    },
    staleTime: 30_000,
  });

  const { data: unsortedData } = useQuery({
    queryKey: ['content-unsorted'],
    queryFn: async () => {
      const res = await fetch('/api/content?status=unsorted&limit=20');
      if (!res.ok) return { items: [] };
      return res.json();
    },
    staleTime: 10_000,
  });

  const { data: todosData } = useQuery({
    queryKey: ['todos-overdue'],
    queryFn: async () => {
      const res = await fetch('/api/todos?status=open&limit=100');
      if (!res.ok) return [];
      return res.json();
    },
    staleTime: 30_000,
  });

  // ─── Mutations ────────────────────────────────────────────────────

  const approveMut = useMutation({
    mutationFn: (draftId: string) => apiPost<unknown>(`/drafts/${draftId}/approve`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      toast('Draft approved', 'success');
    },
    onError: () => {
      toast('Failed to approve draft', 'error');
    },
  });

  const rejectMut = useMutation({
    mutationFn: (draftId: string) => apiPost<unknown>(`/drafts/${draftId}/reject`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] });
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      toast('Draft rejected', 'info');
    },
    onError: () => {
      toast('Failed to reject draft', 'error');
    },
  });

  const classifyMut = useMutation({
    mutationFn: ({ contentId, projectId }: { contentId: string; projectId: string }) =>
      apiPost<unknown>(`/content/${contentId}/classify`, { project_id: projectId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content-unsorted'] });
      queryClient.invalidateQueries({ queryKey: ['queue'] });
      toast('Content classified', 'success');
    },
    onError: () => {
      toast('Failed to classify content', 'error');
    },
  });

  // ─── Build unified inbox items ────────────────────────────────────

  const items: InboxItem[] = [];

  // Queue items (urgent + other queue entries)
  if (queueData?.items && Array.isArray(queueData.items)) {
    for (const qi of queueData.items) {
      items.push({
        id: `queue-${qi.id}`,
        type: qi.type ?? (qi.priority <= 1 ? 'urgent' : 'classify'),
        title: qi.summary ?? qi.title ?? 'Queue item',
        subtitle: qi.project ?? qi.source ?? '',
        project: qi.project,
        source: qi.source,
        timeAgo: qi.created_at ? new Date(qi.created_at).toLocaleDateString() : '',
        sourceId: qi.source_id ?? qi.id,
      });
    }
  }

  // Drafts
  if (Array.isArray(draftsData)) {
    draftsData.forEach((d: Record<string, string>) => {
      items.push({
        id: `draft-${d.id}`,
        type: 'draft_approval',
        title: `${d.template ?? 'Draft'} → ${d.section ?? 'update'}`,
        subtitle: `From: ${d.source ?? 'content'}`,
        project: d.project,
        timeAgo: d.created_at ? new Date(d.created_at).toLocaleDateString() : '',
        sourceId: d.id,
      });
    });
  }

  // Unsorted content for Classify tab
  if (unsortedData?.items && Array.isArray(unsortedData.items)) {
    for (const c of unsortedData.items) {
      const dupeId = `classify-${c.id}`;
      if (!items.some((i) => i.sourceId === c.id && i.type === 'classify')) {
        items.push({
          id: dupeId,
          type: 'classify',
          title: c.title ?? c.summary ?? 'Unsorted content',
          subtitle: `Source: ${c.source ?? 'unknown'}`,
          project: c.project_id,
          source: c.source,
          timeAgo: c.created_at ? new Date(c.created_at).toLocaleDateString() : '',
          sourceId: c.id,
        });
      }
    }
  }

  // Overdue todos
  if (Array.isArray(todosData)) {
    const today = new Date().toISOString().slice(0, 10);
    todosData
      .filter((t: Record<string, string>) => t.due_date && t.due_date < today)
      .forEach((t: Record<string, string>) => {
        items.push({
          id: `overdue-${t.id}`,
          type: 'overdue',
          title: t.title ?? 'Overdue todo',
          subtitle: `Due: ${t.due_date}${t.project_id ? ` · ${t.project_id}` : ''}`,
          project: t.project_id,
          timeAgo: t.due_date ? new Date(t.due_date).toLocaleDateString() : '',
          sourceId: t.id,
        });
      });
  }

  // Health alerts
  if (Array.isArray(healthData)) {
    healthData
      .filter((h: Record<string, string>) => h.status === 'red')
      .forEach((h: Record<string, string>) => {
        items.push({
          id: `health-${h.source}`,
          type: 'health',
          title: `${h.source} adapter is down`,
          subtitle: h.message ?? 'Not synced',
          timeAgo: h.last_sync ? new Date(h.last_sync).toLocaleDateString() : 'never',
        });
      });
  }

  // ─── Deduplicate by sourceId ───────────────────────────────────────

  const seen = new Set<string>();
  const dedupedItems = items.filter(item => {
    const key = item.sourceId ?? item.id;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  // ─── Filtering ────────────────────────────────────────────────────

  const filteredItems = dedupedItems
    .filter(i => showDismissed || getReadState(i.id) !== 'dismissed')
    .filter(i => activeTab === 'all' || i.type === activeTab || (activeTab === 'urgent' && i.type === 'overdue'));

  const handleApprove = useCallback((sourceId: string) => {
    approveMut.mutate(sourceId);
    handleDismiss(`draft-${sourceId}`);
  }, [approveMut, handleDismiss]);

  const handleReject = useCallback((sourceId: string) => {
    rejectMut.mutate(sourceId);
    handleDismiss(`draft-${sourceId}`);
  }, [rejectMut, handleDismiss]);

  const handleClassify = useCallback((sourceId: string, projectId: string) => {
    classifyMut.mutate({ contentId: sourceId, projectId });
    handleDismiss(`classify-${sourceId}`);
  }, [classifyMut, handleDismiss]);

  // j/k keyboard navigation
  const { selectedIndex, containerRef } = useListNavigation(filteredItems, {
    onAction: (key, item) => {
      if (key === 'approve' && item.type === 'draft_approval' && item.sourceId) {
        handleApprove(item.sourceId);
      } else if (key === 'dismiss') {
        handleDismiss(item.id);
      }
    },
  });

  // Counts exclude dismissed items
  const activeDedupedItems = dedupedItems.filter(i => getReadState(i.id) !== 'dismissed');
  const dismissedCount = dedupedItems.filter(i => getReadState(i.id) === 'dismissed').length;
  const unreadCount = dedupedItems.filter(i => getReadState(i.id) === 'unread').length;

  const counts: Record<InboxTab, number> = {
    all: activeDedupedItems.length,
    urgent: activeDedupedItems.filter(i => i.type === 'urgent' || i.type === 'overdue').length,
    drafts: activeDedupedItems.filter(i => i.type === 'draft_approval').length,
    classify: activeDedupedItems.filter(i => i.type === 'classify').length,
    health: activeDedupedItems.filter(i => i.type === 'health').length,
  };

  // ─── Voice mode helpers ──────────────────────────────────────────

  const fetchVoiceItem = useCallback(async (command: string) => {
    setVoiceLoading(true);
    try {
      const res = await apiPost<{ card?: VoiceDecisionItem; message?: string }>(
        '/jarvis/command',
        { text: command },
      );
      setVoiceItem(res.card ?? null);
      if (res.message) toast(res.message, 'info');
    } catch {
      setVoiceItem(null);
    } finally {
      setVoiceLoading(false);
    }
  }, [toast]);

  // Auto-fetch first item when entering voice mode
  useEffect(() => {
    if (voiceMode) {
      fetchVoiceItem('next decision');
    } else {
      setVoiceItem(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voiceMode]);

  const handleVoiceApprove = useCallback(() => {
    fetchVoiceItem('approve');
    queryClient.invalidateQueries({ queryKey: ['drafts'] });
    queryClient.invalidateQueries({ queryKey: ['queue'] });
  }, [fetchVoiceItem, queryClient]);

  const handleVoiceReject = useCallback(() => {
    fetchVoiceItem('reject');
    queryClient.invalidateQueries({ queryKey: ['drafts'] });
    queryClient.invalidateQueries({ queryKey: ['queue'] });
  }, [fetchVoiceItem, queryClient]);

  const handleVoiceDefer = useCallback(() => {
    fetchVoiceItem('defer');
  }, [fetchVoiceItem]);

  const handleVoiceNext = useCallback(() => {
    fetchVoiceItem('next decision');
  }, [fetchVoiceItem]);

  return (
    <div className="space-y-4">
      {/* Header row with tabs + controls */}
      <div className="flex items-center justify-between border-b border-border">
        <div className="flex items-center gap-1">
          {TAB_CONFIG.map(({ key, label, icon: TabIcon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-2 text-sm border-b-2 transition-colors',
                activeTab === key
                  ? 'border-primary text-foreground font-medium'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              )}
            >
              <TabIcon size={14} />
              {label}
              {counts[key] > 0 && (
                <span className={cn(
                  'text-[10px] px-1.5 py-0.5 rounded-full min-w-[18px] text-center',
                  key === 'urgent' || key === 'health'
                    ? 'bg-destructive/10 text-destructive'
                    : 'bg-muted text-muted-foreground'
                )}>
                  {counts[key]}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Right-side controls */}
        <div className="flex items-center gap-3 pb-2">
          <button
            onClick={() => setVoiceMode(v => !v)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              voiceMode
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground hover:bg-accent/10',
            )}
          >
            <Mic size={14} />
            Voice
          </button>
          {unreadCount > 0 && (
            <span className="text-xs text-muted-foreground">
              {unreadCount} unread
            </span>
          )}
          {dismissedCount > 0 && (
            <button
              onClick={() => setShowDismissed(!showDismissed)}
              className={cn(
                'flex items-center gap-1 text-xs px-2 py-1 rounded-md transition-colors',
                showDismissed
                  ? 'bg-accent/50 text-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent/30',
              )}
              title={showDismissed ? 'Hide dismissed' : 'Show dismissed'}
            >
              {showDismissed ? <EyeOff size={12} /> : <Eye size={12} />}
              {dismissedCount} dismissed
            </button>
          )}
        </div>
      </div>

      {/* Voice mode: show large-format decision card */}
      {voiceMode ? (
        <div className="py-4">
          {voiceLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <VoiceDecisionCard
              item={voiceItem}
              onApprove={handleVoiceApprove}
              onReject={handleVoiceReject}
              onDefer={handleVoiceDefer}
              onNext={handleVoiceNext}
              isListening={voiceMode}
            />
          )}
        </div>
      ) : (
        <>
          {/* Items — click container to enable j/k navigation */}
          {filteredItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <Inbox size={40} className="mb-3 opacity-30" />
              <p className="text-sm font-medium">Inbox zero</p>
              <p className="text-xs mt-1">Nothing needs your attention right now.</p>
            </div>
          ) : (
            <div
              ref={containerRef}
              tabIndex={0}
              className="border border-border rounded-xl divide-y divide-border overflow-hidden outline-none"
            >
              {filteredItems.map((item, idx) => (
                <div
                  key={item.id}
                  data-list-index={idx}
                  className={cn(idx === selectedIndex && 'list-nav-selected')}
                >
                  <InboxItemRow
                    item={item}
                    readState={getReadState(item.id)}
                    onMarkSeen={handleMarkSeen}
                    onDismiss={handleDismiss}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    onClassify={handleClassify}
                  />
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
