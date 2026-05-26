import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  type Node,
  type Edge,
  type NodeMouseHandler,
  useReactFlow,
  ReactFlowProvider,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { graphlib, layout as dagreLayout } from '@dagrejs/dagre';
import { Loader2, LayoutGrid, Maximize2 } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { cn } from '../lib/utils';
import { EntityNode, type EntityNodeData } from '../components/canvas/EntityNode';
import { ArticleNode } from '../components/canvas/ArticleNode';
import { ClusterNode } from '../components/canvas/ClusterNode';
import { DetailPanel } from '../components/canvas/DetailPanel';
import {
  CanvasContextMenu,
  type ContextMenuState,
} from '../components/canvas/CanvasContextMenu';
import { EmptyState } from '../components/shared/EmptyState';
import { ErrorState } from '../components/shared/ErrorState';
import { Waypoints } from 'lucide-react';

// ── Types ────────────────────────────────────────────────────────────────

interface GraphNode {
  id: string;
  label: string;
  meta_type: string;
  community?: number;
  degree: number;
  meta_project?: string;
  meta_projects?: string;
}

interface GraphNeighbor {
  id: string;
  label: string;
  meta_type: string;
  relation: string;
  confidence: string;
}

interface NodeDetail extends GraphNode {
  neighbors: GraphNeighbor[];
  source_file?: string;
  [key: string]: unknown;
}

interface GodNodesResponse {
  items: GraphNode[];
}

// ── Custom node types ────────────────────────────────────────────────────

const nodeTypes = {
  entity: EntityNode,
  article: ArticleNode,
  cluster: ClusterNode,
};

// ── Dagre layout helper ──────────────────────────────────────────────────

const NODE_WIDTH = 160;
const NODE_HEIGHT = 60;

function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  direction: 'TB' | 'LR' = 'TB',
): { nodes: Node[]; edges: Edge[] } {
  const g = new graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: direction,
    nodesep: 50,
    ranksep: 80,
    edgesep: 20,
    marginx: 20,
    marginy: 20,
  });

  for (const node of nodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }
  for (const edge of edges) {
    g.setEdge(edge.source, edge.target);
  }

  dagreLayout(g);

  const layoutedNodes = nodes.map((node) => {
    const pos = g.node(node.id);
    return {
      ...node,
      position: {
        x: pos.x - NODE_WIDTH / 2,
        y: pos.y - NODE_HEIGHT / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

// ── Inner canvas (needs ReactFlowProvider wrapper) ───────────────────────

function CanvasInner() {
  const navigate = useNavigate();
  const { fitView } = useReactFlow();

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);
  const [pinnedNodes, setPinnedNodes] = useState<Set<string>>(new Set());
  const expandedNodesRef = useRef<Set<string>>(new Set());
  const edgesRef = useRef<Edge[]>(edges);
  edgesRef.current = edges; // keep ref in sync for reading inside setNodes callbacks

  // ── Fetch initial god nodes ──────────────────────────────────────────
  const { data: godNodes, isLoading: godLoading, isError: godError, error: godErr, refetch: godRefetch } = useQuery({
    queryKey: ['canvas-god-nodes'],
    queryFn: () => apiFetch<GodNodesResponse>('/graph/god-nodes?top_n=30'),
  });

  // ── Fetch selected node detail ───────────────────────────────────────
  const { data: nodeDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['canvas-node-detail', selectedNodeId],
    queryFn: () =>
      apiFetch<NodeDetail>(
        `/graph/node/${encodeURIComponent(selectedNodeId!)}`,
      ),
    enabled: !!selectedNodeId,
  });

  // ── Initial layout from god nodes ────────────────────────────────────
  useEffect(() => {
    if (!godNodes?.items || godNodes.items.length === 0) return;

    const initialNodes: Node[] = godNodes.items.map((n) => ({
      id: n.id,
      type: 'entity',
      position: { x: 0, y: 0 },
      data: {
        label: n.label?.replace(/^\[.*?\]\s*/, '') || n.id,
        entityType: n.meta_type || 'unknown',
        gid: n.id,
        articleCount: n.degree,
        confidence: 0,
      } satisfies EntityNodeData,
    }));

    // No edges from god-nodes, just layout the nodes
    const { nodes: layouted } = getLayoutedElements(initialNodes, [], 'TB');
    setNodes(layouted);
    setEdges([]);

    // Fit view after layout settles
    requestAnimationFrame(() => {
      setTimeout(() => fitView({ padding: 0.2, duration: 400 }), 100);
    });
  }, [godNodes, setNodes, setEdges, fitView]);

  // ── Expand node neighbors ────────────────────────────────────────────
  const expandNode = useCallback(
    async (nodeId: string) => {
      if (expandedNodesRef.current.has(nodeId)) return;
      expandedNodesRef.current.add(nodeId);

      try {
        const detail = await apiFetch<NodeDetail>(
          `/graph/node/${encodeURIComponent(nodeId)}`,
        );

        // Compute new state outside callbacks to avoid nested state updater anti-pattern
        setNodes((prevNodes) => {
          const currentEdges = edgesRef.current;
          const existingIds = new Set(prevNodes.map((n) => n.id));
          const existingEdgeIds = new Set(currentEdges.map((e) => e.id));

          const newNodes: Node[] = [];
          const newEdges: Edge[] = [];

          for (const neighbor of detail.neighbors) {
            if (!existingIds.has(neighbor.id)) {
              existingIds.add(neighbor.id);
              newNodes.push({
                id: neighbor.id,
                type: 'entity',
                position: { x: 0, y: 0 },
                data: {
                  label:
                    neighbor.label?.replace(/^\[.*?\]\s*/, '') || neighbor.id,
                  entityType: neighbor.meta_type || 'unknown',
                  gid: neighbor.id,
                  articleCount: 0,
                  confidence: parseFloat(neighbor.confidence) || 0,
                } satisfies EntityNodeData,
              });
            }

            const edgeId = `${nodeId}--${neighbor.id}`;
            const reverseEdgeId = `${neighbor.id}--${nodeId}`;
            if (
              !existingEdgeIds.has(edgeId) &&
              !existingEdgeIds.has(reverseEdgeId)
            ) {
              existingEdgeIds.add(edgeId);
              newEdges.push({
                id: edgeId,
                source: nodeId,
                target: neighbor.id,
                label: neighbor.relation,
                type: 'default',
                style: { stroke: '#475569', strokeWidth: 1 },
                labelStyle: {
                  fill: '#94a3b8',
                  fontSize: 9,
                  fontWeight: 500,
                },
                labelBgStyle: {
                  fill: '#0f172a',
                  fillOpacity: 0.8,
                },
                labelBgPadding: [4, 2] as [number, number],
                labelBgBorderRadius: 3,
              });
            }
          }

          if (newNodes.length === 0 && newEdges.length === 0) return prevNodes;

          const allNodes = [...prevNodes, ...newNodes];
          const allEdges = [...currentEdges, ...newEdges];

          const { nodes: layouted, edges: layoutedEdges } =
            getLayoutedElements(allNodes, allEdges, 'TB');

          const finalNodes = layouted.map((ln) => {
            if (pinnedNodes.has(ln.id)) {
              const original = prevNodes.find((pn) => pn.id === ln.id);
              if (original) return { ...ln, position: original.position };
            }
            return ln;
          });

          // Set edges separately (not nested)
          setEdges(layoutedEdges);
          setTimeout(() => fitView({ padding: 0.15, duration: 300 }), 50);

          return finalNodes;
        });
      } catch {
        expandedNodesRef.current.delete(nodeId);
      }
    },
    [setNodes, setEdges, fitView, pinnedNodes],
  );

  // ── Re-layout button ─────────────────────────────────────────────────
  const handleRelayout = useCallback(() => {
    setNodes((prevNodes) => {
      const currentEdges = edgesRef.current;
      const { nodes: layouted, edges: layoutedEdges } = getLayoutedElements(
        prevNodes,
        currentEdges,
        'TB',
      );
      setEdges(layoutedEdges);
      setTimeout(() => fitView({ padding: 0.15, duration: 400 }), 50);
      return layouted;
    });
  }, [setNodes, setEdges, fitView]);

  // ── Node click handler ───────────────────────────────────────────────
  const onNodeClick: NodeMouseHandler = useCallback((_event, node) => {
    setSelectedNodeId(node.id);
    setContextMenu(null);
  }, []);

  // ── Node double-click → expand ───────────────────────────────────────
  const onNodeDoubleClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      expandNode(node.id);
    },
    [expandNode],
  );

  // ── Right-click → context menu ───────────────────────────────────────
  const onNodeContextMenu: NodeMouseHandler = useCallback((event, node) => {
    event.preventDefault();
    setContextMenu({
      nodeId: node.id,
      nodeType: node.type || 'entity',
      x: event.clientX,
      y: event.clientY,
    });
  }, []);

  // ── Pane click → deselect ────────────────────────────────────────────
  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
    setContextMenu(null);
  }, []);

  // ── Context menu actions ─────────────────────────────────────────────
  const handleExpandNeighbors = useCallback(
    (nodeId: string) => {
      expandNode(nodeId);
    },
    [expandNode],
  );

  const handleOpenArticle = useCallback(
    (nodeId: string) => {
      // Find the node label for search query
      const node = nodes.find((n) => n.id === nodeId);
      const label = (node?.data as EntityNodeData)?.label ?? nodeId;
      navigate(
        `/knowledge?tab=wiki&q=${encodeURIComponent(label)}`,
      );
    },
    [nodes, navigate],
  );

  const handleRemoveFromCanvas = useCallback(
    (nodeId: string) => {
      setNodes((prev) => prev.filter((n) => n.id !== nodeId));
      setEdges((prev) =>
        prev.filter((e) => e.source !== nodeId && e.target !== nodeId),
      );
      expandedNodesRef.current.delete(nodeId);
      if (selectedNodeId === nodeId) setSelectedNodeId(null);
    },
    [setNodes, setEdges, selectedNodeId],
  );

  const handlePinPosition = useCallback(
    (nodeId: string) => {
      setPinnedNodes((prev) => {
        const next = new Set(prev);
        if (next.has(nodeId)) {
          next.delete(nodeId);
        } else {
          next.add(nodeId);
        }
        return next;
      });
    },
    [],
  );

  // ── Focus on a node (from detail panel) ──────────────────────────────
  const handleFocusNode = useCallback(
    (nodeId: string) => {
      // If node is already in the canvas, just select it
      const exists = nodes.some((n) => n.id === nodeId);
      if (exists) {
        setSelectedNodeId(nodeId);
      } else {
        // Add it and expand
        expandNode(nodeId);
        setSelectedNodeId(nodeId);
      }
    },
    [nodes, expandNode],
  );

  // ── MiniMap node color ───────────────────────────────────────────────
  const miniMapNodeColor = useCallback((node: Node) => {
    const data = node.data as EntityNodeData | undefined;
    const type = data?.entityType;
    const colorMap: Record<string, string> = {
      person: '#3b82f6',
      team: '#a855f7',
      system: '#22c55e',
      document: '#f59e0b',
      role: '#ec4899',
      org_unit: '#14b8a6',
      module: '#6366f1',
      project: '#06b6d4',
    };
    return type ? (colorMap[type] ?? '#6b7280') : '#6b7280';
  }, []);

  // ── Computed: node count display ─────────────────────────────────────
  const nodeCount = nodes.length;
  const edgeCount = edges.length;

  return (
    <div className="flex" style={{ height: 'calc(100vh - 64px)' }}>
      {/* Canvas area */}
      <div className="flex-1 relative">
        {godLoading && (
          <div className="absolute inset-0 flex items-center justify-center z-10 bg-background/50">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-accent" />
              <span className="text-sm text-muted-foreground">Loading brain map...</span>
            </div>
          </div>
        )}
        {godError && (
          <div className="absolute inset-0 flex items-center justify-center z-20 bg-background/80 p-8">
            <ErrorState
              error={godErr}
              title="Couldn't load canvas"
              onRetry={() => void godRefetch()}
            />
          </div>
        )}
        {!godLoading && !godError && godNodes && godNodes.items.length === 0 && nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center z-10 p-8">
            <EmptyState
              icon={<Waypoints className="h-10 w-10" />}
              title="Canvas is empty"
              description="No entities to map yet. Ingest content to seed the brain map."
            />
          </div>
        )}

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onNodeDoubleClick={onNodeDoubleClick}
          onNodeContextMenu={onNodeContextMenu}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          colorMode="dark"
          fitView
          fitViewOptions={{ padding: 0.2 }}
          defaultEdgeOptions={{
            type: 'default',
            animated: false,
            style: { stroke: '#334155', strokeWidth: 1 },
          }}
          minZoom={0.1}
          maxZoom={3}
          proOptions={{ hideAttribution: true }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={20}
            size={1}
            color="#1e293b"
          />
          <Controls
            position="bottom-left"
            showInteractive={false}
            className="!bg-card !border-border !rounded-lg !shadow-lg [&>button]:!bg-card [&>button]:!border-border [&>button]:!text-muted-foreground [&>button:hover]:!bg-accent/10 [&>button:hover]:!text-foreground [&>button>svg]:!fill-current"
          />
          <MiniMap
            position="bottom-right"
            nodeColor={miniMapNodeColor}
            maskColor="rgba(0, 0, 0, 0.7)"
            className="!bg-card/80 !border-border !rounded-lg"
            pannable
            zoomable
          />

          {/* Top-right panel with stats and actions */}
          <Panel position="top-right" className="flex items-center gap-2">
            <div className="bg-card/80 backdrop-blur-sm border border-border rounded-lg px-3 py-1.5 flex items-center gap-3 text-[11px] text-muted-foreground">
              <span>{nodeCount} nodes</span>
              <span className="text-border">|</span>
              <span>{edgeCount} edges</span>
            </div>
            <button
              onClick={handleRelayout}
              title="Re-layout nodes"
              className="bg-card/80 backdrop-blur-sm border border-border rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent/10 transition-colors"
            >
              <LayoutGrid size={14} />
            </button>
            <button
              onClick={() => fitView({ padding: 0.15, duration: 400 })}
              title="Fit to view"
              className="bg-card/80 backdrop-blur-sm border border-border rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent/10 transition-colors"
            >
              <Maximize2 size={14} />
            </button>
          </Panel>
        </ReactFlow>

        {/* Context menu overlay */}
        {contextMenu && (
          <CanvasContextMenu
            menu={contextMenu}
            onClose={() => setContextMenu(null)}
            onExpandNeighbors={handleExpandNeighbors}
            onOpenArticle={handleOpenArticle}
            onRemoveFromCanvas={handleRemoveFromCanvas}
            onPinPosition={handlePinPosition}
          />
        )}
      </div>

      {/* Detail panel */}
      <DetailPanel
        nodeDetail={
          nodeDetail
            ? {
                ...nodeDetail,
                id: nodeDetail.id,
                label: nodeDetail.label,
                meta_type: nodeDetail.meta_type,
                degree: nodeDetail.degree,
                community: nodeDetail.community,
                neighbors: nodeDetail.neighbors,
                source_file: nodeDetail.source_file,
                meta_projects: nodeDetail.meta_projects,
              }
            : null
        }
        isLoading={detailLoading && !!selectedNodeId}
        onClose={() => setSelectedNodeId(null)}
        onFocusNode={handleFocusNode}
      />
    </div>
  );
}

// ── Exported page component (wrapped with provider) ──────────────────────

export default function CanvasPage() {
  return (
    <ReactFlowProvider>
      <CanvasInner />
    </ReactFlowProvider>
  );
}
