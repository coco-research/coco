import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';
import { useQuery } from '@tanstack/react-query';

// ─── Types ──────────────────────────────────────────────────────────

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
  folder_path: string | null;
  github_repo: string | null;
  jira_key: string | null;
  confluence_space: string | null;
  children?: TreeNode[];
}

interface ScopeContextValue {
  tree: TreeNode | null;
  loading: boolean;
  selectedNodeId: string | null;
  selectedNode: TreeNode | null;
  setSelectedNodeId: (id: string | null) => void;
  /** All hub_project_ids under the selected subtree */
  scopeProjectIds: string[];
  /** Ancestor path for breadcrumbs */
  ancestors: TreeNode[];
}

// ─── Helpers ────────────────────────────────────────────────────────

/** Build a flat map of id -> node from the tree */
function buildNodeMap(node: TreeNode | null): Map<string, TreeNode> {
  const map = new Map<string, TreeNode>();
  if (!node) return map;

  function walk(n: TreeNode) {
    map.set(n.id, n);
    n.children?.forEach(walk);
  }
  walk(node);
  return map;
}

/** Collect all hub_project_ids in a subtree (including the node itself) */
function collectProjectIds(node: TreeNode | null): string[] {
  if (!node) return [];
  const ids: string[] = [];

  function walk(n: TreeNode) {
    if (n.hub_project_id) ids.push(n.hub_project_id);
    n.children?.forEach(walk);
  }
  walk(node);
  return ids;
}

/** Parse the path string and find ancestor nodes from the map */
function resolveAncestors(node: TreeNode | null, nodeMap: Map<string, TreeNode>): TreeNode[] {
  if (!node || !node.path) return [];

  // path is like "/root-id/parent-id/self-id" — ancestors are all except the last segment
  const segments = node.path.split('/').filter(Boolean);
  // Remove the node itself (last segment)
  segments.pop();

  const ancestors: TreeNode[] = [];
  for (const seg of segments) {
    const ancestor = nodeMap.get(seg);
    if (ancestor) ancestors.push(ancestor);
  }
  return ancestors;
}

// ─── Context ────────────────────────────────────────────────────────

const ScopeContext = createContext<ScopeContextValue | null>(null);
const STORAGE_KEY = 'coco.selectedNodeId';

export function ScopeProvider({ children }: { children: ReactNode }) {
  const [selectedNodeId, setSelectedNodeIdState] = useState<string | null>(
    () => localStorage.getItem(STORAGE_KEY),
  );

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

  const setSelectedNodeId = useCallback((id: string | null) => {
    setSelectedNodeIdState(id);
    if (id) {
      localStorage.setItem(STORAGE_KEY, id);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const nodeMap = useMemo(() => buildNodeMap(tree), [tree]);

  const selectedNode = useMemo(
    () => (selectedNodeId ? nodeMap.get(selectedNodeId) ?? null : null),
    [nodeMap, selectedNodeId],
  );

  const scopeProjectIds = useMemo(
    () => collectProjectIds(selectedNode),
    [selectedNode],
  );

  const ancestors = useMemo(
    () => resolveAncestors(selectedNode, nodeMap),
    [selectedNode, nodeMap],
  );

  const value = useMemo<ScopeContextValue>(
    () => ({
      tree,
      loading: isLoading,
      selectedNodeId,
      selectedNode,
      setSelectedNodeId,
      scopeProjectIds,
      ancestors,
    }),
    [tree, isLoading, selectedNodeId, selectedNode, setSelectedNodeId, scopeProjectIds, ancestors],
  );

  return (
    <ScopeContext.Provider value={value}>
      {children}
    </ScopeContext.Provider>
  );
}

export function useScope() {
  const ctx = useContext(ScopeContext);
  if (!ctx) throw new Error('useScope must be used within ScopeProvider');
  return ctx;
}
