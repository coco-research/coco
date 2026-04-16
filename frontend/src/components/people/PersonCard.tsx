import { Mail } from 'lucide-react';
import { cn } from '../../lib/utils';
import { timeAgo } from '../../lib/utils';

export interface PersonPatterns {
  email_from?: string[];
  email_patterns?: string[];
  transcription_aliases?: string[];
  typical_topics?: string[];
  frequency?: string;
  communication_frequency?: string;
  observation_counts?: Record<string, number>;
  [key: string]: unknown;
}

export interface Person {
  full_name: string;
  role: string;
  priority: string;
  projects: string[];
  patterns: PersonPatterns;
  learned_at: string;
  source: string;
}

const FREQ_COLORS: Record<string, string> = {
  daily: 'bg-success/15 text-success',
  weekly: 'bg-info/15 text-info',
  monthly: 'bg-muted text-muted-foreground',
  rarely: 'bg-muted text-muted-foreground',
};

const ROLE_COLORS: Record<string, string> = {
  self: 'bg-accent/20 text-accent',
  manager: 'bg-destructive/20 text-destructive',
  collaborator: 'bg-info/20 text-info',
  stakeholder: 'bg-warning/20 text-warning',
  external: 'bg-accent/50 text-muted-foreground',
};

const PRIORITY_DOT: Record<string, string> = {
  high: 'bg-destructive',
  normal: 'bg-warning',
  low: 'bg-border-strong',
};

const SOURCE_STYLES: Record<string, string> = {
  taught: 'bg-accent/20 text-accent',
  observed: 'bg-info/20 text-info',
};

interface PersonCardProps {
  slug: string;
  person: Person;
  isSelected: boolean;
  onSelect: (slug: string) => void;
}

export function PersonCard({ slug, person, isSelected, onSelect }: PersonCardProps) {
  return (
    <div
      onClick={() => onSelect(slug)}
      className={cn(
        'bg-card rounded-xl border border-border p-5 cursor-pointer transition-all hover:shadow-md',
        isSelected && 'border-accent ring-2 ring-accent/20',
      )}
    >
      {/* Header: name + role */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className={cn('h-2 w-2 rounded-full shrink-0', PRIORITY_DOT[person.priority] ?? 'bg-border-strong')} />
          <span className="font-semibold text-sm text-foreground truncate">{person.full_name}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          {person.patterns?.frequency && (
            <span className={cn('rounded-full px-2 py-0.5 text-[10px] font-medium capitalize',
              FREQ_COLORS[person.patterns.frequency] ?? 'bg-muted text-muted-foreground')}>
              {person.patterns.frequency}
            </span>
          )}
          <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium capitalize',
            ROLE_COLORS[person.role] ?? 'bg-accent/50 text-muted-foreground')}>
            {person.role}
          </span>
        </div>
      </div>

      {/* Email count badge */}
      {(person.patterns?.email_from?.length ?? 0) > 0 && (
        <div className="flex items-center gap-1 mb-2">
          <Mail size={10} className="text-muted-foreground" />
          <span className="text-[10px] text-muted-foreground">
            {person.patterns.email_from!.length} address{person.patterns.email_from!.length !== 1 ? 'es' : ''}
          </span>
        </div>
      )}

      {/* Project chips */}
      {person.projects.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {person.projects.slice(0, 5).map((proj) => (
            <span key={proj}
              className="inline-flex items-center rounded-full bg-accent/20 text-accent px-2 py-0.5 text-[10px] font-medium">
              {proj}
            </span>
          ))}
          {person.projects.length > 5 && (
            <span className="inline-flex items-center rounded-full bg-muted text-muted-foreground px-2 py-0.5 text-[10px]">
              +{person.projects.length - 5}
            </span>
          )}
        </div>
      )}

      {/* Typical topics */}
      {(person.patterns?.typical_topics?.length ?? 0) > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {person.patterns.typical_topics!.slice(0, 4).map((t) => (
            <span key={t}
              className="inline-flex items-center rounded bg-muted/60 text-muted-foreground px-1.5 py-0.5 text-[10px]">
              {t}
            </span>
          ))}
        </div>
      )}

      {/* Footer: source + last seen */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className={cn('rounded-full px-2 py-0.5 text-[10px] font-medium capitalize',
          SOURCE_STYLES[person.source] ?? 'bg-accent/50 text-muted-foreground')}>
          {person.source}
        </span>
        <span title={person.learned_at}>seen {timeAgo(person.learned_at)}</span>
      </div>
    </div>
  );
}
