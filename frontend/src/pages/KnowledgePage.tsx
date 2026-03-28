import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { FileText, Sparkles, Network } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { cn } from '../lib/utils';
import { FilterBar } from '../components/knowledge/FilterBar';
import { ContentList } from '../components/knowledge/ContentList';
import { ContentDetail } from '../components/knowledge/ContentDetail';
import { InsightPanel } from '../components/knowledge/InsightPanel';
import { EntityGraph } from '../components/knowledge/EntityGraph';
import type { ContentItem } from '../components/knowledge/ContentList';

interface ContentResponse {
  items: ContentItem[];
  total: number;
}

type Tab = 'content' | 'insights' | 'entities';

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'content', label: 'Content', icon: <FileText className="h-4 w-4" /> },
  { id: 'insights', label: 'Insights', icon: <Sparkles className="h-4 w-4" /> },
  { id: 'entities', label: 'Entities', icon: <Network className="h-4 w-4" /> },
];

export default function KnowledgePage() {
  const [searchParams] = useSearchParams();
  const [selected, setSelected] = useState<ContentItem | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('content');

  const source = searchParams.get('source') ?? '';
  const projectId = searchParams.get('project_id') ?? '';
  const q = searchParams.get('q') ?? '';
  const offset = searchParams.get('offset') ?? '0';

  const params = new URLSearchParams();
  if (source) params.set('source', source);
  if (projectId) params.set('project_id', projectId);
  if (q) params.set('q', q);
  params.set('limit', '50');
  params.set('offset', offset);

  const { data, isLoading } = useQuery({
    queryKey: ['content', { source, project_id: projectId, q, offset }],
    queryFn: () => apiFetch<ContentResponse>(`/content?${params.toString()}`),
    enabled: activeTab === 'content',
  });

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <h1 className="text-2xl font-semibold">Knowledge</h1>
      </div>

      {/* Tab bar */}
      <div className="px-4 flex items-center gap-1 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px',
              activeTab === tab.id
                ? 'border-foreground text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border',
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'content' && (
        <>
          <FilterBar />
          <div className="flex-1 overflow-hidden">
            <ContentList
              items={data?.items ?? []}
              total={data?.total ?? 0}
              isLoading={isLoading}
              selectedId={selected?.id ?? null}
              onSelect={setSelected}
            />
          </div>
          {selected && (
            <ContentDetail
              item={selected}
              onClose={() => setSelected(null)}
            />
          )}
        </>
      )}

      {activeTab === 'insights' && (
        <div className="flex-1 overflow-hidden">
          <InsightPanel />
        </div>
      )}

      {activeTab === 'entities' && (
        <div className="flex-1 overflow-hidden">
          <EntityGraph />
        </div>
      )}
    </div>
  );
}
