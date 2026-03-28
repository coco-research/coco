import { useState, useCallback } from 'react';
import { TreeNodeRow, type TreeNode } from './TreeNodeRow';

interface TreeViewProps {
  tree: TreeNode | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
  compact?: boolean;
  onAdd?: (parentId: string) => void;
  onRename?: (id: string) => void;
  onDelete?: (id: string) => void;
  onMove?: (id: string) => void;
}

export function TreeView({
  tree, selectedId, onSelect, compact,
  onAdd, onRename, onDelete, onMove,
}: TreeViewProps) {
  const [expanded, setExpanded] = useState<Set<string>>(() => {
    // Auto-expand the root and first level
    const initial = new Set<string>();
    if (tree) {
      initial.add(tree.id);
      tree.children?.forEach((c) => initial.add(c.id));
    }
    return initial;
  });

  const toggle = useCallback((id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  if (!tree) {
    return (
      <div className="px-3 py-4 text-sm text-muted-foreground">
        No tree data
      </div>
    );
  }

  function renderNode(node: TreeNode) {
    const isExpanded = expanded.has(node.id);
    const hasChildren = node.children && node.children.length > 0;

    return (
      <div key={node.id}>
        <TreeNodeRow
          node={node}
          selectedId={selectedId}
          expanded={isExpanded}
          onToggle={() => toggle(node.id)}
          onSelect={onSelect}
          compact={compact}
          onAdd={compact ? undefined : onAdd}
          onRename={compact ? undefined : onRename}
          onDelete={compact ? undefined : onDelete}
          onMove={compact ? undefined : onMove}
        />
        {hasChildren && isExpanded && (
          <div className="overflow-hidden transition-all">
            {node.children!
              .sort((a, b) => a.sort_order - b.sort_order)
              .map(renderNode)}
          </div>
        )}
      </div>
    );
  }

  return (
    <div role="tree" className="space-y-0.5">
      {renderNode(tree)}
    </div>
  );
}
