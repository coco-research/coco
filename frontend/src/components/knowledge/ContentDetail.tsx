import { useState } from 'react';
import DOMPurify from 'dompurify';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Mail, Mic, Bug, FileText, FileQuestion, ChevronDown } from 'lucide-react';
import { apiFetch, apiPost } from '../../lib/api';
import { cn, timeAgo } from '../../lib/utils';
import { PropertiesPanel } from '../shared/PropertiesPanel';
import { PropertyField } from '../shared/PropertyField';
import { CommentThread } from '../shared/CommentThread';
import type { ContentItem } from './ContentList';
import type { ReactNode } from 'react';

interface Project {
  id: string;
  name: string;
}

interface ContentDetailProps {
  item: ContentItem;
  onClose: () => void;
}

const SOURCE_ICONS: Record<string, ReactNode> = {
  email: <Mail className="h-4 w-4 text-info" />,
  voice: <Mic className="h-4 w-4 text-accent" />,
  jira: <Bug className="h-4 w-4 text-warning" />,
  confluence: <FileText className="h-4 w-4 text-muted-foreground" />,
};

const STATUS_STYLES: Record<string, string> = {
  complete: 'bg-success/20 text-success',
  triaged: 'bg-warning/20 text-warning',
  classified: 'bg-info/20 text-info',
  ingested: 'bg-accent/50 text-muted-foreground',
};

export function ContentDetail({ item, onClose }: ContentDetailProps) {
  const queryClient = useQueryClient();
  const [classifyOpen, setClassifyOpen] = useState(false);

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiFetch<Project[]>('/projects'),
  });

  const classifyMutation = useMutation({
    mutationFn: (projectId: string) =>
      apiPost(`/content/${item.id}/classify`, { project_id: projectId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
      setClassifyOpen(false);
    },
  });

  const dismissMutation = useMutation({
    mutationFn: () => apiPost(`/content/${item.id}/dismiss`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['content'] });
      onClose();
    },
  });

  const bodyText = item.processed_text || item.raw_text || '';
  const isHtml = item.source === 'email' && bodyText.includes('<');

  return (
    <PropertiesPanel
      open={true}
      onClose={onClose}
      title={item.title}
      subtitle={`${item.source} \u00b7 ${timeAgo(item.created_at)}`}
      width="lg"
    >
      {/* Status + source */}
      <div className="flex items-center gap-2 mb-4">
        {SOURCE_ICONS[item.source] ?? <FileQuestion className="h-4 w-4 text-muted-foreground" />}
        <span
          className={cn(
            'inline-block px-2 py-0.5 rounded-full text-xs font-medium capitalize',
            STATUS_STYLES[item.status] ?? 'bg-accent/50 text-muted-foreground',
          )}
        >
          {item.status}
        </span>
      </div>

      {/* Body */}
      <div className="mb-4">
        {isHtml ? (
          <div
            className="prose prose-sm max-w-none text-foreground"
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(bodyText) }}
          />
        ) : (
          <pre className="whitespace-pre-wrap text-sm text-foreground font-sans leading-relaxed">
            {bodyText || <span className="text-muted-foreground italic">No content available</span>}
          </pre>
        )}
      </div>

      {/* Metadata fields */}
      <div className="border-t border-border pt-4 mb-4">
        {item.metadata?.from && <PropertyField label="From" value={item.metadata.from} />}
        {item.metadata?.to && <PropertyField label="To" value={item.metadata.to} />}
        {item.metadata?.classification?.project_id && (
          <PropertyField label="Project" value={item.metadata.classification.project_id} />
        )}
        {item.metadata?.classification?.category && (
          <PropertyField label="Category" value={item.metadata.classification.category} />
        )}
        {item.relevance_score != null && (
          <PropertyField label="Relevance" value={`${(item.relevance_score * 100).toFixed(0)}%`} />
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 border-t border-border pt-4">
        <div className="relative">
          <button
            onClick={() => setClassifyOpen(!classifyOpen)}
            disabled={classifyMutation.isPending}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg',
              'bg-accent text-accent-foreground hover:bg-accent/80 shadow-sm transition-all',
              classifyMutation.isPending && 'opacity-50',
            )}
          >
            Classify
            <ChevronDown className="h-3.5 w-3.5" />
          </button>
          {classifyOpen && projects && (
            <div className="absolute bottom-full left-0 mb-1 w-48 bg-card border border-border rounded-xl shadow-lg overflow-hidden z-10">
              {projects.map((p) => (
                <button
                  key={p.id}
                  onClick={() => classifyMutation.mutate(p.id)}
                  className="w-full text-left px-3 py-2 text-sm text-foreground hover:bg-accent/50 transition-colors"
                >
                  {p.name}
                </button>
              ))}
              {projects.length === 0 && (
                <div className="px-3 py-2 text-sm text-muted-foreground">No projects</div>
              )}
            </div>
          )}
        </div>

        <button
          onClick={() => dismissMutation.mutate()}
          disabled={dismissMutation.isPending}
          className={cn(
            'px-3 py-1.5 text-sm rounded-lg',
            'bg-destructive/20 text-destructive hover:bg-destructive/30 transition-all',
            dismissMutation.isPending && 'opacity-50',
          )}
        >
          Dismiss
        </button>
      </div>

      {/* Comments */}
      <div className="mt-4">
        <CommentThread entityType="content" entityId={item.id} />
      </div>
    </PropertiesPanel>
  );
}
