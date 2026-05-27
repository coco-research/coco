import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import {
  Search, Loader2, X, ChevronRight, Users, Monitor,
  Building2, Briefcase, Box, FileText, User, Waypoints,
  BookOpen, ExternalLink,
} from 'lucide-react';
import { apiFetch } from '../lib/api';
import { cn } from '../lib/utils';
import { EmptyState } from '../components/shared/EmptyState';
import { ErrorState } from '../components/shared/ErrorState';

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
  meta_project?: string;
  [key: string]: unknown;
}

interface GodNodesResponse { items: GraphNode[] }
interface NodeResponse extends NodeDetail {}
interface CommunityListResponse { items: { id: number; size: number; top_members: { id: string; label: string; degree: number }[] }[]; total: number }
// CommunityResponse / PathResponse — reserved for future single-community / path-query surfaces.
// Kept here so the GraphAPI surface remains documented in one place.
export interface CommunityResponse { community_id: number; nodes: Record<string, unknown>[]; edges: Record<string, unknown>[]; total_members: number }
export interface PathResponse { path: GraphNode[]; hops: number; message?: string }

// ── Color palette for communities ────────────────────────────────────────

const COMMUNITY_COLORS = [
  '#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#06b6d4',
  '#84cc16', '#e11d48', '#0ea5e9', '#a855f7', '#10b981',
];

function communityColor(cid: number | undefined): string {
  if (cid == null) return '#6b7280';
  return COMMUNITY_COLORS[cid % COMMUNITY_COLORS.length];
}

const TYPE_ICONS: Record<string, React.ElementType> = {
  person: User,
  team: Users,
  system: Monitor,
  document: FileText,
  org_unit: Building2,
  role: Briefcase,
  module: Box,
  project: Waypoints,
};

// ── Main Page ────────────────────────────────────────────────────────────

export default function GraphPage() {
  const [searchParams] = useSearchParams();
  const focusNode = searchParams.get('focus');

  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const nodesDataRef = useRef<DataSet<any>>(new DataSet());
  const edgesDataRef = useRef<DataSet<any>>(new DataSet());

  const [searchQ, setSearchQ] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(focusNode);
  const [typeFilter, setTypeFilter] = useState<string>('all');

  // ── Fetch initial god nodes ──────────────────────────────────────────
  const { data: godNodes, isLoading: godLoading, isError: godError, error: godErr, refetch: godRefetch } = useQuery({
    queryKey: ['graph-god-nodes'],
    queryFn: () => apiFetch<GodNodesResponse>('/graph/god-nodes?top_n=60'),
  });

  // ── Fetch selected node detail ───────────────────────────────────────
  const { data: nodeDetail } = useQuery({
    queryKey: ['graph-node', selectedNodeId],
    queryFn: () => apiFetch<NodeResponse>(`/graph/node/${encodeURIComponent(selectedNodeId!)}`),
    enabled: !!selectedNodeId,
  });

  // ── Fetch communities for legend ─────────────────────────────────────
  const { data: communitiesData } = useQuery({
    queryKey: ['graph-communities'],
    queryFn: () => apiFetch<CommunityListResponse>('/graph/communities?limit=15'),
  });

  // ── Search nodes ─────────────────────────────────────────────────────
  const { data: searchResults } = useQuery({
    queryKey: ['graph-search', searchQ],
    queryFn: () => apiFetch<{ items: GraphNode[]; total: number }>(`/graph/nodes?q=${encodeURIComponent(searchQ)}&min_degree=1&limit=20`),
    enabled: searchQ.length >= 2,
  });

  // ── Initialize vis-network ───────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;
    if (networkRef.current) return; // already initialized

    const network = new Network(
      containerRef.current,
      { nodes: nodesDataRef.current, edges: edgesDataRef.current },
      {
        physics: {
          solver: 'forceAtlas2Based',
          forceAtlas2Based: {
            gravitationalConstant: -60,
            centralGravity: 0.008,
            springLength: 120,
            springConstant: 0.02,
            damping: 0.4,
          },
          stabilization: { iterations: 150 },
        },
        nodes: {
          shape: 'dot',
          font: { color: '#e0e0e0', size: 11 },
          borderWidth: 1,
          borderWidthSelected: 3,
        },
        edges: {
          color: { color: '#404060', highlight: '#7c7cff', opacity: 0.6 },
          width: 0.8,
          smooth: { enabled: true, type: 'continuous', roundness: 0.3 },
        },
        interaction: {
          hover: true,
          tooltipDelay: 200,
          zoomView: true,
          dragView: true,
        },
        layout: { improvedLayout: false },
      },
    );

    network.on('click', (params: { nodes: string[] }) => {
      if (params.nodes.length > 0) {
        setSelectedNodeId(params.nodes[0]);
      }
    });

    network.on('doubleClick', (params: { nodes: string[] }) => {
      if (params.nodes.length > 0) {
        expandNode(params.nodes[0]);
      }
    });

    networkRef.current = network;

    return () => {
      network.destroy();
      networkRef.current = null;
    };
  }, []);

  // ── Load god nodes into graph ────────────────────────────────────────
  useEffect(() => {
    if (!godNodes?.items) return;

    const filtered = typeFilter === 'all'
      ? godNodes.items
      : godNodes.items.filter((n) => n.meta_type === typeFilter);

    const visNodes = filtered.map((n) => ({
      id: n.id,
      label: n.label.replace(/^\[.*?\]\s*/, '').substring(0, 30),
      color: communityColor(n.community),
      size: Math.min(5 + Math.sqrt(n.degree) * 2, 40),
      title: `${n.label}\nType: ${n.meta_type}\nDegree: ${n.degree}`,
    }));

    nodesDataRef.current.clear();
    nodesDataRef.current.add(visNodes);
    edgesDataRef.current.clear();

    if (networkRef.current) {
      networkRef.current.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
    }
  }, [godNodes, typeFilter]);

  // ── Expand a node: fetch neighbors and add them ──────────────────────
  const expandNode = useCallback(async (nodeId: string) => {
    try {
      const detail = await apiFetch<NodeResponse>(`/graph/node/${encodeURIComponent(nodeId)}`);
      const newNodes: any[] = [];
      const newEdges: any[] = [];

      for (const neighbor of detail.neighbors) {
        if (!nodesDataRef.current.get(neighbor.id)) {
          newNodes.push({
            id: neighbor.id,
            label: neighbor.label.replace(/^\[.*?\]\s*/, '').substring(0, 25),
            color: '#6b7280',
            size: 8,
            title: `${neighbor.label}\nType: ${neighbor.meta_type}`,
          });
        }
        const edgeId = `${nodeId}-${neighbor.id}`;
        if (!edgesDataRef.current.get(edgeId)) {
          newEdges.push({
            id: edgeId,
            from: nodeId,
            to: neighbor.id,
            title: neighbor.relation,
          });
        }
      }

      if (newNodes.length) nodesDataRef.current.add(newNodes);
      if (newEdges.length) edgesDataRef.current.add(newEdges);
    } catch {
      // ignore expand failures
    }
  }, []);

  // ── Focus on a node ──────────────────────────────────────────────────
  const focusOnNode = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);

    // If node isn't in the graph yet, add it
    if (!nodesDataRef.current.get(nodeId)) {
      nodesDataRef.current.add({
        id: nodeId,
        label: nodeId.substring(0, 25),
        color: '#f59e0b',
        size: 15,
      });
    }

    expandNode(nodeId);

    if (networkRef.current) {
      networkRef.current.focus(nodeId, {
        scale: 1.2,
        animation: { duration: 500, easingFunction: 'easeInOutQuad' },
      });
      networkRef.current.selectNodes([nodeId]);
    }
  }, [expandNode]);

  // ── Focus on URL param node ──────────────────────────────────────────
  useEffect(() => {
    if (focusNode && networkRef.current) {
      focusOnNode(focusNode);
    }
  }, [focusNode, focusOnNode]);

  return (
    <div className="flex" style={{ height: 'calc(100vh - 64px)' }}>
      {/* ── Graph canvas ──────────────────────────────────────────── */}
      <div className="flex-1 relative bg-[#0f0f1a]">
        {godLoading && (
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <Loader2 className="h-8 w-8 animate-spin text-accent" />
          </div>
        )}
        {godError && (
          <div className="absolute inset-0 flex items-center justify-center z-10 p-8">
            <ErrorState
              error={godErr}
              title="Couldn't load graph"
              onRetry={() => void godRefetch()}
            />
          </div>
        )}
        {!godLoading && !godError && godNodes && godNodes.items.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center z-10 p-8">
            <EmptyState
              icon={<Waypoints className="h-10 w-10" />}
              title="Knowledge graph is empty"
              description="Ingest content to build relationships between people, projects, and systems."
            />
          </div>
        )}
        <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

        {/* Type filter pills (top-left overlay) */}
        <div className="absolute top-3 left-3 flex flex-wrap gap-1">
          {['all', 'person', 'team', 'system', 'project', 'document'].map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={cn(
                'px-2 py-1 rounded text-xs font-medium transition-colors',
                typeFilter === t
                  ? 'bg-accent/20 text-accent border border-accent/40'
                  : 'bg-black/50 text-gray-400 border border-gray-700 hover:text-white',
              )}
            >
              {t === 'all' ? 'All' : t}
            </button>
          ))}
        </div>
      </div>

      {/* ── Sidebar ───────────────────────────────────────────────── */}
      <div className="w-80 border-l border-border bg-background flex flex-col overflow-hidden">
        {/* Search */}
        <div className="p-3 border-b border-border">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              value={searchQ}
              onChange={(e) => setSearchQ(e.target.value)}
              placeholder="Search graph..."
              className="w-full pl-8 pr-3 py-1.5 bg-card border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/30"
            />
          </div>
          {searchResults && searchQ.length >= 2 && (
            <div className="mt-2 max-h-48 overflow-y-auto rounded-lg border border-border bg-card">
              {searchResults.items.map((n) => (
                <button
                  key={n.id}
                  onClick={() => { focusOnNode(n.id); setSearchQ(''); }}
                  className="w-full text-left px-3 py-2 text-xs hover:bg-accent/10 flex items-center gap-2"
                >
                  <span className="text-foreground truncate">{n.label}</span>
                  <span className="text-muted-foreground">{n.meta_type}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Node detail */}
        {nodeDetail ? (
          <div className="flex-1 overflow-y-auto p-3 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-semibold text-foreground">{nodeDetail.label || nodeDetail.id}</h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {nodeDetail.meta_type} &middot; {nodeDetail.degree} connections
                </p>
                {nodeDetail.meta_projects && (
                  <p className="text-xs text-accent mt-1">{nodeDetail.meta_projects}</p>
                )}
              </div>
              <button onClick={() => setSelectedNodeId(null)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Action links */}
            <div className="flex items-center gap-2">
              <a
                href={`/knowledge?tab=wiki&q=${encodeURIComponent(nodeDetail.label?.replace(/^\[.*?\]\s*/, '') || nodeDetail.id)}`}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
              >
                <BookOpen className="h-3 w-3" />
                Wiki Article
              </a>
              {nodeDetail.source_file && (
                <span className="text-[10px] text-muted-foreground truncate max-w-[140px]" title={nodeDetail.source_file}>
                  <ExternalLink className="h-2.5 w-2.5 inline mr-0.5" />
                  {nodeDetail.source_file.split('/').pop()}
                </span>
              )}
            </div>

            {nodeDetail.community != null && (
              <div className="flex items-center gap-2 text-xs">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: communityColor(nodeDetail.community) }} />
                <span className="text-muted-foreground">Community {nodeDetail.community}</span>
              </div>
            )}

            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">
                Neighbors ({nodeDetail.neighbors.length})
              </h4>
              <div className="space-y-1 max-h-[400px] overflow-y-auto">
                {nodeDetail.neighbors.slice(0, 50).map((nb) => {
                  const Icon = TYPE_ICONS[nb.meta_type] ?? ChevronRight;
                  return (
                    <button
                      key={nb.id}
                      onClick={() => focusOnNode(nb.id)}
                      className="w-full text-left px-2 py-1.5 rounded hover:bg-accent/10 flex items-center gap-2 text-xs"
                    >
                      <Icon className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                      <span className="text-foreground truncate flex-1">{nb.label}</span>
                      <span className="text-muted-foreground/60 text-[10px]">{nb.relation}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground text-sm p-6 text-center">
            <Waypoints className="h-10 w-10 mb-3 opacity-30" />
            <p>Click a node to see details</p>
            <p className="text-xs mt-1">Double-click to expand its neighbors</p>
          </div>
        )}

        {/* Community legend */}
        {communitiesData && (
          <div className="border-t border-border p-3">
            <h4 className="text-xs font-medium text-muted-foreground mb-2">Communities</h4>
            <div className="grid grid-cols-2 gap-1 max-h-32 overflow-y-auto">
              {communitiesData.items.slice(0, 10).map((c) => (
                <div key={c.id} className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: communityColor(c.id) }} />
                  <span className="truncate">{c.top_members[0]?.label?.replace(/^\[.*?\]\s*/, '') ?? `#${c.id}`}</span>
                  <span className="text-muted-foreground/50">({c.size})</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
