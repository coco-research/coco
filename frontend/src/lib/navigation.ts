/**
 * Shared navigation helpers for cross-view linking.
 * All navigation state lives in URL search params so views are bookmarkable.
 */

export type KnowledgeTab = 'briefing' | 'explore' | 'programs' | 'people';

/** Map legacy tab names to new 4-tab system */
const TAB_REDIRECTS: Record<string, KnowledgeTab> = {
  wiki: 'explore',
  ask: 'explore',
  content: 'explore',
  media: 'explore',
  entities: 'explore',
  insights: 'briefing',
  quality: 'briefing',
  files: 'programs',
};

/** Resolve a tab value from URL params, handling legacy redirects */
export function resolveTab(raw: string | null): KnowledgeTab {
  if (!raw) return 'briefing';
  if (raw in TAB_REDIRECTS) return TAB_REDIRECTS[raw];
  if (['briefing', 'explore', 'programs', 'people'].includes(raw)) return raw as KnowledgeTab;
  return 'briefing';
}

export interface TimelineFilters {
  days?: number;
  program?: string;
  person?: string;
}

/** Build search params for navigating to a project dashboard */
export function projectParams(slug: string, program?: string): URLSearchParams {
  const p = new URLSearchParams({ tab: 'programs' });
  if (program) p.set('program', program);
  p.set('project', slug);
  return p;
}

/** Build search params for navigating to a person card */
export function personParams(gid: string): URLSearchParams {
  return new URLSearchParams({ tab: 'people', person: gid });
}

/** Build search params for navigating to the timeline */
export function timelineParams(filters?: TimelineFilters): URLSearchParams {
  const p = new URLSearchParams({ tab: 'briefing', timeline: 'true' });
  if (filters?.days) p.set('days', String(filters.days));
  if (filters?.program) p.set('program', filters.program);
  if (filters?.person) p.set('person', filters.person);
  return p;
}

/** Build search params for navigating to search/explore */
export function searchParams(query: string): URLSearchParams {
  return new URLSearchParams({ tab: 'explore', q: query });
}
