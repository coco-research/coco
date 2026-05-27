import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ChevronDown, ChevronRight, Download, Clock, CheckCircle2,
  Loader2, XCircle, FileText, FolderSearch, ListTodo, FileEdit, Sparkles,
} from 'lucide-react';
import { apiFetch, apiPost } from '../../lib/api';
import { cn, timeAgo } from '../../lib/utils';
import { RichContent } from '../shared/RichContent';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AnalysisJob {
  id: string;
  node_id: string;
  folder_path: string;
  analysis_type: string;
  status: string;
  file_count: number;
  agent_ids: string[];
  results_summary: string | null;
  created_at: string;
  completed_at: string | null;
  agents?: AgentResult[];
}

interface AgentResult {
  id: string;
  name: string;
  role: string;
  status: string;
  output: string | null;
}

interface AnalysisResultsProps {
  nodeId: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_BADGE: Record<string, { color: string; Icon: React.ElementType }> = {
  running: { color: 'bg-blue-500/20 text-blue-400', Icon: Loader2 },
  completed: { color: 'bg-green-500/20 text-green-400', Icon: CheckCircle2 },
  failed: { color: 'bg-red-500/20 text-red-400', Icon: XCircle },
  pending: { color: 'bg-muted text-muted-foreground', Icon: Clock },
  cancelled: { color: 'bg-muted text-muted-foreground', Icon: XCircle },
};

function exportAsMarkdown(job: AnalysisJob) {
  const content = job.results_summary || 'No results available.';
  const header = [
    `# Analysis Results`,
    `**Folder:** \`${job.folder_path}\``,
    `**Type:** ${job.analysis_type}`,
    `**Files:** ${job.file_count}`,
    `**Date:** ${job.completed_at ?? job.created_at}`,
    '',
    '---',
    '',
  ].join('\n');

  const blob = new Blob([header + content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `analysis-${job.id.slice(0, 8)}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export function AnalysisResults({ nodeId }: AnalysisResultsProps) {
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);

  const { data: jobs = [], isLoading } = useQuery<AnalysisJob[]>({
    queryKey: ['analysis-jobs', nodeId],
    queryFn: () => apiFetch(`/analysis-jobs?node_id=${nodeId}`),
    refetchInterval: (query) => {
      const data = query.state.data ?? [];
      return data.some(j => j.status === 'running') ? 3000 : 30000;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
        <Loader2 size={14} className="animate-spin" />
        Loading analysis history...
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="flex flex-col items-center py-6 text-center text-muted-foreground">
        <FolderSearch size={24} className="mb-2 opacity-40" />
        <p className="text-sm">No analyses yet</p>
        <p className="text-xs mt-0.5">Use "Analyze Folder" to scan documents with your agent team.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {jobs.map((job) => (
        <JobCard
          key={job.id}
          job={job}
          expanded={expandedJobId === job.id}
          onToggle={() => setExpandedJobId(expandedJobId === job.id ? null : job.id)}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Job Card
// ---------------------------------------------------------------------------

function JobCard({
  job,
  expanded,
  onToggle,
}: {
  job: AnalysisJob;
  expanded: boolean;
  onToggle: () => void;
}) {
  const badge = STATUS_BADGE[job.status] ?? STATUS_BADGE.pending;
  const BadgeIcon = badge.Icon;

  // For expanded view, fetch full job details (includes agent outputs)
  const { data: fullJob } = useQuery<AnalysisJob>({
    queryKey: ['analysis-job', job.id],
    queryFn: () => apiFetch(`/analysis-jobs/${job.id}`),
    enabled: expanded,
    refetchInterval: expanded && job.status === 'running' ? 3000 : false,
  });

  const displayJob = fullJob ?? job;

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      {/* Header row */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-accent/30 transition-colors text-left"
      >
        {expanded ? (
          <ChevronDown size={14} className="text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight size={14} className="text-muted-foreground shrink-0" />
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground capitalize">
              {job.analysis_type.replace('-', ' ')} Analysis
            </span>
            <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium', badge.color)}>
              <BadgeIcon size={10} className={job.status === 'running' ? 'animate-spin' : ''} />
              {job.status}
            </span>
          </div>
          <div className="flex items-center gap-3 text-[10px] text-muted-foreground mt-0.5">
            <span>{job.file_count} files</span>
            <span>{job.agent_ids?.length ?? 0} agents</span>
            <span>{timeAgo(job.created_at)}</span>
          </div>
        </div>

        {job.status === 'completed' && (
          <button
            onClick={(e) => { e.stopPropagation(); exportAsMarkdown(displayJob); }}
            className="p-1.5 rounded-lg hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors"
            title="Export as Markdown"
          >
            <Download size={14} />
          </button>
        )}
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-border">
          {/* Action bar for completed jobs */}
          {displayJob.status === 'completed' && (
            <AnalysisActions job={displayJob} />
          )}

          {displayJob.agents && displayJob.agents.length > 0 ? (
            <div className="divide-y divide-border">
              {displayJob.agents.map((agent) => (
                <AgentResultSection key={agent.id} agent={agent} />
              ))}
            </div>
          ) : displayJob.results_summary ? (
            <div className="p-4">
              <MarkdownContent text={displayJob.results_summary} />
            </div>
          ) : (
            <div className="p-4 text-sm text-muted-foreground">
              {job.status === 'running' ? 'Analysis in progress...' : 'No results available.'}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Analysis Actions — post-analysis actions (create PRD, extract todos, etc.)
// ---------------------------------------------------------------------------

function AnalysisActions({ job }: { job: AnalysisJob }) {
  const queryClient = useQueryClient();
  const [actionResult, setActionResult] = useState<string | null>(null);

  const extractTodos = useMutation({
    mutationFn: () => apiPost<{ created: number }>(`/analysis-jobs/${job.id}/extract-todos`, {}),
    onSuccess: (data) => {
      setActionResult(`Extracted ${data.created} action items`);
      void queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  const generateDoc = useMutation({
    mutationFn: (docType: string) =>
      apiPost<{ agent_id: string; document_type: string }>(
        `/analysis-jobs/${job.id}/generate-document`,
        { document_type: docType },
      ),
    onSuccess: (data) => {
      setActionResult(`Generating ${data.document_type}... Agent spawned.`);
      void queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  const hasOutput = job.agents?.some(a => a.output && a.output !== 'No output captured.');

  if (!hasOutput) return null;

  return (
    <div className="px-4 py-2.5 border-b border-border bg-muted/20">
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mr-2">Actions</span>

        <button
          onClick={() => extractTodos.mutate()}
          disabled={extractTodos.isPending}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-lg border border-border hover:bg-accent/20 hover:border-accent/30 transition-colors disabled:opacity-50"
        >
          <ListTodo size={12} />
          {extractTodos.isPending ? 'Extracting...' : 'Extract Todos'}
        </button>

        <button
          onClick={() => generateDoc.mutate('prd')}
          disabled={generateDoc.isPending}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-lg border border-border hover:bg-accent/20 hover:border-accent/30 transition-colors disabled:opacity-50"
        >
          <FileEdit size={12} />
          {generateDoc.isPending ? 'Generating...' : 'Generate PRD'}
        </button>

        <button
          onClick={() => generateDoc.mutate('status-report')}
          disabled={generateDoc.isPending}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-lg border border-border hover:bg-accent/20 hover:border-accent/30 transition-colors disabled:opacity-50"
        >
          <FileText size={12} />
          Status Report
        </button>

        <button
          onClick={() => generateDoc.mutate('executive-summary')}
          disabled={generateDoc.isPending}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-lg border border-border hover:bg-accent/20 hover:border-accent/30 transition-colors disabled:opacity-50"
        >
          <Sparkles size={12} />
          Exec Summary
        </button>
      </div>

      {actionResult && (
        <div className="mt-1.5 text-[10px] text-green-400 flex items-center gap-1">
          <CheckCircle2 size={10} /> {actionResult}
        </div>
      )}
      {(extractTodos.isError || generateDoc.isError) && (
        <div className="mt-1.5 text-[10px] text-red-400">
          Action failed. Check agents tab for details.
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Agent Result Section (collapsible)
// ---------------------------------------------------------------------------

function AgentResultSection({ agent }: { agent: AgentResult }) {
  const [open, setOpen] = useState(true);
  const roleLabel = (agent.role ?? 'custom').replace(/-/g, ' ');

  return (
    <div>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-accent/20 transition-colors text-left"
      >
        {open ? (
          <ChevronDown size={12} className="text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight size={12} className="text-muted-foreground shrink-0" />
        )}
        <FileText size={12} className="text-muted-foreground shrink-0" />
        <span className="text-xs font-medium text-foreground capitalize">{roleLabel}</span>
        <span className="text-[10px] text-muted-foreground">({agent.name})</span>
        <span className={cn(
          'ml-auto text-[10px] capitalize',
          agent.status === 'completed' ? 'text-green-400' :
          agent.status === 'failed' ? 'text-red-400' :
          agent.status === 'running' ? 'text-blue-400' :
          'text-muted-foreground'
        )}>
          {agent.status}
        </span>
      </button>

      {open && agent.output && agent.output !== 'No output captured.' && (
        <div className="px-4 pb-4 pl-10">
          <MarkdownContent text={agent.output} />
        </div>
      )}

      {open && (!agent.output || agent.output === 'No output captured.') && agent.status === 'completed' && (
        <div className="px-4 pb-3 pl-10 text-xs text-muted-foreground">
          No output captured.
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Markdown renderer (with mermaid diagram support via RichContent)
// ---------------------------------------------------------------------------

function MarkdownContent({ text }: { text: string }) {
  return (
    <div className="max-h-80 overflow-y-auto">
      <RichContent text={text} mono />
    </div>
  );
}
