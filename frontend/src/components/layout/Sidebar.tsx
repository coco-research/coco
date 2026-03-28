import { NavLink } from 'react-router-dom';
import {
  FolderKanban, Radio, MessageSquare,
  DollarSign, Settings, CheckSquare, Search, Inbox, Brain,
  Target, Activity, ChevronsUpDown, ChevronRight, Network,
  BarChart3, Home, Sparkles, PanelLeftClose, PanelLeftOpen, Wand2,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useScope, type TreeNode } from '../../context/ScopeContext';
import { useState, useRef, useEffect, useSyncExternalStore } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useEdition } from '../../hooks/useEdition';

// ─── Sidebar collapse state (shared across components) ────────────────
const STORAGE_KEY = 'coco-sidebar-collapsed';

let _collapsed = (() => {
  try { return localStorage.getItem(STORAGE_KEY) === '1'; } catch { return false; }
})();

const listeners = new Set<() => void>();

function setCollapsed(val: boolean) {
  _collapsed = val;
  try { localStorage.setItem(STORAGE_KEY, val ? '1' : '0'); } catch { /* ignore */ }
  listeners.forEach((l) => l());
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => { listeners.delete(cb); };
}
function getSnapshot() { return _collapsed; }

/** Hook to read sidebar collapsed state from any component. */
export function useSidebarCollapsed(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

function SidebarSection({ label, children, defaultOpen = true, collapsed }: {
  label: string; children: React.ReactNode; defaultOpen?: boolean; collapsed?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  if (collapsed) {
    // In collapsed mode, just render children (icons only), no section header
    return <div className="space-y-0.5">{children}</div>;
  }

  return (
    <div className="space-y-0.5">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors w-full"
      >
        <ChevronRight size={12} className={cn('transition-transform', open && 'rotate-90')} />
        {label}
      </button>
      {open && <div className="space-y-0.5">{children}</div>}
    </div>
  );
}

function NavItem({ to, icon: Icon, label, badge, badgeTone = 'default', end, collapsed }: {
  to: string; icon: React.ElementType; label: string;
  badge?: number; badgeTone?: 'default' | 'danger'; end?: boolean; collapsed?: boolean;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      title={collapsed ? label : undefined}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 py-2 text-sm rounded-md transition-colors relative group',
          collapsed ? 'justify-center px-0' : 'px-3',
          isActive
            ? 'text-sidebar-primary-foreground bg-sidebar-accent font-medium nav-item-active'
            : 'text-muted-foreground hover:text-sidebar-foreground hover:bg-sidebar-accent/50'
        )
      }
    >
      {/* Active indicator bar (rendered via CSS using .nav-item-active) */}
      <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-4 bg-accent rounded-r-full opacity-0 transition-opacity nav-active-bar" />
      <Icon size={16} className="shrink-0" />
      {!collapsed && <span className="truncate">{label}</span>}
      {!collapsed && badge != null && badge > 0 && (
        <span className={cn('ml-auto text-[10px] font-medium px-1.5 py-0.5 rounded-full min-w-[20px] text-center',
          badgeTone === 'danger' ? 'bg-destructive text-destructive-foreground' : 'bg-muted text-muted-foreground',
        )}>{badge}</span>
      )}
      {collapsed && badge != null && badge > 0 && (
        <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-destructive rounded-full" />
      )}
    </NavLink>
  );
}

function TreeRow({ node, depth, selectedId, onSelect }: {
  node: TreeNode; depth: number; selectedId: string | null; onSelect: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(depth < 1);
  const hasChildren = (node.children?.length ?? 0) > 0;

  return (
    <>
      <button
        onClick={() => onSelect(node.id)}
        className={cn(
          'w-full flex items-center gap-1.5 py-1.5 text-sm hover:bg-accent/50 transition-colors rounded-sm',
          node.id === selectedId && 'bg-accent/30 font-medium',
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px`, paddingRight: 8 }}
      >
        {hasChildren ? (
          <ChevronRight
            size={12}
            className={cn('shrink-0 transition-transform text-muted-foreground', expanded && 'rotate-90')}
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
          />
        ) : (
          <span className="w-3 shrink-0" />
        )}
        <span className="truncate">{node.label}</span>
      </button>
      {expanded && node.children?.map((child) => (
        <TreeRow key={child.id} node={child} depth={depth + 1} selectedId={selectedId} onSelect={onSelect} />
      ))}
    </>
  );
}

function ScopePicker() {
  const { tree, selectedNode, setSelectedNodeId } = useScope();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-sidebar-accent/50 transition-colors"
      >
        <div className="w-2 h-2 rounded-full bg-success shrink-0" />
        <span className="truncate font-medium text-sidebar-foreground">
          {selectedNode?.label ?? 'All'}
        </span>
        <ChevronsUpDown size={14} className="ml-auto text-muted-foreground shrink-0" />
      </button>

      {open && (
        <div className="absolute left-0 right-0 top-full mt-1 z-50 bg-popover border border-border rounded-lg shadow-lg overflow-hidden animate-fade-in">
          <div className="max-h-[300px] overflow-y-auto py-1">
            <button
              onClick={() => { setSelectedNodeId(null); setOpen(false); }}
              className={cn(
                'w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent/50 transition-colors',
                !selectedNode && 'bg-accent/30 font-medium',
              )}
            >
              <div className="w-2 h-2 rounded-full bg-muted-foreground" />
              <span>All</span>
            </button>
            {tree?.children?.map((child) => (
              <TreeRow
                key={child.id}
                node={child}
                depth={0}
                selectedId={selectedNode?.id ?? null}
                onSelect={(id) => { setSelectedNodeId(id); setOpen(false); }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function useInboxCount(): number {
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
    queryKey: ['drafts-count'],
    queryFn: async () => {
      const res = await fetch('/api/drafts?limit=100');
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

  let count = 0;
  if (queueData?.items && Array.isArray(queueData.items)) count += queueData.items.length;
  if (Array.isArray(draftsData)) count += draftsData.length;
  if (Array.isArray(healthData)) count += healthData.filter((h: Record<string, string>) => h.status === 'red').length;
  if (unsortedData?.items && Array.isArray(unsortedData.items)) count += unsortedData.items.length;
  if (Array.isArray(todosData)) {
    const today = new Date().toISOString().slice(0, 10);
    count += todosData.filter((t: Record<string, string>) => t.due_date && t.due_date < today).length;
  }
  return count;
}

export function Sidebar() {
  const inboxCount = useInboxCount();
  const collapsed = useSidebarCollapsed();
  const { isStudio } = useEdition();

  return (
    <aside
      className={cn(
        'h-screen bg-sidebar border-r border-sidebar-border flex flex-col fixed left-0 top-0 transition-[width] duration-200 ease-out z-40',
        collapsed ? 'w-12' : 'w-60',
      )}
    >
      <div className={cn('py-4 border-b border-sidebar-border', collapsed ? 'px-2' : 'px-4')}>
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-sidebar-primary flex items-center justify-center shrink-0">
            <Brain size={14} className="text-sidebar-primary-foreground" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <h1 className="text-sm font-bold text-sidebar-foreground tracking-tight">CoCo</h1>
              <p className="text-[10px] text-muted-foreground leading-none">Rijul's Brain</p>
            </div>
          )}
        </div>
      </div>

      {!collapsed && <div className="px-2 pt-2"><ScopePicker /></div>}
      <nav className={cn('flex-1 py-2 overflow-y-auto flex flex-col gap-4 scrollbar-auto-hide', collapsed ? 'px-1' : 'px-2')}>
        <SidebarSection label="Home" collapsed={collapsed}>
          <NavItem to="/" icon={Home} label="Home" end collapsed={collapsed} />
          {isStudio && <NavItem to="/?jarvis=true" icon={Sparkles} label="Jarvis" collapsed={collapsed} />}
          <NavItem to="/analytics" icon={BarChart3} label="Analytics" collapsed={collapsed} />
          <NavItem to="/inbox" icon={Inbox} label="Inbox" badge={inboxCount} badgeTone="danger" collapsed={collapsed} />
        </SidebarSection>

        <SidebarSection label="Work" collapsed={collapsed}>
          <NavItem to="/tree" icon={Network} label="My Portfolio" collapsed={collapsed} />
          <NavItem to="/projects" icon={FolderKanban} label="Teams" collapsed={collapsed} />
          <NavItem to="/todos" icon={CheckSquare} label="Todos" collapsed={collapsed} />
          <NavItem to="/goals" icon={Target} label="Goals" collapsed={collapsed} />
        </SidebarSection>

        <SidebarSection label="Intelligence" collapsed={collapsed}>
          <NavItem to="/knowledge" icon={Search} label="Knowledge" collapsed={collapsed} />
          <NavItem to="/chat" icon={MessageSquare} label="Chat" collapsed={collapsed} />
        </SidebarSection>

        <SidebarSection label="System" defaultOpen={false} collapsed={collapsed}>
          <NavItem to="/agents" icon={Radio} label="Agent Team" collapsed={collapsed} />
          <NavItem to="/costs" icon={DollarSign} label="Costs" collapsed={collapsed} />
          <NavItem to="/activity" icon={Activity} label="Activity" collapsed={collapsed} />
          {isStudio && <NavItem to="/self-improve" icon={Wand2} label="Self-Improve" collapsed={collapsed} />}
          <NavItem to="/settings" icon={Settings} label="Settings" collapsed={collapsed} />
        </SidebarSection>
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="mx-auto mb-1 p-1.5 rounded-md text-muted-foreground hover:text-sidebar-foreground hover:bg-sidebar-accent/50 transition-colors"
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
      </button>

      <div className={cn('py-3 border-t border-sidebar-border', collapsed ? 'px-1' : 'px-3')}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-sidebar-accent text-sidebar-accent-foreground flex items-center justify-center text-xs font-semibold shrink-0">RK</div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-sm font-medium text-sidebar-foreground truncate">Rijul Kalra</p>
              <p className="text-[10px] text-muted-foreground truncate">v1.1</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
