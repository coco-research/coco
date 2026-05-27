import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Skeleton } from 'boneyard-js/react';
import { useScope } from '../context/ScopeContext';
import { apiPost, apiFetch, apiPatch } from '../lib/api';
import {
  Inbox, AlertTriangle, FileCheck, FolderOpen, Activity, Check, X, Eye, EyeOff, ChevronRight, Clock, Mic,
  CheckSquare, Square, MinusSquare, Bot, ChevronDown as ChevronDownIcon, Lightbulb, Sparkles, Zap,
} from 'lucide-react';
import { ActionReviewPanel } from '../components/knowledge/ActionReviewPanel';
import { cn } from '../lib/utils';
import { useInViewport } from '../hooks/useInViewport';
import { useToast } from '../components/shared/Toast';
import { useListNavigation } from '../hooks/useListNavigation';
import { VoiceDecisionCard, type VoiceDecisionItem } from '../components/inbox/VoiceDecisionCard';
import { ErrorState } from '../components/shared/ErrorState';

type ReadState = 'unread' | 'seen' | 'dismissed';
type InboxTab = 'all' | 'urgent' | 'drafts' | 'classify' | 'suggestions' | 'health' | 'auto_handled' | 'actions';

interface SuggestionItem {
  id: string;
  hub_content_id: string;
  title: string;
  body?: string;
  source?: string;
  classified_project_id?: string;
  suggested_project_id?: string;
  suggested_project_name?: string;
  confidence: number;
  reasoning?: string;
  content_created_at?: string;
}

interface AutoHandledItem {
  id: string;
  action: string;
  summary: string;
  project?: string;
  confidence?: number;
  timestamp?: string;
}

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
  { key: 'suggestions', label: 'Suggestions', icon: Lightbulb },
  { key: 'health', label: 'Health', icon: Activity },
  { key: 'auto_handled', label: 'Auto-handled', icon: Bot },
  { key: 'actions', label: 'Actions', icon: Zap },
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
  selected,
  selectMode,
  onToggleSelect,
  onMarkSeen,
  onDismiss,
  onApprove,
  onReject,
  onClassify,
}: {
  item: InboxItem;
  readState: ReadState;
  selected: boolean;
  selectMode: boolean;
  onToggleSelect: (id: string) => void;
  onMarkSeen: (id: string) => void;
  onDismiss: (id: string) => void;
  onApprove: (sourceId: string) => void;
  onReject: (sourceId: string) => void;
  onClassify: (sourceId: string, projectId: string) => void;
}) {
  const [showPicker, setShowPicker] = useState(false);
  const [viewRef, hasBeenVisible] = useInViewport(2000);
  const markedSeenRef = useRef(false);

  // Auto-transition: unread -> seen after 2s in viewport
  // Use ref to prevent re-firing (onMarkSeen identity changes each render)
  useEffect(() => {
    if (hasBeenVisible && readState === 'unread' && !markedSeenRef.current) {
      markedSeenRef.current = true;
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
        selected && 'bg-primary/5 ring-1 ring-primary/20',
      )}
    >
      {/* Checkbox for multi-select */}
      {selectMode && (
        <button
          className="shrink-0 text-muted-foreground hover:text-foreground transition-colors"
          onClick={(e) => { e.stopPropagation(); onToggleSelect(item.id); }}
        >
          {selected ? <CheckSquare size={16} className="text-primary" /> : <Square size={16} />}
        </button>
      )}
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
  const [showDismissed, setShowDismissed] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const [voiceItem, setVoiceItem] = useState<VoiceDecisionItem | null>(null);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectMode, setSelectMode] = useState(false);
  const [batchProjectPicker, setBatchProjectPicker] = useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // ─── Server-persisted read states ────────────────────────────────

  const { data: serverReadStates, isLoading: isLoadingReadStates, isError: readStatesError, error: readStatesErr, refetch: refetchReadStates } = useQuery({
    queryKey: ['inbox-read-states'],
    queryFn: () => apiFetch<Record<string, ReadState>>('/inbox/read-states'),
    staleTime: 5_000,
  });

  const readStates: Record<string, ReadState> = serverReadStates ?? {};

  const getReadState = useCallback(
    (id: string): ReadState => readStates[id] ?? 'unread',
    [readStates],
  );

  // Debounce ref: avoid immediate refetch after optimistic update (would cause flicker
  // if the server hasn't committed the dismiss yet and returns the old state).
  const refetchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scheduleReadStatesRefetch = useCallback(() => {
    if (refetchTimerRef.current) clearTimeout(refetchTimerRef.current);
    refetchTimerRef.current = setTimeout(() => {
      refetchTimerRef.current = null;
      refetchReadStates();
    }, 500);
  }, [refetchReadStates]);

  // Mutation: patch a single read state with optimistic cache update.
  // We write directly to the ['inbox-read-states'] cache on mutate, so the row
  // disappears immediately. On error we roll back. We do NOT refetch immediately
  // on success — debounced 500ms — to avoid the brief "row reappears" flicker
  // when the server hasn't yet propagated the change.
  const patchReadStateMut = useMutation({
    mutationFn: ({ item_key, read_state }: { item_key: string; read_state: ReadState }) =>
      apiPatch<unknown>('/inbox/read-state', { item_key, read_state }),
    onMutate: async ({ item_key, read_state }) => {
      await queryClient.cancelQueries({ queryKey: ['inbox-read-states'] });
      const previous = queryClient.getQueryData<Record<string, ReadState>>(['inbox-read-states']);
      queryClient.setQueryData<Record<string, ReadState>>(['inbox-read-states'], (old) => ({
        ...(old ?? {}),
        [item_key]: read_state,
      }));
      return { previous };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.previous) {
        queryClient.setQueryData(['inbox-read-states'], ctx.previous);
      }
    },
    onSettled: () => {
      scheduleReadStatesRefetch();
    },
  });

  // Mutation: batch patch read states with optimistic cache update.
  const batchReadStateMut = useMutation({
    mutationFn: ({ item_keys, read_state }: { item_keys: string[]; read_state: ReadState }) =>
      apiPatch<unknown>('/inbox/read-states/batch', { item_keys, read_state }),
    onMutate: async ({ item_keys, read_state }) => {
      await queryClient.cancelQueries({ queryKey: ['inbox-read-states'] });
      const previous = queryClient.getQueryData<Record<string, ReadState>>(['inbox-read-states']);
      queryClient.setQueryData<Record<string, ReadState>>(['inbox-read-states'], (old) => {
        const next = { ...(old ?? {}) };
        for (const key of item_keys) next[key] = read_state;
        return next;
      });
      return { previous };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.previous) {
        queryClient.setQueryData(['inbox-read-states'], ctx.previous);
      }
    },
    onSettled: () => {
      scheduleReadStatesRefetch();
    },
  });

  // Clean up pending refetch timer on unmount
  useEffect(() => () => {
    if (refetchTimerRef.current) clearTimeout(refetchTimerRef.current);
  }, []);

  // Debounced batch mark-as-seen: collect IDs, flush every 3s to avoid PATCH storm on scroll
  const seenQueueRef = useRef<Set<string>>(new Set());
  const seenTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const flushSeenQueue = useCallback(() => {
    const ids = Array.from(seenQueueRef.current);
    seenQueueRef.current.clear();
    seenTimerRef.current = null;
    if (ids.length > 0) {
      batchReadStateMut.mutate({ item_keys: ids, read_state: 'seen' });
    }
  }, [batchReadStateMut]);

  const handleMarkSeen = useCallback((id: string) => {
    seenQueueRef.current.add(id);
    if (!seenTimerRef.current) {
      seenTimerRef.current = setTimeout(flushSeenQueue, 3000);
    }
  }, [flushSeenQueue]);

  const handleDismiss = useCallback((id: string) => {
    patchReadStateMut.mutate({ item_key: id, read_state: 'dismissed' });
  }, [patchReadStateMut]);

  // ─── Queries ──────────────────────────────────────────────────────

  const { data: queueData } = useQuery({
    queryKey: ['queue'],
    queryFn: async () => {
      const res = await fetch('/api/queue');
      if (!res.ok) return { items: [] };
      return res.json();
    },
    staleTime: 60_000,
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
    staleTime: 60_000,
  });

  const { data: healthData } = useQuery({
    queryKey: ['dashboard-health'],
    queryFn: async () => {
      const res = await fetch('/api/dashboard');
      if (!res.ok) return [];
      const data = await res.json();
      return data.health ?? [];
    },
    staleTime: 60_000,
  });

  const { data: unsortedData } = useQuery({
    queryKey: ['content-unsorted'],
    queryFn: async () => {
      const res = await fetch('/api/content?status=unsorted&limit=20');
      if (!res.ok) return { items: [] };
      return res.json();
    },
    staleTime: 60_000,
  });

  // Suggestions from auto-classifier
  const { data: suggestionsData, refetch: refetchSuggestions } = useQuery({
    queryKey: ['content-suggestions'],
    queryFn: () => apiFetch<{ items: SuggestionItem[]; total: number }>('/content/suggestions'),
    staleTime: 60_000,
  });

  const suggestions: SuggestionItem[] = suggestionsData?.items ?? [];

  const acceptSuggestionMut = useMutation({
    mutationFn: ({ contentId, projectId }: { contentId: string; projectId?: string }) =>
      apiPost<unknown>(`/content/${contentId}/accept-suggestion`, projectId ? { project_id: projectId } : {}),
    onSuccess: () => {
      refetchSuggestions();
      queryClient.invalidateQueries({ queryKey: ['content-unsorted'] });
      toast('Suggestion accepted', 'success');
    },
    onError: () => toast('Failed to accept suggestion', 'error'),
  });

  const rejectSuggestionMut = useMutation({
    mutationFn: (contentId: string) =>
      apiPost<unknown>(`/content/${contentId}/reject-suggestion`, {}),
    onSuccess: () => {
      refetchSuggestions();
      toast('Suggestion rejected', 'info');
    },
    onError: () => toast('Failed to reject suggestion', 'error'),
  });

  const batchAcceptSuggestionsMut = useMutation({
    mutationFn: (minConfidence: number) =>
      apiPost<unknown>(`/content/batch-accept-suggestions?min_confidence=${minConfidence}`, {}),
    onSuccess: () => {
      refetchSuggestions();
      queryClient.invalidateQueries({ queryKey: ['content-unsorted'] });
      toast('High-confidence suggestions accepted', 'success');
    },
    onError: () => toast('Failed to batch accept', 'error'),
  });

  const { data: actionStats } = useQuery({
    queryKey: ['action-stats'],
    queryFn: () => apiFetch<{ staged: number; approved: number; rejected: number; total: number }>('/actions/stats'),
    staleTime: 15_000,
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
      // Humanize raw template summaries like "decision-log -> decisions"
      let title = qi.summary ?? qi.title ?? 'Queue item';
      if (title.includes(' -> ')) {
        const [tpl, sec] = title.split(' -> ');
        const humanTpl = tpl.replace(/[-_]/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
        const humanSec = sec.replace(/[-_]/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
        title = `${humanTpl} — ${humanSec}`;
      }
      items.push({
        id: `queue-${qi.id}`,
        type: qi.type ?? (qi.priority <= 1 ? 'urgent' : 'classify'),
        title,
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
      // Humanize template/section names: "meeting-notes" → "Meeting Notes"
      const tpl = (d.target_template ?? 'draft').replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      const sec = (d.target_section ?? '').replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      const preview = d.content ? d.content.replace(/[|\-#\[\]]/g, '').trim().slice(0, 80) : '';
      items.push({
        id: `draft-${d.id}`,
        type: 'draft_approval',
        title: sec ? `${tpl} — ${sec}` : tpl,
        subtitle: preview || `${d.project_id ?? 'Unknown project'}`,
        project: d.project_id,
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
    .filter(i => activeTab === 'all' || i.type === activeTab || (activeTab === 'urgent' && i.type === 'overdue') || (activeTab === 'drafts' && i.type === 'draft_approval'));

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

  // ─── Auto-handled items from queue data ────────────────────────────
  const autoHandledItems: AutoHandledItem[] = useMemo(() => {
    const raw = queueData?.auto_handled_since_last_session;
    if (!Array.isArray(raw)) return [];
    return raw.map((item: Record<string, unknown>, idx: number) => ({
      id: (item.id as string) ?? `auto-${idx}`,
      action: (item.action as string) ?? (item.status as string) ?? 'processed',
      summary: (item.summary as string) ?? (item.title as string) ?? 'Auto-handled item',
      project: item.project as string | undefined,
      confidence: item.confidence as number | undefined,
      timestamp: (item.timestamp as string | undefined) ?? (item.created_at as string | undefined),
    }));
  }, [queueData]);

  const [autoHandledExpanded, setAutoHandledExpanded] = useState(true);

  // Counts exclude dismissed items
  const activeDedupedItems = dedupedItems.filter(i => getReadState(i.id) !== 'dismissed');
  const dismissedCount = dedupedItems.filter(i => getReadState(i.id) === 'dismissed').length;
  const unreadCount = dedupedItems.filter(i => getReadState(i.id) === 'unread').length;

  const counts: Record<InboxTab, number> = {
    all: activeDedupedItems.length,
    urgent: activeDedupedItems.filter(i => i.type === 'urgent' || i.type === 'overdue').length,
    drafts: activeDedupedItems.filter(i => i.type === 'draft_approval').length,
    classify: activeDedupedItems.filter(i => i.type === 'classify').length,
    suggestions: suggestions.length,
    health: activeDedupedItems.filter(i => i.type === 'health').length,
    auto_handled: autoHandledItems.length,
    actions: actionStats?.staged ?? 0,
  };

  // ─── Multi-select helpers ─────────────────────────────────────────

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (selectedIds.size === filteredItems.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filteredItems.map(i => i.id)));
    }
  }, [filteredItems, selectedIds.size]);

  // Derive selected items
  const selectedItems = useMemo(
    () => filteredItems.filter(i => selectedIds.has(i.id)),
    [filteredItems, selectedIds],
  );

  const selectedDrafts = useMemo(
    () => selectedItems.filter(i => i.type === 'draft_approval' && i.sourceId),
    [selectedItems],
  );

  const selectedClassify = useMemo(
    () => selectedItems.filter(i => i.type === 'classify' && i.sourceId),
    [selectedItems],
  );

  // Exit select mode clears selection
  const exitSelectMode = useCallback(() => {
    setSelectMode(false);
    setSelectedIds(new Set());
    setBatchProjectPicker(false);
  }, []);

  // Select all checkbox state
  const selectAllState: 'none' | 'some' | 'all' =
    selectedIds.size === 0
      ? 'none'
      : selectedIds.size === filteredItems.length
        ? 'all'
        : 'some';

  // ─── Batch action handlers ────────────────────────────────────────

  const handleBatchApprove = useCallback(async () => {
    if (selectedDrafts.length === 0) return;
    let successCount = 0;
    for (const item of selectedDrafts) {
      try {
        await apiPost(`/drafts/${item.sourceId}/approve`, {});
        successCount++;
      } catch { /* skip failed */ }
    }
    // Dismiss all approved items
    const keys = selectedDrafts.map(i => i.id);
    batchReadStateMut.mutate({ item_keys: keys, read_state: 'dismissed' });
    queryClient.invalidateQueries({ queryKey: ['drafts'] });
    queryClient.invalidateQueries({ queryKey: ['queue'] });
    toast(`${successCount} draft${successCount !== 1 ? 's' : ''} approved`, 'success');
    exitSelectMode();
  }, [selectedDrafts, batchReadStateMut, queryClient, toast, exitSelectMode]);

  const handleBatchClassify = useCallback(async (projectId: string) => {
    if (selectedClassify.length === 0) return;
    let successCount = 0;
    for (const item of selectedClassify) {
      try {
        await apiPost(`/content/${item.sourceId}/classify`, { project_id: projectId });
        successCount++;
      } catch { /* skip failed */ }
    }
    const keys = selectedClassify.map(i => i.id);
    batchReadStateMut.mutate({ item_keys: keys, read_state: 'dismissed' });
    queryClient.invalidateQueries({ queryKey: ['content-unsorted'] });
    queryClient.invalidateQueries({ queryKey: ['queue'] });
    toast(`${successCount} item${successCount !== 1 ? 's' : ''} classified`, 'success');
    setBatchProjectPicker(false);
    exitSelectMode();
  }, [selectedClassify, batchReadStateMut, queryClient, toast, exitSelectMode]);

  const handleBatchDismiss = useCallback(() => {
    if (selectedItems.length === 0) return;
    const keys = selectedItems.map(i => i.id);
    batchReadStateMut.mutate({ item_keys: keys, read_state: 'dismissed' });
    toast(`${keys.length} item${keys.length !== 1 ? 's' : ''} dismissed`, 'info');
    exitSelectMode();
  }, [selectedItems, batchReadStateMut, toast, exitSelectMode]);

  const handleBatchMarkSeen = useCallback(() => {
    if (selectedItems.length === 0) return;
    const keys = selectedItems.map(i => i.id);
    batchReadStateMut.mutate({ item_keys: keys, read_state: 'seen' });
    toast(`${keys.length} item${keys.length !== 1 ? 's' : ''} marked seen`, 'info');
    exitSelectMode();
  }, [selectedItems, batchReadStateMut, toast, exitSelectMode]);

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
        <div className="flex items-center gap-1 overflow-x-auto scrollbar-none">
          {/* Select All checkbox in tab header */}
          {selectMode && (
            <button
              onClick={toggleSelectAll}
              className="flex items-center px-2 py-2 text-muted-foreground hover:text-foreground transition-colors"
              title={selectAllState === 'all' ? 'Deselect all' : 'Select all'}
            >
              {selectAllState === 'all' ? (
                <CheckSquare size={16} className="text-primary" />
              ) : selectAllState === 'some' ? (
                <MinusSquare size={16} className="text-primary" />
              ) : (
                <Square size={16} />
              )}
            </button>
          )}
          {TAB_CONFIG.map(({ key, label, icon: TabIcon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-2 text-sm border-b-2 transition-colors whitespace-nowrap',
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

        {/* Right-side controls — visually separated from filter tabs */}
        <div className="flex items-center gap-3 pb-2 pl-3 ml-3 border-l border-border shrink-0">
          <button
            onClick={() => selectMode ? exitSelectMode() : setSelectMode(true)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              selectMode
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-accent/10',
            )}
          >
            <CheckSquare size={14} />
            {selectMode ? 'Cancel' : 'Select'}
          </button>
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

      {/* Error state for failed initial fetch */}
      {readStatesError && !isLoadingReadStates && (
        <div className="py-6">
          <ErrorState
            error={readStatesErr}
            title="Couldn't load inbox"
            onRetry={() => void refetchReadStates()}
          />
        </div>
      )}

      {/* Skeleton loading state for initial data fetch */}
      <Skeleton name="inbox-list" loading={isLoadingReadStates} animate="pulse">

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
      ) : activeTab === 'suggestions' ? (
        /* Suggestions tab: AI-classified content awaiting review */
        suggestions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <Lightbulb size={40} className="mb-3 opacity-30" />
            <p className="text-sm font-medium">No suggestions</p>
            <p className="text-xs mt-1">The auto-classifier has no pending suggestions right now.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Batch accept bar */}
            {suggestions.filter(s => s.confidence >= 0.90).length > 0 && (
              <div className="flex items-center gap-3 px-4 py-2.5 bg-success/5 border border-success/20 rounded-xl">
                <Sparkles size={14} className="text-success" />
                <span className="text-sm text-muted-foreground flex-1">
                  {suggestions.filter(s => s.confidence >= 0.90).length} suggestion{suggestions.filter(s => s.confidence >= 0.90).length !== 1 ? 's' : ''} with 90%+ confidence
                </span>
                <button
                  onClick={() => batchAcceptSuggestionsMut.mutate(0.90)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-success/10 text-success hover:bg-success/20 transition-colors"
                >
                  <Check size={14} />
                  Accept All High-Confidence
                </button>
              </div>
            )}
            <div className="border border-border rounded-xl divide-y divide-border overflow-hidden">
              {suggestions.map(s => (
                <div key={s.id} className="flex items-start gap-3 px-4 py-3 hover:bg-accent/50 transition-colors">
                  <div className="shrink-0 mt-0.5">
                    <Lightbulb size={14} className="text-warning" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{s.title}</p>
                    {s.body && (
                      <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{s.body}</p>
                    )}
                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                      {s.suggested_project_name && (
                        <span className="text-[10px] bg-info/10 text-info px-1.5 py-0.5 rounded font-medium">
                          {s.suggested_project_name}
                        </span>
                      )}
                      <span className={cn(
                        'text-[10px] px-1.5 py-0.5 rounded font-medium',
                        s.confidence >= 0.85 ? 'bg-success/10 text-success' :
                        s.confidence >= 0.70 ? 'bg-warning/10 text-warning' :
                        'bg-muted text-muted-foreground'
                      )}>
                        {Math.round(s.confidence * 100)}% confidence
                      </span>
                      {s.source && (
                        <span className="text-[10px] text-muted-foreground">
                          via {s.source}
                        </span>
                      )}
                      {s.reasoning && (
                        <span className="text-[10px] text-muted-foreground italic">
                          {s.reasoning}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={() => acceptSuggestionMut.mutate({ contentId: s.hub_content_id })}
                      className="p-1.5 rounded hover:bg-success/20 text-success transition-colors"
                      title="Accept suggestion"
                    >
                      <Check size={14} />
                    </button>
                    <button
                      onClick={() => rejectSuggestionMut.mutate(s.hub_content_id)}
                      className="p-1.5 rounded hover:bg-destructive/20 text-destructive transition-colors"
                      title="Reject suggestion"
                    >
                      <X size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      ) : activeTab === 'actions' ? (
        /* Actions tab: staged action items for review */
        <ActionReviewPanel />
      ) : activeTab === 'auto_handled' ? (
        /* Auto-handled tab: separate display */
        autoHandledItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <Bot size={40} className="mb-3 opacity-30" />
            <p className="text-sm font-medium">No auto-handled items</p>
            <p className="text-xs mt-1">Nothing was automatically processed since your last session.</p>
          </div>
        ) : (
          <div className="border border-border rounded-xl overflow-hidden">
            <button
              onClick={() => setAutoHandledExpanded(e => !e)}
              className="flex items-center gap-2 w-full px-4 py-3 bg-muted/30 text-sm font-medium text-muted-foreground hover:bg-muted/50 transition-colors"
            >
              <ChevronDownIcon size={14} className={cn('transition-transform', !autoHandledExpanded && '-rotate-90')} />
              <Bot size={14} />
              Auto-handled since last session ({autoHandledItems.length})
            </button>
            {autoHandledExpanded && (
              <div className="divide-y divide-border">
                {autoHandledItems.map(item => (
                  <div key={item.id} className="flex items-center gap-3 px-4 py-3 opacity-70 hover:opacity-90 transition-opacity">
                    <div className="shrink-0">
                      <Bot size={14} className="text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-muted-foreground truncate">{item.summary}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className={cn(
                          'text-[10px] px-1.5 py-0.5 rounded font-medium',
                          item.action === 'classified' ? 'bg-info/10 text-info' :
                          item.action === 'dismissed' ? 'bg-muted text-muted-foreground' :
                          'bg-success/10 text-success'
                        )}>
                          {item.action}
                        </span>
                        {item.confidence != null && (
                          <span className="text-[10px] text-muted-foreground">
                            {Math.round(item.confidence * 100)}% confidence
                          </span>
                        )}
                      </div>
                    </div>
                    {item.project && (
                      <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded shrink-0">
                        {item.project}
                      </span>
                    )}
                    {item.timestamp && (
                      <span className="text-[10px] text-muted-foreground shrink-0 tabular-nums">
                        {new Date(item.timestamp).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      ) : (
        <>
          {/* Items -- click container to enable j/k navigation */}
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
                    selected={selectedIds.has(item.id)}
                    selectMode={selectMode}
                    onToggleSelect={toggleSelect}
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

      </Skeleton>

      {/* Floating batch action bar */}
      {selectMode && selectedIds.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2.5 bg-card border border-border rounded-xl shadow-2xl animate-fade-in">
          <span className="text-sm font-medium text-foreground mr-2">
            {selectedIds.size} item{selectedIds.size !== 1 ? 's' : ''} selected
          </span>
          <div className="w-px h-5 bg-border" />
          {selectedDrafts.length > 0 && (
            <button
              onClick={handleBatchApprove}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-success/10 text-success hover:bg-success/20 transition-colors"
            >
              <Check size={14} />
              Approve {selectedDrafts.length > 1 ? `(${selectedDrafts.length})` : ''}
            </button>
          )}
          {selectedClassify.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setBatchProjectPicker(p => !p)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-warning/10 text-warning hover:bg-warning/20 transition-colors"
              >
                <FolderOpen size={14} />
                Classify {selectedClassify.length > 1 ? `(${selectedClassify.length})` : ''}
              </button>
              {batchProjectPicker && (
                <div className="absolute bottom-full mb-2 right-0">
                  <ProjectPicker
                    onSelect={handleBatchClassify}
                    onCancel={() => setBatchProjectPicker(false)}
                  />
                </div>
              )}
            </div>
          )}
          <button
            onClick={handleBatchMarkSeen}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-accent/50 text-foreground hover:bg-accent transition-colors"
          >
            <Eye size={14} />
            Mark Seen
          </button>
          <button
            onClick={handleBatchDismiss}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors"
          >
            <X size={14} />
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
}
