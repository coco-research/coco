import { lazy, Suspense, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, Clock, Shield, Network, Link2, ArrowLeft, List } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';
import { articleTypeBadge } from './WikiFilterBar';
import { WikiLinkRenderer } from './WikiLinkRenderer';

// Lazy-load EgoGraphSidebar — pulls in vis-network (~500KB) only when an article is open.
const EgoGraphSidebar = lazy(() =>
  import('./EgoGraphSidebar').then((m) => ({ default: m.EgoGraphSidebar })),
);

interface RelatedArticle {
  gid: string;
  title: string;
  summary: string | null;
  confidence: number;
  article_type: string;
  entity_type: string | null;
}

interface Section {
  heading: string;
  content: string;
}

interface ArticleFull {
  id: number;
  gid: string;
  title: string;
  summary: string | null;
  body_json: { sections: Section[] } | null;
  infobox_json: Record<string, unknown> | null;
  sources_json: unknown[];
  confidence: number;
  generated_at: string;
  article_type: string;
  quality_score: number;
}

interface WikiArticleDetailProps {
  gid: string;
  onClose: () => void;
}

function InfoboxRow({ label, value }: { label: string; value: unknown }) {
  if (value === null || value === undefined || value === '') return null;
  const display = Array.isArray(value) ? value.join(', ') : String(value);
  return (
    <tr>
      <td className="pr-3 py-1 text-xs text-muted-foreground whitespace-nowrap align-top font-medium">{label}</td>
      <td className="py-1 text-xs text-foreground">{display}</td>
    </tr>
  );
}

function TableOfContents({ sections, onScrollTo }: { sections: Section[]; onScrollTo: (index: number) => void }) {
  const [collapsed, setCollapsed] = useState(false);

  if (sections.length < 3) return null;

  return (
    <div className="rounded-lg border border-border bg-accent/5 p-3 mb-4">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider w-full"
      >
        <List className="h-3 w-3" />
        Contents
        <span className="text-[10px] font-normal">({sections.length} sections)</span>
        <span className="ml-auto text-[10px]">{collapsed ? 'Show' : 'Hide'}</span>
      </button>
      {!collapsed && (
        <ol className="mt-2 space-y-0.5 list-decimal list-inside">
          {sections.map((section, i) => (
            <li key={i}>
              <button
                onClick={() => onScrollTo(i)}
                className="text-xs text-foreground hover:text-accent transition-colors"
              >
                {section.heading}
              </button>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

export function WikiArticleDetail({ gid, onClose }: WikiArticleDetailProps) {
  const { data: article, isLoading } = useQuery({
    queryKey: ['wiki-article', gid],
    queryFn: () => apiFetch<ArticleFull>(`/knowledge/article/${gid}`),
  });

  const { data: relatedData } = useQuery({
    queryKey: ['wiki-related', gid],
    queryFn: () => apiFetch<{ items: RelatedArticle[] }>(`/knowledge/article/${gid}/related`),
    enabled: !!article && !('error' in article),
  });

  const { data: backlinksData } = useQuery({
    queryKey: ['wiki-backlinks', gid],
    queryFn: () => apiFetch<{ items: RelatedArticle[] }>(`/knowledge/article/${gid}/backlinks`),
    enabled: !!article && !('error' in article),
  });

  const { data: knownEntities } = useQuery({
    queryKey: ['known-entities'],
    queryFn: () => apiFetch<Array<{ gid: string; name: string; type: string }>>('/knowledge/entities/names'),
    staleTime: 5 * 60 * 1000, // 5 min cache
  });

  if (isLoading) {
    return (
      <div className="border-l border-border bg-card h-full overflow-y-auto p-6 animate-pulse">
        <div className="h-6 bg-muted rounded w-3/4 mb-4" />
        <div className="h-3 bg-muted rounded w-full mb-2" />
        <div className="h-3 bg-muted rounded w-5/6 mb-2" />
        <div className="h-3 bg-muted rounded w-2/3" />
      </div>
    );
  }

  if (!article || 'error' in article) {
    return (
      <div className="border-l border-border bg-card h-full flex items-center justify-center p-6">
        <p className="text-sm text-muted-foreground">Article not found</p>
      </div>
    );
  }

  const sections = article.body_json?.sections ?? [];
  const infobox = article.infobox_json ?? {};
  const sources = article.sources_json ?? [];
  const infoboxEntries = Object.entries(infobox).filter(
    ([k]) => !['type'].includes(k),
  );

  return (
    <div className="border-l border-border bg-card h-full overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-card border-b border-border px-6 py-3 flex items-center justify-between z-10">
        <h2 className="text-lg font-semibold text-foreground truncate">{article.title}</h2>
        <div className="flex items-center gap-1">
          <button
            onClick={() => window.location.href = `/graph?focus=${encodeURIComponent(article.gid)}`}
            title="Open in Graph"
            className="p-1.5 rounded-lg hover:bg-accent/10 text-muted-foreground hover:text-foreground transition-colors"
          >
            <Network className="h-4 w-4" />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-accent/10 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="px-6 py-4 space-y-5">
        {/* Meta bar */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
          <span className={cn(
            'font-semibold',
            article.confidence >= 1.0 ? 'text-success' : article.confidence >= 0.9 ? 'text-info' : 'text-warning',
          )}>
            <Shield className="inline h-3 w-3 mr-0.5" />
            {Math.round(article.confidence * 100)}% confidence
          </span>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {new Date(article.generated_at).toLocaleDateString()}
          </span>
          {sources.length > 0 && (
            <span>{sources.length} source{sources.length !== 1 ? 's' : ''}</span>
          )}
          {article.article_type && (
            <span className={cn('px-2 py-0.5 rounded-full text-[10px] font-medium', articleTypeBadge(article.article_type).className)}>
              {articleTypeBadge(article.article_type).label}
            </span>
          )}
        </div>

        {/* Infobox */}
        {infoboxEntries.length > 0 && (
          <div className="rounded-lg border border-border bg-accent/5 p-3">
            <table>
              <tbody>
                {infoboxEntries.map(([key, val]) => (
                  <InfoboxRow key={key} label={key.replace(/_/g, ' ')} value={val} />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Summary */}
        {article.summary && (
          <p className="text-sm text-foreground leading-relaxed italic border-l-2 border-accent/30 pl-3">
            {article.summary}
          </p>
        )}

        {/* Table of Contents */}
        <TableOfContents
          sections={sections}
          onScrollTo={(i) => {
            const el = document.getElementById(`section-${gid}-${i}`);
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }}
        />

        {/* Sections */}
        {sections.map((section, i) => (
          <div key={i} id={`section-${gid}-${i}`} className="scroll-mt-16">
            <h3 className="text-sm font-semibold text-foreground mb-1.5 border-b border-border/50 pb-1">
              {section.heading}
            </h3>
            <WikiLinkRenderer
              content={section.content}
              knownEntities={knownEntities ?? []}
              onEntityClick={(targetGid) => {
                window.location.hash = `#article/${targetGid}`;
              }}
            />
          </div>
        ))}

        {/* No content fallback */}
        {sections.length === 0 && !article.summary && (
          <p className="text-sm text-muted-foreground">
            This article has no content yet. It may need regeneration.
          </p>
        )}

        {/* Ego Graph */}
        <Suspense fallback={<div className="h-64 flex items-center justify-center text-xs text-muted-foreground">Loading graph…</div>}>
          <EgoGraphSidebar
            entityGid={gid}
            onNodeClick={(targetGid) => {
              window.location.hash = `#article/${targetGid}`;
            }}
          />
        </Suspense>

        {/* Related articles */}
        {relatedData && relatedData.items.length > 0 && (
          <div className="pt-3 border-t border-border">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Link2 className="h-3 w-3" />
              Related Articles
            </h3>
            <div className="space-y-1.5">
              {relatedData.items.slice(0, 8).map((r) => {
                const badge = articleTypeBadge(r.article_type);
                return (
                  <button
                    key={r.gid}
                    onClick={() => window.location.hash = `#article/${r.gid}`}
                    className="w-full text-left px-3 py-2 rounded-lg hover:bg-accent/5 transition-colors flex items-center gap-2"
                  >
                    <span className="text-xs font-medium text-foreground truncate flex-1">{r.title}</span>
                    {r.article_type !== 'entity' && (
                      <span className={cn('px-1.5 py-0.5 rounded-full text-[9px] font-medium shrink-0', badge.className)}>
                        {badge.label}
                      </span>
                    )}
                    <span className={cn('text-[10px] font-semibold shrink-0',
                      r.confidence >= 1.0 ? 'text-success' : r.confidence >= 0.9 ? 'text-info' : 'text-warning'
                    )}>
                      {Math.round(r.confidence * 100)}%
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Backlinks */}
        {backlinksData && backlinksData.items.length > 0 && (
          <div className="pt-3 border-t border-border">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <ArrowLeft className="h-3 w-3" />
              Referenced By
            </h3>
            <div className="space-y-1">
              {backlinksData.items.slice(0, 8).map((r) => (
                <button
                  key={r.gid}
                  onClick={() => window.location.hash = `#article/${r.gid}`}
                  className="w-full text-left px-3 py-1.5 rounded-lg hover:bg-accent/5 transition-colors text-xs text-foreground truncate"
                >
                  {r.title}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
