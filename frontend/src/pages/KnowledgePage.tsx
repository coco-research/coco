import { useState, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Sunrise, Compass, LayoutGrid, Users } from 'lucide-react';
import { apiFetch } from '../lib/api';
import { cn } from '../lib/utils';
import { resolveTab, projectParams, personParams, type KnowledgeTab } from '../lib/navigation';
import { WikiArticleList } from '../components/knowledge/WikiArticleList';
import { WikiArticleDetail } from '../components/knowledge/WikiArticleDetail';
import { WikiFilterBar, type WikiFilters } from '../components/knowledge/WikiFilterBar';
import { PeopleView } from '../components/knowledge/PeopleView';
import { DailyBriefing } from '../components/knowledge/DailyBriefing';
import { ProgramDashboard } from '../components/knowledge/ProgramDashboard';
import { ProgramDetail } from '../components/knowledge/ProgramDetail';
import { ProjectDashboard } from '../components/knowledge/ProjectDashboard';
import { PersonCard } from '../components/knowledge/PersonCard';
import { DecisionTimeline } from '../components/knowledge/DecisionTimeline';
import { AttentionBadge } from '../components/knowledge/AttentionBadge';
import { UnifiedSearch } from '../components/knowledge/UnifiedSearch';
import { KnowledgeStats } from '../components/knowledge/KnowledgeStats';
import type { WikiArticle } from '../components/knowledge/WikiArticleList';

const TABS: { id: KnowledgeTab; label: string; icon: React.ReactNode }[] = [
  { id: 'briefing', label: 'Briefing', icon: <Sunrise className="h-4 w-4" /> },
  { id: 'explore', label: 'Explore', icon: <Compass className="h-4 w-4" /> },
  { id: 'programs', label: 'Programs', icon: <LayoutGrid className="h-4 w-4" /> },
  { id: 'people', label: 'People', icon: <Users className="h-4 w-4" /> },
];

// Map program IDs to their first project slug for filtering
const PROGRAM_SLUG_MAP: Record<string, string> = {
  'anti-corruption': 'anti-corruption',
  'regulatory-compliance': 'regulatory-compliance',
  'privacy': 'privacy',
  'optimize': 'optimize',
};

interface BriefingSection {
  title: string;
  icon: string;
  items: { label: string; value: string; detail?: string; severity?: string }[];
}

interface BriefingResponse {
  generated_at: string;
  sections: BriefingSection[];
  highlights: string[];
  program_health?: { id: string; name: string; health: string; score: number; issues: string[]; article_count: number; pending_decisions: number; stale_articles: number }[];
  from_cache?: boolean;
}

export default function KnowledgePage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Derive state from URL — single source of truth (fixes M4 sync loop)
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
      // Preserve program/project when switching to programs tab
      if (tab === 'programs') {
        const prog = prev.get('program');
        const proj = prev.get('project');
        if (prog) next.set('program', prog);
        if (proj) next.set('project', proj);
      }
      return next;
    });
  }, [setSearchParams]);

  const handleSearchFocus = useCallback(() => {
    if (activeTab !== 'explore') {
      handleTabChange('explore');
    }
  }, [activeTab, handleTabChange]);

  const handleSearchQueryChange = useCallback((q: string) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (q) next.set('q', q);
      else next.delete('q');
      return next;
    });
  }, [setSearchParams]);

  const handleNavigateProgram = useCallback((programId: string) => {
    setSearchParams(new URLSearchParams({ tab: 'programs', program: programId }));
  }, [setSearchParams]);

  const handleNavigateProject = useCallback((slug: string) => {
    setSearchParams((prev) => projectParams(slug, prev.get('program') ?? undefined));
  }, [setSearchParams]);

  const handleNavigatePerson = useCallback((gid: string) => {
    setSearchParams(personParams(gid));
  }, [setSearchParams]);

  const handleNavigateArticle = useCallback((gid: string) => {
    setSelectedWikiGid(gid);
    handleTabChange('explore');
  }, [handleTabChange]);

  const handlePersonClose = useCallback(() => setParam('person', null), [setParam]);

  return (
    <div className="flex flex-col h-full">
      {/* Header with attention badge */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <h1 className="text-2xl font-semibold">Knowledge</h1>
        <AttentionBadge briefingData={briefingQuery.data ?? null} />
      </div>

      {/* Unified search bar — always visible above tabs */}
      <div className="px-4 pb-2">
        <UnifiedSearch
          query={searchQuery}
          onQueryChange={handleSearchQueryChange}
          onFocus={handleSearchFocus}
          isActive={activeTab === 'explore'}
          onSelectArticle={handleNavigateArticle}
        />
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

      {/* Tab content */}
      {activeTab === 'briefing' && (
        <div id="tabpanel-briefing" role="tabpanel" aria-labelledby="tab-briefing" className="flex-1 overflow-auto">
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
            <DecisionTimeline onNavigateProject={handleNavigateProject} />
          </div>
        </div>
      )}

      {activeTab === 'explore' && (
        <div id="tabpanel-explore" role="tabpanel" aria-labelledby="tab-explore">
          {!searchQuery && (
            <WikiFilterBar filters={wikiFilters} onChange={setWikiFilters} />
          )}
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

      {activeTab === 'programs' && (
        <div id="tabpanel-programs" role="tabpanel" aria-labelledby="tab-programs" className="flex-1 overflow-hidden">
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
            <ProgramDashboard
              onSelectProgram={(id) => setParam('program', id)}
              onNavigateWiki={(project) => {
                setWikiFilters((prev) => ({ ...prev, project }));
                handleTabChange('explore');
              }}
            />
          )}
        </div>
      )}
    </div>
  );
}
