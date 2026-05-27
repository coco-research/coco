import { useState, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, LayoutDashboard, FileText, Users } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { cn } from '../lib/utils';
import { resolveTab, projectParams, personParams, type KnowledgeTab } from '../lib/navigation';
import { WikiArticleList } from '../components/knowledge/WikiArticleList';
import { WikiArticleDetail } from '../components/knowledge/WikiArticleDetail';
import { WikiFilterBar, type WikiFilters } from '../components/knowledge/WikiFilterBar';
import { PeopleView } from '../components/knowledge/PeopleView';
import { DailyBriefing, type BriefingResponse } from '../components/knowledge/DailyBriefing';
import { ProgramDashboard } from '../components/knowledge/ProgramDashboard';
import { ProgramDetail } from '../components/knowledge/ProgramDetail';
import { ProjectDashboard } from '../components/knowledge/ProjectDashboard';
import { PersonCard } from '../components/knowledge/PersonCard';
import { DecisionTimeline } from '../components/knowledge/DecisionTimeline';
import { AttentionBadge } from '../components/knowledge/AttentionBadge';
import { UnifiedSearch } from '../components/knowledge/UnifiedSearch';
import { KnowledgeStats } from '../components/knowledge/KnowledgeStats';
import { QualityDashboard } from '../components/knowledge/QualityDashboard';
import type { WikiArticle } from '../components/knowledge/WikiArticleList';

const TABS: { id: KnowledgeTab; label: string; icon: React.ReactNode }[] = [
  { id: 'search', label: 'Search', icon: <Search className="h-4 w-4" /> },
  { id: 'overview', label: 'Overview', icon: <LayoutDashboard className="h-4 w-4" /> },
  { id: 'articles', label: 'Articles', icon: <FileText className="h-4 w-4" /> },
  { id: 'people', label: 'People', icon: <Users className="h-4 w-4" /> },
];

// Map program IDs to their first project slug for filtering
const PROGRAM_SLUG_MAP: Record<string, string> = {
  'anti-corruption': 'anti-corruption',
  'regulatory-compliance': 'regulatory-compliance',
  'privacy': 'privacy',
  'optimize': 'optimize',
};

// BriefingResponse/BriefingSection now imported from DailyBriefing (single source of truth)

export default function KnowledgePage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Derive state from URL — single source of truth
  const activeTab = useMemo(() => resolveTab(searchParams.get('tab')), [searchParams]);
  const selectedProgramId = searchParams.get('program') || null;
  const selectedProjectSlug = searchParams.get('project') || null;
  const selectedPersonGid = searchParams.get('person') || null;
  const searchQuery = searchParams.get('q') ?? '';

  // Local state for things not in URL
  const [selectedWikiGid, setSelectedWikiGid] = useState<string | null>(null);
  const programParam = searchParams.get('program') ?? '';
  const initialProject = programParam ? (PROGRAM_SLUG_MAP[programParam] ?? '') : '';
  const [wikiFilters, setWikiFilters] = useState<WikiFilters>({ articleType: '', entityType: '', minConfidence: 0, project: initialProject });

  // Shared briefing data (used by DailyBriefing and AttentionBadge)
  const briefingQuery = useQuery({
    queryKey: ['briefing'],
    queryFn: () => apiFetch<BriefingResponse>('/knowledge/briefing'),
    staleTime: 5 * 60 * 1000,
  });

  // URL mutation helpers — all state changes go through URL
  const setParam = useCallback((key: string, value: string | null) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) next.set(key, value);
      else next.delete(key);
      return next;
    });
  }, [setSearchParams]);

  const handleTabChange = useCallback((tab: KnowledgeTab) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams();
      next.set('tab', tab);
      // Preserve program/project when navigating into Overview (where the
      // Programs / Project dashboards now live).
      if (tab === 'overview') {
        const prog = prev.get('program');
        const proj = prev.get('project');
        if (prog) next.set('program', prog);
        if (proj) next.set('project', proj);
      }
      // Preserve search query when on the Search tab.
      if (tab === 'search') {
        const q = prev.get('q');
        if (q) next.set('q', q);
      }
      return next;
    });
  }, [setSearchParams]);

  const handleSearchQueryChange = useCallback((q: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (q) next.set('q', q);
      else next.delete('q');
      return next;
    });
  }, [setSearchParams]);

  const handleNavigateProgram = useCallback((programId: string) => {
    setSearchParams(new URLSearchParams({ tab: 'overview', program: programId }));
  }, [setSearchParams]);

  const handleNavigateProject = useCallback((slug: string) => {
    setSearchParams((prev) => projectParams(slug, prev.get('program') ?? undefined));
  }, [setSearchParams]);

  const handleNavigatePerson = useCallback((gid: string) => {
    setSearchParams(personParams(gid));
  }, [setSearchParams]);

  const handleNavigateArticle = useCallback((gid: string) => {
    setSelectedWikiGid(gid);
    handleTabChange('articles');
  }, [handleTabChange]);

  const handlePersonClose = useCallback(() => setParam('person', null), [setParam]);

  return (
    <div className="flex flex-col h-full">
      {/* Header with attention badge */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <h1 className="text-2xl font-semibold">Knowledge</h1>
        <AttentionBadge briefingData={briefingQuery.data ?? null} />
      </div>

      {/* Tab bar */}
      <div className="px-4 flex items-center gap-1 border-b border-border" role="tablist" aria-label="Knowledge sections">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            id={`tab-${tab.id}`}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`tabpanel-${tab.id}`}
            onClick={() => handleTabChange(tab.id)}
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

      {/* Search tab — unified search is the default landing experience */}
      {activeTab === 'search' && (
        <div id="tabpanel-search" role="tabpanel" aria-labelledby="tab-search" className="flex-1 overflow-auto">
          <div className="px-4 pt-4 pb-2">
            <UnifiedSearch
              query={searchQuery}
              onQueryChange={handleSearchQueryChange}
              onFocus={() => { /* no-op: search now lives in its own dedicated tab */ }}
              isActive={true}
              onSelectArticle={handleNavigateArticle}
            />
          </div>
        </div>
      )}

      {/* Overview tab — briefing + program health + project dashboards + stats + quality + timeline */}
      {activeTab === 'overview' && (
        <div id="tabpanel-overview" role="tabpanel" aria-labelledby="tab-overview" className="flex-1 overflow-auto">
          {selectedProjectSlug ? (
            <ProjectDashboard
              slug={selectedProjectSlug}
              onBack={() => setParam('project', null)}
              onSelectPerson={handleNavigatePerson}
              onSelectArticle={handleNavigateArticle}
            />
          ) : selectedProgramId ? (
            <ProgramDetail
              programId={selectedProgramId}
              onBack={() => setParam('program', null)}
              onNavigateWiki={(project) => setParam('project', project)}
            />
          ) : (
            <>
              <DailyBriefing
                briefingData={briefingQuery.data ?? null}
                isLoading={briefingQuery.isLoading}
                onRefresh={() => briefingQuery.refetch()}
                onNavigateProgram={handleNavigateProgram}
              />
              <div className="px-4 pb-4">
                <KnowledgeStats />
              </div>
              <div className="px-6 pb-6">
                <ProgramDashboard
                  onSelectProgram={(id) => setParam('program', id)}
                  onNavigateWiki={(project) => {
                    setWikiFilters((prev) => ({ ...prev, project }));
                    handleTabChange('articles');
                  }}
                />
              </div>
              <div className="px-6 pb-6">
                <DecisionTimeline onNavigateProject={handleNavigateProject} />
              </div>
              <div className="px-6 pb-6">
                <QualityDashboard />
              </div>
            </>
          )}
        </div>
      )}

      {/* Articles tab — wiki article browse + detail */}
      {activeTab === 'articles' && (
        <div id="tabpanel-articles" role="tabpanel" aria-labelledby="tab-articles" className="flex-1 flex flex-col overflow-hidden">
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
        </div>
      )}

      {/* People tab — people view + person card slide-over */}
      {activeTab === 'people' && (
        <div id="tabpanel-people" role="tabpanel" aria-labelledby="tab-people" className="flex-1 overflow-hidden flex">
          <div className={cn('flex-1 overflow-hidden', selectedPersonGid && 'max-w-[450px]')}>
            <PeopleView onSelectGid={handleNavigatePerson} />
          </div>
          {selectedPersonGid && (
            <div className="flex-1 overflow-hidden">
              <PersonCard
                gid={selectedPersonGid}
                onClose={handlePersonClose}
                onNavigateProject={handleNavigateProject}
                onSelectPerson={handleNavigatePerson}
                onSelectArticle={handleNavigateArticle}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
