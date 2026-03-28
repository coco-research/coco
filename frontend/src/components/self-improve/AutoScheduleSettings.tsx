import { useState, useEffect } from 'react';
import { Settings, ChevronDown, ChevronUp, Save, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

// ------------- Types -----------------

interface Preferences {
  auto_enabled: boolean;
  cron_expression: string;
  max_cost_per_cycle: number;
  focus_areas: string[];
}

const DEFAULT_PREFS: Preferences = {
  auto_enabled: false,
  cron_expression: '0 3 * * 1',
  max_cost_per_cycle: 5.0,
  focus_areas: [],
};

const CRON_PRESETS: { label: string; cron: string }[] = [
  { label: 'Weekly Monday 3AM', cron: '0 3 * * 1' },
  { label: 'Daily 2AM', cron: '0 2 * * *' },
  { label: 'Bi-weekly Sunday 4AM', cron: '0 4 * * 0/2' },
  { label: 'Monthly 1st 3AM', cron: '0 3 1 * *' },
];

const FOCUS_OPTIONS = [
  { value: 'performance', label: 'Performance' },
  { value: 'ux', label: 'UX' },
  { value: 'tests', label: 'Tests' },
  { value: 'refactor', label: 'Refactor' },
  { value: 'feature', label: 'Features' },
  { value: 'docs', label: 'Docs' },
];

// ------------- Component -----------------

export function AutoScheduleSettings() {
  const [expanded, setExpanded] = useState(false);
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load preferences on mount
  useEffect(() => {
    fetch('/api/self-improve/preferences')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load preferences');
        return res.json();
      })
      .then((data: Preferences) => {
        setPrefs(data);
        setLoading(false);
      })
      .catch(() => {
        // Use defaults on error
        setLoading(false);
      });
  }, []);

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSaved(false);

    try {
      const res = await fetch('/api/self-improve/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prefs),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || 'Failed to save');
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  }

  function toggleFocus(area: string) {
    setPrefs((prev) => ({
      ...prev,
      focus_areas: prev.focus_areas.includes(area)
        ? prev.focus_areas.filter((a) => a !== area)
        : [...prev.focus_areas, area],
    }));
  }

  function selectPreset(cron: string) {
    setPrefs((prev) => ({ ...prev, cron_expression: cron }));
  }

  const activePreset = CRON_PRESETS.find((p) => p.cron === prefs.cron_expression);

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden">
      {/* Collapsed header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Settings size={16} className="text-muted-foreground" />
          <span className="text-sm font-semibold text-foreground">Auto-Schedule</span>
          {prefs.auto_enabled && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-500/20 text-green-400">
              ON
            </span>
          )}
          {!prefs.auto_enabled && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-zinc-500/20 text-zinc-400">
              OFF
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {activePreset && (
            <span className="text-xs text-muted-foreground">{activePreset.label}</span>
          )}
          {expanded ? (
            <ChevronUp size={16} className="text-muted-foreground" />
          ) : (
            <ChevronDown size={16} className="text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Expanded settings */}
      {expanded && (
        <div className="px-5 pb-5 space-y-5 border-t border-border pt-4">
          {loading ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 size={20} className="animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {/* Enable toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-foreground">Enable auto self-improvement</div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    Automatically run improvement cycles on a schedule
                  </div>
                </div>
                <button
                  onClick={() => setPrefs((p) => ({ ...p, auto_enabled: !p.auto_enabled }))}
                  className={cn(
                    'relative w-11 h-6 rounded-full transition-colors',
                    prefs.auto_enabled ? 'bg-accent' : 'bg-muted',
                  )}
                  role="switch"
                  aria-checked={prefs.auto_enabled}
                >
                  <span
                    className={cn(
                      'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
                      prefs.auto_enabled && 'translate-x-5',
                    )}
                  />
                </button>
              </div>

              {/* Schedule presets */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Schedule</label>
                <div className="flex flex-wrap gap-2">
                  {CRON_PRESETS.map((preset) => (
                    <button
                      key={preset.cron}
                      onClick={() => selectPreset(preset.cron)}
                      className={cn(
                        'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border',
                        prefs.cron_expression === preset.cron
                          ? 'bg-accent/20 text-accent border-accent/40'
                          : 'bg-muted/50 text-muted-foreground border-border hover:border-accent/30',
                      )}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
                {/* Custom cron input */}
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={prefs.cron_expression}
                    onChange={(e) => setPrefs((p) => ({ ...p, cron_expression: e.target.value }))}
                    className="flex-1 px-3 py-1.5 rounded-lg bg-muted/50 border border-border text-xs font-mono text-foreground focus:outline-none focus:border-accent/50"
                    placeholder="0 3 * * 1"
                  />
                  <span className="text-[10px] text-muted-foreground shrink-0">cron</span>
                </div>
              </div>

              {/* Max cost */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Max cost per cycle: <span className="text-accent">${prefs.max_cost_per_cycle.toFixed(2)}</span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={25}
                  step={0.5}
                  value={prefs.max_cost_per_cycle}
                  onChange={(e) => setPrefs((p) => ({ ...p, max_cost_per_cycle: parseFloat(e.target.value) }))}
                  className="w-full accent-accent h-2 rounded-lg appearance-none bg-muted cursor-pointer"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>$1.00</span>
                  <span>$25.00</span>
                </div>
              </div>

              {/* Focus areas */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Focus areas <span className="text-muted-foreground font-normal">(optional)</span>
                </label>
                <div className="flex flex-wrap gap-2">
                  {FOCUS_OPTIONS.map((opt) => (
                    <label
                      key={opt.value}
                      className={cn(
                        'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-colors border',
                        prefs.focus_areas.includes(opt.value)
                          ? 'bg-accent/20 text-accent border-accent/40'
                          : 'bg-muted/50 text-muted-foreground border-border hover:border-accent/30',
                      )}
                    >
                      <input
                        type="checkbox"
                        checked={prefs.focus_areas.includes(opt.value)}
                        onChange={() => toggleFocus(opt.value)}
                        className="sr-only"
                      />
                      <span
                        className={cn(
                          'w-3.5 h-3.5 rounded border flex items-center justify-center shrink-0',
                          prefs.focus_areas.includes(opt.value)
                            ? 'bg-accent border-accent'
                            : 'border-muted-foreground/40',
                        )}
                      >
                        {prefs.focus_areas.includes(opt.value) && (
                          <svg width="8" height="6" viewBox="0 0 8 6" fill="none">
                            <path d="M1 3L3 5L7 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        )}
                      </span>
                      {opt.label}
                    </label>
                  ))}
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-lg bg-red-500/10 border border-red-500/30 p-3 text-xs text-red-400">
                  {error}
                </div>
              )}

              {/* Save button */}
              <div className="flex justify-end">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                    saved
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-accent text-accent-foreground hover:opacity-90',
                    saving && 'opacity-50',
                  )}
                >
                  {saving ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : saved ? (
                    <>
                      <Save size={14} />
                      Saved
                    </>
                  ) : (
                    <>
                      <Save size={14} />
                      Save Settings
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
