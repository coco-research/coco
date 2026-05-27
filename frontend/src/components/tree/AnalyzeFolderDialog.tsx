import { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import {
  X, FolderSearch, FileText, Code, Database, Files,
  Loader2, CheckCircle2, XCircle, Clock, AlertCircle,
} from 'lucide-react';
import { apiFetch, apiPost } from '../../lib/api';
import { cn } from '../../lib/utils';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AnalyzeFolderDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  nodeId: string;
  nodeFolderPath: string | null;
  nodeLabel: string;
}

interface ScanPreview {
  path: string;
  exists: boolean;
  files: { name: string; is_dir: boolean; size: number | null; modified: number }[];
}

interface AnalyzeResponse {
  job_id: string;
  node_id: string;
  folder_path: string;
  analysis_type: string;
  status: string;
  file_count: number;
  agent_count: number;
  agent_ids: string[];
}

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
  agents?: AgentStatus[];
}

interface AgentStatus {
  id: string;
  name: string;
  role: string;
  status: string;
  exit_code: number | null;
  started_at: string | null;
  stopped_at: string | null;
  output: string | null;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ANALYSIS_TYPES = [
  { value: 'full', label: 'Full Analysis', desc: 'Comprehensive review by all agents' },
  { value: 'summary', label: 'Summary Only', desc: 'Quick summary of key points' },
  { value: 'extract-actions', label: 'Extract Actions', desc: 'Find TODOs, decisions, action items' },
  { value: 'custom', label: 'Custom', desc: 'Your own instructions' },
] as const;

const FILE_PATTERN_PRESETS = [
  { label: 'Documents', patterns: ['*.md', '*.txt', '*.pdf', '*.docx', '*.rst'], icon: FileText },
  { label: 'Code', patterns: ['*.py', '*.ts', '*.js', '*.tsx', '*.jsx', '*.sql'], icon: Code },
  { label: 'Data', patterns: ['*.json', '*.yaml', '*.yml', '*.csv', '*.xml', '*.toml'], icon: Database },
  { label: 'All', patterns: [], icon: Files },
] as const;

const inputCls = 'w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-colors';

const STATUS_ICONS: Record<string, React.ElementType> = {
  running: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
  killed: XCircle,
  idle: Clock,
  paused: AlertCircle,
};

const STATUS_COLORS: Record<string, string> = {
  running: 'text-blue-400',
  completed: 'text-green-400',
  failed: 'text-red-400',
  killed: 'text-red-400',
  idle: 'text-muted-foreground',
  paused: 'text-yellow-400',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AnalyzeFolderDialog({
  open,
  onOpenChange,
  nodeId,
  nodeFolderPath,
  nodeLabel,
}: AnalyzeFolderDialogProps) {
  const queryClient = useQueryClient();

  // Form state
  const [folderPath, setFolderPath] = useState(nodeFolderPath ?? '');
  const [analysisType, setAnalysisType] = useState<string>('full');
  const [customPrompt, setCustomPrompt] = useState('');
  const [selectedPatternIdx, setSelectedPatternIdx] = useState(3); // "All" by default
  const [maxFiles, setMaxFiles] = useState(50);

  // Job tracking
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setFolderPath(nodeFolderPath ?? '');
      setAnalysisType('full');
      setCustomPrompt('');
      setSelectedPatternIdx(3);
      setMaxFiles(50);
      setActiveJobId(null);
    }
  }, [open, nodeFolderPath]);

  // Folder preview
  const { data: folderPreview } = useQuery<ScanPreview>({
    queryKey: ['tree-folder', nodeId, nodeFolderPath],
    queryFn: () => apiFetch(`/tree/${nodeId}/folder`),
    enabled: open && !!nodeFolderPath,
    staleTime: 10_000,
  });

  // Start analysis mutation
  const startMutation = useMutation<AnalyzeResponse>({
    mutationFn: () => {
      const patterns = FILE_PATTERN_PRESETS[selectedPatternIdx].patterns;
      return apiPost(`/tree/${nodeId}/analyze-folder`, {
        folder_path: folderPath || undefined,
        analysis_type: analysisType,
        custom_prompt: customPrompt || undefined,
        file_patterns: patterns.length > 0 ? patterns : undefined,
        max_files: maxFiles,
      });
    },
    onSuccess: (data) => {
      setActiveJobId(data.job_id);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      queryClient.invalidateQueries({ queryKey: ['analysis-jobs', nodeId] });
    },
  });

  // Poll job status when active
  const { data: activeJob } = useQuery<AnalysisJob>({
    queryKey: ['analysis-job', activeJobId],
    queryFn: () => apiFetch(`/analysis-jobs/${activeJobId}`),
    enabled: !!activeJobId,
    refetchInterval: (query) => {
      const job = query.state.data;
      if (job?.status === 'completed' || job?.status === 'failed') return false;
      return 3000;
    },
  });

  const fileCount = folderPreview?.files?.filter(f => !f.is_dir).length ?? 0;
  const isRunning = startMutation.isPending;

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40 z-40 animate-fade-in" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-lg max-h-[85vh] overflow-y-auto bg-card border border-border rounded-xl shadow-2xl animate-fade-in">
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-accent/20">
                <FolderSearch size={18} className="text-accent" />
              </div>
              <div>
                <Dialog.Title className="text-base font-semibold text-foreground">
                  Analyze Folder
                </Dialog.Title>
                <Dialog.Description className="text-xs text-muted-foreground">
                  {nodeLabel}
                </Dialog.Description>
              </div>
            </div>
            <Dialog.Close className="p-1 rounded-lg hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors">
              <X size={18} />
            </Dialog.Close>
          </div>

          <div className="p-5 space-y-5">
            {!activeJobId ? (
              <>
                {/* Folder path */}
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">Folder Path</label>
                  {nodeFolderPath ? (
                    <div className="bg-muted/50 border border-border rounded-lg px-3 py-2 text-sm font-mono text-foreground truncate">
                      {nodeFolderPath}
                    </div>
                  ) : (
                    <input
                      type="text"
                      value={folderPath}
                      onChange={(e) => setFolderPath(e.target.value)}
                      placeholder="/Users/.../project-folder"
                      className={inputCls}
                    />
                  )}
                  {folderPreview?.exists && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {fileCount} files, {folderPreview.files.filter(f => f.is_dir).length} folders
                    </p>
                  )}
                </div>

                {/* Analysis type */}
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">Analysis Type</label>
                  <div className="grid grid-cols-2 gap-2">
                    {ANALYSIS_TYPES.map((t) => (
                      <button
                        key={t.value}
                        onClick={() => setAnalysisType(t.value)}
                        className={cn(
                          'text-left px-3 py-2.5 rounded-lg border transition-all',
                          analysisType === t.value
                            ? 'border-accent bg-accent/10 text-foreground'
                            : 'border-border bg-card text-muted-foreground hover:border-accent/50'
                        )}
                      >
                        <span className="block text-xs font-medium">{t.label}</span>
                        <span className="block text-[10px] mt-0.5 opacity-70">{t.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Custom prompt (shown for custom type or as additional instructions) */}
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    {analysisType === 'custom' ? 'Custom Instructions' : 'Additional Instructions (optional)'}
                  </label>
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder={analysisType === 'custom'
                      ? 'Tell the agents what to look for...'
                      : 'Any extra guidance for the agents...'}
                    className={cn(inputCls, 'h-20 resize-none')}
                  />
                </div>

                {/* File patterns */}
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">File Types</label>
                  <div className="flex gap-2">
                    {FILE_PATTERN_PRESETS.map((preset, idx) => {
                      const Icon = preset.icon;
                      return (
                        <button
                          key={preset.label}
                          onClick={() => setSelectedPatternIdx(idx)}
                          className={cn(
                            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs transition-all',
                            selectedPatternIdx === idx
                              ? 'border-accent bg-accent/10 text-foreground'
                              : 'border-border text-muted-foreground hover:border-accent/50'
                          )}
                        >
                          <Icon size={12} />
                          {preset.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Max files */}
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    Max Files: {maxFiles}
                  </label>
                  <input
                    type="range"
                    min={10}
                    max={100}
                    step={10}
                    value={maxFiles}
                    onChange={(e) => setMaxFiles(Number(e.target.value))}
                    className="w-full accent-accent"
                  />
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>10</span>
                    <span>100</span>
                  </div>
                </div>

                {/* Error */}
                {startMutation.isError && (
                  <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-sm text-destructive">
                    {(startMutation.error as Error)?.message || 'Failed to start analysis'}
                  </div>
                )}

                {/* Start button */}
                <button
                  onClick={() => startMutation.mutate()}
                  disabled={isRunning || (!folderPath && !nodeFolderPath)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity"
                >
                  {isRunning ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      Starting Analysis...
                    </>
                  ) : (
                    <>
                      <FolderSearch size={14} />
                      Start Analysis
                    </>
                  )}
                </button>
              </>
            ) : (
              /* Active job tracking */
              <JobProgress job={activeJob ?? null} jobId={activeJobId} />
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// ---------------------------------------------------------------------------
// Job Progress sub-component
// ---------------------------------------------------------------------------

function JobProgress({ job }: { job: AnalysisJob | null; jobId: string }) {
  if (!job) {
    return (
      <div className="flex items-center justify-center py-8 gap-2 text-muted-foreground">
        <Loader2 size={16} className="animate-spin" />
        <span className="text-sm">Loading job status...</span>
      </div>
    );
  }

  const isComplete = job.status === 'completed';
  const isFailed = job.status === 'failed';

  return (
    <div className="space-y-4">
      {/* Job header */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs text-muted-foreground">Analysis Job</span>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={cn(
              'inline-block w-2 h-2 rounded-full',
              isComplete ? 'bg-green-400' : isFailed ? 'bg-red-400' : 'bg-blue-400 animate-pulse'
            )} />
            <span className="text-sm font-medium capitalize">{job.status}</span>
          </div>
        </div>
        <div className="text-right text-xs text-muted-foreground">
          <div>{job.file_count} files</div>
          <div>{job.agent_ids?.length ?? 0} agents</div>
        </div>
      </div>

      {/* Agent status cards */}
      {job.agents && job.agents.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-medium text-muted-foreground">Agent Progress</span>
          {job.agents.map((agent) => {
            const StatusIcon = STATUS_ICONS[agent.status] || Clock;
            const statusColor = STATUS_COLORS[agent.status] || 'text-muted-foreground';
            return (
              <div
                key={agent.id}
                className="flex items-center gap-3 p-3 rounded-lg border border-border bg-muted/30"
              >
                <StatusIcon
                  size={16}
                  className={cn(statusColor, agent.status === 'running' && 'animate-spin')}
                />
                <div className="flex-1 min-w-0">
                  <span className="block text-sm font-medium text-foreground truncate">{agent.name}</span>
                  <span className="block text-[10px] text-muted-foreground capitalize">
                    {(agent.role ?? 'custom').replace('-', ' ')}
                  </span>
                </div>
                <span className={cn('text-xs capitalize', statusColor)}>
                  {agent.status}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Completion message */}
      {isComplete && (
        <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-sm text-green-400">
          Analysis complete. View results in the Analysis Results tab below.
        </div>
      )}
    </div>
  );
}
