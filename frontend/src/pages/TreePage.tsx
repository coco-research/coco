import { useState, useMemo, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import {
  DndContext, DragOverlay, PointerSensor, useSensor, useSensors,
  useDraggable, useDroppable,
  type DragStartEvent, type DragEndEvent, type DragOverEvent,
} from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import {
  Plus, ChevronRight, MoreHorizontal, X, FolderTree, AlertTriangle,
  Move, Trash2, Link2, Users, Package, FolderKanban, Layers,
  GripVertical, Folder, ArrowUp, FolderOpen, Check, FolderSearch,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { apiFetch, apiPost, apiPatch, apiDelete } from '../lib/api';
import type { TreeNode } from '../context/ScopeContext';
import { AnalyzeFolderDialog } from '../components/tree/AnalyzeFolderDialog';
import { AnalysisResults } from '../components/tree/AnalysisResults';

// ─── Types ──────────────────────────────────────────────────────────

interface UnplacedProject {
  id: string;
  name: string;
}

const NODE_TYPES = ['group', 'team', 'product', 'project'] as const;
type NodeType = (typeof NODE_TYPES)[number];

const NODE_TYPE_ICONS: Record<NodeType, React.ElementType> = {
  group: Layers,
  team: Users,
  product: Package,
  project: FolderKanban,
};

const PRESET_COLORS = [
  null,
  '#ef4444', '#f97316', '#eab308', '#22c55e',
  '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280',
];

const inputCls = 'w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';
const selectCls = inputCls;

// ─── Helpers ────────────────────────────────────────────────────────

function flattenTree(node: TreeNode): TreeNode[] {
  const result: TreeNode[] = [node];
  node.children?.forEach(child => {
    result.push(...flattenTree(child));
  });
  return result;
}

function getDescendantIds(node: TreeNode): Set<string> {
  const ids = new Set<string>();
  function walk(n: TreeNode) {
    ids.add(n.id);
    n.children?.forEach(walk);
  }
  walk(node);
  return ids;
}

/** Find a node's parent in the tree */
function findParent(tree: TreeNode, targetId: string): TreeNode | null {
  for (const child of tree.children ?? []) {
    if (child.id === targetId) return tree;
    const found = findParent(child, targetId);
    if (found) return found;
  }
  return null;
}

// ─── Drop position types ───────────────────────────────────────────

type DropPosition = 'before' | 'on' | 'after';

interface DropInfo {
  targetId: string;
  position: DropPosition;
}

// ─── Tree Node Row ──────────────────────────────────────────────────

interface TreeNodeRowProps {
  node: TreeNode;
  depth: number;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onAddChild: (parentId: string) => void;
  onMove: (node: TreeNode) => void;
  onDelete: (node: TreeNode) => void;
  onAnalyze?: (node: TreeNode) => void;
  /** Currently active drag node id (from DndContext) */
  activeDragId?: string | null;
  /** The current drop info for visual feedback */
  dropInfo?: DropInfo | null;
  /** IDs that are descendants of the dragged node (invalid drop targets) */
  dragDescendantIds?: Set<string>;
  /** Whether this node is the root node (not draggable) */
  isRoot?: boolean;
}

function TreeNodeRow({
  node, depth, selectedId, onSelect, onAddChild,
  onMove, onDelete, onAnalyze,
  activeDragId, dropInfo, dragDescendantIds, isRoot,
}: TreeNodeRowProps) {
  const [expanded, setExpanded] = useState(true);
  const children = node.children ?? [];
  const hasChildren = children.length > 0;
  const isSelected = selectedId === node.id;
  const Icon = NODE_TYPE_ICONS[node.node_type] ?? FolderKanban;

  const isDragging = activeDragId === node.id;
  const canDrag = !isRoot;
  const isInvalidTarget = dragDescendantIds?.has(node.id) || activeDragId === node.id;

  // Draggable
  const { attributes, listeners, setNodeRef: setDragRef, transform } = useDraggable({
    id: `drag-${node.id}`,
    data: { node },
    disabled: !canDrag,
  });

  // Droppable
  const rowRef = useRef<HTMLDivElement>(null);
  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id: `drop-${node.id}`,
    data: { node },
    disabled: isInvalidTarget,
  });

  // Combine refs for the row element
  const setRefs = useCallback((el: HTMLDivElement | null) => {
    setDragRef(el);
    setDropRef(el);
    (rowRef as React.MutableRefObject<HTMLDivElement | null>).current = el;
  }, [setDragRef, setDropRef]);

  // Determine visual drop feedback for this node
  const showDropOn = dropInfo?.targetId === node.id && dropInfo.position === 'on' && !isInvalidTarget;
  const showDropBefore = dropInfo?.targetId === node.id && dropInfo.position === 'before' && !isInvalidTarget;
  const showDropAfter = dropInfo?.targetId === node.id && dropInfo.position === 'after' && !isInvalidTarget;

  const dragStyle = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined;

  return (
    <div className="relative">
      {/* Drop-before indicator line */}
      {showDropBefore && (
        <div
          className="absolute left-0 right-0 h-0.5 bg-accent z-10 rounded-full"
          style={{ top: 0, marginLeft: `${depth * 24 + 12}px` }}
        />
      )}

      <div
        ref={setRefs}
        className={cn(
          'group flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors relative',
          isSelected ? 'bg-accent/60 text-foreground' : 'hover:bg-accent/30 text-foreground',
          isDragging && 'opacity-40',
          showDropOn && 'bg-accent/20 border-2 border-dashed border-accent',
        )}
        style={{ paddingLeft: `${depth * 24 + 12}px`, ...dragStyle }}
        onClick={() => onSelect(node.id)}
      >
        {/* Drag handle */}
        {canDrag && (
          <button
            {...attributes}
            {...listeners}
            onClick={(e) => e.stopPropagation()}
            className="shrink-0 p-0.5 rounded hover:bg-accent opacity-0 group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing text-muted-foreground"
            tabIndex={-1}
          >
            <GripVertical size={14} />
          </button>
        )}

        {hasChildren ? (
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            className="shrink-0 p-0.5 rounded hover:bg-accent"
          >
            <ChevronRight
              size={14}
              className={cn('transition-transform text-muted-foreground', expanded && 'rotate-90')}
            />
          </button>
        ) : (
          <div className="w-5 shrink-0" />
        )}

        {node.color ? (
          <div
            className="w-3.5 h-3.5 rounded-full shrink-0 border border-border"
            style={{ backgroundColor: node.color }}
          />
        ) : (
          <Icon size={14} className="text-muted-foreground shrink-0" />
        )}

        <span className="text-sm flex-1 truncate">{node.label}</span>

        <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity">
          {node.node_type}
        </span>

        {/* Add child button */}
        <button
          onClick={(e) => { e.stopPropagation(); onAddChild(node.id); }}
          className="p-1 rounded hover:bg-accent opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
          title="Add child node"
        >
          <Plus size={14} />
        </button>

        {/* Three-dot menu */}
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button
              onClick={(e) => e.stopPropagation()}
              className="p-1 rounded hover:bg-accent opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
            >
              <MoreHorizontal size={14} />
            </button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="min-w-[160px] bg-card border border-border rounded-lg shadow-lg p-1 z-50"
              sideOffset={5}
            >
              {onAnalyze && (node.folder_path || node.node_type === 'team' || node.node_type === 'project') && (
                <DropdownMenu.Item
                  className="flex items-center gap-2 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-accent/50 outline-none"
                  onClick={() => onAnalyze(node)}
                >
                  <FolderSearch size={14} className="text-muted-foreground" />
                  Analyze Folder
                </DropdownMenu.Item>
              )}
              <DropdownMenu.Item
                className="flex items-center gap-2 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-accent/50 outline-none"
                onClick={() => onMove(node)}
              >
                <Move size={14} className="text-muted-foreground" />
                Move to...
              </DropdownMenu.Item>
              <DropdownMenu.Separator className="h-px bg-border my-1" />
              <DropdownMenu.Item
                className="flex items-center gap-2 px-3 py-2 text-sm rounded-md cursor-pointer hover:bg-destructive/10 text-destructive outline-none"
                onClick={() => onDelete(node)}
              >
                <Trash2 size={14} />
                Delete
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>

      {/* Drop-after indicator line */}
      {showDropAfter && !hasChildren && (
        <div
          className="absolute left-0 right-0 h-0.5 bg-accent z-10 rounded-full"
          style={{ bottom: 0, marginLeft: `${depth * 24 + 12}px` }}
        />
      )}

      {hasChildren && expanded && (
        <div>
          {children.map(child => (
            <TreeNodeRow
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedId={selectedId}
              onSelect={onSelect}
              onAddChild={onAddChild}
              onMove={onMove}
              onDelete={onDelete}
              onAnalyze={onAnalyze}
              activeDragId={activeDragId}
              dropInfo={dropInfo}
              dragDescendantIds={dragDescendantIds}
            />
          ))}
        </div>
      )}

      {/* Drop-after indicator for nodes with expanded children (show after last child) */}
      {showDropAfter && hasChildren && expanded && (
        <div
          className="absolute left-0 right-0 h-0.5 bg-accent z-10 rounded-full"
          style={{ bottom: 0, marginLeft: `${depth * 24 + 12}px` }}
        />
      )}
    </div>
  );
}

// ─── Compact Tree Picker (for MoveDialog) ───────────────────────────

interface CompactTreePickerProps {
  node: TreeNode;
  depth: number;
  disabledIds: Set<string>;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function CompactTreePicker({ node, depth, disabledIds, selectedId, onSelect }: CompactTreePickerProps) {
  const [expanded, setExpanded] = useState(true);
  const children = node.children ?? [];
  const hasChildren = children.length > 0;
  const isDisabled = disabledIds.has(node.id);
  const isSelected = selectedId === node.id;
  const Icon = NODE_TYPE_ICONS[node.node_type] ?? FolderKanban;

  return (
    <div>
      <div
        className={cn(
          'flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors',
          isDisabled
            ? 'opacity-40 cursor-not-allowed'
            : isSelected
              ? 'bg-accent/60 cursor-pointer'
              : 'hover:bg-accent/30 cursor-pointer',
        )}
        style={{ paddingLeft: `${depth * 20 + 8}px` }}
        onClick={() => { if (!isDisabled) onSelect(node.id); }}
      >
        {hasChildren ? (
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            className="shrink-0 p-0.5 rounded hover:bg-accent"
          >
            <ChevronRight size={12} className={cn('transition-transform text-muted-foreground', expanded && 'rotate-90')} />
          </button>
        ) : (
          <div className="w-4 shrink-0" />
        )}
        <Icon size={12} className="text-muted-foreground shrink-0" />
        <span className="truncate">{node.label}</span>
      </div>
      {hasChildren && expanded && children.map(child => (
        <CompactTreePicker
          key={child.id}
          node={child}
          depth={depth + 1}
          disabledIds={disabledIds}
          selectedId={selectedId}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

// ─── AddNodeDialog ──────────────────────────────────────────────────

interface AddNodeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  parentId: string | null;
}

function AddNodeDialog({ open, onOpenChange, parentId }: AddNodeDialogProps) {
  const [name, setName] = useState('');
  const [nodeType, setNodeType] = useState<NodeType>('group');
  const [hubProjectId, setHubProjectId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const { data: unplaced = [] } = useQuery<UnplacedProject[]>({
    queryKey: ['tree-unplaced'],
    queryFn: () => apiFetch('/tree/unplaced'),
    enabled: open,
  });

  const reset = () => {
    setName('');
    setNodeType('group');
    setHubProjectId('');
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) { setError('Name is required'); return; }

    setSubmitting(true);
    setError('');
    try {
      await apiPost('/tree', {
        parent_id: parentId,
        label: name.trim(),
        node_type: nodeType,
        hub_project_id: hubProjectId || null,
      });
      queryClient.invalidateQueries({ queryKey: ['tree'] });
      queryClient.invalidateQueries({ queryKey: ['tree-unplaced'] });
      reset();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create node');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={(v) => { if (!v) reset(); onOpenChange(v); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl">
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-lg font-semibold text-foreground">
              {parentId ? 'Add Item' : 'Add Group'}
            </Dialog.Title>
            <Dialog.Close className="text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-accent/50 transition-colors">
              <X size={18} />
            </Dialog.Close>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-muted-foreground mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Engineering"
                className={inputCls}
                autoFocus
              />
            </div>

            <div>
              <label className="block text-sm text-muted-foreground mb-1">Type</label>
              <select
                value={nodeType}
                onChange={(e) => setNodeType(e.target.value as NodeType)}
                className={selectCls}
              >
                {NODE_TYPES.map(t => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                ))}
              </select>
            </div>

            {unplaced.length > 0 && (
              <div>
                <label className="block text-sm text-muted-foreground mb-1">
                  Link to Hub Project (optional)
                </label>
                <select
                  value={hubProjectId}
                  onChange={(e) => setHubProjectId(e.target.value)}
                  className={selectCls}
                >
                  <option value="">None</option>
                  {unplaced.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            )}

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="flex justify-end gap-2 pt-2">
              <Dialog.Close className="px-4 py-2 text-sm rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all">
                Cancel
              </Dialog.Close>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 text-sm rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all disabled:opacity-50"
              >
                {submitting ? 'Creating...' : 'Create'}
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ─── MoveDialog ─────────────────────────────────────────────────────

interface MoveDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  node: TreeNode | null;
  tree: TreeNode | null;
}

function MoveDialog({ open, onOpenChange, node, tree }: MoveDialogProps) {
  const [targetId, setTargetId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const queryClient = useQueryClient();

  const disabledIds = useMemo(
    () => (node ? getDescendantIds(node) : new Set<string>()),
    [node],
  );

  const handleMove = async () => {
    if (!node || !targetId) return;
    setSubmitting(true);
    setError('');
    try {
      await apiPost(`/tree/${node.id}/move`, { new_parent_id: targetId });
      queryClient.invalidateQueries({ queryKey: ['tree'] });
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to move node');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={(v) => { if (!v) { setTargetId(null); setError(''); } onOpenChange(v); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl max-h-[80vh] flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-lg font-semibold text-foreground">
              Move "{node?.label}"
            </Dialog.Title>
            <Dialog.Close className="text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-accent/50 transition-colors">
              <X size={18} />
            </Dialog.Close>
          </div>

          <p className="text-xs text-muted-foreground mb-3">Select a new parent node:</p>

          <div className="flex-1 overflow-y-auto border border-border rounded-lg p-2 min-h-0">
            {tree ? (
              <CompactTreePicker
                node={tree}
                depth={0}
                disabledIds={disabledIds}
                selectedId={targetId}
                onSelect={setTargetId}
              />
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">No tree data</p>
            )}
          </div>

          {error && <p className="text-sm text-destructive mt-2">{error}</p>}

          <div className="flex justify-end gap-2 pt-4">
            <Dialog.Close className="px-4 py-2 text-sm rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all">
              Cancel
            </Dialog.Close>
            <button
              onClick={handleMove}
              disabled={!targetId || submitting}
              className="px-4 py-2 text-sm rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all disabled:opacity-50"
            >
              {submitting ? 'Moving...' : 'Move Here'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ─── PlaceProjectsDialog ────────────────────────────────────────────

interface PlaceProjectsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  unplaced: UnplacedProject[];
  tree: TreeNode | null;
}

function PlaceProjectsDialog({ open, onOpenChange, unplaced, tree }: PlaceProjectsDialogProps) {
  const [assignments, setAssignments] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const queryClient = useQueryClient();

  const handleAssign = (projectId: string, parentId: string) => {
    setAssignments(prev => ({ ...prev, [projectId]: parentId }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      for (const project of unplaced) {
        const parentId = assignments[project.id];
        if (parentId) {
          await apiPost('/tree', {
            parent_id: parentId,
            label: project.name,
            node_type: 'project' as NodeType,
            hub_project_id: project.id,
          });
        }
      }
      queryClient.invalidateQueries({ queryKey: ['tree'] });
      queryClient.invalidateQueries({ queryKey: ['tree-unplaced'] });
      onOpenChange(false);
    } catch {
      // Error handled silently — items that failed remain unplaced
    } finally {
      setSubmitting(false);
    }
  };

  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl max-h-[80vh] flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <Dialog.Title className="text-lg font-semibold text-foreground">
              Place Unlinked Projects
            </Dialog.Title>
            <Dialog.Close className="text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-accent/50 transition-colors">
              <X size={18} />
            </Dialog.Close>
          </div>

          <div className="flex-1 overflow-y-auto min-h-0 space-y-3">
            {unplaced.map(project => (
              <div key={project.id} className="border border-border rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">{project.name}</span>
                  {assignments[project.id] && (
                    <span className="text-[10px] text-success font-medium">Assigned</span>
                  )}
                </div>
                {activeProjectId === project.id && tree ? (
                  <div className="border border-border rounded-lg p-2 max-h-48 overflow-y-auto">
                    <CompactTreePicker
                      node={tree}
                      depth={0}
                      disabledIds={new Set()}
                      selectedId={assignments[project.id] ?? null}
                      onSelect={(parentId) => {
                        handleAssign(project.id, parentId);
                        setActiveProjectId(null);
                      }}
                    />
                  </div>
                ) : (
                  <button
                    onClick={() => setActiveProjectId(project.id)}
                    className="text-xs text-accent hover:underline"
                  >
                    {assignments[project.id] ? 'Change parent' : 'Select parent node'}
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Dialog.Close className="px-4 py-2 text-sm rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-all">
              Cancel
            </Dialog.Close>
            <button
              onClick={handleSubmit}
              disabled={submitting || Object.keys(assignments).length === 0}
              className="px-4 py-2 text-sm rounded-lg bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all disabled:opacity-50"
            >
              {submitting ? 'Placing...' : 'Place Selected'}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ─── Detail Panel ───────────────────────────────────────────────────

interface DetailPanelProps {
  node: TreeNode;
  tree: TreeNode | null;
  onOpenMove: (node: TreeNode) => void;
}

// ─── Folder Picker Dialog ────────────────────────────────────────

interface FolderPickerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (path: string) => void;
  initialPath?: string;
}

interface BrowseResult {
  path: string;
  exists: boolean;
  dirs: { name: string; path: string }[];
  parent: string | null;
}

function FolderPickerDialog({ open, onOpenChange, onSelect, initialPath = '~' }: FolderPickerProps) {
  const [currentPath, setCurrentPath] = useState(initialPath);

  const { data, isLoading } = useQuery<BrowseResult>({
    queryKey: ['filesystem-browse', currentPath],
    queryFn: () => apiFetch(`/filesystem/browse?path=${encodeURIComponent(currentPath)}`),
    enabled: open,
    staleTime: 5_000,
  });

  // Reset path when dialog opens
  useMemo(() => {
    if (open) setCurrentPath(initialPath || '~');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const pathParts = (data?.path ?? '').split('/').filter(Boolean);

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg rounded-2xl border border-border bg-card shadow-2xl flex flex-col" style={{ maxHeight: '70vh' }}>
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
            <Dialog.Title className="text-sm font-semibold text-foreground">Select Folder</Dialog.Title>
            <Dialog.Close className="text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-accent/50 transition-colors">
              <X size={18} />
            </Dialog.Close>
          </div>

          {/* Breadcrumb path */}
          <div className="flex items-center gap-1 px-5 py-2 border-b border-border text-xs text-muted-foreground overflow-x-auto shrink-0">
            <button
              onClick={() => setCurrentPath('/')}
              className="hover:text-foreground transition-colors shrink-0"
            >
              /
            </button>
            {pathParts.map((part, i) => (
              <span key={i} className="flex items-center gap-1 shrink-0">
                <ChevronRight size={10} className="text-muted-foreground/50" />
                <button
                  onClick={() => setCurrentPath('/' + pathParts.slice(0, i + 1).join('/'))}
                  className="hover:text-foreground transition-colors"
                >
                  {part}
                </button>
              </span>
            ))}
          </div>

          {/* Directory listing */}
          <div className="flex-1 overflow-y-auto px-2 py-2">
            {/* Go up */}
            {data?.parent && (
              <button
                onClick={() => setCurrentPath(data.parent!)}
                className="w-full flex items-center gap-3 px-3 py-2 text-sm rounded-lg hover:bg-accent/30 transition-colors text-muted-foreground"
              >
                <ArrowUp size={14} />
                <span>..</span>
              </button>
            )}

            {isLoading ? (
              <div className="space-y-1 p-2">
                {[1, 2, 3, 4, 5].map(i => (
                  <div key={i} className="h-8 bg-muted/50 rounded animate-pulse" />
                ))}
              </div>
            ) : data?.dirs.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-8">No subdirectories</p>
            ) : (
              data?.dirs.map(dir => (
                <button
                  key={dir.path}
                  onClick={() => setCurrentPath(dir.path)}
                  className="w-full flex items-center gap-3 px-3 py-2 text-sm rounded-lg hover:bg-accent/30 transition-colors text-foreground"
                >
                  <Folder size={14} className="text-muted-foreground shrink-0" />
                  <span className="truncate">{dir.name}</span>
                </button>
              ))
            )}
          </div>

          {/* Footer: current path + select button */}
          <div className="flex items-center gap-3 px-5 py-3 border-t border-border shrink-0">
            <div className="flex-1 text-xs text-muted-foreground font-mono truncate">
              {data?.path ?? currentPath}
            </div>
            <button
              onClick={() => onSelect(data?.path ?? currentPath)}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
            >
              <Check size={14} />
              Select This Folder
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ─── Detail Panel ────────────────────────────────────────────────

function DetailPanel({ node, tree, onOpenMove }: DetailPanelProps) {
  const queryClient = useQueryClient();
  const [label, setLabel] = useState(node.label);
  const [nodeType, setNodeType] = useState<NodeType>(node.node_type);
  const [color, setColor] = useState<string | null>(node.color);
  const [folderPath, setFolderPath] = useState(node.folder_path ?? '');
  const [githubRepo, setGithubRepo] = useState(node.github_repo ?? '');
  const [jiraKey, setJiraKey] = useState(node.jira_key ?? '');
  const [confluenceSpace, setConfluenceSpace] = useState(node.confluence_space ?? '');
  const [saving, setSaving] = useState(false);
  const [folderPickerOpen, setFolderPickerOpen] = useState(false);
  const [analyzeDialogOpen, setAnalyzeDialogOpen] = useState(false);

  // Sync local state when selected node changes
  const nodeId = node.id;
  useState(() => {
    setLabel(node.label);
    setNodeType(node.node_type);
    setColor(node.color);
    setFolderPath(node.folder_path ?? '');
    setGithubRepo(node.github_repo ?? '');
    setJiraKey(node.jira_key ?? '');
    setConfluenceSpace(node.confluence_space ?? '');
  });

  // Reset state when node changes
  useMemo(() => {
    setLabel(node.label);
    setNodeType(node.node_type);
    setColor(node.color);
    setFolderPath(node.folder_path ?? '');
    setGithubRepo(node.github_repo ?? '');
    setJiraKey(node.jira_key ?? '');
    setConfluenceSpace(node.confluence_space ?? '');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeId]);

  const childrenCount = node.children?.length ?? 0;
  const hasChildren = childrenCount > 0;

  // Fetch folder contents when folder_path is set
  const { data: folderData } = useQuery({
    queryKey: ['tree-folder', node.id, node.folder_path],
    queryFn: () => apiFetch<{ path: string; exists: boolean; files: { name: string; is_dir: boolean; size: number | null; modified: number }[] }>(`/tree/${node.id}/folder`),
    enabled: !!node.folder_path,
    staleTime: 10_000,
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      setSaving(true);
      await apiPatch(`/tree/${node.id}`, {
        label: label.trim(),
        node_type: nodeType,
        color,
        folder_path: folderPath || null,
        github_repo: githubRepo || null,
        jira_key: jiraKey || null,
        confluence_space: confluenceSpace || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tree'] });
    },
    onSettled: () => setSaving(false),
  });

  const deleteMutation = useMutation({
    mutationFn: () => apiDelete(`/tree/${node.id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tree'] });
      queryClient.invalidateQueries({ queryKey: ['tree-unplaced'] });
    },
  });

  const isDirty = label !== node.label || nodeType !== node.node_type || color !== node.color
    || folderPath !== (node.folder_path ?? '') || githubRepo !== (node.github_repo ?? '')
    || jiraKey !== (node.jira_key ?? '') || confluenceSpace !== (node.confluence_space ?? '');

  return (
    <div className="bg-card border border-border rounded-xl p-5 space-y-5">
      <h3 className="text-sm font-semibold text-foreground">Node Details</h3>

      {/* Label */}
      <div>
        <label className="block text-xs text-muted-foreground mb-1">Label</label>
        <input
          type="text"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          className={inputCls}
        />
      </div>

      {/* Type */}
      <div>
        <label className="block text-xs text-muted-foreground mb-1">Type</label>
        <select
          value={nodeType}
          onChange={(e) => setNodeType(e.target.value as NodeType)}
          className={selectCls}
        >
          {NODE_TYPES.map(t => (
            <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
          ))}
        </select>
      </div>

      {/* Color */}
      <div>
        <label className="block text-xs text-muted-foreground mb-1">Color</label>
        <div className="flex items-center gap-2 flex-wrap">
          {PRESET_COLORS.map((c, i) => (
            <button
              key={i}
              onClick={() => setColor(c)}
              className={cn(
                'w-6 h-6 rounded-full border-2 transition-all',
                color === c ? 'border-foreground scale-110' : 'border-border hover:scale-105',
                !c && 'bg-muted',
              )}
              style={c ? { backgroundColor: c } : undefined}
              title={c ?? 'No color'}
            />
          ))}
        </div>
      </div>

      {/* Folder path */}
      <div>
        <label className="block text-xs text-muted-foreground mb-1">Project Folder</label>
        {folderPath ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-card border border-border rounded-lg px-3 py-2 text-xs text-foreground font-mono truncate">
                {folderPath}
              </div>
              <button
                onClick={() => setFolderPickerOpen(true)}
                className="px-2 py-2 text-xs rounded-lg border border-border hover:bg-accent/30 transition-colors text-muted-foreground"
                title="Change folder"
              >
                <Folder size={14} />
              </button>
              <button
                onClick={() => setFolderPath('')}
                className="px-2 py-2 text-xs rounded-lg border border-border hover:bg-destructive/10 transition-colors text-muted-foreground"
                title="Remove folder"
              >
                <X size={14} />
              </button>
            </div>
            {folderData?.exists && folderData.files.length > 0 && (
              <div className="border border-border rounded-lg max-h-36 overflow-y-auto">
                {folderData.files.map((f) => (
                  <div key={f.name} className="flex items-center gap-2 px-3 py-1.5 text-xs text-muted-foreground hover:bg-accent/30">
                    <span>{f.is_dir ? '📁' : '📄'}</span>
                    <span className="truncate text-foreground">{f.name}</span>
                    {f.size != null && <span className="ml-auto tabular-nums">{(f.size / 1024).toFixed(0)}K</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={() => setFolderPickerOpen(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-border rounded-xl text-xs text-muted-foreground hover:border-accent hover:text-foreground transition-colors"
          >
            <FolderOpen size={16} />
            Browse and select a folder
          </button>
        )}
      </div>

      <FolderPickerDialog
        open={folderPickerOpen}
        onOpenChange={setFolderPickerOpen}
        onSelect={(path) => { setFolderPath(path); setFolderPickerOpen(false); }}
        initialPath={folderPath || '~'}
      />

      {/* Analyze Folder button */}
      {(node.folder_path || folderPath) && (node.node_type === 'team' || node.node_type === 'project') && (
        <div>
          <button
            onClick={() => setAnalyzeDialogOpen(true)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium bg-accent/20 text-accent rounded-lg hover:bg-accent/30 transition-colors border border-accent/30"
          >
            <FolderSearch size={14} />
            Analyze Folder
          </button>
        </div>
      )}

      {/* Analysis Results */}
      {(node.node_type === 'team' || node.node_type === 'project') && (
        <div>
          <label className="block text-xs text-muted-foreground mb-2">Analysis History</label>
          <AnalysisResults nodeId={node.id} />
        </div>
      )}

      <AnalyzeFolderDialog
        open={analyzeDialogOpen}
        onOpenChange={setAnalyzeDialogOpen}
        nodeId={node.id}
        nodeFolderPath={node.folder_path ?? (folderPath || null)}
        nodeLabel={node.label}
      />

      {/* GitHub Repo */}
      <div>
        <label className="block text-xs text-muted-foreground mb-1">GitHub Repo</label>
        <input
          type="text"
          value={githubRepo}
          onChange={(e) => setGithubRepo(e.target.value)}
          placeholder="org/repo-name"
          className={inputCls}
        />
      </div>

      {/* Jira & Confluence */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-muted-foreground mb-1">Jira Key</label>
          <input
            type="text"
            value={jiraKey}
            onChange={(e) => setJiraKey(e.target.value)}
            placeholder="PROJ"
            className={inputCls}
          />
        </div>
        <div>
          <label className="block text-xs text-muted-foreground mb-1">Confluence Space</label>
          <input
            type="text"
            value={confluenceSpace}
            onChange={(e) => setConfluenceSpace(e.target.value)}
            placeholder="SPACE"
            className={inputCls}
          />
        </div>
      </div>

      {/* Hub project link */}
      {node.hub_project_id && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Link2 size={12} />
          <span>Linked to hub project: <span className="font-medium text-foreground">{node.hub_project_id}</span></span>
        </div>
      )}

      {/* Children count */}
      <div className="text-xs text-muted-foreground">
        {childrenCount} {childrenCount === 1 ? 'child' : 'children'}
      </div>

      {/* Save */}
      {isDirty && (
        <button
          onClick={() => saveMutation.mutate()}
          disabled={saving || !label.trim()}
          className="w-full px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      )}

      {/* Action buttons */}
      <div className="flex gap-2 pt-2 border-t border-border">
        <button
          onClick={() => onOpenMove(node)}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border border-border hover:bg-accent/30 transition-colors"
        >
          <Move size={12} />
          Move to...
        </button>
        {!hasChildren && (
          <button
            onClick={() => {
              if (window.confirm(`Delete "${node.label}"? This cannot be undone.`)) {
                deleteMutation.mutate();
              }
            }}
            disabled={deleteMutation.isPending}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-50"
          >
            <Trash2 size={12} />
            Delete
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Main TreePage ──────────────────────────────────────────────────

export default function TreePage() {
  const { nodeId: routeNodeId } = useParams<{ nodeId?: string }>();
  const queryClient = useQueryClient();

  // State
  const [selectedId, setSelectedId] = useState<string | null>(routeNodeId ?? null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [addParentId, setAddParentId] = useState<string | null>(null);
  const [moveDialogOpen, setMoveDialogOpen] = useState(false);
  const [moveNode, setMoveNode] = useState<TreeNode | null>(null);
  const [placeDialogOpen, setPlaceDialogOpen] = useState(false);
  const [analyzeNode, setAnalyzeNode] = useState<TreeNode | null>(null);

  // Drag-and-drop state
  const [activeDragId, setActiveDragId] = useState<string | null>(null);
  const [activeDragNode, setActiveDragNode] = useState<TreeNode | null>(null);
  const [dropInfo, setDropInfo] = useState<DropInfo | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  );

  // Queries
  const { data: tree = null, isLoading } = useQuery<TreeNode | null>({
    queryKey: ['tree'],
    queryFn: async () => {
      const res = await fetch('/api/tree');
      if (!res.ok) return null;
      const data = await res.json();
      // API returns array of root nodes — take the first one
      if (Array.isArray(data)) return data[0] ?? null;
      return data;
    },
    staleTime: 30_000,
  });

  const { data: unplaced = [] } = useQuery<UnplacedProject[]>({
    queryKey: ['tree-unplaced'],
    queryFn: () => apiFetch('/tree/unplaced'),
  });

  // Derived
  const nodeMap = useMemo(() => {
    if (!tree) return new Map<string, TreeNode>();
    const map = new Map<string, TreeNode>();
    function walk(n: TreeNode) {
      map.set(n.id, n);
      n.children?.forEach(walk);
    }
    walk(tree);
    return map;
  }, [tree]);

  const selectedNode = selectedId ? nodeMap.get(selectedId) ?? null : null;

  // Handlers
  const handleAddChild = useCallback((parentId: string) => {
    setAddParentId(parentId);
    setAddDialogOpen(true);
  }, []);

  const handleAddRoot = useCallback(() => {
    setAddParentId('root');
    setAddDialogOpen(true);
  }, []);

  const handleMove = useCallback((node: TreeNode) => {
    setMoveNode(node);
    setMoveDialogOpen(true);
  }, []);

  const handleAnalyze = useCallback((node: TreeNode) => {
    setAnalyzeNode(node);
  }, []);

  const handleDelete = useCallback((node: TreeNode) => {
    const children = node.children?.length ?? 0;
    if (children > 0) {
      window.alert('Cannot delete a node with children. Remove children first.');
      return;
    }
    if (window.confirm(`Delete "${node.label}"? This cannot be undone.`)) {
      void apiDelete(`/tree/${node.id}`).then(() => {
        if (selectedId === node.id) setSelectedId(null);
        queryClient.invalidateQueries({ queryKey: ['tree'] });
        queryClient.invalidateQueries({ queryKey: ['tree-unplaced'] });
      });
    }
  }, [queryClient, selectedId]);

  // ─── Drag & drop ───────────────────────────────────────────────────

  /** Descendant IDs of the dragged node — these are invalid drop targets */
  const dragDescendantIds = useMemo(() => {
    if (!activeDragNode) return new Set<string>();
    return getDescendantIds(activeDragNode);
  }, [activeDragNode]);

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const dragData = event.active.data.current as { node: TreeNode } | undefined;
    if (dragData?.node) {
      setActiveDragId(dragData.node.id);
      setActiveDragNode(dragData.node);
    }
  }, []);

  const handleDragOver = useCallback((event: DragOverEvent) => {
    const overData = event.over?.data.current as { node: TreeNode } | undefined;
    if (!overData?.node || !activeDragNode) {
      setDropInfo(null);
      return;
    }

    const targetNode = overData.node;
    const targetId = targetNode.id;

    // Can't drop onto self or descendants
    if (dragDescendantIds.has(targetId)) {
      setDropInfo(null);
      return;
    }

    // Determine drop position based on pointer position within the drop target
    const overRect = event.over?.rect;
    if (!overRect || !event.delta) {
      setDropInfo({ targetId, position: 'on' });
      return;
    }

    // Use the collision coordinates to determine position within the target
    // The active.rect gives us the pointer position relative to the droppable
    const pointerY = (event.activatorEvent as PointerEvent)?.clientY;
    const deltaY = event.delta.y;
    if (pointerY === undefined) {
      setDropInfo({ targetId, position: 'on' });
      return;
    }

    const currentY = pointerY + deltaY;
    const top = overRect.top;
    const height = overRect.height;
    const relativeY = currentY - top;
    const ratio = relativeY / height;

    // project type nodes can't have children, so only allow before/after
    const isLeafType = targetNode.node_type === 'project';

    let position: DropPosition;
    if (ratio < 0.25) {
      position = 'before';
    } else if (ratio > 0.75 || isLeafType) {
      position = ratio < 0.5 && isLeafType ? 'before' : 'after';
    } else {
      position = 'on';
    }

    setDropInfo({ targetId, position });
  }, [activeDragNode, dragDescendantIds]);

  const handleDragEnd = useCallback(async (event: DragEndEvent) => {
    const dragData = event.active.data.current as { node: TreeNode } | undefined;
    const overData = event.over?.data.current as { node: TreeNode } | undefined;

    const currentDropInfo = dropInfo;

    // Reset drag state
    setActiveDragId(null);
    setActiveDragNode(null);
    setDropInfo(null);

    if (!dragData?.node || !overData?.node || !currentDropInfo || !tree) return;

    const draggedNode = dragData.node;
    const targetNode = overData.node;

    // Can't drop onto self or descendants
    if (getDescendantIds(draggedNode).has(targetNode.id)) return;

    try {
      if (currentDropInfo.position === 'on') {
        // Reparent: move dragged node into target as last child
        const targetChildren = targetNode.children ?? [];
        const newSortOrder = targetChildren.length > 0
          ? Math.max(...targetChildren.map(c => c.sort_order)) + 1
          : 0;
        await apiPost(`/tree/${draggedNode.id}/move`, {
          new_parent_id: targetNode.id,
          sort_order: newSortOrder,
        });
      } else {
        // Reorder: insert before or after target among its siblings
        const targetParent = findParent(tree, targetNode.id);
        if (!targetParent) return;

        const siblings = [...(targetParent.children ?? [])];
        // Remove the dragged node from siblings if it's in the same parent
        const draggedParent = findParent(tree, draggedNode.id);
        const sameParent = draggedParent?.id === targetParent.id;

        let filteredSiblings = sameParent
          ? siblings.filter(s => s.id !== draggedNode.id)
          : siblings;

        // Find target index in filtered siblings
        const targetIdx = filteredSiblings.findIndex(s => s.id === targetNode.id);
        if (targetIdx === -1) return;

        const insertIdx = currentDropInfo.position === 'before' ? targetIdx : targetIdx + 1;

        // If different parent, first move to that parent
        if (!sameParent) {
          await apiPost(`/tree/${draggedNode.id}/move`, {
            new_parent_id: targetParent.id,
            sort_order: insertIdx,
          });
          // Build new order including the moved node
          filteredSiblings = [
            ...filteredSiblings.slice(0, insertIdx),
            draggedNode,
            ...filteredSiblings.slice(insertIdx),
          ];
        } else {
          // Same parent: just reorder
          filteredSiblings = [
            ...filteredSiblings.slice(0, insertIdx),
            draggedNode,
            ...filteredSiblings.slice(insertIdx),
          ];
        }

        // Send reorder request
        const reorderPayload = filteredSiblings.map((s, i) => ({
          id: s.id,
          sort_order: i,
        }));
        await apiPost('/tree/reorder', reorderPayload);
      }

      queryClient.invalidateQueries({ queryKey: ['tree'] });
    } catch (err) {
      console.error('Drag-and-drop failed:', err);
    }
  }, [dropInfo, tree, queryClient]);

  const handleDragCancel = useCallback(() => {
    setActiveDragId(null);
    setActiveDragNode(null);
    setDropInfo(null);
  }, []);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-foreground">My Portfolio</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Build and manage your hierarchy tree
          </p>
        </div>
        <button
          onClick={handleAddRoot}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity"
        >
          <Plus size={14} />
          Add Group
        </button>
      </div>

      {/* Unplaced projects banner */}
      {unplaced.length > 0 && (
        <div className="flex items-center gap-3 px-4 py-3 bg-warning/10 border border-warning/30 rounded-xl text-sm">
          <AlertTriangle size={16} className="text-warning shrink-0" />
          <span className="flex-1 text-foreground">
            {unplaced.length} hub project{unplaced.length !== 1 ? 's' : ''} not in your tree:{' '}
            {unplaced.map((p, i) => (
              <span key={p.id}>
                {i > 0 && ', '}
                <span className="font-medium">[{p.name}]</span>
              </span>
            ))}
          </span>
          <button
            onClick={() => setPlaceDialogOpen(true)}
            className="shrink-0 px-3 py-1 text-xs font-medium bg-warning/20 text-warning rounded-md hover:bg-warning/30 transition-colors"
          >
            Place them
          </button>
        </div>
      )}

      {/* Main content: two-column layout */}
      {isLoading ? (
        <div className="grid grid-cols-5 gap-4">
          <div className="col-span-3 space-y-2">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-10 bg-muted/50 rounded-md animate-pulse" />
            ))}
          </div>
          <div className="col-span-2">
            <div className="h-64 bg-muted/50 rounded-xl animate-pulse" />
          </div>
        </div>
      ) : !tree ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <FolderTree size={40} className="mb-3 opacity-30" />
          <p className="text-sm font-medium">No tree yet</p>
          <p className="text-xs mt-1">Add a root node to start building your org hierarchy.</p>
        </div>
      ) : (
        <DndContext
          sensors={sensors}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
        >
        <div className="grid grid-cols-5 gap-4">
          {/* Left panel: Tree view (60%) */}
          <div className="col-span-3 border border-border rounded-xl overflow-hidden">
            <div className="p-1">
              <TreeNodeRow
                node={tree}
                depth={0}
                selectedId={selectedId}
                onSelect={setSelectedId}
                onAddChild={handleAddChild}
                onMove={handleMove}
                onDelete={handleDelete}
                onAnalyze={handleAnalyze}
                activeDragId={activeDragId}
                dropInfo={dropInfo}
                dragDescendantIds={dragDescendantIds}
                isRoot
              />
            </div>
          </div>

          {/* Right panel: Detail (40%) */}
          <div className="col-span-2">
            {selectedNode ? (
              <DetailPanel
                node={selectedNode}
                tree={tree}
                onOpenMove={handleMove}
              />
            ) : (
              <div className="bg-card border border-border rounded-xl p-5 flex flex-col items-center justify-center text-muted-foreground py-12">
                <FolderTree size={32} className="mb-2 opacity-30" />
                <p className="text-sm font-medium">Select a node</p>
                <p className="text-xs mt-1">Click on a node in the tree to see its details.</p>
              </div>
            )}
          </div>
        </div>

        {/* Drag overlay ghost */}
        <DragOverlay dropAnimation={null}>
          {activeDragNode ? (
            <div
              className={cn(
                'flex items-center gap-2 px-3 py-2 rounded-md bg-card border border-border shadow-lg',
                dropInfo === null || (dropInfo && dragDescendantIds.has(dropInfo.targetId))
                  ? 'opacity-30'
                  : 'opacity-80',
              )}
            >
              {(() => {
                const DragIcon = NODE_TYPE_ICONS[activeDragNode.node_type] ?? FolderKanban;
                return activeDragNode.color ? (
                  <div
                    className="w-3.5 h-3.5 rounded-full shrink-0 border border-border"
                    style={{ backgroundColor: activeDragNode.color }}
                  />
                ) : (
                  <DragIcon size={14} className="text-muted-foreground shrink-0" />
                );
              })()}
              <span className="text-sm truncate">{activeDragNode.label}</span>
            </div>
          ) : null}
        </DragOverlay>
        </DndContext>
      )}

      {/* Dialogs */}
      <AddNodeDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        parentId={addParentId}
      />
      <MoveDialog
        open={moveDialogOpen}
        onOpenChange={setMoveDialogOpen}
        node={moveNode}
        tree={tree}
      />
      <PlaceProjectsDialog
        open={placeDialogOpen}
        onOpenChange={setPlaceDialogOpen}
        unplaced={unplaced}
        tree={tree}
      />
      {analyzeNode && (
        <AnalyzeFolderDialog
          open={!!analyzeNode}
          onOpenChange={(open) => { if (!open) setAnalyzeNode(null); }}
          nodeId={analyzeNode.id}
          nodeFolderPath={analyzeNode.folder_path ?? null}
          nodeLabel={analyzeNode.label}
        />
      )}
    </div>
  );
}
