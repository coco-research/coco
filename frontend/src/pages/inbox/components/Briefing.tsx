/**
 * Briefing — Zone 1 of the Inbox 3-zone deck.
 *
 * Narrative AI memo over today's queue + a strip of hero stats. Pulls from
 * the `/api/briefing` payload (TanStack Query owned by parent — passed in).
 *
 * DESIGN.md §1.3 says the briefing reads like a "morning memo": short prose,
 * bold names, terminal stats line. We keep the styling minimal/light per
 * project_redesign_decision (Path A Light).
 */

import type { ReactElement } from 'react';
import { Bell } from 'lucide-react';
import { cn } from '../../../lib/utils';

export interface BriefingHeroStat {
  value: string | number;
  label: string;
}

export interface BriefingProps {
  /** Greeting line (e.g. "Good morning, Rijul"). */
  greeting?: string;
  /** Localized date string. */
  dateLabel?: string;
  /** Markdown-ish narrative paragraphs. Plain strings — no HTML allowed. */
  paragraphs?: string[];
  /** Up to 4 stat tiles below the memo. */
  heroStats?: BriefingHeroStat[];
  /** Active flag — parent toggles when user navigates with j/k. */
  active?: boolean;
  /** True while the underlying query is loading. */
  loading?: boolean;
  /** True when the query errored out. */
  errored?: boolean;
}

export function Briefing(props: BriefingProps): ReactElement {
  const {
    greeting,
    dateLabel,
    paragraphs,
    heroStats,
    active,
    loading,
    errored,
  } = props;

  if (loading) {
    return (
      <section
        className={cn(
          'rounded-xl border border-border bg-card p-5 space-y-3',
          'animate-pulse',
        )}
        aria-busy="true"
        aria-label="Morning briefing"
      >
        <div className="h-4 w-40 rounded bg-muted/60" />
        <div className="h-7 w-3/5 rounded bg-muted/50" />
        <div className="h-3 w-full rounded bg-muted/40" />
        <div className="h-3 w-11/12 rounded bg-muted/40" />
        <div className="h-3 w-4/5 rounded bg-muted/40" />
      </section>
    );
  }

  if (errored) {
    return (
      <section
        className="rounded-xl border border-border bg-card p-5"
        aria-label="Morning briefing"
      >
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Bell size={14} />
          <span>Briefing unavailable — check the backend connection.</span>
        </div>
      </section>
    );
  }

  return (
    <section
      className={cn(
        'rounded-xl border bg-card p-5 transition-colors',
        active ? 'border-primary/40' : 'border-border',
      )}
      aria-label="Morning briefing"
      data-active={active ? 'true' : 'false'}
    >
      <header className="mb-4">
        <div className="text-[11px] uppercase tracking-wider text-muted-foreground font-medium">
          Morning briefing{dateLabel ? ` · ${dateLabel}` : ''}
        </div>
        {greeting && (
          <h1 className="text-lg font-semibold text-foreground mt-1">
            {greeting}
          </h1>
        )}
      </header>

      {paragraphs && paragraphs.length > 0 ? (
        <div className="text-sm leading-6 text-foreground/90 space-y-2">
          {paragraphs.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground italic">
          Nothing notable since yesterday.
        </p>
      )}

      {heroStats && heroStats.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
          {heroStats.map((stat, i) => (
            <div
              key={i}
              className="rounded-lg border border-border bg-muted/20 px-3 py-2.5"
            >
              <div className="text-xl font-semibold text-foreground tabular-nums">
                {stat.value}
              </div>
              <div className="text-[11px] text-muted-foreground mt-0.5">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default Briefing;
