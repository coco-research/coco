import { useState } from 'react';
import { FileCode, Check, X, ChevronDown, ChevronUp, ShieldCheck, ShieldAlert, TestTube, AlertTriangle } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiPost } from '../../lib/api';
import { cn } from '../../lib/utils';
import { useToast } from '../shared/Toast';
import { DiffViewer } from './DiffViewer';
import type { Improvement, GateResult } from '../../types/self-improve';

const CATEGORY_COLORS: Record<Improvement['category'], { bg: string; text: string }> = {
  performance: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
  ux: { bg: 'bg-purple-500/20', text: 'text-purple-400' },
  tests: { bg: 'bg-green-500/20', text: 'text-green-400' },
  refactor: { bg: 'bg-orange-500/20', text: 'text-orange-400' },
  feature: { bg: 'bg-cyan-500/20', text: 'text-cyan-400' },
  docs: { bg: 'bg-zinc-500/20', text: 'text-zinc-400' },
};

const STATUS_LABELS: Record<string, { label: string; color: string; pulse?: boolean }> = {
  proposed: { label: 'Proposed', color: 'bg-zinc-500' },
  approved: { label: 'Approved', color: 'bg-blue-400' },
  in_progress: { label: 'In Progress', color: 'bg-yellow-400', pulse: true },
  testing: { label: 'Testing', color: 'bg-amber-400', pulse: true },
  review: { label: 'Review', color: 'bg-violet-400', pulse: true },
  documenting: { label: 'Documenting', color: 'bg-indigo-400', pulse: true },
  awaiting_approval: { label: 'Awaiting Approval', color: 'bg-amber-400' },
  approved_by_human: { label: 'Approved', color: 'bg-green-400' },
  rejected_by_human: { label: 'Rejected', color: 'bg-red-400' },
  merged: { label: 'Merged', color: 'bg-green-400' },
  failed: { label: 'Failed', color: 'bg-red-400' },
};

export function ImprovementCard({ improvement, highlight }: { improvement: Improvement; highlight?: boolean }) {
  const qc = useQueryClient();
  const { toast } = useToast();
  const [diffOpen, setDiffOpen] = useState(false);
  const [reviewExpanded, setReviewExpanded] = useState(false);

  const approveMutation = useMutation({
    mutationFn: () => apiPost(`/self-improve/improvements/${improvement.id}/approve`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['self-improve'] });
      toast({ title: 'Improvement approved', description: improvement.title });
    },
    onError: (err) => toast({ title: 'Approve failed', description: String(err), variant: 'destructive' }),
  });

  const rejectMutation = useMutation({
    mutationFn: () => apiPost(`/self-improve/improvements/${improvement.id}/reject`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['self-improve'] });
      toast({ title: 'Improvement rejected', description: improvement.title });
    },
    onError: (err) => toast({ title: 'Reject failed', description: String(err), variant: 'destructive' }),
  });

  const statusInfo = STATUS_LABELS[improvement.status] ?? { label: improvement.status, color: 'bg-zinc-500' };
  const catColor = CATEGORY_COLORS[improvement.category];
  const isAwaitingApproval = improvement.status === 'awaiting_approval';

  return (
    <>
      <div
        className={cn(
          'bg-card rounded-xl border p-5 transition-all',
          highlight ? 'border-amber-400/50 shadow-amber-400/10 shadow-lg' : 'border-border hover:shadow-md',
        )}
      >
        {/* Header */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-muted-foreground font-mono">#{improvement.priority}</span>
          <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium uppercase', catColor.bg, catColor.text)}>
            {improvement.category}
          </span>
          <div className="ml-auto flex items-center gap-1.5">
            <span className={cn('w-2 h-2 rounded-full inline-block', statusInfo.color, statusInfo.pulse && 'animate-pulse')} />
            <span className="text-xs text-muted-foreground">{statusInfo.label}</span>
          </div>
        </div>

        {/* Title & description */}
        <h3 className="text-sm font-semibold text-foreground mb-1">{improvement.title}</h3>
        <p className="text-xs text-muted-foreground leading-relaxed mb-4 line-clamp-3">{improvement.description}</p>

        {/* Meta: branch + diff stats */}
        {(improvement.branch_name || improvement.diff_stat) && (
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground mb-4">
            {improvement.branch_name && (
              <span className="font-mono bg-muted/50 px-1.5 py-0.5 rounded">{improvement.branch_name}</span>
            )}
            {improvement.diff_stat && <span>{improvement.diff_stat}</span>}
          </div>
        )}

        {/* Test results */}
        {improvement.test_results && (
          <div className="rounded-lg bg-muted/30 border border-border p-3 mb-3">
            <div className="flex items-center gap-2 text-xs">
              <TestTube size={14} className="text-muted-foreground" />
              <span className="font-medium text-foreground">Test Results</span>
              <span className="ml-auto flex items-center gap-3">
                <span className="text-green-400">{improvement.test_results.passed} passed</span>
                {improvement.test_results.failed > 0 && (
                  <span className="text-red-400">{improvement.test_results.failed} failed</span>
                )}
                {improvement.test_results.errors > 0 && (
                  <span className="text-red-400">{improvement.test_results.errors} errors</span>
                )}
              </span>
            </div>
          </div>
        )}

        {/* Security scan */}
        {improvement.security_scan && (
          <div className="rounded-lg bg-muted/30 border border-border p-3 mb-3">
            <div className="flex items-center gap-2 text-xs">
              {improvement.security_scan.passed ? (
                <>
                  <ShieldCheck size={14} className="text-green-400" />
                  <span className="text-green-400 font-medium">No issues found</span>
                </>
              ) : (
                <>
                  <ShieldAlert size={14} className="text-red-400" />
                  <span className="text-red-400 font-medium">{improvement.security_scan.issues.length} issue(s)</span>
                </>
              )}
            </div>
            {!improvement.security_scan.passed && improvement.security_scan.issues.length > 0 && (
              <ul className="mt-2 space-y-1 text-xs text-red-400/80">
                {improvement.security_scan.issues.map((issue, i) => (
                  <li key={i} className="flex items-start gap-1">
                    <span className="shrink-0 mt-0.5">-</span>
                    <span>{issue}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* Gate results (issues list) */}
        {improvement.gate_results && improvement.gate_results.length > 0 && (
          <div className="space-y-2 mb-3">
            {improvement.gate_results
              .filter((gr: GateResult) => gr.verdict !== 'pass')
              .map((gr: GateResult, gIdx: number) => {
                const failedChecks = gr.checks.filter((c) => !c.passed);
                if (failedChecks.length === 0) return null;
                return (
                  <div key={gIdx} className="rounded-lg bg-muted/30 border border-border p-3">
                    <div className="flex items-center gap-2 text-xs mb-2">
                      <AlertTriangle size={14} className={gr.verdict === 'fail' ? 'text-red-400' : 'text-yellow-400'} />
                      <span className={cn('font-medium', gr.verdict === 'fail' ? 'text-red-400' : 'text-yellow-400')}>
                        {gr.gate} — {gr.verdict === 'fail' ? 'Failed' : 'Warning'}
                      </span>
                      {gr.retry_count > 0 && (
                        <span className="text-muted-foreground ml-auto">retry {gr.retry_count}</span>
                      )}
                    </div>
                    <ul className="space-y-1 text-xs text-muted-foreground">
                      {failedChecks.map((c, cIdx) => (
                        <li key={cIdx} className="flex items-start gap-1">
                          <span className={cn('shrink-0 mt-0.5', c.severity === 'error' ? 'text-red-400' : 'text-yellow-400')}>-</span>
                          <span>{c.message}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
          </div>
        )}

        {/* Review notes (collapsible) */}
        {improvement.review_notes && (
          <div className="mb-3">
            <button
              onClick={() => setReviewExpanded(!reviewExpanded)}
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              {reviewExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              Review Notes
            </button>
            {reviewExpanded && (
              <div className="mt-2 text-xs text-muted-foreground bg-muted/30 border border-border rounded-lg p-3 leading-relaxed whitespace-pre-wrap">
                {improvement.review_notes}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-2 border-t border-border">
          <button
            onClick={() => setDiffOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          >
            <FileCode size={14} />
            View Diff
          </button>

          {isAwaitingApproval && (
            <>
              <div className="ml-auto flex items-center gap-2">
                <button
                  onClick={() => rejectMutation.mutate()}
                  disabled={rejectMutation.isPending}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-50"
                >
                  <X size={14} />
                  Reject
                </button>
                <button
                  onClick={() => approveMutation.mutate()}
                  disabled={approveMutation.isPending}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors disabled:opacity-50"
                >
                  <Check size={14} />
                  Approve
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      <DiffViewer
        improvementId={improvement.id}
        title={improvement.title}
        open={diffOpen}
        onOpenChange={setDiffOpen}
      />
    </>
  );
}
