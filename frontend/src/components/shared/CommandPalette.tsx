import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, LayoutDashboard, FolderKanban, Radio, MessageSquare,
  DollarSign, Settings, CheckSquare, Users, Inbox, Activity, ListTodo,
  Plus, Bot, Target, Trash2, Network, Home, FileText, FilePenLine, Loader2,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { apiFetch } from '../../lib/api';

interface SearchResult {
  type: 'todo' | 'agent' | 'task' | 'goal' | 'content' | 'draft';
  id: string;
  title: string;
  subtitle: string;
  url: string;
  display_id?: string;
  exact_match?: boolean;
}

const searchTypeIcons: Record<string, React.ElementType> = {
  todo: CheckSquare,
  agent: Bot,
  task: ListTodo,
  goal: Target,
  content: FileText,
  draft: FilePenLine,
};

const searchTypeLabels: Record<string, string> = {
  todo: 'Todos',
  agent: 'Agents',
  task: 'Tasks',
  goal: 'Goals',
  content: 'Content',
  draft: 'Drafts',
};

interface CommandItem {
  label: string;
  path?: string;
  keywords: string;
  icon: React.ElementType;
  shortcut?: string;
  action?: () => void;
  section: 'navigation' | 'actions';
}

const navigationCommands: CommandItem[] = [
  { label: 'Home', path: '/', keywords: 'home dashboard overview', icon: Home, shortcut: 'g h', section: 'navigation' },
  { label: 'My Portfolio', path: '/tree', keywords: 'tree portfolio', icon: Network, shortcut: 'g t', section: 'navigation' },
  { label: 'Inbox', path: '/inbox', keywords: 'inbox decisions queue', icon: Inbox, shortcut: 'g i', section: 'navigation' },
  { label: 'Agent Team', path: '/agents', keywords: 'agent worker station', icon: Radio, shortcut: 'g a', section: 'navigation' },
  { label: 'Chat', path: '/chat', keywords: 'coco talk message', icon: MessageSquare, shortcut: 'g c', section: 'navigation' },
  { label: 'Settings', path: '/settings', keywords: 'config preferences', icon: Settings, shortcut: 'g s', section: 'navigation' },
  { label: 'Knowledge Hub', path: '/knowledge', keywords: 'content email voice search', icon: Search, shortcut: 'g k', section: 'navigation' },
  { label: 'Teams', path: '/projects', keywords: 'project team list', icon: FolderKanban, shortcut: 'g p', section: 'navigation' },
  { label: 'Todos', path: '/todos', keywords: 'todo action item', icon: CheckSquare, shortcut: 'g o', section: 'navigation' },
  { label: 'Goals', path: '/goals', keywords: 'goal objective', icon: Target, shortcut: 'g l', section: 'navigation' },
  { label: 'Costs', path: '/costs', keywords: 'budget spend money', icon: DollarSign, shortcut: 'g $', section: 'navigation' },
  { label: 'Activity', path: '/activity', keywords: 'log history', icon: Activity, shortcut: 'g v', section: 'navigation' },
  { label: 'People', path: '/people', keywords: 'person graph rules', icon: Users, section: 'navigation' },
  { label: 'Tasks', path: '/tasks', keywords: 'task issue', icon: ListTodo, section: 'navigation' },
  { label: 'Analytics', path: '/analytics', keywords: 'analytics dashboard metrics', icon: LayoutDashboard, section: 'navigation' },
];

function makeActionCommands(dispatch: (type: string) => void): CommandItem[] {
  return [
    { label: 'New Agent', keywords: 'create agent station', icon: Bot, shortcut: 'c', action: () => dispatch('agent'), section: 'actions' },
    { label: 'New Goal', keywords: 'create goal objective', icon: Target, action: () => dispatch('goal'), section: 'actions' },
    { label: 'New Todo', keywords: 'create todo task', icon: Plus, action: () => dispatch('todo'), section: 'actions' },
    { label: 'Clear Chat', keywords: 'reset chat clear conversation', icon: Trash2, action: () => dispatch('clear-chat'), section: 'actions' },
  ];
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const navigate = useNavigate();

  const dispatchAction = useCallback((type: string) => {
    window.dispatchEvent(new CustomEvent('coco:action', { detail: { type } }));
  }, []);

  const actionCommands = makeActionCommands(dispatchAction);
  const allCommands = [...navigationCommands, ...actionCommands];

  const filtered = allCommands.filter((cmd) => {
    const q = query.toLowerCase();
    return (
      cmd.label.toLowerCase().includes(q) ||
      cmd.keywords.toLowerCase().includes(q)
    );
  });

  const filteredNav = filtered.filter((c) => c.section === 'navigation');
  const filteredActions = filtered.filter((c) => c.section === 'actions');
  const orderedFiltered = [...filteredNav, ...filteredActions];

  // Debounced search across all entities via /api/search
  // Also resolves display IDs matching XXX-123 pattern via /api/resolve/
  useEffect(() => {
    if (!open) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (query.length < 2) {
      setSearchResults([]);
      setSearching(false);
      return;
    }

    setSearching(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const results: SearchResult[] = [];

        // Check if query matches display ID pattern (e.g. CXR-47)
        const displayIdPattern = /^[A-Za-z]{2,6}-\d+$/;
        if (displayIdPattern.test(query.trim())) {
          try {
            const resolved = await apiFetch<{
              entity_id: string;
              entity_type: string;
              display_id: string;
              node_id: string;
            }>(`/resolve/${encodeURIComponent(query.trim())}`);
            const typeUrlMap: Record<string, string> = {
              todo: '/todos',
              task: '/tasks',
            };
            results.push({
              type: resolved.entity_type as SearchResult['type'],
              id: resolved.entity_id,
              title: `${resolved.display_id}`,
              subtitle: `Go to ${resolved.entity_type} ${resolved.display_id}`,
              url: typeUrlMap[resolved.entity_type] ?? '/todos',
            });
          } catch {
            // Not found -- fall through to normal search
          }
        }

        // Normal search
        const { results: apiResults } = await apiFetch<{ results: SearchResult[]; query: string }>(
          `/search?q=${encodeURIComponent(query)}&types=todos,agents,content,goals,drafts&limit=10`,
        );
        results.push(...apiResults);
        setSearchResults(results);
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, open]);

  // Total selectable items = commands + search results
  const totalItems = orderedFiltered.length + searchResults.length;

  const close = useCallback(() => {
    setOpen(false);
    setQuery('');
    setSelectedIndex(0);
    setSearchResults([]);
    setSearching(false);
  }, []);

  const execute = useCallback(
    (cmd: CommandItem) => {
      if (cmd.path) {
        navigate(cmd.path);
      } else if (cmd.action) {
        cmd.action();
      }
      close();
    },
    [navigate, close],
  );

  // Global Cmd+K / Ctrl+K listener
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const executeSearchResult = useCallback(
    (result: SearchResult) => {
      navigate(result.url);
      close();
    },
    [navigate, close],
  );

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, totalItems - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (selectedIndex < orderedFiltered.length) {
          const cmd = orderedFiltered[selectedIndex];
          if (cmd) execute(cmd);
        } else {
          const srIdx = selectedIndex - orderedFiltered.length;
          const result = searchResults[srIdx];
          if (result) executeSearchResult(result);
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        close();
      }
    },
    [orderedFiltered, searchResults, selectedIndex, totalItems, execute, executeSearchResult, close],
  );

  if (!open) return null;

  let itemIndex = 0;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
        onClick={close}
      />

      {/* Palette */}
      <div
        className="relative w-full max-w-lg rounded-2xl border border-border bg-card shadow-2xl animate-cmd-palette-enter"
        onKeyDown={onKeyDown}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 border-b border-border px-4 py-3">
          <Search className="h-5 w-5 text-muted-foreground shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search pages and actions..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-foreground outline-none placeholder:text-muted-foreground text-sm"
          />
          <kbd className="rounded-lg border border-border bg-card px-2 py-0.5 text-xs text-muted-foreground">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto py-1">
          {orderedFiltered.length === 0 && !searching && searchResults.length === 0 && query.length < 2 && (
            <div className="px-4 py-3 text-sm text-muted-foreground">
              No results found.
            </div>
          )}

          {/* Navigation section */}
          {filteredNav.length > 0 && (
            <div>
              <div className="px-4 pt-2 pb-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Navigation
                </span>
              </div>
              <ul>
                {filteredNav.map((cmd) => {
                  const Icon = cmd.icon;
                  const idx = itemIndex++;
                  return (
                    <li key={cmd.label}>
                      <button
                        className={cn(
                          'w-full px-4 py-2 text-left text-sm transition-colors flex items-center gap-3',
                          idx === selectedIndex
                            ? 'bg-accent/20 text-accent'
                            : 'text-foreground hover:bg-accent/50',
                        )}
                        onClick={() => execute(cmd)}
                        onMouseEnter={() => setSelectedIndex(idx)}
                      >
                        <Icon size={16} className={idx === selectedIndex ? 'text-accent' : 'text-muted-foreground'} />
                        <span className="flex-1">{cmd.label}</span>
                        {cmd.shortcut && (
                          <span className="flex gap-1 ml-auto">
                            {cmd.shortcut.split(' ').map((k, ki) => (
                              <kbd
                                key={ki}
                                className="rounded border border-border bg-background px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground min-w-[18px] text-center"
                              >
                                {k}
                              </kbd>
                            ))}
                          </span>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {/* Actions section */}
          {filteredActions.length > 0 && (
            <div>
              <div className="px-4 pt-3 pb-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Actions
                </span>
              </div>
              <ul>
                {filteredActions.map((cmd) => {
                  const Icon = cmd.icon;
                  const idx = itemIndex++;
                  return (
                    <li key={cmd.label}>
                      <button
                        className={cn(
                          'w-full px-4 py-2 text-left text-sm transition-colors flex items-center gap-3',
                          idx === selectedIndex
                            ? 'bg-accent/20 text-accent'
                            : 'text-foreground hover:bg-accent/50',
                        )}
                        onClick={() => execute(cmd)}
                        onMouseEnter={() => setSelectedIndex(idx)}
                      >
                        <Icon size={16} className={idx === selectedIndex ? 'text-accent' : 'text-muted-foreground'} />
                        <span className="flex-1">{cmd.label}</span>
                        {cmd.shortcut && (
                          <span className="flex gap-1 ml-auto">
                            {cmd.shortcut.split(' ').map((k, ki) => (
                              <kbd
                                key={ki}
                                className="rounded border border-border bg-background px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground min-w-[18px] text-center"
                              >
                                {k}
                              </kbd>
                            ))}
                          </span>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {/* Search Results section */}
          {searching && (
            <div className="flex items-center gap-2 px-4 py-3 text-sm text-muted-foreground">
              <Loader2 size={14} className="animate-spin" />
              Searching...
            </div>
          )}
          {!searching && searchResults.length > 0 && (() => {
            // Group results by type
            const grouped = new Map<string, SearchResult[]>();
            for (const r of searchResults) {
              const existing = grouped.get(r.type) || [];
              existing.push(r);
              grouped.set(r.type, existing);
            }

            return (
              <div>
                <div className="px-4 pt-3 pb-1">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Search Results
                  </span>
                </div>
                {Array.from(grouped.entries()).map(([type, items]) => {
                  const TypeIcon = searchTypeIcons[type] || FileText;
                  const typeLabel = searchTypeLabels[type] || type;
                  return (
                    <div key={type}>
                      <div className="px-4 pt-1.5 pb-0.5">
                        <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground/70">
                          {typeLabel}
                        </span>
                      </div>
                      <ul>
                        {items.map((result) => {
                          const idx = itemIndex++;
                          return (
                            <li key={`${result.type}-${result.id}`}>
                              <button
                                className={cn(
                                  'w-full px-4 py-2 text-left text-sm transition-colors flex items-center gap-3',
                                  idx === selectedIndex
                                    ? 'bg-accent/20 text-accent'
                                    : 'text-foreground hover:bg-accent/50',
                                )}
                                onClick={() => executeSearchResult(result)}
                                onMouseEnter={() => setSelectedIndex(idx)}
                              >
                                <TypeIcon
                                  size={16}
                                  className={idx === selectedIndex ? 'text-accent' : 'text-muted-foreground'}
                                />
                                <div className="flex-1 min-w-0">
                                  <div className="truncate flex items-center gap-1.5">
                                    {result.display_id && (
                                      <span className="inline-flex shrink-0 rounded bg-accent/15 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-accent">
                                        {result.display_id}
                                      </span>
                                    )}
                                    <span className="truncate">{result.title}</span>
                                  </div>
                                  <div className="text-[11px] text-muted-foreground truncate">
                                    {result.subtitle}
                                  </div>
                                </div>
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  );
                })}
              </div>
            );
          })()}
          {!searching && query.length >= 2 && searchResults.length === 0 && orderedFiltered.length === 0 && (
            <div className="px-4 py-3 text-sm text-muted-foreground">
              No results found.
            </div>
          )}
        </div>

        {/* Footer hint */}
        <div className="flex items-center gap-4 border-t border-border px-4 py-2 text-xs text-muted-foreground">
          <span>
            <kbd className="rounded border border-border bg-card px-1 py-0.5 mr-1">
              &uarr;&darr;
            </kbd>
            Navigate
          </span>
          <span>
            <kbd className="rounded border border-border bg-card px-1 py-0.5 mr-1">
              Enter
            </kbd>
            Go
          </span>
          <span>
            <kbd className="rounded border border-border bg-card px-1 py-0.5 mr-1">
              Esc
            </kbd>
            Close
          </span>
        </div>
      </div>
    </div>
  );
}
