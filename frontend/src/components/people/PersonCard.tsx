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
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className={cn('h-2 w-2 rounded-full shrink-0', PRIORITY_DOT[person.priority] ?? 'bg-border-strong')} />
          <span className="font-semibold text-sm text-foreground truncate">{person.full_name}</span>
        </div>
        <span
          className={cn(
            'rounded-full px-2 py-0.5 text-xs font-medium capitalize shrink-0',
            ROLE_COLORS[person.role] ?? 'bg-accent/50 text-muted-foreground',
          )}
        >
          {person.role}
        </span>
      </div>

      {person.projects.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {person.projects.map((proj) => (
            <span
              key={proj}
              className="inline-flex items-center rounded-full bg-accent/20 text-accent px-2 py-0.5 text-[10px] font-medium"
            >
              {proj}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span
          className={cn(
            'rounded-full px-2 py-0.5 text-[10px] font-medium capitalize',
            SOURCE_STYLES[person.source] ?? 'bg-accent/50 text-muted-foreground',
          )}
        >
          {person.source}
        </span>
        <span>{timeAgo(person.learned_at)}</span>
      </div>
    </div>
  );
}
