import React from 'react';
import { Briefcase, ClipboardList, Code2, UserSearch, Bot } from 'lucide-react';
import { cn } from '../../lib/utils';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface OrgNode {
  id: string;
  name: string;
  role: string | null;
  status: string;
  model: string;
  children: OrgNode[];
  // pass-through from Agent
  task_description: string | null;
  pid: number | null;
}

interface OrgChartProps {
  /** Tree roots returned by /api/agents/org-chart */
  roots: OrgNode[];
  onSelect: (agentId: string) => void;
}

/* ------------------------------------------------------------------ */
/*  Role metadata (mirrors AgentCard)                                  */
/* ------------------------------------------------------------------ */

const ROLE_META: Record<string, { label: string; abbr: string; color: string; icon: React.ElementType; emoji: string }> = {
  'product-manager': { label: 'Product Manager', abbr: 'PM',  color: 'bg-info/20 text-info border-info/40',          icon: Briefcase,    emoji: '\uD83E\uDDE0' },
  'project-manager': { label: 'Project Manager', abbr: 'PjM', color: 'bg-warning/20 text-warning border-warning/40', icon: ClipboardList, emoji: '\uD83D\uDCCB' },
  'developer':       { label: 'Developer',       abbr: 'Dev', color: 'bg-success/20 text-success border-success/40', icon: Code2,         emoji: '\uD83D\uDEE0\uFE0F' },
  'user-researcher': { label: 'User Researcher', abbr: 'UXR', color: 'bg-accent/20 text-accent border-accent/40',    icon: UserSearch,    emoji: '\uD83D\uDD0D' },
  'custom':          { label: 'Custom',          abbr: 'Bot', color: 'bg-muted text-muted-foreground border-border',  icon: Bot,           emoji: '\uD83E\uDD16' },
};

const statusDot: Record<string, string> = {
  running:   'bg-success',
  paused:    'bg-warning',
  idle:      'bg-muted-foreground',
  completed: 'bg-info',
  failed:    'bg-destructive',
  killed:    'bg-destructive',
};

/* ------------------------------------------------------------------ */
/*  Single org-chart node                                              */
/* ------------------------------------------------------------------ */

function OrgNodeCard({ node, onSelect }: { node: OrgNode; onSelect: (id: string) => void }) {
  const meta = ROLE_META[node.role ?? 'custom'] ?? ROLE_META['custom'];
  const Icon = meta.icon;

  return (
    <button
      type="button"
      onClick={() => onSelect(node.id)}
      className={cn(
        'group relative flex flex-col items-center gap-1.5 rounded-xl border bg-card p-4 min-w-[140px] max-w-[180px]',
        'transition-all duration-150 hover:border-accent hover:shadow-lg hover:shadow-accent/10 cursor-pointer',
        'animate-fade-in',
      )}
    >
      {/* Avatar circle */}
      <div className={cn(
        'relative flex items-center justify-center w-11 h-11 rounded-full border-2',
        meta.color,
      )}>
        <Icon size={20} />
        {/* Status indicator */}
        <span
          className={cn(
            'absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-card',
            statusDot[node.status] ?? 'bg-muted-foreground',
            node.status === 'running' && 'animate-pulse-dot',
          )}
        />
      </div>

      {/* Name */}
      <span className="text-sm font-medium text-foreground text-center leading-tight truncate w-full">
        {node.name}
      </span>

      {/* Role badge */}
      <span className={cn(
        'inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full',
        meta.color,
      )}>
        {meta.abbr}
      </span>

      {/* Model pill */}
      <span className="text-[10px] text-muted-foreground">{node.model}</span>
    </button>
  );
}

/* ------------------------------------------------------------------ */
/*  Recursive subtree with connectors                                  */
/* ------------------------------------------------------------------ */

function ChildrenRow({ children, onSelect }: { children: OrgNode[]; onSelect: (id: string) => void }) {
  const count = children.length;

  return (
    <div className="flex flex-col items-center">
      {/* Vertical stem from parent */}
      <div className="w-0.5 h-6 bg-border" />

      {/* Horizontal bar connecting all children (only if >1) */}
      {count > 1 && (
        <div className="flex w-full">
          {children.map((_, idx) => (
            <div key={idx} className="flex-1 h-0.5">
              {/* Left half */}
              <div className={cn(
                'h-full',
                idx === 0 ? 'ml-[50%]' : '',
                idx === count - 1 ? 'mr-[50%]' : '',
                'bg-border',
              )} />
            </div>
          ))}
        </div>
      )}

      {/* Children with vertical drops */}
      <div className="flex gap-2 md:gap-6">
        {children.map((child) => (
          <div key={child.id} className="flex flex-col items-center">
            <div className="w-0.5 h-6 bg-border" />
            <SubTree node={child} onSelect={onSelect} />
          </div>
        ))}
      </div>
    </div>
  );
}

function SubTree({ node, onSelect }: { node: OrgNode; onSelect: (id: string) => void }) {
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="flex flex-col items-center">
      <OrgNodeCard node={node} onSelect={onSelect} />
      {hasChildren && (
        <ChildrenRow children={node.children} onSelect={onSelect} />
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main OrgChart component                                            */
/* ------------------------------------------------------------------ */

export function OrgChart({ roots, onSelect }: OrgChartProps) {
  if (!roots || roots.length === 0) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground text-sm">
        No agents to display in org chart.
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto pb-4">
      <div className="flex gap-10 justify-center min-w-max px-4 pt-2 animate-fade-in">
        {roots.map((root) => (
          <SubTree key={root.id} node={root} onSelect={onSelect} />
        ))}
      </div>
    </div>
  );
}
