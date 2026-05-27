import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { Loader2, Network as NetworkIcon } from 'lucide-react';
import { apiFetch } from '../../lib/api';

// ── Types ──────────────────────────────────────────────────────────────

interface SubgraphNode {
  id: string;
  label: string;
  meta_type: string;
  degree?: number;
  community?: number;
}

interface SubgraphEdge {
  from: string;
  to: string;
  label?: string;
  confidence?: number;
}

interface SubgraphResponse {
  nodes: SubgraphNode[];
  edges: SubgraphEdge[];
  center: string;
  total_nodes: number;
}

interface EgoGraphSidebarProps {
  entityGid: string;
  onNodeClick: (gid: string) => void;
}

// ── Type-based node colors (consistent with entity type semantics) ─────

const TYPE_COLORS: Record<string, string> = {
  person: '#3b82f6',   // blue
  team: '#8b5cf6',     // purple
  system: '#22c55e',   // green
  document: '#f59e0b', // amber
  role: '#06b6d4',     // cyan
  module: '#f97316',   // orange
  org_unit: '#ec4899', // pink
  project: '#14b8a6',  // teal
};

function typeColor(type: string): string {
  return TYPE_COLORS[type] ?? '#6b7280';
}

// ── vis-network options (compact, non-interactive zoom/drag) ───────────

const VIS_OPTIONS = {
  physics: {
    solver: 'forceAtlas2Based' as const,
    forceAtlas2Based: {
      gravitationalConstant: -40,
      centralGravity: 0.015,
      springLength: 80,
      springConstant: 0.04,
      damping: 0.5,
    },
    stabilization: { iterations: 50 },
  },
  nodes: {
    shape: 'dot' as const,
    size: 8,
    font: { size: 10, color: '#e0e0e0' },
    borderWidth: 1,
  },
  edges: {
    smooth: { enabled: true, type: 'continuous', roundness: 0.3 },
    color: { color: '#404060', opacity: 0.6 },
    width: 0.6,
  },
  interaction: {
    hover: true,
    zoomView: false,
    dragView: false,
    dragNodes: false,
    tooltipDelay: 150,
  },
  layout: {
    improvedLayout: false,
  },
};

// ── Component ──────────────────────────────────────────────────────────

export function EgoGraphSidebar({ entityGid, onNodeClick }: EgoGraphSidebarProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);

  const { data: subgraph, isLoading, isError } = useQuery({
    queryKey: ['ego-subgraph', entityGid],
    queryFn: () =>
      apiFetch<SubgraphResponse>(
        `/graph/subgraph?center=${encodeURIComponent(entityGid)}&depth=2&max_nodes=50`,
      ),
    staleTime: 5 * 60 * 1000,
    enabled: !!entityGid,
  });

  // Build and render the vis-network when data arrives
  useEffect(() => {
    if (!subgraph || !containerRef.current) return;

    // Destroy previous instance
    if (networkRef.current) {
      networkRef.current.destroy();
      networkRef.current = null;
    }

    const visNodes = new DataSet(
      subgraph.nodes.map((n) => ({
        id: n.id,
        label: n.label.replace(/^\[.*?\]\s*/, '').substring(0, 20),
        color: {
          background: typeColor(n.meta_type),
          border: typeColor(n.meta_type),
          highlight: {
            background: typeColor(n.meta_type),
            border: '#ffffff',
          },
        },
        size: n.id === entityGid ? 14 : 8,
        font: {
          size: n.id === entityGid ? 12 : 10,
          color: '#e0e0e0',
          bold: n.id === entityGid ? { color: '#ffffff', size: 12 } : undefined,
        },
        borderWidth: n.id === entityGid ? 3 : 1,
        title: `${n.label}\nType: ${n.meta_type}`,
      })),
    );

    const visEdges = new DataSet(
      subgraph.edges.map((e, i) => ({
        id: `e-${i}`,
        from: e.from,
        to: e.to,
        title: e.label ?? '',
      })),
    );

    const network = new Network(
      containerRef.current,
      { nodes: visNodes, edges: visEdges },
      VIS_OPTIONS,
    );

    network.on('click', (params: { nodes: string[] }) => {
      if (params.nodes.length > 0) {
        onNodeClick(params.nodes[0]);
      }
    });

    // Fit once stabilized
    network.once('stabilizationIterationsDone', () => {
      network.fit({ animation: { duration: 300, easingFunction: 'easeInOutQuad' } });
    });

    networkRef.current = network;

    return () => {
      network.destroy();
      networkRef.current = null;
    };
  }, [subgraph, entityGid, onNodeClick]);

  // Loading state
  if (isLoading) {
    return (
      <div className="rounded-lg border border-border bg-accent/5 p-3">
        <div className="flex items-center gap-2 mb-2">
          <NetworkIcon className="h-3 w-3 text-muted-foreground" />
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Entity Graph
          </span>
        </div>
        <div className="flex items-center justify-center" style={{ height: '200px' }}>
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  // Error or no data
  if (isError || !subgraph || subgraph.nodes.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border border-border bg-accent/5 p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <NetworkIcon className="h-3 w-3 text-muted-foreground" />
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Entity Graph
          </span>
        </div>
        <span className="text-[10px] text-muted-foreground">
          {subgraph.nodes.length} nodes
        </span>
      </div>

      {/* Type legend */}
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        {Object.entries(TYPE_COLORS)
          .filter(([type]) =>
            subgraph.nodes.some((n) => n.meta_type === type),
          )
          .map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-[9px] text-muted-foreground">{type}</span>
            </div>
          ))}
      </div>

      {/* vis-network container — explicit pixel height required */}
      <div
        ref={containerRef}
        style={{ height: '200px', width: '100%' }}
        className="rounded bg-background/50"
      />
    </div>
  );
}
