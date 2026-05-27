/**
 * Shared navigation helpers for cross-view linking.
 * All navigation state lives in URL search params so views are bookmarkable.
 */

export type KnowledgeTab = 'search' | 'overview' | 'articles' | 'people';

/**
 * Map legacy tab names to new 4-tab system (Overview / Articles / People / Search).
 *
 * Historical names ('briefing', 'explore', 'programs', 'wiki', 'ask', etc.) are
 * still emitted by older links (e.g. QuickCommandBar, KnowledgeEngineCard, Canvas,
 * Graph). We keep those URLs working by redirecting them transparently.
 */
const TAB_REDIRECTS: Record<string, KnowledgeTab> = {
  // Old consolidated names
  briefing: 'overview',
  explore: 'search',
  programs: 'overview',
  // Pre-consolidation tab names
  wiki: 'search',
  ask: 'search',
  content: 'articles',
  media: 'articles',
  entities: 'search',
  insights: 'overview',
  quality: 'overview',
  files: 'overview',
};

const KNOWN_TABS: KnowledgeTab[] = ['search', 'overview', 'articles', 'people'];

/** Resolve a tab value from URL params, handling legacy redirects. Default is 'search'. */
export function resolveTab(raw: string | null): KnowledgeTab {
  if (!raw) return 'search';
  if (raw in TAB_REDIRECTS) return TAB_REDIRECTS[raw];
  if ((KNOWN_TABS as string[]).includes(raw)) return raw as KnowledgeTab;
  return 'search';
}

export interface TimelineFilters {
  days?: number;
  program?: string;
  person?: string;
}

/** Build search params for navigating to a project dashboard (lives under Overview). */
export function projectParams(slug: string, program?: string): URLSearchParams {
  const p = new URLSearchParams({ tab: 'overview' });
  if (program) p.set('program', program);
  p.set('project', slug);
  return p;
}

/** Build search params for navigating to a person card. */
export function personParams(gid: string): URLSearchParams {
  return new URLSearchParams({ tab: 'people', person: gid });
}

/** Build search params for navigating to the timeline (lives under Overview). */
export function timelineParams(filters?: TimelineFilters): URLSearchParams {
  const p = new URLSearchParams({ tab: 'overview', timeline: 'true' });
  if (filters?.days) p.set('days', String(filters.days));
  if (filters?.program) p.set('program', filters.program);
  if (filters?.person) p.set('person', filters.person);
  return p;
}

/** Build search params for navigating to unified search. */
export function searchParams(query: string): URLSearchParams {
  return new URLSearchParams({ tab: 'search', q: query });
}
