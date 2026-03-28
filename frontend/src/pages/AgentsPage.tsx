import { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, FolderKanban, Radio, LayoutGrid, GitFork } from 'lucide-react';
import { apiFetch, apiPost } from '../lib/api';
import { AgentCard, type Agent } from '../components/agents/AgentCard';
import { CreateAgentDialog } from '../components/agents/CreateAgentDialog';
import { AgentDetail } from '../components/agents/AgentDetail';
import { OrgChart, type OrgNode } from '../components/agents/OrgChart';

type ViewMode = 'cards' | 'org-chart';

const VIEW_STORAGE_KEY = 'coco-agents-view';

function getStoredView(): ViewMode {
  try {
    const v = localStorage.getItem(VIEW_STORAGE_KEY);
    if (v === 'cards' || v === 'org-chart') return v;
  } catch { /* ignore */ }
  return 'org-chart';
}

interface Project {
  id: string;
  name: string;
}

export default function AgentsPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>(getStoredView);

  const toggleView = (mode: ViewMode) => {
    setViewMode(mode);
    try { localStorage.setItem(VIEW_STORAGE_KEY, mode); } catch { /* ignore */ }
  };

  const { data: agents = [], isLoading } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: () => apiFetch('/agents'),
    refetchInterval: (query) => {
      const data = query.state.data ?? [];
      return data.some((a: Agent) => a.status === 'running' || a.status === 'paused') ? 3000 : 30000;
    },
  });

  const { data: orgChartRoots = [] } = useQuery<OrgNode[]>({
    queryKey: ['agents-org-chart'],
    queryFn: () => apiFetch('/agents/org-chart'),
    refetchInterval: (query) => {
      // Match the agents polling interval
      return agents.some((a) => a.status === 'running' || a.status === 'paused') ? 3000 : 30000;
    },
    enabled: viewMode === 'org-chart',
  });

  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => apiFetch('/projects'),
  });

  const projectMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const p of projects) map[p.id] = p.name;
    return map;
  }, [projects]);

  // Group agents by project_id
  const grouped = useMemo(() => {
    const groups: Record<string, Agent[]> = {};
    for (const agent of agents) {
      const key = agent.project_id ?? '__unassigned__';
      if (!groups[key]) groups[key] = [];
      groups[key].push(agent);
    }
    return groups;
  }, [agents]);

  const groupKeys = useMemo(() => {
    // Show assigned projects first (sorted by name), then unassigned
    const assigned = Object.keys(grouped).filter(k => k !== '__unassigned__').sort((a, b) =>
      (projectMap[a] ?? a).localeCompare(projectMap[b] ?? b)
    );
    if (grouped['__unassigned__']) assigned.push('__unassigned__');
    return assigned;
  }, [grouped, projectMap]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['agents'] });

  const handleAction = async (agentId: string, action: string) => {
    try {
      await apiPost(`/agents/${agentId}/${action}`, {});
      invalidate();
    } catch {
      // ignore
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Agent Team</h1>
        <div className="flex items-center gap-3">
          {/* View toggle */}
          {agents.length > 0 && (
            <div className="flex items-center rounded-lg border border-border bg-muted/50 p-0.5">
              <button
                onClick={() => toggleView('cards')}
                className={`flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-md transition-all ${
                  viewMode === 'cards'
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <LayoutGrid size={14} />
                Cards
              </button>
              <button
                onClick={() => toggleView('org-chart')}
                className={`flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-md transition-all ${
                  viewMode === 'org-chart'
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <GitFork size={14} />
                Org Chart
              </button>
            </div>
          )}
          <button
            onClick={() => setDialogOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-primary text-primary-foreground rounded-md hover:opacity-90"
          >
            <Plus size={16} />
            New Agent
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-24 bg-muted/50 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <Radio size={40} className="mb-3 opacity-30" />
          <p className="text-sm font-medium">No agents</p>
          <p className="text-xs mt-1">Create an agent to start delegating work.</p>
          <button
            onClick={() => setDialogOpen(true)}
            className="mt-4 flex items-center gap-1.5 px-4 py-2 text-sm rounded-lg bg-accent text-accent-foreground hover:opacity-90"
          >
            <Plus size={14} />
            Recruit Agent
          </button>
        </div>
      ) : viewMode === 'org-chart' ? (
        <OrgChart
          roots={orgChartRoots}
          onSelect={(id) => setSelectedId(id)}
        />
      ) : (
        <div className="space-y-6">
          {groupKeys.map((key) => (
            <section key={key}>
              <div className="flex items-center gap-2 mb-3">
                <FolderKanban size={14} className="text-muted-foreground" />
                <h2 className="text-sm font-medium text-muted-foreground">
                  {key === '__unassigned__' ? 'Unassigned' : (projectMap[key] ?? key)}
                </h2>
                <span className="text-xs text-muted-foreground">({grouped[key].length})</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {grouped[key].map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    onClick={() => setSelectedId(agent.id)}
                    onSpawn={() => handleAction(agent.id, 'spawn')}
                    onPause={() => handleAction(agent.id, 'pause')}
                    onResume={() => handleAction(agent.id, 'resume')}
                    onKill={() => handleAction(agent.id, 'kill')}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      <CreateAgentDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onCreated={() => invalidate()}
      />

      {selectedId && (
        <AgentDetail
          agentId={selectedId}
          onClose={() => setSelectedId(null)}
          onAction={invalidate}
        />
      )}
    </div>
  );
}
