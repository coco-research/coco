import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../lib/api';
import { FilterBar } from '../components/knowledge/FilterBar';
import { ContentList } from '../components/knowledge/ContentList';
import { ContentDetail } from '../components/knowledge/ContentDetail';
import type { ContentItem } from '../components/knowledge/ContentList';

interface ContentResponse {
  items: ContentItem[];
  total: number;
}

export default function KnowledgePage() {
  const [searchParams] = useSearchParams();
  const [selected, setSelected] = useState<ContentItem | null>(null);

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
  });

  return (
    <div className="flex flex-col h-full">
      <h1 className="text-2xl font-semibold px-4 pt-4 pb-2">Knowledge</h1>

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
    </div>
  );
}
