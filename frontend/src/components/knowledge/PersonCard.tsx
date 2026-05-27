import { useQuery } from '@tanstack/react-query';
import { useEffect, useRef, useCallback } from 'react';
import { X, Loader2, Users, FileText, Mail, ChevronRight, ExternalLink } from 'lucide-react';
import { apiFetch } from '../../lib/api';

interface PersonProject {
  slug: string;
  name: string;
}

interface PersonDecision {
  text: string;
  date: string;
  project: string;
  status: string;
}

interface PersonEmail {
  subject: string;
  date: string;
}

interface RelatedPerson {
  gid: string;
  name: string;
  shared_projects: number;
}

interface PersonData {
  gid: string;
  name: string;
  projects: PersonProject[];
  decisions: PersonDecision[];
  email_count: number;
  recent_emails: PersonEmail[];
  related_people: RelatedPerson[];
  article_gid: string | null;
  error?: string;
}

function formatDate(d: string | null | undefined): string {
  if (!d) return '';
  try {
    return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch { return d; }
}

interface PersonCardProps {
  gid: string;
  onClose: () => void;
  onNavigateProject?: (slug: string) => void;
  onSelectPerson?: (gid: string) => void;
  onSelectArticle?: (gid: string) => void;
}

export function PersonCard({ gid, onClose, onNavigateProject, onSelectPerson, onSelectArticle }: PersonCardProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['person-card', gid],
    queryFn: () => apiFetch<PersonData>(`/knowledge/person/${encodeURIComponent(gid)}`),
    enabled: !!gid,
  });

  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Focus close button on mount so Escape key is immediately available
  useEffect(() => {
    closeButtonRef.current?.focus();
  }, [gid]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  return (
    <div
      role="dialog"
      aria-label="Person details"
      aria-modal="false"
      className="h-full flex flex-col bg-background border-l border-border"
      onKeyDown={handleKeyDown}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2 min-w-0">
          <Users className="h-4 w-4 text-accent shrink-0" />
          <h2 className="text-sm font-semibold text-foreground truncate">
            {isLoading ? 'Loading...' : data?.name ?? 'Person'}
          </h2>
        </div>
        <button
          ref={closeButtonRef}
          onClick={onClose}
          aria-label="Close person details"
          className="p-1 rounded hover:bg-muted transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Content */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      )}

      {data && !data.error && (
        <div className="flex-1 overflow-y-auto">
          {/* Summary stats */}
          <div className="px-4 py-3 border-b border-border flex items-center gap-4 text-xs text-muted-foreground">
            <span>{data.projects.length} project{data.projects.length !== 1 ? 's' : ''}</span>
            <span>{data.email_count} email{data.email_count !== 1 ? 's' : ''}</span>
            <span>{data.decisions.length} decision{data.decisions.length !== 1 ? 's' : ''}</span>
          </div>

          {/* Projects */}
          {data.projects.length > 0 && (
            <Section title="Projects">
              {data.projects.map((p) => (
                <button
                  key={p.slug}
                  onClick={() => onNavigateProject?.(p.slug)}
                  className="flex items-center gap-2 w-full text-left px-4 py-2 hover:bg-muted/30 transition-colors group"
                >
                  <ChevronRight className="h-3 w-3 text-muted-foreground group-hover:text-accent" />
                  <span className="text-sm text-foreground group-hover:text-accent truncate">{p.name}</span>
                </button>
              ))}
            </Section>
          )}

          {/* Decisions */}
          {data.decisions.length > 0 && (
            <Section title={`Recent Decisions (${data.decisions.length})`}>
              {data.decisions.slice(0, 5).map((d) => (
                <div key={`${d.date}-${d.text.slice(0, 30)}`} className="px-4 py-2 flex items-start justify-between gap-2">
                  <p className="text-sm text-foreground">{d.text}</p>
                  <span className="text-xs text-muted-foreground shrink-0">{formatDate(d.date)}</span>
                </div>
              ))}
              {data.decisions.length > 5 && (
                <p className="px-4 py-1 text-xs text-muted-foreground">
                  +{data.decisions.length - 5} more
                </p>
              )}
            </Section>
          )}

          {/* Recent Emails */}
          {data.recent_emails.length > 0 && (
            <Section title="Recent Emails">
              {data.recent_emails.map((e) => (
                <div key={`${e.date}-${e.subject}`} className="px-4 py-2 flex items-start justify-between gap-2">
                  <div className="flex items-start gap-2 min-w-0">
                    <Mail className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
                    <p className="text-sm text-foreground truncate">{e.subject}</p>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0">{formatDate(e.date)}</span>
                </div>
              ))}
            </Section>
          )}

          {/* Related People */}
          {data.related_people.length > 0 && (
            <Section title="Related People">
              <div className="px-4 py-2 flex flex-wrap gap-1.5">
                {data.related_people.map((rp) => (
                  <button
                    key={rp.gid}
                    onClick={() => onSelectPerson?.(rp.gid)}
                    className="flex items-center gap-1 px-2 py-1 bg-muted/50 rounded text-xs hover:bg-muted transition-colors"
                  >
                    <Users className="h-2.5 w-2.5" />
                    {rp.name}
                    <span className="text-muted-foreground">({rp.shared_projects})</span>
                  </button>
                ))}
              </div>
            </Section>
          )}

          {/* View article link */}
          {data.article_gid && (
            <div className="px-4 py-3 border-t border-border">
              <button
                onClick={() => onSelectArticle?.(data.article_gid!)}
                className="flex items-center gap-2 text-sm text-accent hover:underline"
              >
                <FileText className="h-3.5 w-3.5" />
                View wiki article
                <ExternalLink className="h-3 w-3" />
              </button>
            </div>
          )}

          {/* Empty state */}
          {data.projects.length === 0 && data.decisions.length === 0 && (
            <div className="px-4 py-8 text-center">
              <p className="text-sm text-muted-foreground">No detailed information available for this person.</p>
            </div>
          )}
        </div>
      )}

      {data?.error && (
        <div className="px-4 py-8 text-center">
          <p className="text-sm text-red-600 dark:text-red-400">{data.error}</p>
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-border">
      <div className="px-4 py-2 bg-muted/20">
        <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</h3>
      </div>
      {children}
    </div>
  );
}
