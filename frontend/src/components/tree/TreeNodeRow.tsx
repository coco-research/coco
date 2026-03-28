import { useState } from 'react';
import {
  ChevronRight, Folder, Users, Package, FolderKanban,
  Plus, MoreHorizontal,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { InlineEditor } from '../shared/InlineEditor';
import { apiPatch } from '../../lib/api';

export interface TreeNode {
  id: string;
  parent_id: string | null;
  label: string;
  node_type: 'group' | 'team' | 'product' | 'project';
  hub_project_id: string | null;
  path: string;
  depth: number;
  sort_order: number;
  icon: string | null;
  color: string | null;
  children?: TreeNode[];
}

const NODE_ICONS = {
  group: Folder,
  team: Users,
  product: Package,
  project: FolderKanban,
} as const;

interface TreeNodeRowProps {
  node: TreeNode;
  selectedId: string | null;
  expanded: boolean;
  onToggle: () => void;
  onSelect: (id: string) => void;
  compact?: boolean;
  onAdd?: (parentId: string) => void;
  onRename?: (id: string) => void;
  onDelete?: (id: string) => void;
  onMove?: (id: string) => void;
}

export function TreeNodeRow({
  node, selectedId, expanded, onToggle, onSelect,
  compact, onAdd, onRename, onDelete, onMove,
}: TreeNodeRowProps) {
  const [hovered, setHovered] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const Icon = NODE_ICONS[node.node_type];
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedId === node.id;

  return (
    <div
      role="treeitem"
      aria-selected={isSelected}
      aria-expanded={hasChildren ? expanded : undefined}
      tabIndex={0}
      className={cn(
        'flex items-center gap-1.5 px-2 py-1.5 text-sm rounded-md cursor-pointer transition-colors group relative',
        isSelected
          ? 'bg-sidebar-accent text-sidebar-primary-foreground font-medium'
          : 'text-muted-foreground hover:text-sidebar-foreground hover:bg-sidebar-accent/50'
      )}
      style={{ paddingLeft: `${node.depth * 16 + 8}px` }}
      onClick={() => onSelect(node.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => { setHovered(false); setMenuOpen(false); }}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onSelect(node.id);
        if (e.key === ' ' && hasChildren) { e.preventDefault(); onToggle(); }
      }}
    >
      {/* Chevron */}
      <button
        className={cn(
          'shrink-0 w-4 h-4 flex items-center justify-center',
          !hasChildren && 'invisible'
        )}
        onClick={(e) => { e.stopPropagation(); onToggle(); }}
        tabIndex={-1}
        aria-label={expanded ? 'Collapse' : 'Expand'}
      >
        <ChevronRight
          size={12}
          className={cn('transition-transform', expanded && 'rotate-90')}
        />
      </button>

      {/* Icon */}
      <Icon size={14} className="shrink-0" style={node.color ? { color: node.color } : undefined} />

      {/* Label */}
      {compact ? (
        <span className="truncate flex-1">{node.label}</span>
      ) : (
        <InlineEditor
          value={node.label}
          onSave={async (label) => { await apiPatch(`/tree/${node.id}`, { label }); }}
          className="truncate flex-1 text-inherit"
        />
      )}

      {/* Child count badge */}
      {hasChildren && (
        <span className="text-[10px] text-muted-foreground ml-auto tabular-nums">
          {node.children!.length}
        </span>
      )}

      {/* Full-mode actions */}
      {!compact && hovered && (
        <div className="flex items-center gap-0.5 ml-1 shrink-0">
          {onAdd && (
            <button
              className="w-5 h-5 flex items-center justify-center rounded hover:bg-accent/60 text-muted-foreground hover:text-foreground"
              onClick={(e) => { e.stopPropagation(); onAdd(node.id); }}
              aria-label="Add child"
            >
              <Plus size={12} />
            </button>
          )}
          {(onRename || onDelete || onMove) && (
            <div className="relative">
              <button
                className="w-5 h-5 flex items-center justify-center rounded hover:bg-accent/60 text-muted-foreground hover:text-foreground"
                onClick={(e) => { e.stopPropagation(); setMenuOpen(!menuOpen); }}
                aria-label="More actions"
              >
                <MoreHorizontal size={12} />
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-full mt-1 z-50 bg-popover border border-border rounded-lg shadow-lg py-1 min-w-[120px] animate-fade-in">
                  {onRename && (
                    <button
                      className="w-full text-left px-3 py-1.5 text-sm hover:bg-accent/50"
                      onClick={(e) => { e.stopPropagation(); setMenuOpen(false); onRename(node.id); }}
                    >Rename</button>
                  )}
                  {onMove && (
                    <button
                      className="w-full text-left px-3 py-1.5 text-sm hover:bg-accent/50"
                      onClick={(e) => { e.stopPropagation(); setMenuOpen(false); onMove(node.id); }}
                    >Move</button>
                  )}
                  {onDelete && (
                    <button
                      className="w-full text-left px-3 py-1.5 text-sm text-destructive hover:bg-accent/50"
                      onClick={(e) => { e.stopPropagation(); setMenuOpen(false); onDelete(node.id); }}
                    >Delete</button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
