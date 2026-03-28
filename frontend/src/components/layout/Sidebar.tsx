import { NavLink } from 'react-router-dom';
import {
  FolderKanban, Radio, MessageSquare,
  DollarSign, Settings, CheckSquare, Search, Inbox, Brain,
  Target, Activity, ChevronsUpDown, ChevronRight, Network,
  BarChart3, Home, Sparkles,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useScope, type TreeNode } from '../../context/ScopeContext';
import { useState, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

function SidebarSection({ label, children, defaultOpen = true }: {
  label: string; children: React.ReactNode; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
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

function NavItem({ to, icon: Icon, label, badge, badgeTone = 'default', end }: {
  to: string; icon: React.ElementType; label: string;
  badge?: number; badgeTone?: 'default' | 'danger'; end?: boolean;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors relative group',
          isActive
            ? 'text-sidebar-primary-foreground bg-sidebar-accent font-medium'
            : 'text-muted-foreground hover:text-sidebar-foreground hover:bg-sidebar-accent/50'
        )
      }
    >
      <Icon size={16} className="shrink-0" />
      <span className="truncate">{label}</span>
      {badge != null && badge > 0 && (
        <span className={cn('ml-auto text-[10px] font-medium px-1.5 py-0.5 rounded-full min-w-[20px] text-center',
          badgeTone === 'danger' ? 'bg-destructive text-destructive-foreground' : 'bg-muted text-muted-foreground',
        )}>{badge}</span>
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

  return (
    <aside className="w-60 h-screen bg-sidebar border-r border-sidebar-border flex flex-col fixed left-0 top-0">
      <div className="px-4 py-4 border-b border-sidebar-border">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-sidebar-primary flex items-center justify-center">
            <Brain size={14} className="text-sidebar-primary-foreground" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-sidebar-foreground tracking-tight">CoCo</h1>
            <p className="text-[10px] text-muted-foreground leading-none">Rijul's Brain</p>
          </div>
        </div>
      </div>

      <div className="px-2 pt-2"><ScopePicker /></div>
      <nav className="flex-1 py-2 overflow-y-auto px-2 flex flex-col gap-4 scrollbar-auto-hide">
        <SidebarSection label="Home">
          <NavItem to="/" icon={Home} label="Home" end />
          <NavItem to="/jarvis" icon={Sparkles} label="Jarvis" />
          <NavItem to="/analytics" icon={BarChart3} label="Analytics" />
          <NavItem to="/inbox" icon={Inbox} label="Inbox" badge={inboxCount} badgeTone="danger" />
        </SidebarSection>

        <SidebarSection label="Work">
          <NavItem to="/tree" icon={Network} label="My Portfolio" />
          <NavItem to="/projects" icon={FolderKanban} label="Teams" />
          <NavItem to="/todos" icon={CheckSquare} label="Todos" />
          <NavItem to="/goals" icon={Target} label="Goals" />
        </SidebarSection>

        <SidebarSection label="Intelligence">
          <NavItem to="/knowledge" icon={Search} label="Knowledge" />
          <NavItem to="/chat" icon={MessageSquare} label="Chat" />
        </SidebarSection>

        <SidebarSection label="System" defaultOpen={false}>
          <NavItem to="/agents" icon={Radio} label="Agent Team" />
          <NavItem to="/costs" icon={DollarSign} label="Costs" />
          <NavItem to="/activity" icon={Activity} label="Activity" />
          <NavItem to="/settings" icon={Settings} label="Settings" />
        </SidebarSection>
      </nav>

      <div className="px-3 py-3 border-t border-sidebar-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-sidebar-accent text-sidebar-accent-foreground flex items-center justify-center text-xs font-semibold shrink-0">RK</div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-sidebar-foreground truncate">Rijul Kalra</p>
            <p className="text-[10px] text-muted-foreground truncate">v1.1</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
