import { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, apiPatch } from '../../lib/api';
import { cn } from '../../lib/utils';

type AutonomyMode = 'careful' | 'normal' | 'yolo';
type PerToolLevel = 'auto' | 'ask' | 'always_ask';

interface PerToolConfig {
  classify_knowledge: PerToolLevel;
  reclassify: PerToolLevel;
  dismiss_todos: PerToolLevel;
  approve_drafts: PerToolLevel;
  update_brain: PerToolLevel;
  create_jira: PerToolLevel;
  update_confluence: PerToolLevel;
  external_comms: PerToolLevel;
  git_push: PerToolLevel;
  delete: PerToolLevel;
}

interface YoloProfile {
  description: string;
  per_tool: Partial<PerToolConfig>;
}

interface TimeAwareScheduleEntry {
  hours?: number[];
  bias?: string;
  threshold_adjust?: number;
}

interface TimeAwareConfig {
  enabled?: boolean;
  schedule?: Record<string, TimeAwareScheduleEntry>;
  deadline_proximity_days?: number;
  deadline_threshold_adjust?: number;
}

interface YoloConfig {
  auto_approve_above?: number;
  skip_and_queue_below?: number;
  always_ask?: string[];
  max_jira_tickets_per_session?: number;
  max_draft_approvals_per_session?: number;
  per_tool?: Partial<PerToolConfig>;
  active_profile?: string | null;
  profiles?: Record<string, YoloProfile>;
  time_aware?: TimeAwareConfig;
  audit_log?: string;
}

interface Config {
  launch_ui?: string;
  autonomy_mode?: AutonomyMode;
  yolo?: YoloConfig;
  yolo_guardrails?: {
    auto_approve_threshold?: number;
    skip_below_threshold?: number;
    max_jira_tickets?: number;
    max_draft_approvals?: number;
  };
}

interface AutonomySettingsProps {
  onSaveStatus: (status: 'idle' | 'saving' | 'saved' | 'error') => void;
}

// --- Constants ---

const modeDescriptions: Record<AutonomyMode, string> = {
  careful: 'Ask before every action. Maximum oversight.',
  normal: 'Auto-approve routine tasks. Flag anything unusual.',
  yolo: 'Full autonomy with guardrails. CoCo acts, you review.',
};

const modeColors: Record<AutonomyMode, string> = {
  careful: 'border-info text-info bg-info/20',
  normal: 'border-warning text-warning bg-warning/20',
  yolo: 'border-error text-destructive bg-destructive/20',
};

const perToolActions: { key: keyof PerToolConfig; label: string; defaultLevel: PerToolLevel }[] = [
  { key: 'classify_knowledge', label: 'Classify knowledge', defaultLevel: 'auto' },
  { key: 'reclassify', label: 'Reclassify items', defaultLevel: 'auto' },
  { key: 'dismiss_todos', label: 'Dismiss todos', defaultLevel: 'auto' },
  { key: 'approve_drafts', label: 'Approve drafts', defaultLevel: 'ask' },
  { key: 'update_brain', label: 'Update brain.json', defaultLevel: 'ask' },
  { key: 'create_jira', label: 'Create Jira tickets', defaultLevel: 'ask' },
  { key: 'update_confluence', label: 'Update Confluence', defaultLevel: 'ask' },
  { key: 'external_comms', label: 'Send emails / replies', defaultLevel: 'always_ask' },
  { key: 'git_push', label: 'Git push', defaultLevel: 'always_ask' },
  { key: 'delete', label: 'Delete anything', defaultLevel: 'always_ask' },
];

const levelColors: Record<PerToolLevel, string> = {
  auto: 'bg-accent/20 text-accent border-accent',
  ask: 'bg-warning/20 text-warning border-warning',
  always_ask: 'bg-destructive/20 text-destructive border-destructive',
};

const levelLabels: Record<PerToolLevel, string> = {
  auto: 'Auto',
  ask: 'Ask',
  always_ask: 'Always Ask',
};

const profileColors: Record<string, string> = {
  triage: 'border-info text-info bg-info/10',
  pm: 'border-warning text-warning bg-warning/10',
  full: 'border-destructive text-destructive bg-destructive/10',
};

const trustMatrix: { action: string; careful: string; normal: string; yolo: string }[] = [
  { action: 'Create Jira tickets', careful: 'Ask', normal: 'Ask', yolo: 'Per-tool' },
  { action: 'Approve email drafts', careful: 'Ask', normal: 'Ask', yolo: 'Per-tool' },
  { action: 'Reclassify knowledge', careful: 'Ask', normal: 'Auto', yolo: 'Per-tool' },
  { action: 'Dismiss low-priority todos', careful: 'Ask', normal: 'Ask', yolo: 'Per-tool' },
  { action: 'Spend > $1', careful: 'Ask', normal: 'Ask', yolo: 'Ask' },
  { action: 'Update brain.json', careful: 'Ask', normal: 'Ask', yolo: 'Per-tool' },
];

const periodLabels: Record<string, string> = {
  morning: 'Morning (6-9)',
  focus: 'Focus (10-11, 14-16)',
  eod: 'End of day (17-19)',
  off_hours: 'Off hours (20-5)',
};

const biasLabels: Record<string, { label: string; color: string }> = {
  higher: { label: 'More permissive', color: 'text-accent' },
  normal: { label: 'No change', color: 'text-muted-foreground' },
  lower: { label: 'More cautious', color: 'text-warning' },
};

// Actions that can never be downgraded below always_ask (safety invariant)
const IMMUTABLE_ALWAYS_ASK = new Set<keyof PerToolConfig>([
  'external_comms',
  'git_push',
  'delete',
]);

// --- Helpers ---

function deepMergePatches(base: Record<string, unknown>, patch: Record<string, unknown>): Record<string, unknown> {
  const result = { ...base };
  for (const [k, v] of Object.entries(patch)) {
    if (v && typeof v === 'object' && !Array.isArray(v) && result[k] && typeof result[k] === 'object') {
      result[k] = deepMergePatches(result[k] as Record<string, unknown>, v as Record<string, unknown>);
    } else {
      result[k] = v;
    }
  }
  return result;
}

function buildFullPerTool(profilePerTool: Partial<PerToolConfig>): PerToolConfig {
  return Object.fromEntries(
    perToolActions.map(({ key, defaultLevel }) => [key, profilePerTool[key] ?? defaultLevel]),
  ) as PerToolConfig;
}

// --- Component ---

export function AutonomySettings({ onSaveStatus }: AutonomySettingsProps) {
  const qc = useQueryClient();
  const { data: config, isLoading } = useQuery<Config>({
    queryKey: ['settings'],
    queryFn: () => apiFetch<Config>('/settings'),
  });

  const [mode, setMode] = useState<AutonomyMode | null>(null);
  const [autoApprove, setAutoApprove] = useState<number | null>(null);
  const [skipBelow, setSkipBelow] = useState<number | null>(null);
  const [maxJira, setMaxJira] = useState<number | null>(null);
  const [maxDrafts, setMaxDrafts] = useState<number | null>(null);
  const [perTool, setPerTool] = useState<Partial<PerToolConfig> | null>(null);
  const [activeProfile, setActiveProfile] = useState<string | null>(null);
  const [timeAwareEnabled, setTimeAwareEnabled] = useState<boolean | null>(null);
  const [deadlineProximity, setDeadlineProximity] = useState<number | null>(null);
  const [dirty, setDirty] = useState(false);

  // Sync from server only when not dirty (prevents overwriting in-progress edits)
  useEffect(() => {
    if (!config || dirty) return;
    if (config.autonomy_mode) setMode(config.autonomy_mode);
    const y = config.yolo;
    if (y) {
      if (y.auto_approve_above != null) setAutoApprove(y.auto_approve_above);
      if (y.skip_and_queue_below != null) setSkipBelow(y.skip_and_queue_below);
      if (y.max_jira_tickets_per_session != null) setMaxJira(y.max_jira_tickets_per_session);
      if (y.max_draft_approvals_per_session != null) setMaxDrafts(y.max_draft_approvals_per_session);
      if (y.per_tool) setPerTool(y.per_tool);
      if (y.active_profile !== undefined) setActiveProfile(y.active_profile);
      if (y.time_aware) {
        if (y.time_aware.enabled != null) setTimeAwareEnabled(y.time_aware.enabled);
        if (y.time_aware.deadline_proximity_days != null)
          setDeadlineProximity(y.time_aware.deadline_proximity_days);
      }
    }
    // Legacy fallback
    const g = config.yolo_guardrails;
    if (g) {
      if (g.auto_approve_threshold != null) setAutoApprove(g.auto_approve_threshold);
      if (g.skip_below_threshold != null) setSkipBelow(g.skip_below_threshold);
      if (g.max_jira_tickets != null) setMaxJira(g.max_jira_tickets);
      if (g.max_draft_approvals != null) setMaxDrafts(g.max_draft_approvals);
    }
  }, [config, dirty]);

  // Accumulating debounced save — merges rapid patches, flushes once
  const pendingRef = useRef<Record<string, unknown>>({});
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const save = useCallback(
    (patch: Record<string, unknown>) => {
      setDirty(true);
      onSaveStatus('saving');
      pendingRef.current = deepMergePatches(pendingRef.current, patch);
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(async () => {
        const merged = pendingRef.current;
        pendingRef.current = {};
        try {
          await apiPatch('/settings', merged);
          void qc.invalidateQueries({ queryKey: ['settings'] });
          onSaveStatus('saved');
          setTimeout(() => {
            onSaveStatus('idle');
            setDirty(false);
          }, 2000);
        } catch {
          onSaveStatus('error');
          // Re-sync from server on failure
          void qc.invalidateQueries({ queryKey: ['settings'] });
          setTimeout(() => {
            onSaveStatus('idle');
            setDirty(false);
          }, 3000);
        }
      }, 1000);
    },
    [onSaveStatus, qc],
  );

  function selectMode(m: AutonomyMode) {
    setMode(m);
    save({ autonomy_mode: m });
  }

  function selectProfile(name: string | null) {
    const profiles = config?.yolo?.profiles;
    if (name && profiles?.[name]) {
      const profile = profiles[name];
      const fullPerTool = buildFullPerTool(profile.per_tool);
      setActiveProfile(name);
      setPerTool(fullPerTool);
      save({ yolo: { active_profile: name, per_tool: fullPerTool } });
    } else {
      setActiveProfile(null);
      save({ yolo: { active_profile: null } });
    }
  }

  function setToolLevel(key: keyof PerToolConfig, level: PerToolLevel) {
    if (IMMUTABLE_ALWAYS_ASK.has(key) && level !== 'always_ask') return;
    const updated = { ...(perTool ?? {}), [key]: level };
    setPerTool(updated);
    setActiveProfile(null);
    save({ yolo: { per_tool: { [key]: level }, active_profile: null } });
  }

  // Derived values with safe defaults
  const effectiveMode = mode ?? config?.autonomy_mode ?? 'normal';
  const effectiveAutoApprove = autoApprove ?? config?.yolo?.auto_approve_above ?? 0.85;
  const effectiveSkipBelow = skipBelow ?? config?.yolo?.skip_and_queue_below ?? 0.7;
  const effectiveMaxJira = maxJira ?? config?.yolo?.max_jira_tickets_per_session ?? 10;
  const effectiveMaxDrafts = maxDrafts ?? config?.yolo?.max_draft_approvals_per_session ?? 20;
  const effectivePerTool = perTool ?? config?.yolo?.per_tool ?? {};
  const effectiveTimeEnabled = timeAwareEnabled ?? config?.yolo?.time_aware?.enabled ?? true;
  const effectiveDeadline = deadlineProximity ?? config?.yolo?.time_aware?.deadline_proximity_days ?? 2;
  const profiles = config?.yolo?.profiles ?? {};
  const timeAware = config?.yolo?.time_aware;

  // Threshold validation warnings
  const thresholdWarning =
    effectiveAutoApprove < 0.75
      ? 'Very permissive — most items will auto-approve'
      : effectiveAutoApprove <= effectiveSkipBelow
        ? 'Auto-approve must be higher than skip-below'
        : null;

  const inputCls =
    'w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

  if (isLoading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-24 bg-card/50 rounded-lg" />
        <div className="h-48 bg-card/50 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Mode selector */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
          Autonomy Mode
        </h3>
        <div role="radiogroup" aria-label="Autonomy mode" className="grid grid-cols-3 gap-3">
          {(['careful', 'normal', 'yolo'] as AutonomyMode[]).map((m) => (
            <button
              key={m}
              role="radio"
              aria-checked={effectiveMode === m}
              onClick={() => selectMode(m)}
              className={cn(
                'p-4 rounded-lg border-2 text-left transition-all cursor-pointer',
                effectiveMode === m
                  ? modeColors[m]
                  : 'border-border text-muted-foreground hover:border-border hover:bg-accent/50/50',
              )}
            >
              <p className="text-lg font-semibold uppercase mb-1">{m}</p>
              <p className="text-xs opacity-80">{modeDescriptions[m]}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Trust matrix */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
          Trust Matrix
        </h3>
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left">
                <th className="px-4 py-2 font-medium text-muted-foreground">Action</th>
                <th className="px-4 py-2 font-medium text-info text-center">Careful</th>
                <th className="px-4 py-2 font-medium text-warning text-center">Normal</th>
                <th className="px-4 py-2 font-medium text-destructive text-center">Yolo</th>
              </tr>
            </thead>
            <tbody>
              {trustMatrix.map((row) => (
                <tr key={row.action} className="border-b border-border/50">
                  <td className="px-4 py-2 text-foreground">{row.action}</td>
                  {(['careful', 'normal', 'yolo'] as const).map((col) => (
                    <td
                      key={col}
                      className={cn(
                        'px-4 py-2 text-center text-xs font-medium',
                        row[col] === 'Auto' || row[col] === 'Per-tool'
                          ? 'text-accent'
                          : 'text-muted-foreground',
                      )}
                    >
                      {row[col]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* YOLO settings */}
      {effectiveMode === 'yolo' && (
        <>
          {/* Profile selector */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-1">
              YOLO Profile
            </h3>
            <p className="text-xs text-muted-foreground mb-3">
              Preset per-tool configurations. Selecting a profile overrides individual tool settings.
            </p>
            <div role="radiogroup" aria-label="YOLO profile" className="grid grid-cols-4 gap-3">
              <button
                role="radio"
                aria-checked={activeProfile === null}
                onClick={() => selectProfile(null)}
                className={cn(
                  'p-3 rounded-lg border-2 text-left transition-all cursor-pointer',
                  activeProfile === null
                    ? 'border-accent text-accent bg-accent/10'
                    : 'border-border text-muted-foreground hover:bg-accent/5',
                )}
              >
                <p className="text-sm font-semibold">Custom</p>
                <p className="text-xs opacity-70">Manual per-tool</p>
              </button>
              {Object.entries(profiles).map(([name, profile]) => (
                <button
                  key={name}
                  role="radio"
                  aria-checked={activeProfile === name}
                  onClick={() => selectProfile(name)}
                  className={cn(
                    'p-3 rounded-lg border-2 text-left transition-all cursor-pointer',
                    activeProfile === name
                      ? profileColors[name] ?? 'border-accent text-accent bg-accent/10'
                      : 'border-border text-muted-foreground hover:bg-accent/5',
                  )}
                >
                  <p className="text-sm font-semibold capitalize">{name}</p>
                  <p className="text-xs opacity-70">{profile.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Guardrails */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
              YOLO Guardrails
            </h3>
            {thresholdWarning && (
              <p className="text-xs text-warning mb-2">{thresholdWarning}</p>
            )}
            <div className="grid grid-cols-2 gap-4 max-w-lg">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Auto-approve threshold (0.75–0.95)
                </label>
                <input
                  type="number"
                  min={0.75}
                  max={0.95}
                  step={0.05}
                  value={effectiveAutoApprove}
                  onChange={(e) => {
                    const v = Math.min(0.95, Math.max(0.75, Number(e.target.value)));
                    setAutoApprove(v);
                    save({ yolo: { auto_approve_above: v } });
                  }}
                  className={inputCls}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Skip-below threshold (0.50–0.85)
                </label>
                <input
                  type="number"
                  min={0.5}
                  max={0.85}
                  step={0.05}
                  value={effectiveSkipBelow}
                  onChange={(e) => {
                    const v = Math.min(0.85, Math.max(0.5, Number(e.target.value)));
                    setSkipBelow(v);
                    save({ yolo: { skip_and_queue_below: v } });
                  }}
                  className={inputCls}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Max Jira tickets / session
                </label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={effectiveMaxJira}
                  onChange={(e) => {
                    const v = Number(e.target.value);
                    setMaxJira(v);
                    save({ yolo: { max_jira_tickets_per_session: v } });
                  }}
                  className={inputCls}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Max draft approvals / session
                </label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={effectiveMaxDrafts}
                  onChange={(e) => {
                    const v = Number(e.target.value);
                    setMaxDrafts(v);
                    save({ yolo: { max_draft_approvals_per_session: v } });
                  }}
                  className={inputCls}
                />
              </div>
            </div>
          </div>

          {/* Per-tool autonomy grid */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-1">
              Per-Tool Autonomy
            </h3>
            <p className="text-xs text-muted-foreground mb-3">
              {activeProfile
                ? `Using "${activeProfile}" profile. Change any toggle to switch to Custom.`
                : 'Override YOLO behavior per action. Controls what CoCo does automatically vs. asks about.'}
            </p>
            <div className="bg-card border border-border rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    <th className="px-4 py-2 font-medium text-muted-foreground">Action</th>
                    <th className="px-4 py-2 font-medium text-accent text-center">Auto</th>
                    <th className="px-4 py-2 font-medium text-warning text-center">Ask</th>
                    <th className="px-4 py-2 font-medium text-destructive text-center">Always Ask</th>
                  </tr>
                </thead>
                <tbody>
                  {perToolActions.map(({ key, label, defaultLevel }) => {
                    const current = effectivePerTool[key] ?? defaultLevel;
                    const locked = IMMUTABLE_ALWAYS_ASK.has(key);
                    return (
                      <tr key={key} className="border-b border-border/50">
                        <td className="px-4 py-2 text-foreground">
                          {label}
                          {locked && (
                            <span className="ml-1.5 text-[10px] text-muted-foreground">(locked)</span>
                          )}
                        </td>
                        <td colSpan={3} className="px-2 py-2">
                          <div
                            role="radiogroup"
                            aria-label={`Autonomy level for ${label}`}
                            className="flex justify-around"
                          >
                            {(['auto', 'ask', 'always_ask'] as PerToolLevel[]).map((level) => (
                              <button
                                key={level}
                                role="radio"
                                aria-checked={current === level}
                                aria-label={levelLabels[level]}
                                onClick={() => setToolLevel(key, level)}
                                disabled={locked && level !== 'always_ask'}
                                className={cn(
                                  'px-3 py-1 rounded-md text-xs font-medium border transition-all',
                                  locked && level !== 'always_ask'
                                    ? 'border-transparent text-muted-foreground/30 cursor-not-allowed'
                                    : 'cursor-pointer',
                                  current === level
                                    ? levelColors[level]
                                    : !locked || level === 'always_ask'
                                      ? 'border-transparent text-muted-foreground hover:bg-accent/10'
                                      : '',
                                )}
                              >
                                {levelLabels[level]}
                              </button>
                            ))}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Time-aware autonomy */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                  Time-Aware Autonomy
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Adjust confidence thresholds by time of day and deadline proximity.
                </p>
              </div>
              <button
                role="switch"
                aria-checked={effectiveTimeEnabled}
                aria-label="Enable time-aware autonomy"
                onClick={() => {
                  const next = !effectiveTimeEnabled;
                  setTimeAwareEnabled(next);
                  save({ yolo: { time_aware: { enabled: next } } });
                }}
                className={cn(
                  'relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors',
                  effectiveTimeEnabled ? 'bg-accent' : 'bg-border',
                )}
              >
                <span
                  className={cn(
                    'pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-sm transition-transform',
                    effectiveTimeEnabled ? 'translate-x-5' : 'translate-x-0',
                  )}
                />
              </button>
            </div>

            {effectiveTimeEnabled && timeAware?.schedule && (
              <div className="space-y-4">
                <div className="bg-card border border-border rounded-xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left">
                        <th className="px-4 py-2 font-medium text-muted-foreground">Period</th>
                        <th className="px-4 py-2 font-medium text-muted-foreground text-center">Bias</th>
                        <th className="px-4 py-2 font-medium text-muted-foreground text-right">
                          Threshold Adjust
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(timeAware.schedule).map(([period, entry]) => {
                        const bias = biasLabels[entry.bias ?? 'normal'] ?? biasLabels.normal;
                        const adjust = entry.threshold_adjust ?? 0;
                        return (
                          <tr key={period} className="border-b border-border/50">
                            <td className="px-4 py-2 text-foreground">
                              {periodLabels[period] ?? period}
                            </td>
                            <td className={cn('px-4 py-2 text-center text-xs font-medium', bias.color)}>
                              {bias.label}
                            </td>
                            <td className="px-4 py-2 text-right text-xs font-mono text-muted-foreground">
                              {adjust > 0 ? '+' : ''}
                              {adjust.toFixed(2)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                <div className="max-w-xs">
                  <label className="block text-xs font-medium text-muted-foreground mb-1">
                    Deadline proximity (days)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={7}
                    value={effectiveDeadline}
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      setDeadlineProximity(v);
                      save({ yolo: { time_aware: { deadline_proximity_days: v } } });
                    }}
                    className={inputCls}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Within this many days of a deadline, thresholds tighten by +
                    {(timeAware.deadline_threshold_adjust ?? 0.1).toFixed(2)}
                  </p>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
