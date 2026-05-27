import { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiPatch } from '../../lib/api';
import { cn } from '../../lib/utils';

interface DisplayConfig {
  max_projects_shown?: number;
  collapse_quiet_projects?: boolean;
  show_cost?: boolean;
  emoji?: boolean;
}

interface Config {
  display?: DisplayConfig;
  // Flat legacy fallbacks
  max_projects_shown?: number;
  collapse_quiet_projects?: boolean;
  show_cost_on_dashboard?: boolean;
  [key: string]: unknown;
}

interface DisplaySettingsProps {
  onSaveStatus: (status: 'idle' | 'saving' | 'saved') => void;
}

export function DisplaySettings({ onSaveStatus }: DisplaySettingsProps) {
  const qc = useQueryClient();
  const { data: config } = useQuery<Config>({
    queryKey: ['settings'],
    queryFn: () => apiFetch<Config>('/settings'),
  });

  const [maxProjects, setMaxProjects] = useState(10);
  const [collapseQuiet, setCollapseQuiet] = useState(true);
  const [showCost, setShowCost] = useState(true);

  useEffect(() => {
    if (!config) return;
    const d = config.display;
    if (d) {
      if (d.max_projects_shown != null) setMaxProjects(d.max_projects_shown);
      if (d.collapse_quiet_projects != null) setCollapseQuiet(d.collapse_quiet_projects);
      if (d.show_cost != null) setShowCost(d.show_cost);
    }
    // Flat legacy fallbacks
    if (config.max_projects_shown != null) setMaxProjects(config.max_projects_shown);
    if (config.collapse_quiet_projects != null) setCollapseQuiet(config.collapse_quiet_projects);
    if (config.show_cost_on_dashboard != null) setShowCost(config.show_cost_on_dashboard);
  }, [config]);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const save = useCallback(
    (patch: Partial<Config>) => {
      onSaveStatus('saving');
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(async () => {
        await apiPatch('/settings', patch);
        void qc.invalidateQueries({ queryKey: ['settings'] });
        onSaveStatus('saved');
        setTimeout(() => onSaveStatus('idle'), 2000);
      }, 1000);
    },
    [onSaveStatus, qc],
  );

  const inputCls =
    'w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

  return (
    <div className="space-y-6 max-w-lg">
      <div>
        <label htmlFor="display-max-projects" className="block text-sm font-medium text-foreground mb-1">Max Projects Shown</label>
        <p id="display-max-projects-desc" className="text-xs text-muted-foreground mb-2">
          Number of projects visible on the dashboard before &quot;Show more&quot;.
        </p>
        <input
          id="display-max-projects"
          aria-describedby="display-max-projects-desc"
          type="number"
          min={1}
          max={50}
          value={maxProjects}
          onChange={(e) => {
            const v = Number(e.target.value);
            setMaxProjects(v);
            save({ display: { ...config?.display, max_projects_shown: v } });
          }}
          className={inputCls}
        />
      </div>

      <div className="flex items-center justify-between py-3 border-b border-border">
        <div>
          <p className="text-sm font-medium text-foreground">Collapse Quiet Projects</p>
          <p className="text-xs text-muted-foreground">
            Auto-collapse projects with no activity in 7+ days.
          </p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={collapseQuiet}
          aria-label="Collapse quiet projects"
          onClick={() => {
            const v = !collapseQuiet;
            setCollapseQuiet(v);
            save({ display: { ...config?.display, collapse_quiet_projects: v } });
          }}
          className={cn(
            'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
            collapseQuiet ? 'bg-accent' : 'bg-border',
          )}
        >
          <span
            className={cn(
              'inline-block h-4 w-4 transform rounded-full bg-card transition-transform',
              collapseQuiet ? 'translate-x-6' : 'translate-x-1',
            )}
          />
        </button>
      </div>

      <div className="flex items-center justify-between py-3 border-b border-border">
        <div>
          <p className="text-sm font-medium text-foreground">Show Cost on Dashboard</p>
          <p className="text-xs text-muted-foreground">
            Display the cost summary card on the main dashboard.
          </p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={showCost}
          aria-label="Show cost on dashboard"
          onClick={() => {
            const v = !showCost;
            setShowCost(v);
            save({ display: { ...config?.display, show_cost: v } });
          }}
          className={cn(
            'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
            showCost ? 'bg-accent' : 'bg-border',
          )}
        >
          <span
            className={cn(
              'inline-block h-4 w-4 transform rounded-full bg-card transition-transform',
              showCost ? 'translate-x-6' : 'translate-x-1',
            )}
          />
        </button>
      </div>
    </div>
  );
}
