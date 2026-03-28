import { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiPatch } from '../../lib/api';

interface Config {
  morning_cutoff_hour?: number;
  quick_reopen_minutes?: number;
  quick_reopen_threshold_min?: number;  // legacy fallback
  briefing_lookback_default?: string;
  [key: string]: unknown;
}

interface GeneralSettingsProps {
  onSaveStatus: (status: 'idle' | 'saving' | 'saved') => void;
}

export function GeneralSettings({ onSaveStatus }: GeneralSettingsProps) {
  const qc = useQueryClient();
  const { data: config } = useQuery<Config>({
    queryKey: ['settings'],
    queryFn: () => apiFetch<Config>('/settings'),
  });

  const [morningHour, setMorningHour] = useState(10);
  const [reopenThreshold, setReopenThreshold] = useState(30);

  // Sync from server
  useEffect(() => {
    if (!config) return;
    if (config.morning_cutoff_hour != null) setMorningHour(config.morning_cutoff_hour);
    const reopenVal = config.quick_reopen_minutes ?? config.quick_reopen_threshold_min;
    if (reopenVal != null) setReopenThreshold(reopenVal);
  }, [config]);

  // Debounced save
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
        <label className="block text-sm font-medium text-foreground mb-1">Morning Cutoff Hour</label>
        <p className="text-xs text-muted-foreground mb-2">
          CoCo waits until this hour before sending morning briefs.
        </p>
        <input
          type="number"
          min={1}
          max={12}
          value={morningHour}
          onChange={(e) => {
            const v = Number(e.target.value);
            setMorningHour(v);
            save({ morning_cutoff_hour: v });
          }}
          className={inputCls}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-1">
          Quick Reopen Threshold (minutes)
        </label>
        <p className="text-xs text-muted-foreground mb-2">
          If you reopen a dismissed item within this window, CoCo re-promotes it.
        </p>
        <input
          type="number"
          min={1}
          max={120}
          value={reopenThreshold}
          onChange={(e) => {
            const v = Number(e.target.value);
            setReopenThreshold(v);
            save({ quick_reopen_minutes: v });
          }}
          className={inputCls}
        />
      </div>

    </div>
  );
}
