import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  User,
  FolderOpen,
  Calendar,
  Gavel,
  ListChecks,
  Tag,
  Loader2,
  Network,
} from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';
import type { ReactNode } from 'react';

interface EntityItem {
  id: string;
  content_id: string;
  entity_type: string;
  value: string;
  confidence: number;
  source_mode: string;
  context_snippet: string | null;
  created_at: string;
}

interface EntitiesResponse {
  items: EntityItem[];
  total: number;
}

const TYPE_CONFIG: Record<
  string,
  { icon: ReactNode; label: string; color: string }
> = {
  person: { icon: <User className="h-3.5 w-3.5" />, label: 'People', color: 'text-info' },
  project: { icon: <FolderOpen className="h-3.5 w-3.5" />, label: 'Projects', color: 'text-accent' },
  date: { icon: <Calendar className="h-3.5 w-3.5" />, label: 'Dates', color: 'text-warning' },
  decision: { icon: <Gavel className="h-3.5 w-3.5" />, label: 'Decisions', color: 'text-success' },
  action_item: { icon: <ListChecks className="h-3.5 w-3.5" />, label: 'Action Items', color: 'text-error' },
  topic: { icon: <Tag className="h-3.5 w-3.5" />, label: 'Topics', color: 'text-muted-foreground' },
};

const ALL_TYPES = ['person', 'project', 'date', 'decision', 'action_item', 'topic'];

export function EntityGraph() {
  const [selectedType, setSelectedType] = useState('');

  const params = new URLSearchParams();
  if (selectedType) params.set('type', selectedType);
  params.set('limit', '200');

  const { data, isLoading } = useQuery({
    queryKey: ['entities', { type: selectedType }],
    queryFn: () => apiFetch<EntitiesResponse>(`/entities?${params.toString()}`),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  // Group entities by type and then by normalized value
  const grouped: Record<string, { value: string; count: number; avgConf: number; contentIds: Set<string> }[]> = {};
  for (const item of items) {
    if (!grouped[item.entity_type]) {
      grouped[item.entity_type] = [];
    }
    const existing = grouped[item.entity_type].find(
      (g) => g.value.toLowerCase() === item.value.toLowerCase(),
    );
    if (existing) {
      existing.count++;
      existing.avgConf = (existing.avgConf * (existing.count - 1) + item.confidence) / existing.count;
      existing.contentIds.add(item.content_id);
    } else {
      grouped[item.entity_type].push({
        value: item.value,
        count: 1,
        avgConf: item.confidence,
        contentIds: new Set([item.content_id]),
      });
    }
  }

  // Sort each group by count desc
  for (const type of Object.keys(grouped)) {
    grouped[type].sort((a, b) => b.count - a.count);
  }

  const displayTypes = selectedType ? [selectedType] : ALL_TYPES.filter((t) => grouped[t]?.length);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground text-sm gap-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading entities...
      </div>
    );
  }

  if (total === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground text-sm gap-3">
        <Network className="h-8 w-8" />
        <p>No entities extracted yet</p>
        <p className="text-xs">
          Use the entity extraction API or generate insights to populate this view.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Type filter tabs */}
      <div className="px-4 py-3 border-b border-border flex items-center gap-2 flex-wrap">
        <button
          onClick={() => setSelectedType('')}
          className={cn(
            'px-3 py-1 rounded-full text-xs font-medium transition-colors',
            !selectedType
              ? 'bg-foreground text-background'
              : 'bg-accent/20 text-muted-foreground hover:text-foreground',
          )}
        >
          All ({total})
        </button>
        {ALL_TYPES.map((type) => {
          const config = TYPE_CONFIG[type];
          const count = grouped[type]?.length ?? 0;
          if (!count && !selectedType) return null;
          return (
            <button
              key={type}
              onClick={() => setSelectedType(selectedType === type ? '' : type)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors',
                selectedType === type
                  ? 'bg-foreground text-background'
                  : 'bg-accent/20 text-muted-foreground hover:text-foreground',
              )}
            >
              <span className={config.color}>{config.icon}</span>
              {config.label} ({count})
            </button>
          );
        })}
      </div>

      {/* Entity network view */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-6">
          {displayTypes.map((type) => {
            const config = TYPE_CONFIG[type] ?? TYPE_CONFIG.topic;
            const entities = grouped[type] ?? [];
            if (!entities.length) return null;

            return (
              <div key={type}>
                <h3 className={cn('text-sm font-medium mb-2 flex items-center gap-2', config.color)}>
                  {config.icon}
                  {config.label}
                  <span className="text-xs text-muted-foreground font-normal">
                    ({entities.length} unique)
                  </span>
                </h3>
                <div className="flex flex-wrap gap-2">
                  {entities.slice(0, 30).map((entity) => {
                    const size = entity.count >= 5 ? 'text-sm' : entity.count >= 2 ? 'text-xs' : 'text-xs';
                    const opacity = entity.avgConf >= 0.8 ? '' : entity.avgConf >= 0.5 ? 'opacity-80' : 'opacity-60';
                    const crossSource = entity.contentIds.size >= 2;

                    return (
                      <span
                        key={entity.value}
                        className={cn(
                          'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border transition-colors',
                          size,
                          opacity,
                          crossSource
                            ? 'border-accent/40 bg-accent/10 text-foreground'
                            : 'border-border bg-card text-foreground',
                        )}
                        title={`${entity.value} - ${entity.count} occurrence(s), ${entity.contentIds.size} source(s), confidence: ${Math.round(entity.avgConf * 100)}%`}
                      >
                        {entity.value.length > 50
                          ? entity.value.slice(0, 50) + '...'
                          : entity.value}
                        {entity.count > 1 && (
                          <span className="text-muted-foreground text-[10px] ml-0.5">
                            x{entity.count}
                          </span>
                        )}
                        {crossSource && (
                          <span className="text-accent text-[10px]">
                            {entity.contentIds.size}src
                          </span>
                        )}
                      </span>
                    );
                  })}
                  {entities.length > 30 && (
                    <span className="text-xs text-muted-foreground self-center">
                      +{entities.length - 30} more
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
