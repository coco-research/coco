import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Skeleton } from 'boneyard-js/react';
import { FileText, Sparkles, Network, BookOpen, Users, Image, MessageSquare } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { cn } from '../lib/utils';
import { FilterBar } from '../components/knowledge/FilterBar';
import { ContentList } from '../components/knowledge/ContentList';
import { ContentDetail } from '../components/knowledge/ContentDetail';
import { InsightPanel } from '../components/knowledge/InsightPanel';
import { EntityGraph } from '../components/knowledge/EntityGraph';
import { WikiArticleList } from '../components/knowledge/WikiArticleList';
import { WikiArticleDetail } from '../components/knowledge/WikiArticleDetail';
import { WikiFilterBar, type WikiFilters } from '../components/knowledge/WikiFilterBar';
import { PeopleView } from '../components/knowledge/PeopleView';
import { MediaView } from '../components/knowledge/MediaView';
import { KnowledgeQA } from '../components/knowledge/KnowledgeQA';
import type { ContentItem } from '../components/knowledge/ContentList';
import type { WikiArticle } from '../components/knowledge/WikiArticleList';

interface ContentResponse {
  items: ContentItem[];
  total: number;
}

type Tab = 'ask' | 'content' | 'insights' | 'entities' | 'wiki' | 'people' | 'media';

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'ask', label: 'Ask', icon: <MessageSquare className="h-4 w-4" /> },
  { id: 'content', label: 'Content', icon: <FileText className="h-4 w-4" /> },
  { id: 'insights', label: 'Insights', icon: <Sparkles className="h-4 w-4" /> },
  { id: 'entities', label: 'Entities', icon: <Network className="h-4 w-4" /> },
  { id: 'wiki', label: 'Wiki', icon: <BookOpen className="h-4 w-4" /> },
  { id: 'people', label: 'People', icon: <Users className="h-4 w-4" /> },
  { id: 'media', label: 'Media', icon: <Image className="h-4 w-4" /> },
];

// Map program IDs to their first project slug for filtering
const PROGRAM_SLUG_MAP: Record<string, string> = {
  'anti-corruption': 'anti-corruption',
  'regulatory-compliance': 'regulatory-compliance',
  'privacy': 'privacy',
  'optimize': 'optimize',
};

export default function KnowledgePage() {
  const [searchParams] = useSearchParams();
  const [selected, setSelected] = useState<ContentItem | null>(null);
  const [selectedWikiGid, setSelectedWikiGid] = useState<string | null>(null);
  const programParam = searchParams.get('program') ?? '';
  const initialProject = programParam ? (PROGRAM_SLUG_MAP[programParam] ?? '') : '';
  const [wikiFilters, setWikiFilters] = useState<WikiFilters>({ articleType: '', entityType: '', minConfidence: 0, project: initialProject });
  const initialTab = (searchParams.get('tab') as Tab) || 'ask';
  const [activeTab, setActiveTab] = useState<Tab>(initialTab);

  // Sync program param changes into wiki filters
  useEffect(() => {
    if (programParam) {
      const slug = PROGRAM_SLUG_MAP[programParam] ?? '';
      if (slug) {
        setWikiFilters((prev) => ({ ...prev, project: slug }));
      }
    }
  }, [programParam]);

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
      <div className="px-4 flex items-center gap-1 border-b border-border" role="tablist" aria-label="Knowledge sections">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
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
      {activeTab === 'ask' && (
        <div className="flex-1 overflow-hidden">
          <KnowledgeQA onSelectArticle={(gid) => {
            setSelectedWikiGid(gid);
            setActiveTab('wiki');
          }} />
        </div>
      )}

      {activeTab === 'content' && (
        <>
          <FilterBar />
          <Skeleton name="knowledge-content" loading={isLoading && activeTab === 'content'}>
            <div className="flex-1 overflow-hidden">
              <ContentList
                items={data?.items ?? []}
                total={data?.total ?? 0}
                isLoading={isLoading}
                selectedId={selected?.id ?? null}
                onSelect={setSelected}
              />
            </div>
          </Skeleton>
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

      {activeTab === 'wiki' && (
        <>
          <WikiFilterBar filters={wikiFilters} onChange={setWikiFilters} />
          <div className="flex-1 overflow-hidden flex">
            <div className={cn('flex-1 overflow-hidden', selectedWikiGid && 'max-w-[400px]')}>
              <WikiArticleList
                selectedGid={selectedWikiGid}
                onSelect={(article: WikiArticle) => setSelectedWikiGid(article.gid)}
                filters={wikiFilters}
              />
            </div>
            {selectedWikiGid && (
              <div className="flex-1 overflow-hidden">
                <WikiArticleDetail
                  gid={selectedWikiGid}
                  onClose={() => setSelectedWikiGid(null)}
                />
              </div>
            )}
          </div>
        </>
      )}

      {activeTab === 'people' && (
        <div className="flex-1 overflow-hidden flex">
          <div className={cn('flex-1 overflow-hidden', selectedWikiGid && 'max-w-[450px]')}>
            <PeopleView onSelectGid={(gid) => setSelectedWikiGid(gid)} />
          </div>
          {selectedWikiGid && (
            <div className="flex-1 overflow-hidden">
              <WikiArticleDetail
                gid={selectedWikiGid}
                onClose={() => setSelectedWikiGid(null)}
              />
            </div>
          )}
        </div>
      )}

      {activeTab === 'media' && (
        <div className="flex-1 overflow-hidden">
          <MediaView />
        </div>
      )}
    </div>
  );
}
