import { useState, useEffect, useCallback, useRef } from 'react';
import { Activity, ChevronDown, ChevronUp, CheckCircle, XCircle, Loader2, Circle } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useEventSource } from '../../lib/sse';

// ------------- Types -----------------

type StageKey = 'analyze' | 'plan' | 'apply' | 'verify';
type StageStatus = 'pending' | 'active' | 'done' | 'failed';

interface StageInfo {
  key: StageKey;
  label: string;
  status: StageStatus;
  output: string | null;
  startedAt: string | null;
  completedAt: string | null;
}

const INITIAL_STAGES: StageInfo[] = [
  { key: 'analyze', label: 'Analyze', status: 'pending', output: null, startedAt: null, completedAt: null },
  { key: 'plan', label: 'Plan', status: 'pending', output: null, startedAt: null, completedAt: null },
  { key: 'apply', label: 'Apply', status: 'pending', output: null, startedAt: null, completedAt: null },
  { key: 'verify', label: 'Verify', status: 'pending', output: null, startedAt: null, completedAt: null },
];

// Map cycle statuses to our simplified stages
const STATUS_TO_STAGE: Record<string, StageKey> = {
  planning: 'analyze',
  architecting: 'plan',
  developing: 'apply',
  testing: 'verify',
  reviewing: 'verify',
  documenting: 'verify',
};

const DONE_STATUSES = new Set(['completed', 'rejected', 'failed', 'awaiting_approval', 'merging', 'integrating']);

// ------------- Stage Status Icon -----------------

function StageIcon({ status }: { status: StageStatus }) {
  switch (status) {
    case 'done':
      return <CheckCircle size={16} className="text-green-400" />;
    case 'failed':
      return <XCircle size={16} className="text-red-400" />;
    case 'active':
      return <Loader2 size={16} className="text-accent animate-spin" />;
    case 'pending':
    default:
      return <Circle size={16} className="text-muted-foreground/40" />;
  }
}

// ------------- Stage Stepper -----------------

function StageStepper({ stages }: { stages: StageInfo[] }) {
  const [expandedStage, setExpandedStage] = useState<StageKey | null>(null);

  return (
    <div className="space-y-1">
      {/* Horizontal stepper */}
      <div className="flex items-center gap-1 py-2">
        {stages.map((stage, idx) => (
          <div key={stage.key} className="flex items-center gap-1">
            {idx > 0 && (
              <div
                className={cn(
                  'w-8 h-px',
                  stage.status === 'done' || stage.status === 'active' ? 'bg-accent' : 'bg-border',
                )}
              />
            )}
            <button
              onClick={() => setExpandedStage(expandedStage === stage.key ? null : stage.key)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors text-xs',
                stage.status === 'active' && 'bg-accent/10 border border-accent/30',
                stage.status === 'done' && 'bg-green-500/10',
                stage.status === 'failed' && 'bg-red-500/10',
                stage.status === 'pending' && 'bg-muted/30',
                'hover:bg-muted/50',
              )}
            >
              <StageIcon status={stage.status} />
              <span
                className={cn(
                  'font-medium',
                  stage.status === 'active' && 'text-accent',
                  stage.status === 'done' && 'text-green-400',
                  stage.status === 'failed' && 'text-red-400',
                  stage.status === 'pending' && 'text-muted-foreground',
                )}
              >
                {stage.label}
              </span>
              {stage.output && (
                expandedStage === stage.key
                  ? <ChevronUp size={12} className="text-muted-foreground" />
                  : <ChevronDown size={12} className="text-muted-foreground" />
              )}
            </button>
          </div>
        ))}
      </div>

      {/* Expanded detail */}
      {expandedStage && (() => {
        const stage = stages.find((s) => s.key === expandedStage);
        if (!stage?.output) return null;
        return (
          <div className="bg-muted/20 border border-border rounded-lg p-3 mt-1 animate-fade-in">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-foreground">{stage.label} Output</span>
              {stage.startedAt && (
                <span className="text-[10px] text-muted-foreground">
                  {new Date(stage.startedAt).toLocaleTimeString()}
                  {stage.completedAt && ` - ${new Date(stage.completedAt).toLocaleTimeString()}`}
                </span>
              )}
            </div>
            <pre className="text-xs text-muted-foreground font-mono whitespace-pre-wrap leading-relaxed max-h-48 overflow-auto">
              {stage.output}
            </pre>
          </div>
        );
      })()}
    </div>
  );
}

// ------------- Main Component -----------------

interface AgentActivityPanelProps {
  cycleId: string | null;
  cycleStatus: string | null;
}

export function AgentActivityPanel({ cycleId, cycleStatus }: AgentActivityPanelProps) {
  const [stages, setStages] = useState<StageInfo[]>(INITIAL_STAGES);
  const [eventLog, setEventLog] = useState<string[]>([]);
  const [logExpanded, setLogExpanded] = useState(false);
  const stagesRef = useRef(stages);
  stagesRef.current = stages;

  // Derive stage statuses from cycle status
  useEffect(() => {
    if (!cycleStatus) return;

    setStages((prev) => {
      const activeStageKey = STATUS_TO_STAGE[cycleStatus];
      const isDone = DONE_STATUSES.has(cycleStatus);
      const isFailed = cycleStatus === 'failed';

      return prev.map((stage) => {
        if (isDone) {
          // All stages done (or failed on last)
          if (isFailed && stage.key === 'verify') {
            return { ...stage, status: 'failed' as StageStatus };
          }
          return { ...stage, status: 'done' as StageStatus };
        }

        if (!activeStageKey) return stage;

        const stageOrder = INITIAL_STAGES.map((s) => s.key);
        const activeIdx = stageOrder.indexOf(activeStageKey);
        const thisIdx = stageOrder.indexOf(stage.key);

        if (thisIdx < activeIdx) return { ...stage, status: 'done' as StageStatus };
        if (thisIdx === activeIdx) return { ...stage, status: 'active' as StageStatus };
        return { ...stage, status: 'pending' as StageStatus };
      });
    });
  }, [cycleStatus]);

  // SSE event handler
  const handleSSEEvent = useCallback(
    (eventType: string, data: unknown) => {
      if (!eventType.startsWith('self_improve.')) return;

      const payload = data as Record<string, unknown>;
      const logMsg = `[${new Date().toLocaleTimeString()}] ${eventType}: ${JSON.stringify(payload).slice(0, 200)}`;
      setEventLog((prev) => [...prev.slice(-49), logMsg]);

      // Update stage output if present
      if (payload.stage && typeof payload.stage === 'string') {
        const stageKey = payload.stage as StageKey;
        setStages((prev) =>
          prev.map((s) => {
            if (s.key !== stageKey) return s;
            return {
              ...s,
              output: payload.output ? String(payload.output) : s.output,
              startedAt: payload.started_at ? String(payload.started_at) : s.startedAt,
              completedAt: payload.completed_at ? String(payload.completed_at) : s.completedAt,
            };
          }),
        );
      }
    },
    [],
  );

  // Connect to SSE
  const isActive = !!cycleId && !!cycleStatus && !DONE_STATUSES.has(cycleStatus);

  useEventSource('/api/events/stream', {
    enabled: isActive,
    onAnyEvent: handleSSEEvent,
  });

  if (!cycleId || !cycleStatus) return null;
  if (DONE_STATUSES.has(cycleStatus) && eventLog.length === 0) return null;

  return (
    <div className="bg-card rounded-xl border border-border p-5 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-accent" />
          <span className="text-sm font-semibold text-foreground">Agent Activity</span>
          {isActive && (
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              <span className="text-[10px] text-green-400">LIVE</span>
            </span>
          )}
        </div>
      </div>

      <StageStepper stages={stages} />

      {/* Raw event log (collapsible) */}
      {eventLog.length > 0 && (
        <div>
          <button
            onClick={() => setLogExpanded(!logExpanded)}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {logExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            Event Log ({eventLog.length})
          </button>
          {logExpanded && (
            <pre className="mt-2 text-[10px] font-mono text-muted-foreground bg-muted/20 border border-border rounded-lg p-3 max-h-40 overflow-auto leading-relaxed">
              {eventLog.join('\n')}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
