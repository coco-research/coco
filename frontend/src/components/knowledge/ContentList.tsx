import { useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Mail, Mic, Bug, FileText, FileQuestion } from 'lucide-react';
import { cn } from '../../lib/utils';
import { timeAgo } from '../../lib/utils';
import { useListNavigation } from '../../hooks/useListNavigation';
import type { ReactNode } from 'react';

export interface ContentItemMetadata {
  from?: string;
  to?: string;
  cc?: string | null;
  date?: string;
  classification?: {
    category?: string;
    confidence?: number;
    reason?: string;
    project_id?: string;
  };
  [key: string]: unknown;
}

export interface ContentItem {
  id: string;
  title: string;
  source: string;
  source_id: string | null;
  source_path: string | null;
  content_type: string | null;
  raw_text: string | null;
  processed_text: string | null;
  metadata: ContentItemMetadata | null;
  status: string;
  relevance_score: number | null;
  created_at: string;
  updated_at: string;
  ingested_at: string | null;
  processed_at: string | null;
}

interface ContentListProps {
  items: ContentItem[];
  total: number;
  isLoading: boolean;
  selectedId: string | null;
  onSelect: (item: ContentItem) => void;
}

const SOURCE_ICONS: Record<string, ReactNode> = {
  email: <Mail className="h-4 w-4 text-info" />,
  voice: <Mic className="h-4 w-4 text-accent" />,
  jira: <Bug className="h-4 w-4 text-warning" />,
  confluence: <FileText className="h-4 w-4 text-muted-foreground" />,
};

const STATUS_STYLES: Record<string, string> = {
  complete: 'bg-success/20 text-success',
  processed: 'bg-success/20 text-success',
  triaged: 'bg-warning/20 text-warning',
  classified: 'bg-info/20 text-info',
  ingested: 'bg-accent/50 text-muted-foreground',
  pending: 'bg-accent/50 text-muted-foreground',
};

const ROW_HEIGHT = 52; // estimated row height in px
const LIMIT = 50;

export function ContentList({ items, total, isLoading, selectedId, onSelect }: ContentListProps) {
  const [searchParams, setSearchParams] = useSearchParams();
  const offset = parseInt(searchParams.get('offset') ?? '0', 10);
  const scrollRef = useRef<HTMLDivElement>(null);

  // j/k keyboard navigation
  const { selectedIndex, getItemProps, containerRef } = useListNavigation(items, {
    onSelect: (item) => onSelect(item),
  });

  // List virtualization for 1000+ items
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 10,
  });

  function setOffset(next: number) {
    setSearchParams((prev) => {
      const p = new URLSearchParams(prev);
      if (next > 0) {
        p.set('offset', String(next));
      } else {
        p.delete('offset');
      }
      return p;
    });
  }

  const page = Math.floor(offset / LIMIT) + 1;
  const totalPages = Math.ceil(total / LIMIT);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground text-sm">
        Loading content...
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground text-sm gap-2">
        <FileQuestion className="h-8 w-8" />
        No content found
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="flex flex-col h-full"
      tabIndex={0}
      onFocus={() => {/* ensure container is focusable for j/k nav */}}
    >
      {/* Header row */}
      <div className="grid grid-cols-[2rem_1fr_8rem_6rem_5rem] gap-3 px-4 py-2 text-xs font-medium text-muted-foreground border-b border-border uppercase tracking-wide bg-card">
        <span />
        <span>Title</span>
        <span>Project</span>
        <span>Status</span>
        <span>Date</span>
      </div>

      {/* Virtualized content rows */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div
          style={{
            height: virtualizer.getTotalSize(),
            position: 'relative',
            width: '100%',
          }}
        >
          {virtualizer.getVirtualItems().map((virtualRow) => {
            const item = items[virtualRow.index];
            const isKbSelected = virtualRow.index === selectedIndex;

            return (
              <button
                key={item.id}
                ref={virtualizer.measureElement}
                data-index={virtualRow.index}
                {...getItemProps(virtualRow.index)}
                onClick={() => onSelect(item)}
                className={cn(
                  'w-full grid grid-cols-[2rem_1fr_8rem_6rem_5rem] gap-3 px-4 py-3 text-left text-sm',
                  'border-b border-border/50 transition-colors',
                  'hover:bg-accent/50',
                  selectedId === item.id && 'bg-accent/20',
                  isKbSelected && 'ring-2 ring-primary/40 bg-primary/5',
                )}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualRow.start}px)`,
                }}
              >
                <span className="flex items-center justify-center">
                  {SOURCE_ICONS[item.source] ?? <FileQuestion className="h-4 w-4 text-muted-foreground" />}
                </span>
                <span className="truncate text-foreground">{item.title}</span>
                <span className="truncate text-muted-foreground text-xs">
                  {item.metadata?.classification?.project_id ?? '--'}
                </span>
                <span>
                  <span
                    className={cn(
                      'inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize',
                      STATUS_STYLES[item.status] ?? 'bg-accent/50 text-muted-foreground',
                    )}
                  >
                    {item.status}
                  </span>
                </span>
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {timeAgo(item.created_at)}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-border text-sm text-muted-foreground">
        <span>
          {total} item{total !== 1 ? 's' : ''} — page {page} of {totalPages || 1}
        </span>
        <div className="flex gap-2">
          <button
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - LIMIT))}
            className={cn(
              'px-3 py-1.5 rounded-lg text-sm border border-border bg-card',
              offset === 0
                ? 'opacity-40 cursor-not-allowed'
                : 'hover:bg-accent/50 text-foreground',
            )}
          >
            Previous
          </button>
          <button
            disabled={offset + LIMIT >= total}
            onClick={() => setOffset(offset + LIMIT)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-sm border border-border bg-card',
              offset + LIMIT >= total
                ? 'opacity-40 cursor-not-allowed'
                : 'hover:bg-accent/50 text-foreground',
            )}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
