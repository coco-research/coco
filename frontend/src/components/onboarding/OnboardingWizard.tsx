import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, ArrowRight, ArrowLeft, Check, Sparkles, FolderOpen, Plug, Bot, Command } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import { cn } from '../../lib/utils';
import type { HomeData, HomeProject } from '../../types/home';

export const ONBOARDING_COMPLETE_KEY = 'coco_onboarding_complete';
export const ONBOARDING_NAME_KEY = 'coco_onboarding_name';
export const ONBOARDING_PROJECTS_KEY = 'coco_onboarding_projects';
export const ONBOARDING_AGENT_KEY = 'coco_onboarding_first_agent';
// Feature flag — Knowledge Hub connect flow is mocked until real OAuth/source onboarding ships.
export const ONBOARDING_KH_CONNECT_REAL = false;

export function isOnboardingComplete(): boolean {
  try {
    return localStorage.getItem(ONBOARDING_COMPLETE_KEY) === 'true';
  } catch {
    return true; // fail-safe: don't block the app if storage is unavailable
  }
}

export function resetOnboarding(): void {
  try {
    localStorage.removeItem(ONBOARDING_COMPLETE_KEY);
    localStorage.removeItem(ONBOARDING_NAME_KEY);
    localStorage.removeItem(ONBOARDING_PROJECTS_KEY);
    localStorage.removeItem(ONBOARDING_AGENT_KEY);
  } catch {
    // ignore
  }
}

interface OnboardingWizardProps {
  open: boolean;
  onClose: () => void;
}

type StepIndex = 0 | 1 | 2 | 3 | 4;

const STEP_TITLES = [
  'Welcome to CoCo',
  'Pick your top 3 projects',
  'Connect Knowledge Hub',
  'Spawn your first agent',
  'Cmd+K — your fastest tool',
];

export default function OnboardingWizard({ open, onClose }: OnboardingWizardProps) {
  const [step, setStep] = useState<StepIndex>(0);
  const [name, setName] = useState('');
  const [selectedProjects, setSelectedProjects] = useState<string[]>([]);
  const [khConnected, setKhConnected] = useState(false);
  const [agentSpawned, setAgentSpawned] = useState(false);

  // Hydrate from any previous partial progress
  useEffect(() => {
    if (!open) return;
    try {
      const savedName = localStorage.getItem(ONBOARDING_NAME_KEY);
      if (savedName) setName(savedName);
      const savedProjects = localStorage.getItem(ONBOARDING_PROJECTS_KEY);
      if (savedProjects) setSelectedProjects(JSON.parse(savedProjects));
    } catch {
      // ignore
    }
  }, [open]);

  // Fetch projects from KH via the home endpoint (already cached on HomePage)
  const { data: homeData } = useQuery<HomeData>({
    queryKey: ['home'],
    queryFn: () => apiFetch<HomeData>('/home'),
    enabled: open,
    staleTime: 60_000,
  });

  const projects: HomeProject[] = useMemo(() => {
    if (!homeData?.projects) return [];
    // Rank by item_count desc so the user sees the busiest projects first.
    return [...homeData.projects].sort((a, b) => b.item_count - a.item_count);
  }, [homeData]);

  if (!open) return null;

  const toggleProject = (id: string) => {
    setSelectedProjects((prev) => {
      if (prev.includes(id)) return prev.filter((p) => p !== id);
      if (prev.length >= 3) return prev; // cap at 3
      return [...prev, id];
    });
  };

  const canAdvance = (() => {
    switch (step) {
      case 0:
        return name.trim().length > 0;
      case 1:
        return selectedProjects.length > 0 && selectedProjects.length <= 3;
      case 2:
        return khConnected; // mocked accept
      case 3:
        return agentSpawned;
      case 4:
        return true;
      default:
        return false;
    }
  })();

  const finish = () => {
    try {
      localStorage.setItem(ONBOARDING_COMPLETE_KEY, 'true');
      if (name.trim()) localStorage.setItem(ONBOARDING_NAME_KEY, name.trim());
      localStorage.setItem(ONBOARDING_PROJECTS_KEY, JSON.stringify(selectedProjects));
      if (agentSpawned) localStorage.setItem(ONBOARDING_AGENT_KEY, 'Daily Briefing');
    } catch {
      // best-effort persistence
    }
    onClose();
  };

  const skip = () => {
    try {
      localStorage.setItem(ONBOARDING_COMPLETE_KEY, 'true');
    } catch {
      // ignore
    }
    onClose();
  };

  const next = () => {
    if (step >= 4) {
      finish();
      return;
    }
    setStep((s) => Math.min(4, (s + 1)) as StepIndex);
  };

  const back = () => {
    setStep((s) => Math.max(0, (s - 1)) as StepIndex);
  };

  const triggerCommandPalette = () => {
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4"
    >
      <div className="relative w-full max-w-xl rounded-2xl border border-border bg-card shadow-2xl">
        {/* Close / skip */}
        <button
          onClick={skip}
          className="absolute top-3 right-3 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Skip onboarding"
        >
          <X size={18} />
        </button>

        {/* Progress dots */}
        <div className="flex gap-1.5 px-6 pt-6">
          {STEP_TITLES.map((_, i) => (
            <span
              key={i}
              className={cn(
                'h-1 flex-1 rounded-full transition-colors',
                i <= step ? 'bg-accent' : 'bg-border',
              )}
            />
          ))}
        </div>

        <div className="px-6 pt-5 pb-6 space-y-5 min-h-[340px]">
          <header className="space-y-1">
            <p className="text-[11px] uppercase tracking-wider text-muted-foreground">
              Step {step + 1} of 5
            </p>
            <h2 id="onboarding-title" className="text-xl font-semibold text-foreground">
              {STEP_TITLES[step]}
            </h2>
          </header>

          {step === 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-muted-foreground">
                <Sparkles size={18} className="text-accent" />
                <p className="text-sm">
                  CoCo helps you keep your projects, todos, and Knowledge Hub in sync.
                  Let&apos;s set up the basics.
                </p>
              </div>
              <label className="block">
                <span className="text-xs font-medium text-foreground">What should we call you?</span>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  className="mt-1.5 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                  autoFocus
                />
              </label>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-muted-foreground">
                <FolderOpen size={18} className="text-accent" />
                <p className="text-sm">
                  Choose up to 3 projects to track on your dashboard.
                </p>
              </div>
              <div className="max-h-56 overflow-y-auto rounded-md border border-border divide-y divide-border">
                {projects.length === 0 && (
                  <div className="px-3 py-6 text-sm text-muted-foreground text-center">
                    No projects found in Knowledge Hub yet.
                  </div>
                )}
                {projects.slice(0, 12).map((p) => {
                  const checked = selectedProjects.includes(p.id);
                  const disabled = !checked && selectedProjects.length >= 3;
                  return (
                    <button
                      key={p.id}
                      onClick={() => toggleProject(p.id)}
                      disabled={disabled}
                      className={cn(
                        'flex w-full items-center justify-between px-3 py-2 text-left transition-colors',
                        checked ? 'bg-accent/20' : 'hover:bg-accent/10',
                        disabled && 'opacity-40 cursor-not-allowed',
                      )}
                    >
                      <div>
                        <p className="text-sm font-medium text-foreground">{p.name}</p>
                        <p className="text-[11px] text-muted-foreground">
                          {p.item_count} items · {p.todo_open} open todos
                        </p>
                      </div>
                      <span
                        className={cn(
                          'h-4 w-4 rounded border flex items-center justify-center',
                          checked ? 'bg-accent border-accent' : 'border-border',
                        )}
                      >
                        {checked && <Check size={12} className="text-accent-foreground" />}
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="text-[11px] text-muted-foreground">
                {selectedProjects.length}/3 selected
              </p>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-muted-foreground">
                <Plug size={18} className="text-accent" />
                <p className="text-sm">
                  Connect a Knowledge Hub source so CoCo can sync your emails, docs, and tickets.
                </p>
              </div>
              <div className="rounded-md border border-border bg-background p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground">Knowledge Hub</p>
                    <p className="text-[11px] text-muted-foreground">
                      {ONBOARDING_KH_CONNECT_REAL
                        ? 'Authorize CoCo to read your Knowledge Hub.'
                        : 'Mock connection — real OAuth flow is coming soon.'}
                    </p>
                  </div>
                  {khConnected ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-success">
                      <Check size={12} /> Connected
                    </span>
                  ) : (
                    <button
                      onClick={() => setKhConnected(true)}
                      className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-accent-foreground hover:bg-accent/80 transition-colors"
                    >
                      Connect
                    </button>
                  )}
                </div>
                {!ONBOARDING_KH_CONNECT_REAL && (
                  <p className="text-[11px] text-muted-foreground italic">
                    Flag: <code className="font-mono">ONBOARDING_KH_CONNECT_REAL=false</code>
                  </p>
                )}
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-muted-foreground">
                <Bot size={18} className="text-accent" />
                <p className="text-sm">
                  Agents run on a schedule and do work for you. We recommend starting with one.
                </p>
              </div>
              <div className="rounded-md border border-border bg-background p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-foreground">Daily Briefing</p>
                    <p className="text-[11px] text-muted-foreground">
                      Summarizes overnight activity and your top priorities every morning.
                    </p>
                  </div>
                  {agentSpawned ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-success">
                      <Check size={12} /> Spawned
                    </span>
                  ) : (
                    <button
                      onClick={() => setAgentSpawned(true)}
                      className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-accent-foreground hover:bg-accent/80 transition-colors"
                    >
                      Spawn
                    </button>
                  )}
                </div>
              </div>
              <p className="text-[11px] text-muted-foreground">
                You can add more agents anytime from the Agents page.
              </p>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 text-muted-foreground">
                <Command size={18} className="text-accent" />
                <p className="text-sm">
                  Hit <kbd className="rounded border border-border px-1.5 py-0.5 font-mono text-[11px] text-foreground">Cmd</kbd>{' '}
                  + <kbd className="rounded border border-border px-1.5 py-0.5 font-mono text-[11px] text-foreground">K</kbd>{' '}
                  anywhere to jump to projects, todos, or run agents.
                </p>
              </div>
              <button
                onClick={triggerCommandPalette}
                className="w-full rounded-md border border-border bg-background px-4 py-3 text-left text-sm text-muted-foreground hover:border-accent hover:text-foreground transition-colors"
              >
                Try it now — open the command palette
              </button>
              <p className="text-[11px] text-muted-foreground">
                You&apos;re all set, {name.trim() || 'friend'}. Click finish to start using CoCo.
              </p>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-between border-t border-border px-6 py-3">
          <button
            onClick={skip}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Skip
          </button>
          <div className="flex items-center gap-2">
            {step > 0 && (
              <button
                onClick={back}
                className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-accent/30 transition-colors"
              >
                <ArrowLeft size={12} /> Back
              </button>
            )}
            <button
              onClick={next}
              disabled={!canAdvance}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
                canAdvance
                  ? 'bg-accent text-accent-foreground hover:bg-accent/80'
                  : 'bg-muted text-muted-foreground cursor-not-allowed',
              )}
            >
              {step === 4 ? 'Finish' : 'Next'} <ArrowRight size={12} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
